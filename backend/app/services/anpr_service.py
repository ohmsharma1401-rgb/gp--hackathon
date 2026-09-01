import re
import time
import logging
import cv2
import numpy as np
import torch
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from app.config import get_settings
from app.services.plate_detector import modular_plate_detector, HeuristicPlateDetector

logger = logging.getLogger(__name__)

# Minimum Resolution Thresholds for Meaningful OCR
MIN_PLATE_WIDTH = 35
MIN_PLATE_HEIGHT = 12

# Indian License Plate Standard Patterns Regex
INDIAN_PLATE_PATTERNS = [
    r'^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}$',   # Standard e.g. GJ01AB1234, MH12DE5678, DL3CBA9999
    r'^[0-9]{2}BH[0-9]{4}[A-Z]{1,2}$',         # Bharat Series e.g. 22BH1234AA
    r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{1,4}$'  # Commercial / Vintage e.g. GJ1A1234
]

class IndianPlateValidator:
    """Normalizes and validates Indian vehicle registration plate formats with OCR confusion correction heuristics."""

    LETTER_CORRECTIONS = {'0': 'O', '1': 'I', '8': 'B', '5': 'S', '2': 'Z'}
    DIGIT_CORRECTIONS = {'O': '0', 'I': '1', 'Z': '2', 'S': '5', 'B': '8', 'G': '6', 'Q': '0'}

    @classmethod
    def clean_text(cls, raw_text: str) -> str:
        if not raw_text:
            return ""
        return re.sub(r'[^A-Za-z0-9]', '', raw_text).upper()

    @classmethod
    def apply_heuristics(cls, text: str) -> str:
        if len(text) < 7 or len(text) > 11:
            return text

        chars = list(text)
        # 1. State Code (Letters)
        for i in range(min(2, len(chars))):
            if chars[i] in cls.LETTER_CORRECTIONS:
                chars[i] = cls.LETTER_CORRECTIONS[chars[i]]

        # 2. District Code (Digits)
        for i in range(2, min(4, len(chars))):
            if chars[i] in cls.DIGIT_CORRECTIONS:
                chars[i] = cls.DIGIT_CORRECTIONS[chars[i]]

        # 3. Final 4 Digits
        start_last = max(4, len(chars) - 4)
        for i in range(start_last, len(chars)):
            if chars[i] in cls.DIGIT_CORRECTIONS:
                chars[i] = cls.DIGIT_CORRECTIONS[chars[i]]

        return "".join(chars)

    @classmethod
    def validate(cls, text: str) -> Tuple[bool, str, float]:
        cleaned = cls.clean_text(text)
        if not cleaned or len(cleaned) < 5:
            return False, cleaned, 0.0

        for pattern in INDIAN_PLATE_PATTERNS:
            if re.match(pattern, cleaned):
                return True, cleaned, 1.0

        corrected = cls.apply_heuristics(cleaned)
        for pattern in INDIAN_PLATE_PATTERNS:
            if re.match(pattern, corrected):
                return True, corrected, 0.9

        if len(corrected) >= 6 and re.match(r'^[A-Z]{2}[0-9]{2}', corrected):
            return True, corrected, 0.65

        return False, corrected, 0.20


class MultiVariantOCRPreprocessor:
    """
    Step 5 & 7: Multi-variant image upscaling and preprocessing pipeline.
    Tests Variant A (Lanczos), Variant B (CLAHE + Cubic), Variant C (Bilateral Denoise)
    to compare OCR evidence and select the clearest result.
    """
    @staticmethod
    def compute_metrics(crop: np.ndarray) -> Tuple[float, float]:
        if crop is None or crop.size == 0:
            return 0.0, 0.0
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        contrast = float(np.std(gray))
        return sharpness, contrast

    @classmethod
    def generate_variants(cls, plate_crop: np.ndarray) -> List[Dict[str, Any]]:
        if plate_crop is None or plate_crop.size == 0:
            return []

        # Add 15px border padding around plate crop to prevent character edge clipping
        padded_crop = cv2.copyMakeBorder(plate_crop, 15, 15, 25, 25, cv2.BORDER_CONSTANT, value=[255, 255, 255])

        h, w = padded_crop.shape[:2]
        target_h = 96
        scale = target_h / float(h) if h > 0 else 1.0
        target_w = int(w * scale)

        gray = cv2.cvtColor(padded_crop, cv2.COLOR_BGR2GRAY) if len(padded_crop.shape) == 3 else padded_crop

        # Variant A: Original + Lanczos Upscaling
        var_a = cv2.resize(gray, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)

        # Variant B: CLAHE Contrast Enhancement + Cubic Upscaling
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        var_b = cv2.resize(enhanced, (target_w, target_h), interpolation=cv2.INTER_CUBIC)

        # Variant C: Bilateral Denoising + Upscaling
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        var_c = cv2.resize(denoised, (target_w, target_h), interpolation=cv2.INTER_CUBIC)

        return [
            {"variant_id": "A_LANCZOS", "image": var_a},
            {"variant_id": "B_CLAHE_CUBIC", "image": var_b},
            {"variant_id": "C_DENOISED", "image": var_c}
        ]


