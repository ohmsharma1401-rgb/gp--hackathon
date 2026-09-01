import logging
import time
import httpx
import re
from typing import List, Dict, Any, Optional
from app.config import get_settings

logger = logging.getLogger(__name__)

class CatalogueService:
    def __init__(self):
        self.settings = get_settings()
        self._cache: List[Dict[str, Any]] = []
        self._last_fetch_time: float = 0.0
        self._ttl_seconds: float = 60.0  # 60s cache TTL
        self._session: Optional[httpx.AsyncClient] = None
        self._authenticated: bool = False

    async def _get_client(self) -> httpx.AsyncClient:
        if self._session is None or self._session.is_closed:
            self._session = httpx.AsyncClient(
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CCTV-Surveillance-Platform/1.0"},
                timeout=10.0
            )
        return self._session

    async def _ensure_auth(self, client: httpx.AsyncClient) -> bool:
        """Authenticate with Sentinel portal if required."""
        if self._authenticated:
            return True

        if not self.settings.SENTINEL_PASSWORD:
            logger.info("No SENTINEL_PASSWORD set, attempting registration...")
            try:
                reg_res = await client.post(
                    "https://cctv.corp8.cloud/auth/register",
                    data={
                        "name": "Surveillance Team",
                        "org": "Gov Hackathon",
                        "email": self.settings.SENTINEL_EMAIL,
                        "purpose": "AI Traffic Surveillance Platform"
                    }
                )
                match = re.search(r'class="v">([^<]+)<', reg_res.text)
                if match:
                    self.settings.SENTINEL_PASSWORD = match.group(1).strip()
                    logger.info(f"Registered new Sentinel password: {self.settings.SENTINEL_PASSWORD}")
            except Exception as e:
                logger.error(f"Registration failed: {e}")

        if self.settings.SENTINEL_PASSWORD:
            try:
                login_res = await client.post(
                    "https://cctv.corp8.cloud/auth/login",
                    data={"password": self.settings.SENTINEL_PASSWORD}
                )
                if login_res.status_code == 200:
                    self._authenticated = True
                    logger.info("Successfully authenticated with Sentinel portal.")
                    return True
            except Exception as e:
                logger.error(f"Login failed: {e}")

        return False

    def _generate_fallback_catalogue(self) -> List[Dict[str, Any]]:
        """Generate default dynamic fallback catalogue for cam01 to cam30."""
        fallback = []
        for i in range(1, 31):
            cam_id = f"cam{i:02d}"
            fallback.append({
                "id": cam_id,
                "name": f"Camera {cam_id.upper()}",
                "raw_name": f"{i:02d} Camera {cam_id.upper()}",
                "location": f"Zone {i:02d}",
                "rtsp_url": f"{self.settings.RTSP_BASE_URL}/{cam_id}",
                "hls_url": f"{self.settings.HLS_BASE_URL}/{cam_id}/index.m3u8",
                "whep_url": f"{self.settings.WHEP_BASE_URL}/{cam_id}/whep",
                "status": "AVAILABLE"
            })
        return fallback

    async def fetch_catalogue(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Fetch camera catalogue dynamically with TTL caching and resilient fallback."""
        now = time.time()
        if not force_refresh and self._cache and (now - self._last_fetch_time) < self._ttl_seconds:
            return self._cache

        try:
            client = await self._get_client()
            res = await client.get(self.settings.CATALOGUE_URL, timeout=1.5)
            content_type = res.headers.get("content-type", "")

            if "application/json" not in content_type and ("Sign in" in res.text or "<form" in res.text):
                logger.info("Catalogue endpoint returned auth challenge. Authenticating...")
                auth_ok = await self._ensure_auth(client)
                if auth_ok:
                    res = await client.get(self.settings.CATALOGUE_URL)

            raw_cameras = res.json()
            processed_cameras = []

            for cam in raw_cameras:
                cam_id = cam.get("id")
                raw_name = cam.get("name", cam_id)

                clean_name = raw_name
                location = "Unknown Location"
                parts = raw_name.split(" ", 1)
                if len(parts) == 2 and parts[0].isdigit():
                    location = parts[1]
                    clean_name = parts[1]

                processed_cameras.append({
                    "id": cam_id,
                    "name": clean_name,
                    "raw_name": raw_name,
                    "location": location,
                    "rtsp_url": f"{self.settings.RTSP_BASE_URL}/{cam_id}",
                    "hls_url": f"{self.settings.HLS_BASE_URL}/{cam_id}/index.m3u8",
                    "whep_url": f"{self.settings.WHEP_BASE_URL}/{cam_id}/whep",
                    "status": "AVAILABLE"
                })

            self._cache = processed_cameras
            self._last_fetch_time = now
            logger.info(f"Dynamically fetched {len(processed_cameras)} cameras from catalogue.")
            return self._cache

        except Exception as e:
            logger.error(f"Error fetching camera catalogue: {e}")
            if self._cache:
                logger.warning("Returning stale cached camera catalogue as fallback.")
                return self._cache
            
            logger.warning("Network issue reaching catalogue endpoint. Using dynamic fallback catalogue.")
            self._cache = self._generate_fallback_catalogue()
            self._last_fetch_time = now
            return self._cache

    async def get_camera_by_id(self, camera_id: str) -> Optional[Dict[str, Any]]:
        cameras = await self.fetch_catalogue()
        for cam in cameras:
            if cam["id"] == camera_id:
                return cam
        return None

    async def close(self):
        if self._session and not self._session.is_closed:
            await self._session.aclose()

# Global singleton instance
catalogue_service = CatalogueService()
