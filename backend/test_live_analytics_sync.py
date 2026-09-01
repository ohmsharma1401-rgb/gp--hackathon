import sys
import time
import asyncio
import logging
from app.services.catalogue import catalogue_service
from app.services.stream_manager import stream_manager
from app.services.traffic_analytics import traffic_analytics_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TestLiveAnalytics")

async def run_live_analytics_test(camera_id: str = "cam04", test_duration: int = 15):
    print("=" * 65)
    print(f"LIVE ANALYTICS SYNCHRONIZATION TEST — {camera_id.upper()}")
    print("=" * 65)

    # 1. Fetch camera info
    cam = await catalogue_service.get_camera_by_id(camera_id)
    if not cam:
        print(f"ERROR: Camera ID '{camera_id}' not found in catalogue.")
        return False

    print(f"[1/4] Camera Location: {cam.get('name')} ({cam.get('location')})")
    print(f"[1/4] RTSP URL: {cam.get('rtsp_url')}")

    # 2. Start worker
    worker = stream_manager.start_camera(camera_id, cam["rtsp_url"])
    print(f"[2/4] Started worker process for {camera_id}. Waiting for stream connection...")

    # Wait for connection
    start = time.time()
    while time.time() - start < 10.0:
        if worker.status == "CONNECTED":
            break
        await asyncio.sleep(0.5)

    if worker.status != "CONNECTED":
        print(f"FAILED: Could not establish RTSP connection within 10s (Status: {worker.status})")
        return False

    print(f"[3/4] RTSP Connected. Processing live stream for {test_duration} seconds...")
    await asyncio.sleep(test_duration)

    # 3. Retrieve analytics telemetry
    analytics = traffic_analytics_engine.get_camera_analytics(camera_id).get_analytics()
    recent_dets = worker.get_recent_detections()

    print("\n" + "=" * 65)
    print("LIVE ANALYTICS SYNCHRONIZATION RESULTS")
    print("=" * 65)
    print(f"Camera ID:             {analytics.get('camera_id')}")
    print(f"Stream Status:         {worker.status}")
    print(f"Frames Received:       {worker.frames_received}")
    print(f"Recent YOLO Detections:{len(recent_dets)}")
    print(f"Active Vehicles:       {analytics.get('active_vehicles')}")
    print(f"Total Unique Vehicles: {analytics.get('total_unique_vehicles')}")
    print(f"Traffic Density:       {analytics.get('traffic_density')}")
    
    breakdown = analytics.get("unique_vehicle_breakdown", {})
    print(f"Cars:                  {breakdown.get('cars', 0)}")
    print(f"Motorcycles:           {breakdown.get('motorcycles', 0)}")
    print(f"Buses:                 {breakdown.get('buses', 0)}")
    print(f"Trucks:                {breakdown.get('trucks', 0)}")
    
    flow = analytics.get("flow_metrics", {})
    print(f"Vehicles Per Minute:   {flow.get('vehicles_per_minute')} VPM")
    print("=" * 65)

    # Verification Logic
    is_sync_ok = worker.frames_received > 0 and analytics.get("camera_id") == camera_id
    if is_sync_ok:
        print("\nVERDICT: [PASS] LIVE ANALYTICS & STREAM ARE SYNCHRONIZED SUCCESSFULLY!\n")
        return True
    else:
        print("\nVERDICT: [FAIL] TELEMETRY DISCONNECT DETECTED\n")
        return False

if __name__ == "__main__":
    cid = sys.argv[1] if len(sys.argv) > 1 else "cam04"
    asyncio.run(run_live_analytics_test(cid, 12))
