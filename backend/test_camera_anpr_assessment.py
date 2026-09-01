import os
import sys
import time
import argparse
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.catalogue import catalogue_service
from app.services.anpr_assessor import anpr_assessor
from app.services.yolo_service import yolo_detector

async def run_assessment(camera_id: str = None, duration_seconds: int = 15, run_all: bool = False):
    print("=" * 65)
    print("PHASE 7.6 MULTI-CAMERA ANPR CAPABILITY ASSESSMENT & RANKING")
    print("=" * 65)

    yolo_telemetry = yolo_detector.get_telemetry()
    print(f"Computation Device: {yolo_telemetry['device_name']} ({yolo_telemetry['device']})")
    print(f"Sampling Duration Per Camera: {duration_seconds} seconds")

    target_cam = camera_id if not run_all else None
    
    start_time = time.time()
    summary = await anpr_assessor.run_assessment_all_cameras(
        duration_per_camera=duration_seconds,
        target_camera_id=target_cam
    )
    total_time = time.time() - start_time

    await catalogue_service.close()

    results = summary.get("results", [])
    total_cams = summary.get("total_cameras", len(results))
    online_cams = summary.get("online_cameras", 0)
    offline_cams = summary.get("offline_cameras", 0)
    suitable_cams = summary.get("anpr_suitable_cameras", 0)
    recommended = summary.get("recommended_cameras", [])
    unsuitable = summary.get("unsuitable_cameras", [])

    total_frames = sum(r.get("frames_processed", 0) for r in results)
    total_vehicles = sum(r.get("vehicles_detected", 0) for r in results)
    total_candidates = sum(r.get("plate_candidates", 0) for r in results)

    # Print Table of Camera Rankings
    print("\n" + "-" * 115)
    print(f"{'RANK':<5} | {'CAMERA':<8} | {'STATUS':<8} | {'FRAMES':<7} | {'VEHICLES':<9} | {'PLATERES':<10} | {'SHARPNESS':<10} | {'SCORE':<7} | {'CLASSIFICATION':<12}")
    print("-" * 115)

    for r in results:
        rank_str = f"#{r.get('rank', 1)}"
        c_id = r.get("camera_id", "N/A")
        c_status = r.get("connection_status", "OFFLINE")
        c_frames = r.get("frames_processed", 0)
        c_veh = r.get("vehicles_detected", 0)
        c_res = f"{r.get('best_plate_width', 0)}x{r.get('best_plate_height', 0)}"
        c_sharp = f"{r.get('average_sharpness', 0.0):.1f}"
        c_score = f"{r.get('anpr_score', 0.0):.1f}"
        c_class = r.get("classification", "UNSUITABLE")

        print(f"{rank_str:<5} | {c_id:<8} | {c_status:<8} | {c_frames:<7} | {c_veh:<9} | {c_res:<10} | {c_sharp:<10} | {c_score:<7} | {c_class:<12}")

    print("-" * 115)

    best_cam = results[0] if results else None

    # Print Final Structured Report
    print("\n" + "=" * 65)
    print("PHASE 7.6 MULTI-CAMERA ANPR ASSESSMENT FINAL REPORT")
    print("=" * 65)
    print(f"TOTAL CAMERAS CONFIGURED: {total_cams}")
    print(f"ONLINE: {online_cams}")
    print(f"OFFLINE: {offline_cams}")
    print(f"TOTAL FRAMES ANALYSED: {total_frames}")
    print(f"TOTAL VEHICLES DETECTED: {total_vehicles}")
    print(f"TOTAL PLATE CANDIDATES: {total_candidates}")
    print(f"CAMERAS SUITABLE FOR ANPR: {suitable_cams}")
    
    print("\nTOP CAMERAS RANKING:")
    for r in results[:5]:
        print(f"  {r.get('rank', 1)}. {r.get('camera_id')} | Score: {r.get('anpr_score')}/100 | Classification: {r.get('classification')} | Res: {r.get('best_plate_width')}x{r.get('best_plate_height')}")

    print("\nRECOMMENDED CAMERAS FOR ANPR DEMONSTRATION:")
    print(f"  RECOMMENDED: {recommended}")
    print(f"  UNSUITABLE:  {unsuitable}")

    if best_cam:
        print("\nRECOMMENDED CAMERA FOR HACKATHON ANPR DEMONSTRATION:")
        print(f"  BEST CAMERA: {best_cam['camera_id']} ({best_cam['camera_name']})")
        print(f"  ANPR SCORE: {best_cam['anpr_score']}/100")
        print(f"  CLASSIFICATION: {best_cam['classification']}")
    
    print(f"\nCOMPUTATION DEVICE: {yolo_telemetry['device_name']} ({yolo_telemetry['device']})")
    print("=" * 65)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 7.6 Multi-Camera ANPR Capability Assessment")
    parser.add_argument("--camera", type=str, default=None, help="Specific camera ID to assess (e.g. cam01)")
    parser.add_argument("--duration", type=int, default=15, help="Sampling duration per camera in seconds")
    parser.add_argument("--all", action="store_true", help="Assess all available configured cameras")
    args = parser.parse_args()

    run_all = args.all or (args.camera is None)
    asyncio.run(run_assessment(camera_id=args.camera, duration_seconds=args.duration, run_all=run_all))
