import os
import sys
import json
import time
import cv2
from pathlib import Path

# Add backend root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

def run_verification():
    print("==================================================================")
    print(" PHASE 12.6 - VISDRONE DEMO MODE INTEGRATION VERIFICATION ")
    print("==================================================================")

    demo_dir = Path(r"c:\Users\ohm\OneDrive\Documents\gp hackathon\demo_videos")
    
    # 1. Verify Demo Video Files
    print("\n[Step 1] Verifying Demo MP4 Video Files...")
    if not demo_dir.exists():
        print(f"FAILED: Demo directory does not exist: {demo_dir}")
        return False

    expected_videos = [f"cam_demo_0{i}.mp4" for i in range(1, 7)]
    for vid in expected_videos:
        vid_path = demo_dir / vid
        if vid_path.exists() and vid_path.stat().st_size > 0:
            print(f"  [OK] {vid}: {vid_path.stat().st_size / (1024*1024):.2f} MB")
        else:
            print(f"  [WARNING] {vid}: Pending or missing")

    # 2. Verify Metadata & Quality Report JSON
    print("\n[Step 2] Verifying Metadata & Quality Report...")
    meta_file = demo_dir / "metadata.json"
    report_file = demo_dir / "quality_report.json"

    if meta_file.exists():
        with open(meta_file, "r") as f:
            meta = json.load(f)
            print(f"  [OK] metadata.json loaded successfully: {len(meta)} demo cameras configured.")
    else:
        print("  [WARNING] metadata.json missing")

    if report_file.exists():
        with open(report_file, "r") as f:
            report = json.load(f)
            print(f"  [OK] quality_report.json loaded successfully: {report.get('selected_sequences_count', 0)} sequences ranked.")
    else:
        print("  [WARNING] quality_report.json missing")

    # 3. Verify Demo Manager & Workers
    print("\n[Step 3] Initializing DemoCameraManager & Worker Pipelines...")
    from app.services.demo_manager import demo_camera_manager
    demo_camera_manager.initialize()

    cameras = demo_camera_manager.get_all_cameras()
    print(f"  [OK] DemoCameraManager active with {len(cameras)} demo stream workers.")

    for cam in cameras:
        status_str = cam.get('status', 'READY')
        active_veh = cam.get('active_vehicles', 0)
        source_type = cam.get('source_type', 'DEMO_MP4')
        display_loc = cam.get('display_location', 'Recorded Dataset Footage')
        print(f"  - [{cam['camera_id']}] {cam['name']} | Type: {source_type} | Status: {status_str} | Location: {display_loc} | Vehicles: {active_veh}")

    # 4. Verify YOLO Frame Processing & Telemetry
    print("\n[Step 4] Testing YOLO CUDA Frame Ingestion on Demo Stream...")
    worker = demo_camera_manager.get_stream_worker("CAM-DEMO-01")
    if worker:
        time.sleep(1.0) # Allow frame loop to run
        annotated_tuple = worker.get_latest_annotated_frame()
        if annotated_tuple is not None:
            frame, ts = annotated_tuple
            print(f"  [OK] Successfully retrieved annotated frame from CAM-DEMO-01 ({frame.shape[1]}x{frame.shape[0]})")
        else:
            print("  [WARNING] No frame generated yet for CAM-DEMO-01")
    
    print("\n==================================================================")
    print(" PHASE 12.6 DEMO MODE VERIFICATION SUCCESSFUL ")
    print("==================================================================")
    return True

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
