from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 1. Import Base, Models và Settings từ app
from app.db.session import Base
from app.db.models import *  # Import tất cả models để metadata nhận diện các bảng
from app.core.config import settings

config = context.config

# 2. Gán target_metadata để autogenerate hoạt động
target_metadata = Base.metadata

# 3. Lấy URL kết nối trực tiếp từ config của app (.env.local)
db_url = settings.database_url
if db_url.startswith("postgresql://"):
    # Hỗ trợ driver psycopg v3 nếu có
    try:
        import psycopg
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    except ImportError:
        pass

config.set_main_option("sqlalchemy.url", db_url)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()

# --- Logic chính ---
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
