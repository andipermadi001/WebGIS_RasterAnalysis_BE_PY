import os
import tempfile

import requests
from fastapi import HTTPException
from rasterio.errors import RasterioIOError
import rasterio


def safe_remove(*paths):
    for p in paths:
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except OSError:
            pass


def download_raster(url: str, timeout: int = 60) -> str:
    """Unduh raster ke /tmp (streaming) dan kembalikan path-nya."""
    fd, path = tempfile.mkstemp(suffix=".tif")
    try:
        with os.fdopen(fd, "wb") as tmp:
            with requests.get(url, stream=True, timeout=timeout) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    tmp.write(chunk)
        return path
    except requests.exceptions.RequestException as e:
        safe_remove(path)
        raise HTTPException(status_code=400, detail=f"Gagal fetch raster: {e}")
    except Exception:
        safe_remove(path)
        raise


def read_metadata(path: str, url: str) -> dict:
    try:
        with rasterio.open(path) as src:
            return {
                "filename": url.split("?")[0].split("/")[-1],
                "width": src.width,
                "height": src.height,
                "crs": src.crs.to_string() if src.crs else "unknown",
            }
    except RasterioIOError as e:
        raise HTTPException(status_code=422, detail=f"File bukan raster valid: {e}")
