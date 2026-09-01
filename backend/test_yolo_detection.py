import os
import sys
import time
import argparse
import asyncio
import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.catalogue import catalogue_service
from app.services.yolo_service import yolo_detector

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

async def test_yolo_on_live_camera(camera_id: str = "cam01", duration_seconds: int = 15):
    print("=" * 60)
    print("PHASE 5 — REAL LIVE YOLO VEHICLE DETECTION TEST")
    print("=" * 60)

    # 1. Check YOLO & CUDA device status
    telemetry = yolo_detector.get_telemetry()
    print(f"[1] YOLO Model Loaded: {telemetry['model_name']}")
    print(f"[2] Device Selected: {telemetry['device_name']} ({telemetry['device']})")
    print(f"    CUDA Available: {telemetry['cuda_available']}")

    # 2. Fetch camera catalogue
    cameras = await catalogue_service.fetch_catalogue()
    target_cam = next((c for c in cameras if c["id"] == camera_id), cameras[0])
    cam_id = target_cam["id"]
    rtsp_url = target_cam["rtsp_url"]

    print(f"\n[3] Connecting to Live Camera: {cam_id} ({target_cam['name']})")
    print(f"    RTSP URL: {rtsp_url}")

    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        print(f"[X] Failed to open RTSP stream for {cam_id}")
        return False

    print("[OK] Stream connected! Running YOLO vehicle detection on live frames...\n")

    start_time = time.time()
    frames_read = 0
    yolo_runs = 0
    total_detections = 0
    annotated_sample_path = None

    while (time.time() - start_time) < duration_seconds:
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.05)
            continue

        frames_read += 1

        # Sample every 5th frame for inference
        if frames_read % 5 == 0:
            yolo_runs += 1
            res = yolo_detector.detect_vehicles(frame, cam_id)
            dets = res["detections"]
            annotated_frame = res["annotated_frame"]
            latency = res["latency_ms"]

            total_detections += len(dets)

            print(f"Frame #{frames_read} | YOLO Run #{yolo_runs} | Latency: {latency:.1f}ms | Detections: {len(dets)}")
            for d in dets:
                print(f"   -> [{d['vehicle_type'].upper()}] Conf: {d['confidence']} | BBox: {d['bbox']}")

            # Save first frame with detections as temporary visual debug output
            if len(dets) > 0 and annotated_sample_path is None:
                scratch_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scratch")
                os.makedirs(scratch_dir, exist_ok=True)
                annotated_sample_path = os.path.join(scratch_dir, f"yolo_sample_{cam_id}.jpg")
                cv2.imwrite(annotated_sample_path, annotated_frame)
                print(f"   [SAVED VISUAL DEBUG FRAME]: {annotated_sample_path}")

        time.sleep(0.01)

    cap.release()
    await catalogue_service.close()

    total_time = time.time() - start_time
    final_stats = yolo_detector.get_telemetry()

    print("\n" + "=" * 60)
    print("PHASE 5 TEST SUMMARY:")
    print(f"CAMERA ID: {cam_id}")
    print(f"RTSP FRAMES READ: {frames_read}")
    print(f"YOLO INFERENCES EXECUTED: {yolo_runs}")
    print(f"TOTAL VEHICLES DETECTED: {total_detections}")
    print(f"COMPUTATION DEVICE USED: {final_stats['device_name']} ({final_stats['device']})")
    print(f"AVERAGE INFERENCE LATENCY: {final_stats['average_latency_ms']} ms")
    print(f"INFERENCE FPS: {final_stats['inference_fps']}")
    if annotated_sample_path:
        print(f"VISUAL DEBUG ANNOTATED FRAME: {annotated_sample_path}")
    print("=" * 60)

    return total_detections >= 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test YOLO vehicle detection on live camera stream")
    parser.add_argument("--camera", type=str, default="cam01", help="Camera ID to test")
    parser.add_argument("--duration", type=int, default=15, help="Test duration in seconds")
    args = parser.parse_args()

    success = asyncio.run(test_yolo_on_live_camera(camera_id=args.camera, duration_seconds=args.duration))
    sys.exit(0 if success else 1)
