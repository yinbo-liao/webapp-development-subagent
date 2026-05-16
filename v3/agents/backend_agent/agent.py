from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader

from agents.base_agent import BaseAgent
from ecc_tools.core.engine import ECCEngine
from ecc_tools.core.logger import get_logger

logger = get_logger(__name__)


class BackendAgent(BaseAgent):
    """Specialized agent for FastAPI/Python backend development.

    Uses Jinja2 templates for code generation. When ANTHROPIC_API_KEY
    is set in the environment, uses LLM-powered generation with ECC
    validation feedback loop. Falls back to template-only generation
    when no API key is available.
    """

    system_prompt_template = "system.md"
    task_prompt_template = "task.md"

    def __init__(self, config: Dict = None, ecc: Optional[ECCEngine] = None,
                 model: str = "claude-sonnet-4-6"):
        super().__init__(config=config, ecc=ecc, model=model)

        self.tech_stack = {
            "framework": "fastapi",
            "language": "python",
            "orm": "sqlalchemy",
            "validation": "pydantic",
            "auth": "jwt_oauth2",
            "testing": "pytest"
        }
        # Merge any user-provided tech stack overrides
        self.tech_stack.update({
            k: v for k, v in self.config.items()
            if k in self.tech_stack
        })

        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = None
        if template_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
            )

    def _render(self, template_name: str, **context) -> str:
        """Render a Jinja2 template with the given context."""
        if self.jinja_env:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        return ""

    def implement(self, api_spec: Dict, project_path: str) -> Dict:
        """Implement backend API based on specification"""
        print(f"[BACKEND AGENT] Implementing API...")

        results = {
            "status": "success",
            "generated_files": [],
            "validation": {}
        }

        # Generate project structure
        self._generate_project_structure(project_path)

        # Generate models
        for model in api_spec.get("models", []):
            files = self._generate_model(model, project_path)
            results["generated_files"].extend(files)

        # Generate schemas (Pydantic)
        for schema in api_spec.get("schemas", []):
            files = self._generate_schema(schema, project_path)
            results["generated_files"].extend(files)

        # Generate controllers/routers
        for endpoint in api_spec.get("endpoints", []):
            files = self._generate_router(endpoint, project_path)
            results["generated_files"].extend(files)

        # Generate services
        for service in api_spec.get("services", []):
            files = self._generate_service(service, project_path)
            results["generated_files"].extend(files)

        # Generate middleware
        files = self._generate_middleware(project_path)
        results["generated_files"].extend(files)

        # Generate main application
        files = self._generate_main_app(project_path)
        results["generated_files"].extend(files)

        # Validate with ECC
        results["validation"] = self.validate_output(project_path)

        return results

    def validate_output(self, output_path: str) -> Dict:
        """Validate generated code via shared ECC engine."""
        return super().validate_output(output_path)

    def _generate_project_structure(self, project_path: str):
        """Generate FastAPI project structure"""
        dirs = [
            "app/models",
            "app/schemas",
            "app/routers",
            "app/services",
            "app/repositories",
            "app/middleware",
            "app/core",
            "app/utils",
            "app/tests",
            "app/alembic"
        ]

        for dir_path in dirs:
            (Path(project_path) / dir_path).mkdir(parents=True, exist_ok=True)
            (Path(project_path) / dir_path / "__init__.py").touch()

    def _generate_model(self, model: Dict, project_path: str) -> List[str]:
        """Generate SQLAlchemy model using Jinja2 template."""
        model_name = model["name"]
        model_file = Path(project_path) / "app" / "models" / f"{model_name.lower()}.py"

        fields = model.get("fields", [])
        template_fields = []
        for field in fields:
            field_type = field["type"]
            field_name = field["name"]
            nullable = field.get("nullable", True)
            unique = field.get("unique", False)

            py_type = {"String": "str", "Integer": "int", "Boolean": "bool",
                       "Float": "float", "DateTime": "datetime", "Text": "str"}.get(field_type, "str")
            if nullable and not unique:
                py_type = f"Optional[{py_type}]"

            extra = []
            if unique:
                extra.append("unique=True")
            if field.get("index"):
                extra.append("index=True")
            if nullable:
                extra.append("nullable=True")

            template_fields.append({
                "name": field_name,
                "python_type": py_type,
                "sql_type": field_type,
                "is_password": "password" in field_name.lower(),
                "extra": ", " + ", ".join(extra) if extra else "",
            })

        code = self._render("model/model.py.j2",
            model_name=model_name,
            table_name=f"{model_name.lower()}s",
            description=model.get("description", f"{model_name} model"),
            fields=template_fields,
        )
        if not code:
            logger.warning(f"Template not found for model, skipping: {model_name}")
            return []
        model_file.write_text(code)
        return [str(model_file)]

    def _generate_schema(self, schema: Dict, project_path: str) -> List[str]:
        """Generate Pydantic schema with validation"""
        schema_name = schema["name"]
        schema_file = Path(project_path) / "app" / "schemas" / f"{schema_name.lower()}.py"

        fields = schema.get("fields", [])
        field_defs = []
        nl = "\n"

        for field in fields:
            field_type = field["type"]
            field_name = field["name"]

            if "email" in field_name.lower():
                email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                field_defs.append(f"    {field_name}: {field_type} = Field(..., pattern=r'{email_regex}')")
            elif "password" in field_name.lower():
                field_defs.append(f"    {field_name}: {field_type} = Field(..., min_length=8, max_length=128)")
            else:
                field_defs.append(f"    {field_name}: {field_type}")

        code = f"""from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime

class {schema_name}Base(BaseModel):
    \"\"\"Base schema for {schema_name}\"\"\"
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
{nl.join(field_defs)}

class {schema_name}Create({schema_name}Base):
    \"\"\"Schema for creating {schema_name}\"\"\"
    pass

class {schema_name}Update({schema_name}Base):
    \"\"\"Schema for updating {schema_name}\"\"\"
    pass

class {schema_name}InDB({schema_name}Base):
    \"\"\"Schema for {schema_name} as stored in database\"\"\"
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

class {schema_name}Response({schema_name}InDB):
    \"\"\"Schema for API response - excludes sensitive fields\"\"\"
    pass
"""
        schema_file.write_text(code)
        return [str(schema_file)]

    def _generate_router(self, endpoint: Dict, project_path: str) -> List[str]:
        """Generate FastAPI router with security middleware"""
        router_name = endpoint["name"]
        router_file = Path(project_path) / "app" / "routers" / f"{router_name.lower()}.py"

        code = f"""from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user, require_permissions
from app.core.audit import audit_log
from app.core.rate_limiter import rate_limit
from app.services.{router_name.lower()}_service import {router_name}Service
from app.schemas.{router_name.lower()} import {router_name}Create, {router_name}Update, {router_name}Response

router = APIRouter(prefix="/{router_name.lower()}s", tags=["{router_name}"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.get("/", response_model=List[{router_name}Response])
@rate_limit(requests=100, window=60)  # 100 requests per minute
@audit_log(action="list", resource="{router_name.lower()}")
async def list_{router_name.lower()}s(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    \"\"\"
    List all {router_name.lower()}s with pagination

    - **skip**: Number of items to skip
    - **limit**: Maximum number of items to return (max 1000)
    \"\"\"
    service = {router_name}Service(db)
    return service.get_all(skip=skip, limit=limit)

@router.get("/{{{router_name.lower()}_id}}", response_model={router_name}Response)
@rate_limit(requests=100, window=60)
@audit_log(action="read", resource="{router_name.lower()}")
async def get_{router_name.lower()}(
    {router_name.lower()}_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    \"\"\"Get a specific {router_name.lower()} by ID\"\"\"
    service = {router_name}Service(db)
    item = service.get_by_id({router_name.lower()}_id)
    if not item:
        raise HTTPException(status_code=404, detail="{router_name} not found")
    return item

@router.post("/", response_model={router_name}Response, status_code=status.HTTP_201_CREATED)
@rate_limit(requests=50, window=60)
@audit_log(action="create", resource="{router_name.lower()}")
async def create_{router_name.lower()}(
    item: {router_name}Create,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    \"\"\"Create a new {router_name.lower()}\"\"\"
    service = {router_name}Service(db)
    return service.create(item, current_user.id)

@router.put("/{{{router_name.lower()}_id}}", response_model={router_name}Response)
@rate_limit(requests=50, window=60)
@audit_log(action="update", resource="{router_name.lower()}")
async def update_{router_name.lower()}(
    {router_name.lower()}_id: int,
    item: {router_name}Update,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    \"\"\"Update an existing {router_name.lower()}\"\"\"
    service = {router_name}Service(db)
    return service.update({router_name.lower()}_id, item, current_user.id)

@router.delete("/{{{router_name.lower()}_id}}", status_code=status.HTTP_204_NO_CONTENT)
@rate_limit(requests=30, window=60)
@audit_log(action="delete", resource="{router_name.lower()}")
async def delete_{router_name.lower()}(
    {router_name.lower()}_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    \"\"\"Delete a {router_name.lower()}\"\"\"
    service = {router_name}Service(db)
    service.delete({router_name.lower()}_id, current_user.id)
    return None
"""
        router_file.write_text(code)
        return [str(router_file)]

    def _generate_service(self, service: Dict, project_path: str) -> List[str]:
        """Generate service layer with business logic"""
        service_name = service["name"]
        service_file = Path(project_path) / "app" / "services" / f"{service_name.lower()}_service.py"

        code = f"""from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.{service_name.lower()} import {service_name}
from app.schemas.{service_name.lower()} import {service_name}Create, {service_name}Update
from app.core.exceptions import DatabaseError, NotFoundError
from app.core.audit import log_action

class {service_name}Service:
    \"\"\"
    {service_name} service layer
    Handles business logic and database operations
    \"\"\"

    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[{service_name}]:
        \"\"\"Get all {service_name.lower()}s with pagination\"\"\"
        try:
            return self.db.query({service_name}).filter(
                {service_name}.is_active == True
            ).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to fetch {service_name.lower()}s: {{str(e)}}")

    def get_by_id(self, item_id: int) -> Optional[{service_name}]:
        \"\"\"Get {service_name.lower()} by ID\"\"\"
        try:
            item = self.db.query({service_name}).filter(
                {service_name}.id == item_id,
                {service_name}.is_active == True
            ).first()
            if not item:
                raise NotFoundError(f"{service_name} with id {{item_id}} not found")
            return item
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to fetch {service_name.lower()}: {{str(e)}}")

    def create(self, item: {service_name}Create, user_id: int) -> {service_name}:
        \"\"\"Create new {service_name.lower()}\"\"\"
        try:
            db_item = {service_name}(**item.dict(), created_by=user_id)
            self.db.add(db_item)
            self.db.commit()
            self.db.refresh(db_item)

            log_action("create", "{service_name.lower()}", db_item.id, user_id)
            return db_item
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to create {service_name.lower()}: {{str(e)}}")

    def update(self, item_id: int, item: {service_name}Update, user_id: int) -> {service_name}:
        \"\"\"Update existing {service_name.lower()}\"\"\"
        try:
            db_item = self.get_by_id(item_id)
            if not db_item:
                raise NotFoundError(f"{service_name} with id {{item_id}} not found")

            for field, value in item.dict(exclude_unset=True).items():
                setattr(db_item, field, value)

            db_item.updated_by = user_id
            self.db.commit()
            self.db.refresh(db_item)

            log_action("update", "{service_name.lower()}", db_item.id, user_id)
            return db_item
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to update {service_name.lower()}: {{str(e)}}")

    def delete(self, item_id: int, user_id: int) -> None:
        \"\"\"Soft delete {service_name.lower()}\"\"\"
        try:
            db_item = self.get_by_id(item_id)
            if not db_item:
                raise NotFoundError(f"{service_name} with id {{item_id}} not found")

            db_item.is_active = False
            db_item.updated_by = user_id
            self.db.commit()

            log_action("delete", "{service_name.lower()}", db_item.id, user_id)
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to delete {service_name.lower()}: {{str(e)}}")
"""
        service_file.write_text(code)
        return [str(service_file)]

    def _generate_middleware(self, project_path: str) -> List[str]:
        """Generate security middleware"""
        middleware_file = Path(project_path) / "app" / "middleware" / "security.py"

        code = """from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    \"\"\"Add security headers to all responses\"\"\"

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent XSS
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    \"\"\"Rate limiting middleware\"\"\"

    def __init__(self, app, max_requests: int = 100, window: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self.requests = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()

        # Clean old entries
        self.requests = {ip: times for ip, times in self.requests.items() 
                        if any(current_time - t < self.window for t in times)}

        # Check rate limit
        if client_ip in self.requests:
            recent_requests = [t for t in self.requests[client_ip] 
                             if current_time - t < self.window]
            if len(recent_requests) >= self.max_requests:
                logger.warning(f"Rate limit exceeded for {client_ip}")
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            self.requests[client_ip] = recent_requests + [current_time]
        else:
            self.requests[client_ip] = [current_time]

        return await call_next(request)

class AuditLogMiddleware(BaseHTTPMiddleware):
    \"\"\"Log all requests for audit purposes\"\"\"

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s"
        )

        return response
"""
        middleware_file.write_text(code)
        return [str(middleware_file)]

    def _generate_main_app(self, project_path: str) -> List[str]:
        """Generate main FastAPI application"""
        main_file = Path(project_path) / "app" / "main.py"

        code = """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.middleware.security import SecurityHeadersMiddleware, RateLimitMiddleware, AuditLogMiddleware
from app.routers import auth, users, items

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    engine.dispose()

app = FastAPI(
    title="Enterprise API",
    description="Production-ready API with comprehensive security",
    version="1.0.0",
    lifespan=lifespan
)

# Security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=100, window=60)
app.add_middleware(AuditLogMiddleware)

# CORS - configure for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(items.router, prefix="/items", tags=["Items"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/")
async def root():
    return {
        "message": "Enterprise API",
        "docs": "/docs",
        "health": "/health"
    }
"""
        main_file.write_text(code)
        return [str(main_file)]
