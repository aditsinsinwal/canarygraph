"""Database configuration; PostgreSQL in deployment, SQLite for local smoke tests."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CANARYGRAPH_", env_file=".env")

    database_url: str = "sqlite:///./canarygraph.db"
    allowed_repository_roots: str = ""


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self, url: str) -> None:
        arguments: dict[str, Any] = {"check_same_thread": False} if url.startswith("sqlite") else {}
        self.engine = create_engine(url, pool_pre_ping=True, connect_args=arguments)
        self.sessions = sessionmaker(self.engine, expire_on_commit=False, class_=Session)

    def create_schema(self) -> None:
        from canarygraph.persistence import models  # noqa: F401

        Base.metadata.create_all(self.engine)


@lru_cache
def get_database() -> Database:
    return Database(Settings().database_url)
