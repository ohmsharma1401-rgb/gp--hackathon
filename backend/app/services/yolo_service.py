import time
import logging
import cv2
import torch
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from ultralytics import YOLO
from app.config import get_settings
from app.services.track_manager import track_manager
from app.services.anpr_service import anpr_manager

logger = logging.getLogger(__name__)

# COCO Dataset Vehicle Class IDs
VEHICLE_CLASS_MAP = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}

# Color palette for bounding box visualization (BGR format)
CLASS_COLORS = {
    "car": (0, 225, 120),        # Emerald Green
    "bus": (0, 180, 255),        # Amber / Orange
    "truck": (255, 120, 0),      # Blue
    "motorcycle": (255, 0, 220)  # Magenta / Purple
}

PLATE_COLOR = (0, 255, 255)  # Bright Yellow for License Plate Bounding Box

class YOLOVehicleDetector:
    """
    Singleton service performing CUDA-accelerated YOLO vehicle detection,
    ByteTrack multi-object tracking, and ANPR License Plate Recognition.
    """
    def __init__(self):
        self.settings = get_settings()
        self.model: Optional[YOLO] = None
        self.device: str = "cpu"
        self.cuda_available: bool = False
        self.device_name: str = "CPU"
        
        # Performance Telemetry Metrics
        self.total_frames_processed: int = 0
        self.total_detections_count: int = 0
        self.total_inference_time_ms: float = 0.0
        self.last_latency_ms: float = 0.0
        self.inference_fps: float = 0.0
        self._fps_window: List[float] = []

        self._initialize_model()

    def _initialize_model(self):
        logger.info("Initializing YOLO Vehicle Detection, Tracking & ANPR Model...")
        
        # 1. Check CUDA Availability
        self.cuda_available = torch.cuda.is_available()
        if self.cuda_available:
            self.device = "cuda:0"
            self.device_name = torch.cuda.get_device_name(0)
            logger.info(f"NVIDIA GPU Detected! CUDA is AVAILABLE. Device: {self.device_name} ({self.device})")
        else:
            self.device = "cpu"
            self.device_name = "CPU"
            logger.warning("CUDA is NOT available. Falling back to CPU for YOLO inference.")

        # 2. Load Model ONCE
        model_name = self.settings.YOLO_MODEL_NAME
        logger.info(f"Loading Ultralytics YOLO model '{model_name}' on device '{self.device}'...")
        try:
            self.model = YOLO(model_name)
            # Warmup inference
            logger.info("Warming up YOLO model with dummy frame...")
            dummy_frame = torch.zeros((640, 640, 3), dtype=torch.uint8).numpy()
            self.model.track(dummy_frame, persist=True, tracker=self.settings.YOLO_TRACKER, device=self.device, verbose=False)
            logger.info(f"YOLO Model '{model_name}' initialized successfully on {self.device_name}!")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise RuntimeError(f"YOLO initialization error: {e}")

    def detect_vehicles(self, frame, camera_id: str) -> Dict[str, Any]:
        """
        PHASE 5 MODE: Detection-only mode.
        """
        if self.model is None or frame is None:
            return {"camera_id": camera_id, "detections": [], "annotated_frame": frame, "latency_ms": 0.0}

        start_time = time.time()
        conf_thresh = self.settings.YOLO_CONFIDENCE_THRESHOLD
        iso_timestamp = datetime.now(timezone.utc).isoformat()

        results = self.model.predict(
            source=frame,
            device=self.device,
            conf=conf_thresh,
            classes=list(VEHICLE_CLASS_MAP.keys()),
            verbose=False
        )

        latency_ms = (time.time() - start_time) * 1000.0
        self.last_latency_ms = latency_ms
        self.total_frames_processed += 1
        self.total_inference_time_ms += latency_ms

        now = time.time()
        self._fps_window.append(now)
        if len(self._fps_window) > 30:
            self._fps_window.pop(0)
        if len(self._fps_window) > 1:
            diff = self._fps_window[-1] - self._fps_window[0]
            if diff > 0:
                self.inference_fps = (len(self._fps_window) - 1) / diff

        detections: List[Dict[str, Any]] = []
        annotated_frame = frame.copy()

        if results and len(results) > 0:
            boxes = results[0].boxes
            for box in boxes:
                cls_id = int(box.cls[0].item())
                confidence = float(box.conf[0].item())
                xyxy = box.xyxy[0].cpu().numpy().tolist()
                
                vehicle_type = VEHICLE_CLASS_MAP.get(cls_id, "vehicle")
                bbox_int = [int(v) for v in xyxy]
                
                det_info = {
                    "camera_id": camera_id,
                    "vehicle_type": vehicle_type,
                    "confidence": round(confidence, 3),
                    "bbox": bbox_int,
                    "timestamp": iso_timestamp
                }
                detections.append(det_info)
                self.total_detections_count += 1

                x1, y1, x2, y2 = bbox_int
                color = CLASS_COLORS.get(vehicle_type, (0, 255, 0))
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                
                label = f"{vehicle_type.upper()} {int(confidence * 100)}%"
                (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(annotated_frame, (x1, max(y1 - 20, 0)), (x1 + w + 8, max(y1, 20)), color, -1)
                cv2.putText(annotated_frame, label, (x1 + 4, max(y1 - 5, 15)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

        telemetry_text = f"CAM: {camera_id} | YOLO DETECT | Device: {self.device_name} | Latency: {latency_ms:.1f}ms | FPS: {self.inference_fps:.1f}"
        cv2.rectangle(annotated_frame, (0, 0), (620, 26), (0, 0, 0), -1)
        cv2.putText(annotated_frame, telemetry_text, (10, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)

        return {
            "camera_id": camera_id,
            "mode": "DETECTION_ONLY",
            "detections": detections,
            "annotated_frame": annotated_frame,
            "latency_ms": round(latency_ms, 2),
            "timestamp": iso_timestamp
        }

    def track_vehicles(self, frame, camera_id: str) -> Dict[str, Any]:
        """
        PHASE 6 & 7 MODE: Detection + ByteTrack Vehicle Tracking + Real ANPR.
        """
        if self.model is None or frame is None:
            return {"camera_id": camera_id, "detections": [], "annotated_frame": frame, "latency_ms": 0.0}

        start_time = time.time()
        conf_thresh = self.settings.YOLO_CONFIDENCE_THRESHOLD
        iso_timestamp = datetime.now(timezone.utc).isoformat()
        fh, fw = frame.shape[:2]

        results = self.model.track(
            source=frame,
            persist=True,
            tracker=self.settings.YOLO_TRACKER,
            device=self.device,
            conf=conf_thresh,
            classes=list(VEHICLE_CLASS_MAP.keys()),
            verbose=False
        )

        latency_ms = (time.time() - start_time) * 1000.0
        self.last_latency_ms = latency_ms
        self.total_frames_processed += 1
        self.total_inference_time_ms += latency_ms

        now = time.time()
        self._fps_window.append(now)
        if len(self._fps_window) > 30:
            self._fps_window.pop(0)
        if len(self._fps_window) > 1:
            diff = self._fps_window[-1] - self._fps_window[0]
            if diff > 0:
                self.inference_fps = (len(self._fps_window) - 1) / diff

        detections: List[Dict[str, Any]] = []
        annotated_frame = frame.copy()

        if results and len(results) > 0:
            boxes = results[0].boxes
            for box in boxes:
                cls_id = int(box.cls[0].item())
                confidence = float(box.conf[0].item())
                xyxy = box.xyxy[0].cpu().numpy().tolist()
                
                track_id = int(box.id[0].item()) if box.id is not None else None
                vehicle_type = VEHICLE_CLASS_MAP.get(cls_id, "vehicle")
                bbox_int = [int(v) for v in xyxy]
                
                if track_id is not None:
                    track_manager.update_track(
                        camera_id=camera_id,
                        track_id=track_id,
                        vehicle_type=vehicle_type,
                        confidence=confidence,
                        bbox=bbox_int,
                        timestamp=iso_timestamp
                    )

                # ANPR Integration (Phase 7.5): Modular Plate Detector (Primary Trained + Secondary Fallback)
                anpr_result = None
                if self.settings.ANPR_ENABLE and track_id is not None:
                    x1, y1, x2, y2 = bbox_int
                    vx1, vy1 = max(0, x1), max(0, y1)
                    vx2, vy2 = min(fw, x2), min(fh, y2)
                    
                    if (vy2 - vy1) >= 25 and (vx2 - vx1) >= 25:
                        anpr_result = anpr_manager.process_vehicle_crop(
                            camera_id=camera_id,
                            track_id=track_id,
                            vehicle_type=vehicle_type,
                            full_frame=frame,
                            vehicle_bbox=[vx1, vy1, vx2, vy2],
                            timestamp=iso_timestamp
                        )

                det_info = {
                    "camera_id": camera_id,
                    "track_id": track_id,
                    "vehicle_type": vehicle_type,
                    "confidence": round(confidence, 3),
                    "bbox": bbox_int,
                    "timestamp": iso_timestamp,
                    "anpr": anpr_result
                }
                detections.append(det_info)
                self.total_detections_count += 1

                # Visual Debug Annotation
                x1, y1, x2, y2 = bbox_int
                color = CLASS_COLORS.get(vehicle_type, (0, 255, 0))
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                
                track_label = f"#{track_id}" if track_id is not None else ""
                label = f"{vehicle_type.upper()} {track_label} {int(confidence * 100)}%"
                
                (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(annotated_frame, (x1, max(y1 - 22, 0)), (x1 + w + 10, max(y1, 22)), color, -1)
                cv2.putText(annotated_frame, label, (x1 + 5, max(y1 - 6, 16)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

                # Draw ANPR License Plate Overlay if detected
                if anpr_result and "abs_plate_bbox" in anpr_result:
                    px1, py1, px2, py2 = anpr_result["abs_plate_bbox"]
                    plate_num = anpr_result.get("plate_number", "UNREADABLE")
                    plate_conf = anpr_result.get("plate_confidence", 0.0)

                    # License Plate Box (Yellow)
                    cv2.rectangle(annotated_frame, (px1, py1), (px2, py2), PLATE_COLOR, 2)

                    # Plate text label below or above plate
                    plate_lbl = f"PLATE: {plate_num} ({int(plate_conf * 100)}%)" if plate_num != "UNREADABLE" else "PLATE: UNREADABLE"
                    (pw, ph), _ = cv2.getTextSize(plate_lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                    cv2.rectangle(annotated_frame, (px1, max(py1 - 18, 0)), (px1 + pw + 8, max(py1, 18)), PLATE_COLOR, -1)
                    cv2.putText(annotated_frame, plate_lbl, (px1 + 4, max(py1 - 4, 14)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

        # PHASE 8 & 9 Integration: Real-Time Traffic & Incident Event Analytics
        from app.services.traffic_analytics import traffic_analytics_engine
        from app.services.incident_detector import incident_engine

        analytics = traffic_analytics_engine.update_camera_detections(camera_id, detections)
        cam_events = incident_engine.events_db

        # Draw Event Overlays (STATIONARY, WRONG DIRECTION, POSSIBLE INCIDENT)
        for evt in cam_events:
            if evt.get("camera_id") == camera_id and evt.get("status") == "ACTIVE":
                tid = evt.get("track_id")
                etype = evt.get("event_type")
                if tid is not None:
                    match_det = next((d for d in detections if d.get("track_id") == tid), None)
                    if match_det:
                        bx1, by1, bx2, by2 = match_det["bbox"]
                        if etype == "STATIONARY_VEHICLE":
                            warn_lbl = f"⚠ STATIONARY ({int(evt.get('metadata', {}).get('stationary_duration_seconds', 0))}s)"
                            b_color = (0, 0, 255)
                        elif etype == "WRONG_DIRECTION":
                            warn_lbl = "⚠ WRONG DIRECTION"
                            b_color = (0, 0, 255)
                        elif etype == "POSSIBLE_INCIDENT":
                            warn_lbl = "🚨 POSSIBLE INCIDENT"
                            b_color = (0, 0, 255)
                        else:
                            warn_lbl = f"⚠ {etype}"
                            b_color = (0, 165, 255)

                        (sw, sh), _ = cv2.getTextSize(warn_lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                        cv2.rectangle(annotated_frame, (bx1, min(by2 + 4, fh - 20)), (bx1 + sw + 8, min(by2 + 22, fh)), b_color, -1)
                        cv2.putText(annotated_frame, warn_lbl, (bx1 + 4, min(by2 + 18, fh - 4)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

        # Telemetry Banner with Traffic Density, Active Vehicle Count, & Active Event Count
        density = analytics.get("traffic_density", "LOW")
        active_veh = analytics.get("active_vehicles", 0)
        total_unique = analytics.get("total_unique_vehicles", 0)
        active_evts_count = sum(1 for e in cam_events if e.get("camera_id") == camera_id and e.get("status") == "ACTIVE")

        telemetry_text = f"CAM: {camera_id} | GPU: {self.device_name} | Latency: {latency_ms:.1f}ms | Density: {density} | Active: {active_veh} | Events: {active_evts_count}"
        cv2.rectangle(annotated_frame, (0, 0), (780, 26), (0, 0, 0), -1)
        cv2.putText(annotated_frame, telemetry_text, (10, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)

        return {
            "camera_id": camera_id,
            "mode": "DETECTION_TRACKING_ANPR_ANALYTICS",
            "detections": detections,
            "analytics": analytics,
            "annotated_frame": annotated_frame,
            "latency_ms": round(latency_ms, 2),
            "timestamp": iso_timestamp
        }

    def get_telemetry(self) -> Dict[str, Any]:
        avg_latency = (self.total_inference_time_ms / self.total_frames_processed) if self.total_frames_processed > 0 else 0.0
        track_stats = track_manager.get_summary_stats()
        anpr_stats = anpr_manager.get_telemetry()
        return {
            "model_name": self.settings.YOLO_MODEL_NAME,
            "tracker": self.settings.YOLO_TRACKER,
            "device": self.device,
            "device_name": self.device_name,
            "cuda_available": self.cuda_available,
            "total_frames_processed": self.total_frames_processed,
            "total_detections_count": self.total_detections_count,
            "total_unique_tracks": track_stats["total_unique_tracks"],
            "total_active_tracks": track_stats["total_active_tracks"],
            "anpr": anpr_stats,
            "last_latency_ms": round(self.last_latency_ms, 2),
            "average_latency_ms": round(avg_latency, 2),
            "inference_fps": round(self.inference_fps, 2),
            "confidence_threshold": self.settings.YOLO_CONFIDENCE_THRESHOLD,
            "frame_sampling_interval": self.settings.YOLO_FRAME_INTERVAL
        }

# Global singleton instance
yolo_detector = YOLOVehicleDetector()
