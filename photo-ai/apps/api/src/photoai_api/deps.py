"""API dependencies (P0 task 7)."""
from __future__ import annotations

from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from .db import get_db
from .services.asset_service import AssetService
from .services.audit_service import AuditService
from .services.job_service import JobService


def get_job_service(db: Session = Depends(get_db)) -> JobService:
    return JobService(db)


def get_asset_service(db: Session = Depends(get_db)) -> AssetService:
    return AssetService(db)


def get_audit_service(db: Session = Depends(get_db)) -> AuditService:
    return AuditService(db)


def get_db_dep() -> Generator[Session, None, None]:
    yield from get_db()
