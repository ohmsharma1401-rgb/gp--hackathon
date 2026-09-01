import sys
import os
import time
import asyncio
import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.catalogue import catalogue_service
from app.services.stream_manager import stream_manager

async def run_integration_test():
    print("=" * 60)
    print("TESTING API & MULTI-CAMERA STREAM MANAGER INTEGRATION")
    print("=" * 60)

    # 1. Test Catalogue Fetching (Phase 1)
    print("[Phase 1] Testing dynamic catalogue fetching...")
    cameras = await catalogue_service.fetch_catalogue()
    print(f" -> Successfully retrieved {len(cameras)} cameras from official catalogue.")
    assert len(cameras) > 0, "Catalogue should contain cameras"
    print(f" -> Sample Camera 0: {cameras[0]['id']} | {cameras[0]['name']} | {cameras[0]['location']}")

    # 2. Test Multi-Camera Workers (Phase 4 Isolation & Telemetry)
    print("\n[Phase 4] Launching isolated stream workers for cam01 and cam02...")
    cam1 = cameras[0]["id"]
    cam2 = cameras[1]["id"] if len(cameras) > 1 else "cam02"

    worker1 = stream_manager.start_camera(cam1, f"rtsp://103.250.160.189:8554/stream/{cam1}")
    worker2 = stream_manager.start_camera(cam2, f"rtsp://103.250.160.189:8554/stream/{cam2}")

    print(" -> Stream workers started. Ingesting frames concurrently for 5 seconds...")
    await asyncio.sleep(5.0)

    status1 = worker1.get_status()
    status2 = worker2.get_status()

    print(f"\nTELEMETRY [{cam1}]: Status={status1['status']}, FPS={status1['fps']}, Frames={status1['frames_received']}, Resolution={status1['resolution']}")
    print(f"TELEMETRY [{cam2}]: Status={status2['status']}, FPS={status2['fps']}, Frames={status2['frames_received']}, Resolution={status2['resolution']}")

    assert status1["frames_received"] > 0, f"Worker {cam1} failed to receive frames"
    assert status2["frames_received"] > 0, f"Worker {cam2} failed to receive frames"

    # 3. Test isolated stopping (stopping cam1 should not affect cam2)
    print(f"\n[Phase 4] Testing non-blocking worker isolation (stopping {cam1})...")
    stream_manager.stop_camera(cam1)
    await asyncio.sleep(2.0)

    status1_after = worker1.get_status()
    status2_after = worker2.get_status()

    print(f" -> {cam1} Status: {status1_after['status']}")
    print(f" -> {cam2} Status: {status2_after['status']} (Frames received: {status2_after['frames_received']})")

    assert status1_after["status"] == "DISCONNECTED"
    assert status2_after["status"] == "CONNECTED"

    # Clean up remaining workers
    stream_manager.stop_all()
    await catalogue_service.close()

    print("\n[OK] Integration Test Passed Successfully!")

if __name__ == "__main__":
    asyncio.run(run_integration_test())
