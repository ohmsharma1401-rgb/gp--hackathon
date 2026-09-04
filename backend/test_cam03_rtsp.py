import sys
import os
import time
import cv2
import numpy as np

def run_cam03_rtsp_diagnostic():
    rtsp_url = "rtsp://103.250.160.189:8554/stream/cam03"
    print("=" * 60)
    print("CAM03 RTSP DIAGNOSTIC")
    print("=" * 60)
    print(f"RTSP Target URL: {rtsp_url}")

    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;5000000"
    start_time = time.time()
    
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    connection_success = cap.isOpened()
    conn_time = (time.time() - start_time) * 1000.0

    print(f"RTSP Connection: {'SUCCESS' if connection_success else 'FAILED'} ({conn_time:.1f} ms)")

    if not connection_success:
        print("First Frame:     FAILED (Could not open RTSP connection)")
        print("Resolution:      N/A")
        print("FPS:             0.0")
        print("Frames Received: 0")
        print("Last Frame:      N/A")
        print("Error:           RTSP stream connection timed out or rejected.")
        print("=" * 60)
        return

    first_frame_received = False
    frames_received = 0
    width, height = 0, 0
    last_frame_ts = None
    frame_means = []

    test_start = time.time()
    while time.time() - test_start < 10.0:
        ret, frame = cap.read()
        now = time.time()
        if ret and frame is not None:
            if not first_frame_received:
                first_frame_received = True
                height, width = frame.shape[:2]
                print(f"First Frame:     SUCCESS (Received in {(now - start_time):.2f}s)")
                print(f"Resolution:      {width}x{height}")

            frames_received += 1
            last_frame_ts = now
            mean_intensity = float(np.mean(frame))
            frame_means.append(mean_intensity)

        time.sleep(0.02)

    cap.release()
    elapsed = max(0.1, time.time() - test_start)
    calculated_fps = round(frames_received / elapsed, 2)
    avg_intensity = float(np.mean(frame_means)) if frame_means else 0.0

    print(f"FPS:             {calculated_fps}")
    print(f"Frames Received: {frames_received}")
    print(f"Mean Pixel Val:  {avg_intensity:.2f} {'(⚠️ BLACK FRAME DETECTED!)' if avg_intensity < 1.0 else '(COLOR VIDEO)'}")
    print(f"Last Frame:      {time.strftime('%H:%M:%S', time.localtime(last_frame_ts)) if last_frame_ts else 'N/A'}")
    
    if not first_frame_received:
        print("Error:           Connected to RTSP, but zero video frames were received within 10s.")
    elif avg_intensity < 1.0:
        print("Error:           Video stream is producing 100% BLACK FRAMES (all pixel values = 0).")
    else:
        print("Error:           None. Stream is active and producing valid color video frames.")

    print("=" * 60)

if __name__ == "__main__":
    run_cam03_rtsp_diagnostic()
