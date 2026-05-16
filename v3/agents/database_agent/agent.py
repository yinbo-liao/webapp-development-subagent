from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader

from ecc_tools.core.engine import ECCEngine


class DatabaseAgent:
    """Specialized agent for PostgreSQL schema design and Alembic migrations."""

    def __init__(self, config: Dict = None, ecc: Optional[ECCEngine] = None):
        self.config = config or {}
        self.ecc = ecc or ECCEngine.get_instance("config")

        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = None
        if template_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
            )

    def implement(self, data_model: Dict, project_path: str) -> Dict:
        """Implement database schema and migrations"""
        print(f"[DATABASE AGENT] Implementing database schema...")

        results = {
            "status": "success",
            "generated_files": [],
            "validation": {}
        }

        # Generate database configuration
        files = self._generate_database_config(project_path)
        results["generated_files"].extend(files)

        # Generate migrations
        files = self._generate_migrations(data_model, project_path)
        results["generated_files"].extend(files)

        # Generate seed data
        files = self._generate_seed_data(data_model, project_path)
        results["generated_files"].extend(files)

        # Validate with ECC
        results["validation"] = self.validate_output(project_path)

        return results

    def validate_output(self, output_path: str) -> Dict:
        """Validate via shared ECC engine."""
        report = self.ecc.full_scan(output_path)
        sec_ok = report.security.critical_count == 0 if report.security else True
        stab_ok = len([i for i in report.stability if i.severity == 'critical']) == 0
        return {
            "passed": sec_ok and stab_ok,
            "security": report.security,
            "stability": report.stability,
            "performance": report.performance,
            "maintainability": report.maintainability,
        }

    def _generate_database_config(self, project_path: str) -> List[str]:
        """Generate database configuration"""
        config_file = Path(project_path) / "app" / "core" / "database.py"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        code = """from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator

from app.core.config import settings

# Async engine with connection pooling
engine = create_async_engine(
    str(settings.DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://"),
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    \"\"\"Dependency for async database sessions\"\"\"
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    \"\"\"Initialize database tables\"\"\"
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
"""
        config_file.write_text(code)
        return [str(config_file)]

    def _generate_migrations(self, data_model: Dict, project_path: str) -> List[str]:
        """Generate Alembic migrations"""
        migration_dir = Path(project_path) / "app" / "alembic" / "versions"
        migration_dir.mkdir(parents=True, exist_ok=True)

        migration_file = migration_dir / "001_initial_migration.py"

        code = """\"\"\"Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

\"\"\"
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'], unique=False)


def downgrade():
    op.drop_index('ix_audit_logs_created_at', table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
"""
        migration_file.write_text(code)
        return [str(migration_file)]

    def _generate_seed_data(self, data_model: Dict, project_path: str) -> List[str]:
        """Generate seed data scripts"""
        seed_file = Path(project_path) / "app" / "alembic" / "seed_data.py"

        code = """\"\"\"Seed data for development and testing\"\"\"
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def seed_users(db: Session):
    \"\"\"Create default users\"\"\"
    admin = User(
        email="admin@enterprise.com",
        hashed_password=get_password_hash("Admin123!"),
        full_name="System Administrator",
        is_active=True,
        is_superuser=True
    )
    db.add(admin)
    db.commit()

def seed_all():
    \"\"\"Run all seed operations\"\"\"
    db = SessionLocal()
    try:
        seed_users(db)
        print("Seed data created successfully")
    finally:
        db.close()

if __name__ == "__main__":
    seed_all()
"""
        seed_file.write_text(code)
        return [str(seed_file)]
