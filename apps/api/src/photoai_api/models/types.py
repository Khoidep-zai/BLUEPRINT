"""Cross-dialect column types (design \u00a74).

``JSONB`` on Postgres, ``JSON`` elsewhere, so tests can run on SQLite while
production uses Postgres.
"""
from __future__ import annotations

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

JSONVariant = JSON().with_variant(JSONB, "postgresql")
