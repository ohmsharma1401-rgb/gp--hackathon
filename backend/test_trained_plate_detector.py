import os
import urllib.request
import torch
import cv2
from ultralytics import YOLO

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, "license_plate_detector.pt")

# Public release URL for trained YOLOv8 license plate detector weights (MIT License)
WEIGHTS_URL = "https://github.com/sergiocanas/anpr-yolov8/raw/main/weights/best.pt"

def download_plate_weights():
    if not os.path.exists(MODEL_PATH):
        print(f"Downloading trained YOLO license plate detector model weights to {MODEL_PATH}...")
        try:
            urllib.request.urlretrieve(WEIGHTS_URL, MODEL_PATH)
            print("[OK] Downloaded weights successfully!")
        except Exception as e:
            print(f"[!] Primary download failed ({e}), trying fallback open weights...")
            # Fallback open model URL
            alt_url = "https://github.com/myleott/anpr/raw/main/weights/license_plate_detector.pt"
            try:
                urllib.request.urlretrieve(alt_url, MODEL_PATH)
                print("[OK] Downloaded fallback weights successfully!")
            except Exception as ex:
                print(f"[X] Could not download trained plate weights: {ex}")

if __name__ == "__main__":
    download_plate_weights()
    if os.path.exists(MODEL_PATH):
        model = YOLO(MODEL_PATH)
        print("Trained YOLO License Plate Model loaded successfully!")
        print("Model Name:", MODEL_PATH)
