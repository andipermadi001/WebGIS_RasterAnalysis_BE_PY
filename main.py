import os

from dotenv import load_dotenv

load_dotenv()  # hanya berpengaruh di lokal; di Vercel pakai Environment Variables

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import analyze

app = FastAPI()

# Isi CORS_ORIGINS dengan domain frontend, pisahkan dengan koma.
# contoh: https://frontend-kamu.vercel.app,http://localhost:5173
origins = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
@app.get("/ping")
def ping():
    return {"status": "ok"}


app.include_router(analyze.router)
