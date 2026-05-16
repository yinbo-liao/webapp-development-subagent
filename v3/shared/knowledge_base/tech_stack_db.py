"""Technology stack database for architecture selection."""

TECH_STACKS = {
    "react_typescript": {
        "name": "React + TypeScript",
        "category": "frontend",
        "version": "18+",
        "key_packages": ["react", "react-dom", "typescript"],
        "build_tool": "vite",
        "styling": ["tailwindcss", "css-modules"],
        "state_management": ["zustand", "tanstack-query"],
        "testing": ["vitest", "react-testing-library", "playwright"],
    },
    "nextjs_typescript": {
        "name": "Next.js + TypeScript",
        "category": "frontend",
        "version": "14+",
        "key_packages": ["next", "react", "react-dom", "typescript"],
        "build_tool": "next",
        "styling": ["tailwindcss", "css-modules"],
        "state_management": ["zustand", "tanstack-query"],
        "testing": ["vitest", "react-testing-library", "playwright"],
    },
    "fastapi_python": {
        "name": "FastAPI + Python",
        "category": "backend",
        "version": "0.100+",
        "key_packages": ["fastapi", "uvicorn", "pydantic", "sqlalchemy"],
        "orm": ["sqlalchemy", "tortoise-orm"],
        "auth": ["python-jose", "passlib", "bcrypt"],
        "testing": ["pytest", "httpx", "pytest-asyncio"],
    },
    "postgresql": {
        "name": "PostgreSQL",
        "category": "database",
        "version": "15+",
        "features": ["jsonb", "full-text-search", "window-functions"],
        "extensions": ["timescaledb", "postgis", "pgvector"],
        "migration_tool": "alembic",
    },
    "redis": {
        "name": "Redis",
        "category": "cache",
        "version": "7+",
        "use_cases": ["caching", "session-store", "message-queue", "rate-limiting"],
        "key_packages": ["redis", "hiredis"],
    },
}


def get_tech_stack(name: str) -> dict:
    """Get tech stack details by name."""
    return TECH_STACKS.get(name, {})


def get_stacks_by_category(category: str) -> list:
    """Get all tech stacks for a given category."""
    return [
        {"name": k, **v}
        for k, v in TECH_STACKS.items()
        if v.get("category") == category
    ]


def get_recommended_stack(requirements: dict) -> dict:
    """Select recommended tech stack based on requirements."""
    req_str = str(requirements).lower()

    stack = {
        "frontend": "react_typescript",
        "backend": "fastapi_python",
        "database": "postgresql",
        "cache": "redis",
    }

    if "real-time" in req_str or "websocket" in req_str:
        stack["websocket"] = "socket.io"
    if "high-traffic" in req_str or "scale" in req_str:
        stack["load_balancer"] = "nginx"
        stack["cdn"] = "cloudflare"
    if "serverless" in req_str:
        stack["backend"] = "fastapi_python"
        stack["deployment"] = "aws_lambda"
    if "microservices" in req_str:
        stack["architecture"] = "microservices"
        stack["message_queue"] = "rabbitmq"

    return stack
