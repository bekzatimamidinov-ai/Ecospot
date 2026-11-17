from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routers import auth, common, events, notifications, problems

app = FastAPI(
    title="EcoSpot API",
    description="Веб-платформа для поиска и совместного решения экологических проблем Бишкека",
    version="0.5.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth.router, common.router, problems.router, events.router, notifications.router):
    app.include_router(r)

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/api/health", tags=["Служебное"])
def health():
    return {"status": "ok"}
