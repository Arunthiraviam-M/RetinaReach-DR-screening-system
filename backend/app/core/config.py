"""
Centralized application configuration.

All values are sourced from environment variables (see .env.example).
Nothing here is hard-coded to a specific deployment so the same image can
run in dev, staging, or production simply by swapping the .env file.
"""
from __future__ import annotations

import json
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "RetinaScan District Screening API"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    BACKEND_CORS_ORIGINS: str = '["http://localhost:5173"]'

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "retinascan"

    # Auth
    JWT_SECRET_KEY: str = "insecure-dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Storage
    STORAGE_BACKEND: str = "local"
    LOCAL_STORAGE_DIR: str = "./storage"
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET_NAME: str = "retinascan-images"
    S3_REGION: str = "ap-south-1"

    # ML
    DR_CLASSIFIER_WEIGHTS_PATH: str = "../ml_models/weights/dr_classifier.pt"
    SEGMENTATION_WEIGHTS_PATH: str = "../ml_models/weights/segmentation.pt"
    OCT_MODEL_WEIGHTS_PATH: str = "../ml_models/weights/oct_model.pt"
    MODEL_DEVICE: str = "cpu"

    # Rate limiting
    UPLOAD_RATE_LIMIT: str = "20/minute"
    ANALYZE_RATE_LIMIT: str = "10/minute"

    # Compliance
    DATA_RETENTION_DAYS: int = 1825
    AUDIT_LOG_ENABLED: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> List[str]:
        try:
            return json.loads(self.BACKEND_CORS_ORIGINS)
        except json.JSONDecodeError:
            return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
