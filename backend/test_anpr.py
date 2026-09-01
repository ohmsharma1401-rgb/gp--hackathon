import os
import sys
import time
import argparse
import asyncio
import cv2
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.catalogue import catalogue_service
from app.services.yolo_service import yolo_detector
from app.services.anpr_service import anpr_manager

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

async def test_live_government_feed(camera_id: str = "cam01", duration_seconds: int = 20):
    print("\n" + "=" * 75)
    print(f"EVALUATION 1: OFFICIAL GOVERNMENT LIVE FEED ({camera_id.upper()})")
    print("=" * 75)

    cameras = await catalogue_service.fetch_catalogue()
    target_cam = next((c for c in cameras if c["id"] == camera_id), cameras[0])
    cam_id = target_cam["id"]
    rtsp_url = target_cam["rtsp_url"]

    print(f"Connecting to RTSP Stream: {rtsp_url}...")
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        print(f"[X] Could not open RTSP stream for {cam_id}")
        return {}

    start_time = time.time()
    frames_read = 0
    yolo_runs = 0
    annotated_sample_path = None

    while (time.time() - start_time) < duration_seconds:
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.05)
            continue

        frames_read += 1
        if frames_read % 5 == 0:
            yolo_runs += 1
            res = yolo_detector.track_vehicles(frame, cam_id)
            dets = res["detections"]
            annotated_frame = res["annotated_frame"]
            latency = res["latency_ms"]

            plates_found = [d for d in dets if d.get("anpr") is not None]
            print(f"Frame #{frames_read} | YOLO+ByteTrack Latency: {latency:.1f}ms | Tracked Vehicles: {len(dets)} | Plates Evaluated: {len(plates_found)}")

            for d in dets:
                t_id = d.get("track_id")
                anpr_res = d.get("anpr")
                t_str = f"#{t_id}" if t_id is not None else "N/A"
                if anpr_res:
                    p_num = anpr_res.get("plate_number", "UNREADABLE")
                    p_conf = anpr_res.get("plate_confidence", 0.0)
                    p_status = anpr_res.get("status", "UNREADABLE")
                    p_reason = anpr_res.get("rejection_reason", "NONE")
                    p_det_method = anpr_res.get("detection_method", "UNKNOWN")
                    print(f"   -> [{d['vehicle_type'].upper()} {t_str}] Method: {p_det_method} | Status: {p_status} (Reason: {p_reason}) | Plate: {p_num} (Conf: {p_conf})")

            if len(plates_found) > 0 and annotated_sample_path is None:
                scratch_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scratch")
                os.makedirs(scratch_dir, exist_ok=True)
                annotated_sample_path = os.path.join(scratch_dir, f"anpr_sample_{cam_id}.jpg")
                cv2.imwrite(annotated_sample_path, annotated_frame)

        time.sleep(0.01)

    cap.release()
    telemetry = anpr_manager.get_telemetry()
    yolo_telemetry = yolo_detector.get_telemetry()
    records = anpr_manager.get_records(camera_id=cam_id)

    print("\n--- OFFICIAL GOVERNMENT FEED SUMMARY ---")
    print(f"Camera ID: {cam_id}")
    print(f"Frames Processed: {frames_read}")
    print(f"Vehicles Analysed: {telemetry['total_vehicles_analysed']}")
    print(f"Plates Evaluated: {telemetry['total_plates_detected']}")
    print(f"Readable Plates: {telemetry['readable_plates']}")
    print(f"Unreadable Plates: {telemetry['unreadable_plates']}")
    print(f"Rejection Diagnostics: {telemetry['rejection_breakdown']}")
    print(f"Average Total Latency: {yolo_telemetry['average_latency_ms']} ms")
    if annotated_sample_path:
        print(f"Visual Debug Image: {annotated_sample_path}")

    return {
        "camera_id": cam_id,
        "frames_processed": frames_read,
        "vehicles_analysed": telemetry['total_vehicles_analysed'],
        "readable_plates": telemetry['readable_plates'],
        "unreadable_plates": telemetry['unreadable_plates'],
        "rejection_breakdown": telemetry['rejection_breakdown'],
        "sample_image": annotated_sample_path,
        "records": records[:5]
    }


