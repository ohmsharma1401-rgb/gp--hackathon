import sys
import time
import requests
import cv2
import numpy as np

def run_backend_annotated_stream_diagnostic():
    url = "http://localhost:8000/api/cameras/cam03/annotated"
    print("=" * 60)
    print("CAM03 BACKEND ANNOTATED STREAM DIAGNOSTIC")
    print("=" * 60)
    print(f"Target Endpoint: {url}")

    start_time = time.time()
    try:
        res = requests.get(url, stream=True, timeout=5.0)
    except Exception as ex:
        print(f"HTTP Status:     FAILED (Exception: {ex})")
        print("Content-Type:    N/A")
        print("First Frame:     FAILED")
        print(f"Error:           Could not connect to FastAPI server at {url}")
        print("=" * 60)
        return

    print(f"HTTP Status:     {res.status_code} {res.reason}")
    content_type = res.headers.get("Content-Type", "N/A")
    print(f"Content-Type:    {content_type}")

    if res.status_code != 200:
        print("First Frame:     FAILED (HTTP error)")
        print("=" * 60)
        return

    first_frame = False
    frame_count = 0
    buffer = b""
    jpeg_means = []

    stream_start = time.time()
    for chunk in res.iter_content(chunk_size=1024 * 32):
        if time.time() - stream_start > 5.0:
            break

        buffer += chunk
        # Find JPEG delimiters
        a = buffer.find(b'\xff\xd8')
        b = buffer.find(b'\xff\xd9')
        
        while a != -1 and b != -1 and b > a:
            jpg_bytes = buffer[a:b+2]
            buffer = buffer[b+2:]
            
            # Decode JPEG
            nparr = np.frombuffer(jpg_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is not None:
                if not first_frame:
                    first_frame = True
                    h, w = img.shape[:2]
                    print(f"First Frame:     SUCCESS (Decoded JPEG {w}x{h})")

                frame_count += 1
                mean_val = float(np.mean(img))
                jpeg_means.append(mean_val)

            a = buffer.find(b'\xff\xd8')
            b = buffer.find(b'\xff\xd9')

    res.close()
    elapsed = max(0.1, time.time() - stream_start)
    stream_fps = round(frame_count / elapsed, 2)
    avg_intensity = float(np.mean(jpeg_means)) if jpeg_means else 0.0

    print(f"Frame Count:     {frame_count}")
    print(f"Stream FPS:      {stream_fps}")
    print(f"Mean Pixel Val:  {avg_intensity:.2f} {'(⚠️ ALL BLACK JPEGs SENT!)' if avg_intensity < 1.0 else '(VALID IMAGES SENT)'}")
    
    if frame_count == 0:
        print("Error:           HTTP 200 returned, but zero JPEG frames yielded within 5s.")
    elif avg_intensity < 1.0:
        print("Error:           Backend is streaming 100% BLACK JPEG images to browser.")
    else:
        print("Result:          SUCCESS. Backend is streaming valid JPEG frames.")

    print("=" * 60)

if __name__ == "__main__":
    run_backend_annotated_stream_diagnostic()
