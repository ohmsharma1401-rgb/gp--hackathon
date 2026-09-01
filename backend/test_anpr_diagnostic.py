import os
import sys
import time
import argparse
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.catalogue import catalogue_service
from app.services.anpr_diagnostic import anpr_diagnostic_service
from app.services.yolo_service import yolo_detector

async def run_cli_diagnostic(camera_id: str = None, duration_seconds: int = 45, recommended_mode: bool = False):
    yolo_telemetry = yolo_detector.get_telemetry()
    device_str = f"{yolo_telemetry['device_name']} ({yolo_telemetry['device']})"

    if recommended_mode or camera_id is None:
        target_cams = ["cam15", "cam16", "cam06", "cam04", "cam05"]
    else:
        target_cams = [camera_id]

    print("=" * 70)
    print("PHASE 7.7 — GOVERNMENT CCTV ANPR DIAGNOSTIC & REAL VALIDATION")
    print("=" * 70)
    print(f"Target Cameras: {target_cams}")
    print(f"Sampling Duration Per Camera: {duration_seconds} seconds")
    print(f"Computation Device: {device_str}\n")

    summary = await anpr_diagnostic_service.run_diagnostics_selected(
        camera_ids=target_cams,
        duration_per_camera=duration_seconds
    )

    await catalogue_service.close()

    results = summary.get("results", [])

    for r in results:
        print("\n" + "=" * 65)
        print("PHASE 7.7 REAL ANPR DIAGNOSTIC REPORT")
        print("=" * 65)
        print(f"CAMERA: {r.get('camera_id')} ({r.get('camera_name', 'N/A')})")
        print(f"RTSP STATUS: {r.get('rtsp_status', 'OFFLINE')}")
        print(f"FRAMES PROCESSED: {r.get('frames_processed', 0)}")
        print(f"VEHICLES DETECTED: {r.get('vehicles_detected', 0)}")
        print(f"UNIQUE TRACKS: {r.get('unique_tracks', 0)}")
        print(f"VEHICLE CROPS ANALYSED: {r.get('vehicle_crops_analysed', 0)}")
        print(f"PRIMARY PLATE DETECTIONS: {r.get('primary_plate_detections', 0)}")
        print(f"FALLBACK PLATE DETECTIONS: {r.get('fallback_plate_detections', 0)}")
        print(f"TOTAL PLATE CANDIDATES: {r.get('total_plate_candidates', 0)}")
        print(f"GOOD FOR OCR: {r.get('good_for_ocr', 0)}")
        print(f"TOO SMALL: {r.get('too_small', 0)}")
        print(f"MOTION BLUR: {r.get('motion_blur', 0)}")
        print(f"LOW CONTRAST: {r.get('low_contrast', 0)}")
        print(f"INVALID SHAPE: {r.get('invalid_shape', 0)}")
        print(f"OCR FAILED: {r.get('ocr_failed', 0)}")
        print(f"OCR ATTEMPTS: {r.get('ocr_attempts', 0)}")
        print(f"VALID PLATE READS: {r.get('valid_plate_reads', 0)}")
        print(f"CONFIRMED PLATES: {r.get('confirmed_plates', [])}")
        print(f"BEST PLATE RESOLUTION: {r.get('best_plate_resolution', '0x0')}")
        print(f"BEST PLATE SHARPNESS: {r.get('best_plate_sharpness', 0.0)}")
        print(f"FINAL CLASSIFICATION: {r.get('classification')}")
        print(f"SUMMARY DIAGNOSTIC IMAGE: {r.get('summary_image')}")
        print(f"GPU DEVICE: {device_str}")
        print("=" * 65)

    print("\n" + "=" * 70)
    print("PHASE 7.7 FINAL SUMMARY")
    print("=" * 70)
    print(f"Total Cameras Diagnosed: {summary.get('total_cameras_diagnosed', 0)}")
    print(f"Confirmed ANPR Capable: {summary.get('confirmed_anpr_capable_count', 0)}")
    print(f"Potential ANPR Capable: {summary.get('potential_anpr_capable_count', 0)}")
    print(f"Vehicle Analytics Only: {summary.get('vehicle_analytics_only_count', 0)}")
    if summary.get("top_ranked_camera"):
        print(f"Top Real ANPR Camera: {summary['top_ranked_camera']}")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 7.7 ANPR Diagnostic CLI Runner")
    parser.add_argument("--camera", type=str, default=None, help="Camera ID to diagnose (e.g. cam15)")
    parser.add_argument("--duration", type=int, default=30, help="Sampling duration per camera in seconds")
    parser.add_argument("--recommended", action="store_true", help="Diagnose top recommended cameras (cam15, cam16, cam06, cam04, cam05)")
    args = parser.parse_args()

    asyncio.run(run_cli_diagnostic(
        camera_id=args.camera,
        duration_seconds=args.duration,
        recommended_mode=args.recommended or (args.camera is None)
    ))
