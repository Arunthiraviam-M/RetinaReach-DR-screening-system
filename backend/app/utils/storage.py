"""
Minimal storage abstraction so the rest of the app never cares whether
files live on local disk (demo/dev) or in S3-compatible object storage
(production). Controlled entirely by STORAGE_BACKEND in .env.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from app.core.config import settings

_LOCAL_ROOT = Path(settings.LOCAL_STORAGE_DIR).resolve()
_LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
(_LOCAL_ROOT / "originals").mkdir(exist_ok=True)
(_LOCAL_ROOT / "enhanced").mkdir(exist_ok=True)
(_LOCAL_ROOT / "gradcam").mkdir(exist_ok=True)
(_LOCAL_ROOT / "reports").mkdir(exist_ok=True)


def new_filename(prefix: str, ext: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}{ext}"


def save_bytes(subfolder: str, filename: str, data: bytes) -> str:
    """Saves bytes and returns a relative path usable by url_for_path()."""
    if settings.STORAGE_BACKEND == "s3":
        return _save_to_s3(subfolder, filename, data)
    target = _LOCAL_ROOT / subfolder / filename
    target.write_bytes(data)
    return f"{subfolder}/{filename}"


def read_bytes(relative_path: str) -> bytes:
    if settings.STORAGE_BACKEND == "s3":
        return _read_from_s3(relative_path)
    target = _LOCAL_ROOT / relative_path
    return target.read_bytes()


def absolute_path(relative_path: str) -> str:
    """Only meaningful for local backend; used by services needing a real path (OpenCV)."""
    return str(_LOCAL_ROOT / relative_path)


def url_for_path(relative_path: str | None) -> str | None:
    if not relative_path:
        return None
    return f"/media/{relative_path}"


def _save_to_s3(subfolder: str, filename: str, data: bytes) -> str:
    import boto3  # imported lazily so local/demo installs don't require boto3

    client = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL or None,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
    )
    key = f"{subfolder}/{filename}"
    client.put_object(Bucket=settings.S3_BUCKET_NAME, Key=key, Body=data)
    return key


def _read_from_s3(key: str) -> bytes:
    import boto3

    client = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL or None,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
    )
    obj = client.get_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
    return obj["Body"].read()
