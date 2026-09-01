import sys
import torch
import easyocr

print("=" * 50)
print("EASYOCR WARMUP & GPU CHECK")
print("=" * 50)
print("CUDA Available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("Device Name:", torch.cuda.get_device_name(0))

print("Initializing EasyOCR Reader...")
reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available(), verbose=False)
print("[OK] EasyOCR Reader initialized successfully!")
print("=" * 50)
