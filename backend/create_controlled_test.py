import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def generate_controlled_anpr_video(
    output_path: str = "scratch/controlled_vehicle_test.mp4",
    num_frames: int = 100,
    fps: int = 25,
    plate_text: str = "GJ01AB1234"
):
    """
    Generates a controlled test video featuring a car with a clear,
    solid-font Indian license plate ('GJ01AB1234') to prove end-to-end
    YOLO + ByteTrack + ANPR OCR recognition.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    width, height = 1280, 720
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"Generating Controlled Test Video: {output_path} ({num_frames} frames)...")

    # Pre-render solid-font License Plate Image using PIL
    pw, ph = 260, 70
    pil_plate = Image.new("RGB", (pw, ph), color=(0, 225, 255))
    draw = ImageDraw.Draw(pil_plate)
    
    try:
        font = ImageFont.truetype("arial.ttf", 42)
    except Exception:
        font = ImageFont.load_default()

    draw.rectangle([0, 0, pw - 1, ph - 1], outline=(0, 0, 0), width=3)
    draw.text((16, 10), plate_text, fill=(0, 0, 0), font=font)
    plate_np = cv2.cvtColor(np.array(pil_plate), cv2.COLOR_RGB2BGR)

    # Generate video frames
    for i in range(num_frames):
        frame = np.full((height, width, 3), (80, 85, 90), dtype=np.uint8)
        
        # Road lane
        cv2.rectangle(frame, (0, 200), (1280, 680), (45, 45, 45), -1)
        for line_x in range(0, 1280, 100):
            cv2.line(frame, (line_x, 440), (line_x + 50, 440), (240, 240, 240), 4)

        # Vehicle position moving horizontally
        curr_x = 200 + i * 6
        curr_y = 260
        vw, vh = 520, 270

        # Car Body
        cv2.rectangle(frame, (curr_x, curr_y + 70), (curr_x + vw, curr_y + vh), (30, 60, 200), -1)
        cv2.ellipse(frame, (curr_x + 260, curr_y + 80), (160, 90), 0, 180, 360, (20, 40, 160), -1)
        cv2.ellipse(frame, (curr_x + 260, curr_y + 80), (140, 75), 0, 180, 360, (180, 210, 230), -1)
        cv2.rectangle(frame, (curr_x + 250, curr_y + 5), (curr_x + 270, curr_y + 80), (20, 40, 160), -1)

        # Wheels
        cv2.circle(frame, (curr_x + 100, curr_y + vh), 50, (15, 15, 15), -1)
        cv2.circle(frame, (curr_x + 100, curr_y + vh), 25, (150, 150, 150), -1)
        cv2.circle(frame, (curr_x + 420, curr_y + vh), 50, (15, 15, 15), -1)
        cv2.circle(frame, (curr_x + 420, curr_y + vh), 25, (150, 150, 150), -1)

        # Overlay License Plate Image
        px = curr_x + (vw - pw) // 2
        py = curr_y + vh - ph - 20
        frame[py:py+ph, px:px+pw] = plate_np

        out.write(frame)

    out.release()
    print(f"[OK] Controlled Test Video created at {output_path}!")

if __name__ == "__main__":
    generate_controlled_anpr_video()
