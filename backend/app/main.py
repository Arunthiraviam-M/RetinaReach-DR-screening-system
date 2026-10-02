from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.db.mongodb import close_db, init_db
from app.routers import auth, dashboard, patients, reports, simulation, studies

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Explainable Diabetic Retinopathy Screening System — API for image quality "
        "assessment, DR grading, Grad-CAM explainability, report generation, and "
        "district-level workflow simulation."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded/processed images and generated PDFs
app.mount("/media", StaticFiles(directory=settings.LOCAL_STORAGE_DIR), name="media")

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(patients.router, prefix=settings.API_V1_PREFIX)
app.include_router(studies.router, prefix=settings.API_V1_PREFIX)
app.include_router(reports.router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)
app.include_router(simulation.router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": settings.APP_NAME,
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