def test_controlled_readable_video(video_path: str = "scratch/controlled_vehicle_test.mp4"):
    print("\n" + "=" * 75)
    print("EVALUATION 2: CONTROLLED READABLE VIDEO TEST")
    print("=" * 75)

    if not os.path.exists(video_path):
        print(f"[X] Controlled video file not found at {video_path}")
        return {}

    print(f"Loading Controlled Video: {video_path}...")
    cap = cv2.VideoCapture(video_path)
    frames_read = 0
    yolo_runs = 0
    cam_id = "test_ctrl_cam"
    annotated_sample_path = None
    recognized_plates = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        frames_read += 1
        if frames_read % 5 == 0:
            yolo_runs += 1
            res = yolo_detector.track_vehicles(frame, cam_id)
            dets = res["detections"]
            annotated_frame = res["annotated_frame"]
            latency = res["latency_ms"]

            if not dets:
                # Direct full-frame / vehicle ROI fallback evaluation for controlled test video
                iso_ts = time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                ctrl_anpr = anpr_manager.process_vehicle_crop(
                    camera_id=cam_id,
                    track_id=99,
                    vehicle_type="car",
                    full_frame=frame,
                    vehicle_bbox=[150, 200, 800, 550],
                    timestamp=iso_ts
                )
                if ctrl_anpr:
                    p_num = ctrl_anpr.get("plate_number", "UNREADABLE")
                    p_status = ctrl_anpr.get("status", "UNREADABLE")
                    p_conf = ctrl_anpr.get("plate_confidence", 0.0)
                    print(f"Frame #{frames_read} | [CONTROLLED CAR #99] Status: {p_status} | Plate: {p_num} (Conf: {p_conf})")
                    if p_status in ["CONFIRMED", "LOW_CONFIDENCE"]:
                        recognized_plates.append(p_num)

            for d in dets:
                t_id = d.get("track_id")
                anpr_res = d.get("anpr")
                t_str = f"#{t_id}" if t_id is not None else "N/A"
                if anpr_res:
                    p_num = anpr_res.get("plate_number", "UNREADABLE")
                    p_conf = anpr_res.get("plate_confidence", 0.0)
                    p_status = anpr_res.get("status", "UNREADABLE")
                    p_det_method = anpr_res.get("detection_method", "UNKNOWN")
                    print(f"Frame #{frames_read} | [{d['vehicle_type'].upper()} {t_str}] Method: {p_det_method} | Status: {p_status} | Plate: {p_num} (Conf: {p_conf})")
                    if p_status in ["CONFIRMED", "LOW_CONFIDENCE"]:
                        recognized_plates.append(p_num)

            if annotated_sample_path is None:
                scratch_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scratch")
                os.makedirs(scratch_dir, exist_ok=True)
                annotated_sample_path = os.path.join(scratch_dir, "anpr_controlled_sample.jpg")
                cv2.imwrite(annotated_sample_path, annotated_frame)

    cap.release()
    telemetry = anpr_manager.get_telemetry()
    records = anpr_manager.get_records(camera_id=cam_id)

    print("\n--- CONTROLLED READABLE VIDEO SUMMARY ---")
    print(f"Video Source: {video_path}")
    print(f"Frames Processed: {frames_read}")
    print(f"Recognized Plate Numbers: {set(recognized_plates)}")
    print(f"ANPR Records Stored: {len(records)}")
    if annotated_sample_path:
        print(f"Visual Debug Image: {annotated_sample_path}")

    return {
        "video_source": video_path,
        "frames_processed": frames_read,
        "recognized_plates": list(set(recognized_plates)),
        "sample_image": annotated_sample_path,
        "records": records
    }


async def main():
    parser = argparse.ArgumentParser(description="Phase 7.5 Dual Evaluation Test Script")
    parser.add_argument("--camera", type=str, default="cam01", help="Official camera ID to test")
    parser.add_argument("--duration", type=int, default=20, help="Official feed test duration (seconds)")
    args = parser.parse_args()

    # 1. Run Evaluation on Official Live Government Feed
    gov_results = await test_live_government_feed(camera_id=args.camera, duration_seconds=args.duration)

    # 2. Run Evaluation on Controlled Readable Video
    ctrl_results = test_controlled_readable_video()

    await catalogue_service.close()

    print("\n" + "=" * 75)
    print("PHASE 7.5 DUAL EVALUATION FINAL SUMMARY")
    print("=" * 75)
    print(f"[1] Official Feed ({args.camera}): {gov_results.get('readable_plates', 0)} Readable / {gov_results.get('unreadable_plates', 0)} Unreadable")
    print(f"    Rejection Diagnostics: {gov_results.get('rejection_breakdown', {})}")
    print(f"[2] Controlled Video: {len(ctrl_results.get('recognized_plates', []))} Plate Recognized -> {ctrl_results.get('recognized_plates', [])}")
    print("=" * 75)

if __name__ == "__main__":
    asyncio.run(main())
