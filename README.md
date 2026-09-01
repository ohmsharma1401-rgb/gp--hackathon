# 🛡️ AI-Powered Unified CCTV Surveillance & Smart City Command Center

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.6.0%2Bcu124-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org)
[![NVIDIA GPU](https://img.shields.io/badge/NVIDIA-GeForce_RTX_4050-76B900?style=flat-square&logo=nvidia&logoColor=white)](https://nvidia.com)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF?style=flat-square)](https://ultralytics.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://reactjs.org)
[![Vite](https://img.shields.io/badge/Vite-6.4-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev)

A comprehensive, production-grade **Smart City CCTV Surveillance & Traffic Analytics Command Center** designed for real-time multi-camera video ingestion, AI vehicle detection, persistent ByteTrack tracking, automated traffic incident detection, and empirical infrastructure capability assessment across public CCTV streams.

---

## 🏛️ Command Center Overview

![Command Center Interface](https://img.shields.io/badge/UI_Theme-Government_Smart_City-1976D2?style=for-the-badge)

The platform provides a **bright, clean, modern Government Smart City Traffic Control Center** dashboard interface built with React + Tailwind CSS and powered by a FastAPI backend accelerated by an **NVIDIA GeForce RTX 4050 Laptop GPU (`cuda:0`)**.

```
                           ┌────────────────────────────────────────┐
                           │    Government RTSP CCTV Cameras        │
                           └───────────────────┬────────────────────┘
                                               │
                                               ▼
                           ┌────────────────────────────────────────┐
                           │   OpenCV RTSP Ingestion Workers        │
                           │     (TCP / Bounded Ring Buffers)       │
                           └───────────────────┬────────────────────┘
                                               │
                                               ▼
                           ┌────────────────────────────────────────┐
                           │  YOLOv8 + ByteTrack CUDA Inference     │
                           │   (Persistent Track IDs & Overlays)    │
                           └───────────────────┬────────────────────┘
                                               │
                                 ┌─────────────┴─────────────┐
                                 ▼                           ▼
                     ┌───────────────────────┐   ┌───────────────────────┐
                     │ Live MJPEG Annotated  │   │  Traffic Analytics    │
                     │    Video Stream       │   │   & Incident Engine   │
                     └───────────┬───────────┘   └───────────┬───────────┘
                                 │                           │
                                 └─────────────┬─────────────┘
                                               ▼
                           ┌────────────────────────────────────────┐
                           │  FastAPI REST & Streaming API Layer    │
                           └───────────────────┬────────────────────┘
                                               │
                                               ▼
                           ┌────────────────────────────────────────┐
                           │   React Smart City Command Center      │
                           └────────────────────────────────────────┘
```

---

## ✨ Key Features & System Capabilities

### 1. 📹 Multi-Camera RTSP Stream Management
- Dynamic ingestion of **30 public government CCTV feeds** with automated authentication and catalogue caching.
- Single-worker architecture with bounded ring buffers (`deque(maxlen=2)`) ensuring zero video lag backlog, memory leak prevention, and zero duplicate RTSP camera connections.
- Instant HTTP stream initialization (`< 5ms` header delivery) using initial status frames to prevent browser loading black screens.

### 2. ⚡ AI Vehicle Detection & ByteTrack Tracking
- **CUDA Acceleration**: Powered by PyTorch `2.6.0+cu124` on **NVIDIA GeForce RTX 4050 Laptop GPU**.
- Multi-class vehicle detection: `cars`, `motorcycles`, `buses`, `trucks`.
- **ByteTrack Integration**: Assigns persistent track IDs across frames to track vehicle trajectories and flow parameters.

### 3. 📊 Real-Time Traffic Analytics Engine
- **Unique Vehicle Counting**: Tracks new `track_id` spawns to eliminate duplicate counting across continuous frames.
- **Vehicle Class Distribution**: Computes percentages and class totals dynamically.
- **Traffic Density Classifier**: Categorizes traffic density per feed into `LOW` ($\le 5$), `MODERATE` ($6-15$), `HIGH` ($16-30$), and `VERY_HIGH` ($31+$).
- **Vehicles Per Minute (VPM)**: Calculates rolling entry flow rates per camera location.

### 4. 🚨 Intelligent Traffic Event & Incident Detection
- **Direction Vector Tracking**: Evaluates trajectory vectors to detect vehicles traveling against opposing lane direction (`WRONG_DIRECTION`).
- **Stationary Vehicle Tracking**: Detects vehicles remaining motionless within a 30px radius for $> 60$ seconds (`STATIONARY_VEHICLE`).
- **Congestion & Incident Rules**: Flags low-movement traffic slowdowns (`POSSIBLE_CONGESTION`) and sudden vehicle stops (`POSSIBLE_INCIDENT`).
- **Conservative Terminology**: Enforces strict, professional safety terminology (never outputs "Confirmed Accident" without full multi-modal validation).

### 5. 🔍 Empirical ANPR Capability Assessment
- Complete modular ANPR pipeline (Trained Plate Detector + Morphological CV Fallback + EasyOCR GPU Ensemble + Indian Registration Regex Validator `GJ01AB1234`).
- **Empirical Scientific Verdict**: Honest engineering reporting identifying character pixel height limitations on wide-angle public CCTV feeds (`LIMITED BY CAMERA RESOLUTION`) while demonstrating technical success on controlled test video.

### 6. 🎬 Dual Operating Modes
- **🟢 LIVE GOVERNMENT CCTV**: Connects to live official RTSP feeds over TCP.
- **🎬 DEMONSTRATION VIDEO MODE**: Uses recorded video samples while retaining the **exact same** YOLO + ByteTrack + Analytics + Incident backend pipeline.

---

## 🛠️ Technology Stack

| Domain | Technology / Framework |
| :--- | :--- |
| **Backend Framework** | FastAPI, Uvicorn (ASGI) |
| **Machine Learning / Vision** | PyTorch 2.6.0+cu124, Ultralytics YOLOv8, ByteTrack |
| **OCR & Processing** | EasyOCR (CUDA Accelerated), OpenCV (FFmpeg TCP) |
| **Hardware Target** | NVIDIA GeForce RTX 4050 Laptop GPU (6 GB VRAM) |
| **Frontend Framework** | React 18, Vite 6.4, Tailwind CSS, Lucide Icons |
| **State & Networking** | Async HTTP Streaming (`multipart/x-mixed-replace`), REST APIs |

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Node.js 18+ and npm
- NVIDIA GPU with CUDA drivers (Optional, falls back to CPU if unavailable)

---

### Step 1: Clone Repository
```bash
git clone https://github.com/ohmsharma1401-rgb/gp--hackathon.git
cd gp--hackathon
```

---

### Step 2: Set Up Backend
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Start FastAPI Backend Server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
*Backend API will run at `http://localhost:8000`.*

---

### Step 3: Set Up Frontend (Terminal 2)
```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start React + Vite Dev Server
cmd /c "npm run dev"
```
*Frontend Command Center will open at `http://localhost:5173/`.*

---

## 📡 REST API Reference

### Camera Catalogue & Streaming
- `GET /api/cameras` — Returns list of all 30 CCTV feeds with live connection statuses.
- `POST /api/cameras/{id}/connect` — Starts background RTSP ingestion worker for specified camera.
- `POST /api/cameras/{id}/disconnect` — Stops streaming worker process.
- `GET /api/cameras/{id}/annotated` — Live MJPEG stream with YOLO + ByteTrack overlays (`multipart/x-mixed-replace`).
- `GET /api/cameras/{id}/stream-status` — Detailed stream health metrics (`rtsp_status`, `fps`, `frames_received`, `stream_clients`).

### Traffic Analytics
- `GET /api/analytics` — Returns live analytics for all active camera workers.
- `GET /api/analytics/summary` — Returns system-wide vehicle count, busiest camera, and density breakdown.
- `GET /api/analytics/{camera_id}` — Returns detailed telemetry for a single camera location.

### Incident Detection
- `GET /api/events` — Returns filtered list of traffic anomaly events.
- `GET /api/events/summary` — Returns active alerts count, session events total, and type breakdown.

### ANPR Assessment
- `GET /api/cameras/anpr-assessment` — Multi-camera suitability scores and resolution assessment report.

---

## 🧪 Automated Verification & Testing

Run the included verification scripts to validate system functionality:

```bash
# Test Live Telemetry Synchronization
python backend/test_live_analytics_sync.py cam04

# Test Incident Engine Evaluation
python backend/test_incident_detection.py

# Check GPU CUDA Availability
python backend/check_gpu.py
```

---

## 🔒 Data Integrity Compliance

1. **Zero Hallucination Policy**: Real-world government CCTV feeds showed insufficient character resolution for OCR. The platform explicitly reports `LIMITED BY CAMERA RESOLUTION` instead of generating fake registration numbers.
2. **Conservative Incident Terminology**: Incident alerts use `POSSIBLE INCIDENT` and `POSSIBLE CONGESTION` rather than unverified definitive statements.
3. **Empirical Engineering**: All vehicle counts, traffic densities, and flow rates originate strictly from live inference.

---

## 📜 License
This project is developed for the Smart City CCTV Traffic Surveillance Hackathon. Distributed under the MIT License.
