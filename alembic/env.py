"""
Alembic environment.

Per Alembic autogenerate docs, ``target_metadata`` must point at your ORM
``MetaData`` so ``alembic revision --autogenerate`` can diff models vs DB.
"""

from __future__ import annotations

import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from colcommute.db.base import Base  # noqa: E402
import colcommute.db.models  # noqa: F401, E402  # registers ORM models on Base.metadata

target_metadata = Base.metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    return config.get_main_option("sqlalchemy.url") or ""


def run_migrations_offline() -> None:
    url = get_url()
    if not url:
        raise RuntimeError("Set DATABASE_URL or sqlalchemy.url in alembic.ini for migrations.")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = get_url()
    if not url:
        raise RuntimeError("Set DATABASE_URL or sqlalchemy.url in alembic.ini for migrations.")

    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = url

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
