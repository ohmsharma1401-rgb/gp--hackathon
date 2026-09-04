import os
import glob
import json
import cv2
import numpy as np
from pathlib import Path

VISDRONE_DIR = r"C:\Users\ohm\OneDrive\Documents\VisDrone2019-VID-val\sequences"
OUTPUT_DIR = Path(r"c:\Users\ohm\OneDrive\Documents\gp hackathon\demo_videos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CAMERA_CONFIGS = [
    {
        "id": "CAM-DEMO-01",
        "name": "SG Highway Junction",
        "location": "SG Highway, Ahmedabad",
        "scenario": "Dense Multi-Lane Traffic",
        "type": "Dense Congestion",
        "anpr_capability": "Medium Quality",
        "target_file": "cam_demo_01.mp4"
    },
    {
        "id": "CAM-DEMO-02",
        "name": "Ashram Road Corridor",
        "location": "Ashram Road, Ahmedabad",
        "scenario": "Urban Arterial Corridor",
        "type": "Normal Traffic",
        "anpr_capability": "High Quality",
        "target_file": "cam_demo_02.mp4"
    },
    {
        "id": "CAM-DEMO-03",
        "name": "Paldi Circle Intersect",
        "location": "Paldi Circle, Ahmedabad",
        "scenario": "Major Roundabout Junction",
        "type": "Heavy Traffic",
        "anpr_capability": "Medium Quality",
        "target_file": "cam_demo_03.mp4"
    },
    {
        "id": "CAM-DEMO-04",
        "name": "CG Road Commercial",
        "location": "CG Road, Ahmedabad",
        "scenario": "Commercial Hub Mixed Mobility",
        "type": "Multi-Class",
        "anpr_capability": "Low Quality (Wide Angle)",
        "target_file": "cam_demo_04.mp4"
    },
    {
        "id": "CAM-DEMO-05",
        "name": "Sindhu Bhavan Express",
        "location": "Sindhu Bhavan Rd, Ahmedabad",
        "scenario": "High Speed Corridor",
        "type": "ANPR High Quality",
        "anpr_capability": "Optimal ANPR Quality",
        "target_file": "cam_demo_05.mp4"
    },
    {
        "id": "CAM-DEMO-06",
        "name": "Science City Gate",
        "location": "Science City Rd, Ahmedabad",
        "scenario": "Perimeter Entrance Gate",
        "type": "Complex Angle",
        "anpr_capability": "Medium Quality",
        "target_file": "cam_demo_06.mp4"
    }
]

def analyze_sequence(seq_path):
    image_files = sorted(glob.glob(os.path.join(seq_path, "*.jpg")))
    if not image_files:
        return None
    
    # Sample up to 30 frames evenly
    sample_indices = np.linspace(0, len(image_files) - 1, min(30, len(image_files)), dtype=int)
    sample_files = [image_files[i] for i in sample_indices]
    
    sharpness_scores = []
    contrast_scores = []
    brightness_scores = []
    height, width = 0, 0
    
    for img_path in sample_files:
        frame = cv2.imread(img_path)
        if frame is None:
            continue
        height, width = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Laplacian variance for sharpness
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness_scores.append(lap_var)
        
        # Contrast (std dev)
        contrast_scores.append(float(gray.std()))
        
        # Brightness (mean)
        brightness_scores.append(float(gray.mean()))
        
    avg_sharpness = float(np.mean(sharpness_scores)) if sharpness_scores else 0.0
    avg_contrast = float(np.mean(contrast_scores)) if contrast_scores else 0.0
    avg_brightness = float(np.mean(brightness_scores)) if brightness_scores else 0.0
    
    return {
        "sequence_name": os.path.basename(seq_path),
        "total_frames": len(image_files),
        "resolution": f"{width}x{height}",
        "width": width,
        "height": height,
        "avg_sharpness": round(avg_sharpness, 2),
        "avg_contrast": round(avg_contrast, 2),
        "avg_brightness": round(avg_brightness, 2),
        "image_files": image_files
    }

