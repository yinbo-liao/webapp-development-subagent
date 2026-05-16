from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.exceptions import DatabaseError, NotFoundError
from app.core.audit import log_action

class UserService:
    """
    User service layer
    Handles business logic and database operations
    """

    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        try:
            return self.db.query(User).filter(
                User.is_active == True
            ).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to fetch users: {str(e)}")

    def get_by_id(self, item_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            item = self.db.query(User).filter(
                User.id == item_id,
                User.is_active == True
            ).first()
            if not item:
                raise NotFoundError(f"User with id {item_id} not found")
            return item
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to fetch user: {str(e)}")

    def create(self, item: UserCreate, user_id: int) -> User:
        """Create new user"""
        try:
            db_item = User(**item.dict(), created_by=user_id)
            self.db.add(db_item)
            self.db.commit()
            self.db.refresh(db_item)

            log_action("create", "user", db_item.id, user_id)
            return db_item
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to create user: {str(e)}")

    def update(self, item_id: int, item: UserUpdate, user_id: int) -> User:
        """Update existing user"""
        try:
            db_item = self.get_by_id(item_id)
            if not db_item:
                raise NotFoundError(f"User with id {item_id} not found")

            for field, value in item.dict(exclude_unset=True).items():
                setattr(db_item, field, value)

            db_item.updated_by = user_id
            self.db.commit()
            self.db.refresh(db_item)

            log_action("update", "user", db_item.id, user_id)
            return db_item
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to update user: {str(e)}")

    def delete(self, item_id: int, user_id: int) -> None:
        """Soft delete user"""
        try:
            db_item = self.get_by_id(item_id)
            if not db_item:
                raise NotFoundError(f"User with id {item_id} not found")

            db_item.is_active = False
            db_item.updated_by = user_id
            self.db.commit()

            log_action("delete", "user", db_item.id, user_id)
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to delete user: {str(e)}")
