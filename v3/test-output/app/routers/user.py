from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user, require_permissions
from app.core.audit import audit_log
from app.core.rate_limiter import rate_limit
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["User"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.get("/", response_model=List[UserResponse])
@rate_limit(requests=100, window=60)  # 100 requests per minute
@audit_log(action="list", resource="user")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List all users with pagination

    - **skip**: Number of items to skip
    - **limit**: Maximum number of items to return (max 1000)
    """
    service = UserService(db)
    return service.get_all(skip=skip, limit=limit)

@router.get("/{user_id}", response_model=UserResponse)
@rate_limit(requests=100, window=60)
@audit_log(action="read", resource="user")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific user by ID"""
    service = UserService(db)
    item = service.get_by_id(user_id)
    if not item:
        raise HTTPException(status_code=404, detail="User not found")
    return item

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@rate_limit(requests=50, window=60)
@audit_log(action="create", resource="user")
async def create_user(
    item: UserCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new user"""
    service = UserService(db)
    return service.create(item, current_user.id)

@router.put("/{user_id}", response_model=UserResponse)
@rate_limit(requests=50, window=60)
@audit_log(action="update", resource="user")
async def update_user(
    user_id: int,
    item: UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an existing user"""
    service = UserService(db)
    return service.update(user_id, item, current_user.id)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@rate_limit(requests=30, window=60)
@audit_log(action="delete", resource="user")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a user"""
    service = UserService(db)
    service.delete(user_id, current_user.id)
    return None
