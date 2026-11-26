import rasterio
import numpy as np
import tempfile
import os
import requests
from fastapi import HTTPException

# Fungsi utama untuk menghitung NDVI dari file raster lokal
async def generate_ndvi_geotiff(input_path: str) -> str:
    try:
        with rasterio.open(input_path) as src:
            print("📦 Eksplorasi Band Raster:")
            print(f"Jumlah Band: {src.count}")
            for i in range(1, src.count + 1):
                band_data = src.read(i)
                print(f"Band {i} → shape: {band_data.shape}, dtype: {band_data.dtype}")

            # Deteksi otomatis band RED dan NIR
            if src.count >= 8:
                red = src.read(4).astype("float32")
                nir = src.read(8).astype("float32")
                print("Menggunakan RED = Band 4, NIR = Band 8 (Sentinel-2)")
            elif src.count >= 4:
                red = src.read(3).astype("float32")
                nir = src.read(4).astype("float32")
                print("Menggunakan RED = Band 3, NIR = Band 4 (Landsat/preprocessed)")
            else:
                raise HTTPException(status_code=422, detail="Raster tidak punya cukup band untuk NDVI")

            # Hitung NDVI
            ndvi = (nir - red) / (nir + red + 1e-6)
            ndvi = np.clip(ndvi, -1, 1)

            # Simpan sebagai GeoTIFF
            fd, ndvi_path = tempfile.mkstemp(suffix="_ndvi.tif")
            os.close(fd)

            profile = src.profile.copy()
            profile.update({
                "count": 1,
                "dtype": "float32",
                "compress": "lzw"
            })

            with rasterio.open(ndvi_path, "w", **profile) as dst:
                dst.write(ndvi, 1)

            return ndvi_path

    except rasterio.errors.RasterioIOError as e:
        raise HTTPException(status_code=422, detail=f"Gagal baca raster: {str(e)}")

# Fungsi tambahan untuk memproses NDVI langsung dari URL raster
async def process_ndvi_from_url(url: str) -> str:
    try:
        # Ambil file raster dari URL
        response = requests.get(url)
        response.raise_for_status()

        # Simpan file raster sementara
        fd, path = tempfile.mkstemp(suffix=".tif")
        with os.fdopen(fd, "wb") as tmp:
            tmp.write(response.content)

        # Proses NDVI dari file yang diunduh
        ndvi_path = await generate_ndvi_geotiff(path)

        # Hapus file raster asli setelah diproses
        os.remove(path)

        return ndvi_path

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Gagal fetch raster: {str(e)}")