import os
import sys
import time
import argparse
import asyncio
import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.catalogue import catalogue_service
from app.services.yolo_service import yolo_detector
from app.services.traffic_analytics import traffic_analytics_engine

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

async def test_camera_analytics(cam_id: str, duration_seconds: int = 25, sample_interval: int = 5) -> dict:
    cam_info = await catalogue_service.get_camera_by_id(cam_id)
    if not cam_info:
        cam_info = {"id": cam_id, "name": cam_id, "rtsp_url": f"rtsp://103.250.160.189:8554/stream/{cam_id}"}

    cam_name = cam_info.get("name", cam_id)
    rtsp_url = cam_info["rtsp_url"]

    print(f"\n[{cam_id.upper()}] Starting Traffic Analytics Test on '{cam_name}' ({duration_seconds}s)...")
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        print(f"[{cam_id.upper()}] ERROR: Connection to RTSP stream failed.")
        return {}

    frames_processed = 0
    latencies = []

    start_time = time.time()
    while (time.time() - start_time) < duration_seconds:
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.04)
            continue

        frames_processed += 1
        if frames_processed % sample_interval == 0:
            res = yolo_detector.track_vehicles(frame, cam_id)
            latencies.append(res.get("latency_ms", 0.0))

    cap.release()

    cam_analytics = traffic_analytics_engine.cameras.get(cam_id)
    an_data = cam_analytics.get_analytics() if cam_analytics else {}
    avg_latency = float(np.mean(latencies)) if latencies else 0.0

    # Save visual debug summary frame if available
    debug_out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scratch", f"analytics_sample_{cam_id}.jpg")
    if 'res' in locals() and "annotated_frame" in res and res["annotated_frame"] is not None:
        cv2.imwrite(debug_out_path, res["annotated_frame"])

    return {
        "camera_id": cam_id,
        "camera_name": cam_name,
        "frames_processed": frames_processed,
        "total_unique_vehicles": an_data.get("total_unique_vehicles", 0),
        "breakdown": an_data.get("unique_vehicle_breakdown", {}),
        "active_vehicles": an_data.get("active_vehicles", 0),
        "traffic_density": an_data.get("traffic_density", "LOW"),
        "vehicles_per_minute": an_data.get("flow_metrics", {}).get("vehicles_per_minute", 0.0),
        "events_count": an_data.get("recent_events_count", 0),
        "avg_latency": round(avg_latency, 2),
        "debug_image": debug_out_path
    }

async def run_analytics_benchmark():
    yolo_telemetry = yolo_detector.get_telemetry()
    device_str = f"{yolo_telemetry['device_name']} ({yolo_telemetry['device']})"

    target_cams = ["cam06", "cam04", "cam15"]

    print("=" * 70)
    print("PHASE 8 — REAL-TIME TRAFFIC & VEHICLE ANALYTICS TEST")
    print("=" * 70)
    print(f"Target Cameras: {target_cams}")
    print(f"Sampling Duration Per Camera: 25 Seconds")
    print(f"Computation Device: {device_str}\n")

    results = []
    for cid in target_cams:
        res = await test_camera_analytics(cid, duration_seconds=25)
        if res:
            results.append(res)

    await catalogue_service.close()

    print("\n" + "=" * 70)
    print("PHASE 8 TRAFFIC ANALYTICS TEST SUMMARY")
    print("=" * 70)

    for r in results:
        print(f"\nCamera: {r['camera_id']} ({r['camera_name']})")
        print(f"Frames Processed: {r['frames_processed']}")
        print(f"Unique Vehicles: {r['total_unique_vehicles']}")
        print(f"  Cars: {r['breakdown'].get('cars', 0)}")
        print(f"  Motorcycles: {r['breakdown'].get('motorcycles', 0)}")
        print(f"  Buses: {r['breakdown'].get('buses', 0)}")
        print(f"  Trucks: {r['breakdown'].get('trucks', 0)}")
        print(f"Current Active Vehicles: {r['active_vehicles']}")
        print(f"Traffic Density: {r['traffic_density']}")
        print(f"Vehicles Per Minute: {r['vehicles_per_minute']}")
        print(f"Events Generated: {r['events_count']}")
        print(f"Average Pipeline Latency: {r['avg_latency']} ms")
        print(f"Debug Image: {r['debug_image']}")

    print("\nSystem Multi-Camera Summary:")
    summary = traffic_analytics_engine.get_system_summary()
    print(f"Total Active Cameras: {summary['total_cameras']}")
    print(f"Total System Active Vehicles: {summary['total_active_vehicles']}")
    print(f"Traffic Density Distribution: {summary['traffic_density_summary']}")
    print(f"Busiest Camera: {summary['busiest_camera']} ({summary['highest_active_vehicle_count']} active vehicles)")
    print(f"\nGPU Device: {device_str}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_analytics_benchmark())
