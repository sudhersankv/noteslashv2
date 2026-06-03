"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.projects import router as projects_router
from app.routes.voice import router as voice_router

app = FastAPI(
    title="Noteslash API",
    description="Turn any audio into searchable, cited notes.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router)
app.include_router(voice_router)


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.app_env, "product": "noteslash"}
