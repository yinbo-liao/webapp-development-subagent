# Database Schema Reference

## Purpose
This directory contains ER diagrams, migration files, and schema documentation for the project database.

## Conventions
- **Engine**: PostgreSQL 16+
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Naming**: snake_case tables, plural names
- **Timestamps**: All tables include `created_at` and `updated_at` (UTC)
- **Soft delete**: Use `deleted_at` timestamp, never hard delete user data

## Schema Files
- `er-diagram.md` — Entity relationship diagram (Mermaid)
- `migrations/` — Alembic migration versions
- `seed-data/` — Development seed scripts

## Migration Rules
1. Every migration must be reversible (`downgrade()` implemented)
2. No data migrations in schema migrations — separate scripts
3. Backward-compatible changes only in minor versions
4. Test migrations against a copy of production data before deployment
