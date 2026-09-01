import os
import sys
import time
import argparse
import asyncio
import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.catalogue import catalogue_service
from app.services.yolo_service import yolo_detector
from app.services.track_manager import track_manager

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

async def test_vehicle_tracking_on_live_camera(camera_id: str = "cam01", duration_seconds: int = 20):
    print("=" * 65)
    print("PHASE 6 — REAL-TIME MULTI-OBJECT VEHICLE TRACKING TEST")
    print("=" * 65)

    telemetry = yolo_detector.get_telemetry()
    print(f"[1] YOLO Model: {telemetry['model_name']} | Tracker: {telemetry['tracker']}")
    print(f"[2] Computation Device: {telemetry['device_name']} ({telemetry['device']})")
    print(f"    CUDA Available: {telemetry['cuda_available']}")

    # Fetch camera catalogue
    cameras = await catalogue_service.fetch_catalogue()
    target_cam = next((c for c in cameras if c["id"] == camera_id), cameras[0])
    cam_id = target_cam["id"]
    rtsp_url = target_cam["rtsp_url"]

    print(f"\n[3] Connecting to Live Camera Stream: {cam_id} ({target_cam['name']})")
    print(f"    RTSP Endpoint: {rtsp_url}")

    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        print(f"[X] Failed to open RTSP stream for {cam_id}")
        return False

    print("[OK] Stream connected! Running ByteTrack multi-object vehicle tracking...\n")

    start_time = time.time()
    frames_read = 0
    yolo_runs = 0
    annotated_sample_path = None
    seen_track_ids = set()
    id_switches = 0
    last_frame_tracks = {}

    while (time.time() - start_time) < duration_seconds:
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.05)
            continue

        frames_read += 1

        # Frame Sampling (Every 5th frame)
        if frames_read % 5 == 0:
            yolo_runs += 1
            res = yolo_detector.track_vehicles(frame, cam_id)
            dets = res["detections"]
            annotated_frame = res["annotated_frame"]
            latency = res["latency_ms"]

            current_frame_tracks = {}
            for d in dets:
                t_id = d.get("track_id")
                if t_id is not None:
                    seen_track_ids.add(t_id)
                    current_frame_tracks[t_id] = d["vehicle_type"]

            print(f"Frame #{frames_read} | YOLO Run #{yolo_runs} | Latency: {latency:.1f}ms | Active Tracked Vehicles: {len(dets)}")
            for d in dets:
                t_id = d.get("track_id")
                t_str = f"#{t_id}" if t_id is not None else "N/A"
                print(f"   -> [{d['vehicle_type'].upper()} {t_str}] Conf: {d['confidence']} | BBox: {d['bbox']}")

            # Save ONE visual debug annotated frame showing Track IDs
            if len(dets) > 0 and annotated_sample_path is None:
                scratch_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scratch")
                os.makedirs(scratch_dir, exist_ok=True)
                annotated_sample_path = os.path.join(scratch_dir, f"yolo_track_sample_{cam_id}.jpg")
                cv2.imwrite(annotated_sample_path, annotated_frame)
                print(f"   [SAVED VISUAL DEBUG FRAME WITH TRACK IDs]: {annotated_sample_path}")

            last_frame_tracks = current_frame_tracks

        time.sleep(0.01)

    cap.release()
    await catalogue_service.close()

    total_time = time.time() - start_time
    final_stats = yolo_detector.get_telemetry()
    track_summary = track_manager.get_summary_stats()

    print("\n" + "=" * 65)
    print("PHASE 6 VEHICLE TRACKING TEST SUMMARY:")
    print(f"CAMERA ID: {cam_id}")
    print(f"RTSP FRAMES PROCESSED: {frames_read}")
    print(f"TRACKING INFERENCES EXECUTED: {yolo_runs}")
    print(f"UNIQUE VEHICLE TRACK IDs CREATED: {len(seen_track_ids)}")
    print(f"CURRENTLY ACTIVE TRACKS: {track_summary['total_active_tracks']}")
    print(f"COMPUTATION DEVICE: {final_stats['device_name']} ({final_stats['device']})")
    print(f"AVERAGE TRACKING LATENCY: {final_stats['average_latency_ms']} ms")
    print(f"INFERENCE FPS: {final_stats['inference_fps']}")
    if annotated_sample_path:
        print(f"VISUAL DEBUG ANNOTATED FRAME: {annotated_sample_path}")
    print("=" * 65)

    return len(seen_track_ids) > 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Phase 6 ByteTrack vehicle tracking")
    parser.add_argument("--camera", type=str, default="cam01", help="Camera ID to test")
    parser.add_argument("--duration", type=int, default=20, help="Test duration in seconds")
    args = parser.parse_args()

    success = asyncio.run(test_vehicle_tracking_on_live_camera(camera_id=args.camera, duration_seconds=args.duration))
    sys.exit(0 if success else 1)