class ANPRManager:
    """
    Singleton ANPR Manager orchestrating Primary+Fallback Plate Detectors, Minimum Resolution Check,
    Multi-Variant Preprocessing, EasyOCR Engine, Format Validation, Diagnostic Rejection Classification,
    and Temporal Consensus Voting.
    """
    def __init__(self):
        self.settings = get_settings()
        self.ocr_reader = None
        self.gpu_available = False

        # Multi-frame candidate buffers per vehicle track: Dict[track_key, List[CandidateFrame]]
        self._candidate_buffers: Dict[str, List[Dict[str, Any]]] = {}

        # Persistent ANPR Records: Dict[track_key, Dict[str, Any]]
        self._anpr_records: Dict[str, Dict[str, Any]] = {}

        # Telemetry & Diagnostic Rejection Counters
        self.total_vehicles_analysed: int = 0
        self.total_plates_detected: int = 0
        self.total_readable_plates: int = 0
        self.total_unreadable_plates: int = 0
        self.total_det_latency_ms: float = 0.0
        self.total_ocr_latency_ms: float = 0.0
        self.ocr_runs_count: int = 0

        self.rejection_breakdown: Dict[str, int] = {
            "TOO_SMALL": 0,
            "MOTION_BLUR": 0,
            "LOW_CONTRAST": 0,
            "INVALID_FORMAT": 0,
            "OCR_FAILED": 0
        }

        self._initialize_ocr()

    def _initialize_ocr(self):
        logger.info("Initializing EasyOCR Engine for Phase 7.5 ANPR...")
        self.gpu_available = torch.cuda.is_available() and self.settings.ANPR_USE_GPU
        try:
            import easyocr
            self.ocr_reader = easyocr.Reader(['en'], gpu=self.gpu_available, verbose=False)
            logger.info(f"EasyOCR Reader initialized (GPU Acceleration: {self.gpu_available}).")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR Reader: {e}")
            self.ocr_reader = None

    def process_vehicle_crop(
        self,
        camera_id: str,
        track_id: Optional[int],
        vehicle_type: str,
        full_frame: np.ndarray,
        vehicle_bbox: List[int],
        timestamp: str
    ) -> Optional[Dict[str, Any]]:
        """
        Full ANPR Pipeline: Runs Primary+Fallback Plate Detector, Minimum Resolution Check,
        Multi-Variant Preprocessing, EasyOCR, Format Validation, Rejection Diagnostics, and Temporal Consensus.
        """
        if full_frame is None or full_frame.size == 0 or track_id is None:
            return None

        track_key = f"{camera_id}_{track_id}"
        det_start = time.time()

        # Step 2 & 3: Run Modular License Plate Detector (Primary Trained + Secondary Fallback with ROI)
        plate_candidates = modular_plate_detector.detect_plates(full_frame, vehicle_bbox=vehicle_bbox)
        det_latency = (time.time() - det_start) * 1000.0
        self.total_det_latency_ms += det_latency

        if not plate_candidates:
            return None

        best_cand = plate_candidates[0]
        plate_crop = best_cand["plate_crop"]
        det_conf = best_cand["confidence"]
        det_method = best_cand["detection_method"]
        abs_plate_bbox = best_cand.get("abs_bbox", best_cand["bbox"])

        ph, pw = plate_crop.shape[:2]

        # Step 4: Minimum Resolution Check
        if pw < MIN_PLATE_WIDTH or ph < MIN_PLATE_HEIGHT:
            self.rejection_breakdown["TOO_SMALL"] += 1
            self.total_unreadable_plates += 1
            record = {
                "camera_id": camera_id,
                "track_id": track_id,
                "vehicle_type": vehicle_type,
                "plate_number": "TOO_SMALL",
                "status": "TOO_SMALL",
                "rejection_reason": "TOO_SMALL",
                "plate_width": pw,
                "plate_height": ph,
                "detection_method": det_method,
                "plate_confidence": 0.0,
                "detector_confidence": det_conf,
                "ocr_confidence": 0.0,
                "first_seen": timestamp,
                "last_seen": timestamp,
                "best_frame_timestamp": timestamp,
                "abs_plate_bbox": abs_plate_bbox,
                "consensus_votes": {}
            }
            self._anpr_records[track_key] = record
            return record

        # Step 6: Quality Metrics Calculation
        sharpness, contrast = MultiVariantOCRPreprocessor.compute_metrics(plate_crop)

        if sharpness < 20.0:
            rejection = "MOTION_BLUR"
        elif contrast < 12.0:
            rejection = "LOW_CONTRAST"
        else:
            rejection = None

        # Step 2: Multi-Frame Candidate Buffer
        if track_key not in self._candidate_buffers:
            self._candidate_buffers[track_key] = []
            self.total_vehicles_analysed += 1

        cand_entry = {
            "plate_crop": plate_crop,
            "abs_plate_bbox": abs_plate_bbox,
            "det_method": det_method,
            "det_confidence": det_conf,
            "sharpness": sharpness,
            "contrast": contrast,
            "plate_width": pw,
            "plate_height": ph,
            "timestamp": timestamp
        }

        buf = self._candidate_buffers[track_key]
        buf.append(cand_entry)
        if len(buf) > self.settings.ANPR_MAX_CANDIDATES_PER_TRACK:
            buf.pop(0)

        # Select Best Candidate based on composite quality
        top_cand = max(buf, key=lambda c: (c["det_confidence"] * 0.4 + (c["sharpness"] / 100.0) * 0.3 + (c["plate_width"] / 100.0) * 0.3))

        # Step 5 & 7: Multi-Variant OCR Ensemble
        if self.ocr_reader is None:
            return None

        ocr_start = time.time()
        variants = MultiVariantOCRPreprocessor.generate_variants(top_cand["plate_crop"])

        best_variant_result = None
        highest_composite_score = -1.0

        for var in variants:
            try:
                ocr_out = self.ocr_reader.readtext(var["image"])
            except Exception as e:
                logger.error(f"OCR error on variant {var['variant_id']}: {e}")
                ocr_out = []

            raw_txt = ""
            ocr_conf = 0.0
            if ocr_out:
                txt_parts = [r[1] for r in ocr_out if len(r) >= 2]
                conf_parts = [r[2] for r in ocr_out if len(r) >= 3]
                raw_txt = " ".join(txt_parts)
                ocr_conf = float(np.mean(conf_parts)) if conf_parts else 0.5

            is_valid, final_plate, val_score = IndianPlateValidator.validate(raw_txt)
            composite_score = ocr_conf * top_cand["det_confidence"] * val_score

            if composite_score > highest_composite_score:
                highest_composite_score = composite_score
                best_variant_result = {
                    "raw_text": raw_txt,
                    "final_plate": final_plate,
                    "is_valid": is_valid,
                    "ocr_conf": ocr_conf,
                    "val_score": val_score,
                    "variant_id": var["variant_id"],
                    "composite_score": composite_score
                }

        ocr_latency = (time.time() - ocr_start) * 1000.0
        self.total_ocr_latency_ms += ocr_latency
        self.ocr_runs_count += 1
        self.total_plates_detected += 1

        if not best_variant_result or not best_variant_result["raw_text"]:
            rejection_reason = rejection if rejection else "OCR_FAILED"
            self.rejection_breakdown[rejection_reason] += 1
            self.total_unreadable_plates += 1
            status = "UNREADABLE"
            final_plate = "UNREADABLE"
        elif best_variant_result["is_valid"] and best_variant_result["composite_score"] >= self.settings.ANPR_MIN_CONFIDENCE:
            status = "CONFIRMED"
            rejection_reason = None
            final_plate = best_variant_result["final_plate"]
            self.total_readable_plates += 1
        elif len(best_variant_result["final_plate"]) >= 5 and best_variant_result["composite_score"] >= 0.30:
            status = "LOW_CONFIDENCE"
            rejection_reason = None
            final_plate = best_variant_result["final_plate"]
            self.total_readable_plates += 1
        else:
            rejection_reason = rejection if rejection else "INVALID_FORMAT"
            self.rejection_breakdown[rejection_reason] += 1
            self.total_unreadable_plates += 1
            status = "UNREADABLE"
            final_plate = "UNREADABLE"

        # Temporal Consensus Record Update
        if track_key not in self._anpr_records:
            self._anpr_records[track_key] = {
                "camera_id": camera_id,
                "track_id": track_id,
                "vehicle_type": vehicle_type,
                "plate_number": final_plate,
                "status": status,
                "rejection_reason": rejection_reason,
                "plate_width": pw,
                "plate_height": ph,
                "detection_method": top_cand["det_method"],
                "plate_confidence": round(highest_composite_score, 3),
                "detector_confidence": round(top_cand["det_confidence"], 3),
                "ocr_confidence": round(best_variant_result["ocr_conf"], 3) if best_variant_result else 0.0,
                "first_seen": timestamp,
                "last_seen": timestamp,
                "best_frame_timestamp": top_cand["timestamp"],
                "abs_plate_bbox": top_cand["abs_plate_bbox"],
                "consensus_votes": {final_plate: 1} if status != "UNREADABLE" else {}
            }
        else:
            rec = self._anpr_records[track_key]
            rec["last_seen"] = timestamp
            
            if status != "UNREADABLE":
                votes = rec["consensus_votes"]
                votes[final_plate] = votes.get(final_plate, 0) + 1
                winner = max(votes.keys(), key=lambda k: votes[k])
                rec["plate_number"] = winner
                rec["status"] = "CONFIRMED" if rec["plate_confidence"] >= 0.50 else "LOW_CONFIDENCE"
                rec["rejection_reason"] = None
                rec["plate_confidence"] = max(rec["plate_confidence"], round(highest_composite_score, 3))
                rec["abs_plate_bbox"] = top_cand["abs_plate_bbox"]

        return self._anpr_records[track_key]

    def get_records(
        self,
        camera_id: Optional[str] = None,
        track_id: Optional[int] = None,
        plate_number: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        results = list(self._anpr_records.values())

        if camera_id:
            results = [r for r in results if r["camera_id"] == camera_id]
        if track_id is not None:
            results = [r for r in results if r["track_id"] == track_id]
        if plate_number:
            query_clean = IndianPlateValidator.clean_text(plate_number)
            results = [r for r in results if query_clean in IndianPlateValidator.clean_text(r["plate_number"])]
        if status:
            results = [r for r in results if r["status"].upper() == status.upper()]

        results.sort(key=lambda r: r["last_seen"], reverse=True)
        return results[:limit]

    def search_plate(self, query: str) -> List[Dict[str, Any]]:
        return self.get_records(plate_number=query)

    def get_telemetry(self) -> Dict[str, Any]:
        avg_det = (self.total_det_latency_ms / self.ocr_runs_count) if self.ocr_runs_count > 0 else 0.0
        avg_ocr = (self.total_ocr_latency_ms / self.ocr_runs_count) if self.ocr_runs_count > 0 else 0.0
        return {
            "ocr_engine": "EasyOCR",
            "gpu_acceleration": self.gpu_available,
            "device": "cuda:0" if self.gpu_available else "cpu",
            "total_vehicles_analysed": self.total_vehicles_analysed,
            "total_plates_detected": self.total_plates_detected,
            "readable_plates": self.total_readable_plates,
            "unreadable_plates": self.total_unreadable_plates,
            "rejection_breakdown": self.rejection_breakdown,
            "avg_plate_detection_latency_ms": round(avg_det, 2),
            "avg_ocr_latency_ms": round(avg_ocr, 2),
            "max_candidates_per_track": self.settings.ANPR_MAX_CANDIDATES_PER_TRACK
        }

# Global singleton instance
anpr_manager = ANPRManager()