def main():
    print(f"Discovering VisDrone sequences in: {VISDRONE_DIR}")
    seq_dirs = [os.path.join(VISDRONE_DIR, d) for d in os.listdir(VISDRONE_DIR) if os.path.isdir(os.path.join(VISDRONE_DIR, d))]
    
    results = []
    for seq_dir in seq_dirs:
        info = analyze_sequence(seq_dir)
        if info:
            results.append(info)
            print(f"Analyzed {info['sequence_name']}: {info['total_frames']} frames, Sharpness: {info['avg_sharpness']}, Contrast: {info['avg_contrast']}")

    if not results:
        print("ERROR: No VisDrone sequence directories found.")
        return

    # Normalize metrics to compute composite quality score (0 - 100)
    max_sharp = max(r["avg_sharpness"] for r in results) or 1.0
    max_contrast = max(r["avg_contrast"] for r in results) or 1.0
    max_frames = max(r["total_frames"] for r in results) or 1.0

    for r in results:
        # Composite score weighting: Sharpness (50%), Contrast (30%), Frame count / length (20%)
        norm_sharp = (r["avg_sharpness"] / max_sharp) * 100
        norm_contrast = (r["avg_contrast"] / max_contrast) * 100
        norm_length = (r["total_frames"] / max_frames) * 100
        r["composite_quality_score"] = round(norm_sharp * 0.50 + norm_contrast * 0.30 + norm_length * 0.20, 1)

    # Sort descending by composite score
    results.sort(key=lambda x: x["composite_quality_score"], reverse=True)

    print("\n--- VISDRONE QUALITY RANKING ---")
    for i, r in enumerate(results, 1):
        print(f"Rank {i}: {r['sequence_name']} | Score: {r['composite_quality_score']} | Sharpness: {r['avg_sharpness']} | Resolution: {r['resolution']}")

    # Select top 6 sequences
    top_6 = results[:6]
    
    metadata_list = []
    quality_report = {
        "total_discovered_sequences": len(results),
        "selected_sequences_count": len(top_6),
        "ranking": []
    }

    for idx, (seq_info, cfg) in enumerate(zip(top_6, CAMERA_CONFIGS)):
        target_path = OUTPUT_DIR / cfg["target_file"]
        print(f"\nProcessing [{cfg['id']}] {cfg['name']} from sequence '{seq_info['sequence_name']}'...")
        
        imgs = seq_info["image_files"]
        first_frame = cv2.imread(imgs[0])
        h, w = first_frame.shape[:2]
        
        fps = 25
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(target_path), fourcc, fps, (w, h))
        
        for img_path in imgs:
            frame = cv2.imread(img_path)
            if frame is not None:
                out.write(frame)
        out.release()
        
        print(f"Created MP4 video: {target_path} ({len(imgs)} frames)")
        
        cam_meta = {
            "id": cfg["id"],
            "name": cfg["name"],
            "location": cfg["location"],
            "scenario": cfg["scenario"],
            "type": cfg["type"],
            "anpr_capability": cfg["anpr_capability"],
            "source_sequence": seq_info["sequence_name"],
            "resolution": seq_info["resolution"],
            "frames": seq_info["total_frames"],
            "fps": fps,
            "duration_sec": round(seq_info["total_frames"] / fps, 1),
            "quality_score": seq_info["composite_quality_score"],
            "sharpness": seq_info["avg_sharpness"],
            "contrast": seq_info["avg_contrast"],
            "video_filename": cfg["target_file"],
            "video_path": str(target_path)
        }
        metadata_list.append(cam_meta)
        
        quality_report["ranking"].append({
            "rank": idx + 1,
            "camera_id": cfg["id"],
            "sequence_name": seq_info["sequence_name"],
            "quality_score": seq_info["composite_quality_score"],
            "sharpness": seq_info["avg_sharpness"],
            "contrast": seq_info["avg_contrast"],
            "resolution": seq_info["resolution"],
            "duration_sec": round(seq_info["total_frames"] / fps, 1)
        })

    # Save metadata.json and quality_report.json
    meta_file = OUTPUT_DIR / "metadata.json"
    report_file = OUTPUT_DIR / "quality_report.json"

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata_list, f, indent=2)

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(quality_report, f, indent=2)

    print(f"\nMetadata saved to {meta_file}")
    print(f"Quality report saved to {report_file}")
    print("VisDrone to MP4 conversion complete!")

if __name__ == "__main__":
    main()
