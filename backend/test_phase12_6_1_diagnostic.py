import os
import sys
import time
import json
import cv2
import torch
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

def run_diagnostics():
    print("==================================================================")
    print(" PHASE 12.6.1 — VISDRONE MP4 VIDEO PIPELINE DIAGNOSTIC ")
    print("==================================================================")

    demo_dir = Path(r"c:\Users\ohm\OneDrive\Documents\gp hackathon\demo_videos")
    
    # 1. Inspect MP4 Files
    print("\n[Step 1] Inspecting VisDrone MP4 Files...")
    mp4_files = sorted(list(demo_dir.glob("cam_demo_*.mp4")))
    if not mp4_files:
        print(f"FAIL: No MP4 files found in {demo_dir}")
        return False

    for vid in mp4_files:
        size_mb = vid.stat().st_size / (1024 * 1024)
        cap = cv2.VideoCapture(str(vid))
        is_opened = cap.isOpened()
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0

        ret, frame = cap.read()
        cap.release()

        status = "PASS" if (is_opened and ret and frame is not None) else "FAIL"
        print(f"  [{status}] {vid.name}: Size={size_mb:.2f}MB, Res={width}x{height}, FPS={fps}, Frames={total_frames}, ReadFrame={ret}")

    # 2. Test YOLO CUDA Inference & ByteTrack on CAM-DEMO-02
    print("\n[Step 2] Testing YOLO CUDA Inference on cam_demo_02.mp4...")
    cam2_path = demo_dir / "cam_demo_02.mp4"
    cap2 = cv2.VideoCapture(str(cam2_path))
    ret, test_frame = cap2.read()
    cap2.release()

    if not ret or test_frame is None:
        print("FAIL: Could not read frame 1 from cam_demo_02.mp4")
        return False

    from app.services.yolo_service import yolo_detector
    print(f"  YOLO Device: {yolo_detector.device_name} ({yolo_detector.device})")
    
    t0 = time.time()
    res = yolo_detector.track_vehicles(test_frame, "CAM-DEMO-02")
    t1 = time.time()

    dets = res.get("detections", [])
    annotated = res.get("annotated_frame")
    print(f"  [PASS] YOLO Inference Latency: {(t1 - t0)*1000:.1f}ms | Detections: {len(dets)}")
    if annotated is not None:
        print(f"  [PASS] Annotated Frame Shape: {annotated.shape}")
    else:
        print("  [FAIL] Annotated Frame is None!")

    # 3. Test JPEG Encoding
    print("\n[Step 3] Testing OpenCV JPEG Encoding...")
    ret_encode, jpeg_bytes = cv2.imencode(".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if ret_encode and len(jpeg_bytes) > 0:
        print(f"  [PASS] JPEG Encoded successfully: {len(jpeg_bytes)} bytes")
    else:
        print("  [FAIL] JPEG encoding failed!")

    # 4. Test DemoStreamWorker & DemoCameraManager for CAM-DEMO-02
    print("\n[Step 4] Testing DemoStreamWorker Lifecycle for CAM-DEMO-02...")
    from app.services.demo_manager import demo_camera_manager
    demo_camera_manager.initialize()
    demo_camera_manager.set_active_scenario("CAM-DEMO-02")

    worker2 = demo_camera_manager.get_stream_worker("CAM-DEMO-02")
    if not worker2:
        print("  [FAIL] Worker for CAM-DEMO-02 not found in DemoCameraManager")
        return False

    print(f"  Worker status: {worker2.status}")
    print(f"  Worker active focus: {worker2.is_active_focus}")

    # Wait 1.5 seconds for worker loop to process frames
    time.sleep(1.5)
    
    latest = worker2.get_latest_annotated_frame()
    if latest is not None:
        f_img, f_ts = latest
        print(f"  [PASS] Latest annotated frame available: Shape={f_img.shape}, TS={f_ts}")
    else:
        print("  [FAIL] Latest annotated frame in worker buffer is None!")

    # 5. Check Health Telemetry for CAM-DEMO-02
    health2 = worker2.get_health()
    print("\n[Step 5] CAM-DEMO-02 Health Telemetry:")
    print(json.dumps(health2, indent=2))

    print("\n==================================================================")
    print(" VISDRONE MP4 VIDEO PIPELINE DIAGNOSTIC COMPLETE ")
    print("==================================================================")
    return True

if __name__ == "__main__":
    run_diagnostics()
