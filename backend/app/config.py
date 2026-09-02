import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    CATALOGUE_URL: str = "https://cctv.corp8.cloud/cameras.json"
    RTSP_BASE_URL: str = "rtsp://103.250.160.189:8554/stream"
    WHEP_BASE_URL: str = "http://103.250.160.189:8889/stream"
    HLS_BASE_URL: str = "https://cctv.corp8.cloud"
    SENTINEL_EMAIL: str = "team@hackathon.gov"
    SENTINEL_PASSWORD: str = ""
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # YOLO & Tracking Configuration (Phase 11 Optimized)
    YOLO_MODEL_NAME: str = "yolov8n.pt"
    YOLO_CONFIDENCE_THRESHOLD: float = 0.30
    YOLO_IOU_THRESHOLD: float = 0.45
    YOLO_IMAGE_SIZE: int = 960
    YOLO_FRAME_INTERVAL: int = 3
    YOLO_DEVICE: str = "auto"  # auto, cuda, cpu
    YOLO_TRACKER: str = "bytetrack.yaml"
    TRACK_INACTIVE_TIMEOUT_SECONDS: float = 10.0

    # Auto-Rickshaw Classification Configuration (Phase 11)
    AUTO_RICKSHAW_CONFIDENCE_THRESHOLD: float = 0.75
    TEMPORAL_VOTE_MIN_FRAMES: int = 3

    # ANPR Configuration (Phase 11)
    ANPR_ENABLE: bool = True
    ANPR_MAX_CANDIDATES_PER_TRACK: int = 5
    ANPR_MIN_CONFIDENCE: float = 0.45
    ANPR_USE_GPU: bool = True
    ANPR_MIN_PLATE_CHAR_HEIGHT: int = 25

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
