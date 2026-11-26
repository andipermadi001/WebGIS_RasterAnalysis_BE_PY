# Deploy backend Python (FastAPI) ke Vercel

1. Pastikan folder venv `env-fastapi-raster/` TIDAK ikut ter-commit (`git ls-files | grep env-fastapi-raster` harus kosong).
2. Push ke GitHub -> Import di vercel.com (tanpa build command).
3. Settings -> Environment Variables: `SUPABASE_URL`, `SUPABASE_KEY`, `CORS_ORIGINS`.
4. Redeploy. Tes: `GET https://<project>.vercel.app/ping` -> `{"status":"ok"}`.
5. Kalau masih 500: Vercel -> Deployments -> (deployment) -> Logs; cari baris `Traceback`.

Catatan: endpoint `POST /analyze` menerima `{ "url": "...tif", "userId": "..." }`. URL harus dari host Supabase (atau host di `ALLOWED_RASTER_HOSTS`).
Jika raster besar membuat timeout/memori habis, pakai `container-image/Dockerfile.railway` di Railway/Render/Fly.
