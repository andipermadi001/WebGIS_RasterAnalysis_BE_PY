import os
import tempfile

import numpy as np
import rasterio
from fastapi import HTTPException

from services.getRasterUrl import safe_remove


# Simpan array sebagai GeoTIFF (di /tmp)
def save_geotiff(array, profile, suffix):
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    profile = profile.copy()
    profile.update({"count": 1, "dtype": "float32", "compress": "lzw"})
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(array, 1)
    return path


def compute_all_indices(raster_path: str) -> dict:
    """Hitung NDVI, NDBI, NDDI dari file raster lokal. Kembalikan path hasilnya."""
    created = []
    try:
        with rasterio.open(raster_path) as src:
            profile = src.profile.copy()

            # Deteksi band
            count = src.count
            if count >= 8:
                red = src.read(4).astype("float32")
                nir = src.read(8).astype("float32")
                green = src.read(3).astype("float32")
                swir = (
                    src.read(11).astype("float32")
                    if count >= 11
                    else src.read(6).astype("float32")
                )
            elif count >= 6:
                red = src.read(3).astype("float32")
                nir = src.read(4).astype("float32")
                green = src.read(2).astype("float32")
                swir = src.read(6).astype("float32")
            else:
                raise HTTPException(
                    status_code=422,
                    detail="Raster tidak punya cukup band untuk analisis",
                )

        # NDVI
        ndvi = np.clip((nir - red) / (nir + red + 1e-6), -1, 1)
        created.append(save_geotiff(ndvi, profile, "_ndvi.tif"))

        # NDBI
        ndbi = np.clip((swir - nir) / (swir + nir + 1e-6), -1, 1)
        created.append(save_geotiff(ndbi, profile, "_ndbi.tif"))

        # NDWI -> NDDI
        ndwi = np.clip((green - nir) / (green + nir + 1e-6), -1, 1)
        nddi = np.clip((ndvi - ndwi) / (ndvi + ndwi + 1e-6), -1, 1)
        created.append(save_geotiff(nddi, profile, "_nddi.tif"))

        return {"ndvi": created[0], "ndbi": created[1], "nddi": created[2]}

    except HTTPException:  # jangan diubah jadi 500
        safe_remove(*created)
        raise
    except Exception as e:
        safe_remove(*created)
        raise HTTPException(status_code=500, detail=f"Gagal proses indeks: {e}")
