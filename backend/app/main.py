import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api import cameras, detections, tracks, anpr, analytics
from app.db.database import init_db
from app.services.stream_manager import stream_manager
from app.services.catalogue import catalogue_service
from app.services.yolo_service import yolo_detector
from app.services.anpr_service import anpr_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("CCTV-Backend")

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing CCTV Surveillance Platform Backend...")
    # 1. Initialize DB
    await init_db()
    
    # 2. Log YOLO ByteTrack & ANPR initialization state
    yolo_telemetry = yolo_detector.get_telemetry()
    logger.info(f"YOLO ByteTrack + ANPR initialized on {yolo_telemetry['device_name']} ({yolo_telemetry['device']}).")
    
    # 3. Warm up camera catalogue
    try:
        cams = await catalogue_service.fetch_catalogue()
        logger.info(f"Loaded {len(cams)} cameras into catalogue cache on startup.")
    except Exception as e:
        logger.warning(f"Catalogue warmup failed: {e}")

    yield

    # Cleanup on shutdown
    logger.info("Shutting down CCTV Surveillance Platform Backend...")
    stream_manager.stop_all()
    await catalogue_service.close()
    logger.info("Shutdown complete.")

app = FastAPI(
    title="AI-Powered Unified CCTV Surveillance Platform API",
    description="Official CCTV Stream Ingestion, Catalogue, ByteTrack & Real ANPR License Plate Recognition API",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
import os

# Register routes
app.include_router(cameras.router)
app.include_router(detections.router)
app.include_router(tracks.router)
app.include_router(anpr.router)
app.include_router(analytics.router)
app.include_router(analytics.events_router)

# Mount frontend production build statically if available
dist_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "dist")
if os.path.exists(dist_path):
    app.mount("/dashboard", StaticFiles(directory=dist_path, html=True), name="dashboard")

@app.get("/")
async def root():
    return {
        "status": "ONLINE",
        "service": "AI Unified CCTV Surveillance Platform Backend",
        "version": "1.0.0",
        "dashboard_ui": "/dashboard/",
        "catalogue_endpoint": "/api/cameras",
        "detections_endpoint": "/api/detections",
        "tracks_endpoint": "/api/tracks",
        "anpr_endpoint": "/api/anpr",
        "analytics_endpoint": "/api/analytics",
        "events_endpoint": "/api/events",
        "yolo_telemetry": "/api/yolo/stats"
    }

@app.get("/health")
async def health():
    return {
        "status": "HEALTHY",
        "active_streams": len(stream_manager.get_active_camera_ids()),
        "yolo_device": yolo_detector.device_name,
        "ocr_gpu": anpr_manager.gpu_available
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
