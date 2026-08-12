"""
Legal AI System - Alembic Environment Configuration
=====================================================
Configures Alembic to use our SQLAlchemy models and database settings.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import Base and ALL models so Alembic can detect them
from app.database.session import Base
from app.models import (  # noqa: F401 - imported for side effects
    Role, User, Client, Advocate, Case, CaseDocument,
    AISummary, LegalOpinion, Payment, Report, Citation,
    Notification, AuditLog, CaseStatusHistory,
)

# Alembic Config object
config = context.config

# Setup logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate
target_metadata = Base.metadata


def get_database_url() -> str:
    """
    Get the SYNC database URL for migrations.
    Uses DATABASE_URL_SYNC from .env (psycopg2, not asyncpg).
    Falls back to alembic.ini value if env var not available.
    """
    try:
        from app.config import get_settings
        settings = get_settings()
        return settings.database_url_sync
    except Exception:
        return config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    Generates SQL script without connecting to the database.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    Connects to the database and applies migrations directly.
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
