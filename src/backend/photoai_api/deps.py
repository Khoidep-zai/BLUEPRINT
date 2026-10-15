"""API dependencies (P0 task 7) backed by the in-memory store."""
from __future__ import annotations

from typing import Generator

from fastapi import Depends

from .services.asset_service import AssetService
from .services.audit_service import AuditService
from .services.job_service import JobService
from .store import default_store


def get_job_service() -> JobService:
    return JobService(default_store)


def get_asset_service() -> AssetService:
    return AssetService(default_store)


def get_audit_service() -> AuditService:
    return AuditService(default_store)


def get_store() -> Generator:
    """Yield the shared in-memory store (stand-in for a DB session)."""
    yield default_store
