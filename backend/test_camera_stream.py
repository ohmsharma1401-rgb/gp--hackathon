import os
import sys
import time
import argparse
import asyncio
import cv2

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.catalogue import catalogue_service

# Force TCP transport for RTSP stability
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

async def test_single_camera(requested_camera_id: str = None, duration_seconds: int = 10):
    print("=" * 60)
    print("PHASE 3 — RTSP CAMERA CONNECTION TEST")
    print("=" * 60)

    # 1. Fetch official catalogue dynamically
    print("[1] Fetching official camera catalogue dynamically...")
    cameras = await catalogue_service.fetch_catalogue()
    print(f"[OK] Catalogue fetched! Found {len(cameras)} total cameras.")

    # 2. Select camera
    target_cam = None
    if requested_camera_id:
        for c in cameras:
            if c["id"] == requested_camera_id:
                target_cam = c
                break
        if not target_cam:
            print(f"[!] Requested camera ID '{requested_camera_id}' not found in catalogue. Defaulting to first available.")
    
    if not target_cam:
        target_cam = cameras[0]

    cam_id = target_cam["id"]
    rtsp_url = target_cam["rtsp_url"]
    
    print(f"\n[2] Selected Camera: {cam_id} ({target_cam['name']})")
    print(f"[3] Constructed RTSP URL: {rtsp_url}")
    print(f"[4] Connecting to RTSP stream using OpenCV...")

    # 3. Connect via OpenCV
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        print(f"\nCAMERA: {cam_id}")
        print("STATUS: CONNECTION_FAILED")
        print("FPS: 0.0")
        print("FRAMES RECEIVED: 0")
        print("[X] Could not open RTSP stream.")
        return False

    print("[OK] Stream opened! Reading frames continuously in real-time...\n")

    # 4. Read frames frame-by-frame
    start_time = time.time()
    frames_received = 0
    last_print = time.time()

    while (time.time() - start_time) < duration_seconds:
        ret, frame = cap.read()
        if not ret or frame is None:
            print(f"[!] Read frame failure at frame count {frames_received}")
            time.sleep(0.05)
            continue

        frames_received += 1
        now = time.time()
        elapsed = now - start_time
        current_fps = frames_received / elapsed if elapsed > 0 else 0.0

        # Print telemetry output every ~1 second
        if (now - last_print) >= 1.0:
            print(f"CAMERA: {cam_id}")
            print(f"STATUS: CONNECTED")
            print(f"FPS: {current_fps:.2f}")
            print(f"FRAMES RECEIVED: {frames_received}")
            print("-" * 30)
            last_print = now

        time.sleep(0.005)

    cap.release()
    await catalogue_service.close()

    total_elapsed = time.time() - start_time
    final_fps = frames_received / total_elapsed if total_elapsed > 0 else 0.0

    print("=" * 60)
    print("FINAL TEST RESULT:")
    print(f"CAMERA: {cam_id}")
    print(f"STATUS: CONNECTED")
    print(f"FPS: {final_fps:.2f}")
    print(f"FRAMES RECEIVED: {frames_received}")
    print("=" * 60)
    
    return frames_received > 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test single RTSP camera connection")
    parser.add_argument("--camera", type=str, default=None, help="Camera ID to test (e.g. cam01)")
    parser.add_argument("--duration", type=int, default=10, help="Test duration in seconds")
    args = parser.parse_args()

    success = asyncio.run(test_single_camera(requested_camera_id=args.camera, duration_seconds=args.duration))
    sys.exit(0 if success else 1)
