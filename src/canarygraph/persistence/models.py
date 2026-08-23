"""Relational persistence shape for durable analysis artifacts."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from canarygraph.persistence.database import Base


class RepositoryRecord(Base):
    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    path: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AnalysisRecord(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    repository_id: Mapped[str] = mapped_column(ForeignKey("repositories.id"), nullable=False)
    library: Mapped[str] = mapped_column(String(255), nullable=False)
    old_version: Mapped[str] = mapped_column(String(100), nullable=False)
    new_version: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="COMPLETED")
    report: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MigrationRecord(Base):
    __tablename__ = "migrations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"), nullable=False)
    finding_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    repository: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    patches: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    validation: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
