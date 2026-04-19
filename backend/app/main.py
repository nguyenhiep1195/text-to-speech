from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import auth_routes, tts_routes

app = FastAPI(
    title="Text-to-Speech API",
    description="API for converting text to speech with Vietnamese and English voices",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, prefix="/api/auth")
app.include_router(tts_routes.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
