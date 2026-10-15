"""QA report repository."""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import QaReportRow


class QaReportRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, **kwargs) -> QaReportRow:
        row = QaReportRow(**kwargs)
        self.db.add(row)
        self.db.flush()
        self.db.refresh(row)
        return row
