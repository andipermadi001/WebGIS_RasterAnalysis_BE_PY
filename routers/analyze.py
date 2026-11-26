import os
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from services.getRasterUrl import download_raster, read_metadata, safe_remove
from services.indices import compute_all_indices
from services.supabase_client import supabase

router = APIRouter()

BUCKET = "analysis-result"


def _allowed_hosts() -> set:
    """Hanya izinkan unduh raster dari host ini (cegah SSRF). Default: host Supabase."""
    extra = os.getenv("ALLOWED_RASTER_HOSTS", "")
    hosts = {h.strip() for h in extra.split(",") if h.strip()}
    sb = urlparse(os.getenv("SUPABASE_URL", "")).netloc
    if sb:
        hosts.add(sb)
    return hosts


class AnalyzeRequest(BaseModel):
    url: str
    userId: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")


class AnalyzeResponse(BaseModel):
    filename: str
    width: int
    height: int
    crs: str
    ndvi_url: str
    ndbi_url: str
    nddi_url: str
    message: str


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_raster(data: AnalyzeRequest):
    parsed = urlparse(data.url)
    if not parsed.path.lower().endswith((".tif", ".tiff")):
        raise HTTPException(status_code=400, detail="URL must point to a .tif raster file")
    if parsed.scheme not in ("http", "https") or parsed.netloc not in _allowed_hosts():
        raise HTTPException(status_code=400, detail="Host raster tidak diizinkan")

    storage = supabase.storage.from_(BUCKET)
    raster_path = await run_in_threadpool(download_raster, data.url)
    result_paths = {}

    try:
        metadata = await run_in_threadpool(read_metadata, raster_path, data.url)
        filename = metadata["filename"]
        names = {k: f"{data.userId}_{k}_{filename}" for k in ("ndvi", "ndbi", "nddi")}

        # file hasil milik user ini yang sudah ada
        listed = await run_in_threadpool(
            lambda: storage.list(options={"limit": 1000, "search": f"{data.userId}_"})
        )
        existing = [
            f["name"] for f in listed if f["name"].startswith(f"{data.userId}_")
        ]

        def url_of(key):
            return storage.get_public_url(names[key])

        def build(message):
            return AnalyzeResponse(
                message=message,
                filename=filename,
                width=metadata["width"],
                height=metadata["height"],
                crs=metadata["crs"],
                ndvi_url=url_of("ndvi"),
                ndbi_url=url_of("ndbi"),
                nddi_url=url_of("nddi"),
            )

        if all(n in existing for n in names.values()):
            return build("File sudah dianalisis sebelumnya.")

        # Proses dulu; hasil lama baru dihapus setelah hasil baru berhasil diupload
        result_paths = await run_in_threadpool(compute_all_indices, raster_path)

        for key, name in names.items():
            await run_in_threadpool(
                storage.upload,
                name,
                result_paths[key],
                {"content-type": "image/tiff", "upsert": "true"},
            )

        stale = [n for n in existing if n not in names.values()]
        if stale:
            await run_in_threadpool(storage.remove, stale)

        return build("Analisis NDVI, NDBI, dan NDDI berhasil dilakukan dan file lama diganti.")
    finally:
        safe_remove(raster_path, *result_paths.values())
