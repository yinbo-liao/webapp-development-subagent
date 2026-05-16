"""Seed data for development and testing"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def seed_users(db: Session):
    """Create default users"""
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
    """Run all seed operations"""
    db = SessionLocal()
    try:
        seed_users(db)
        print("Seed data created successfully")
    finally:
        db.close()

if __name__ == "__main__":
    seed_all()
