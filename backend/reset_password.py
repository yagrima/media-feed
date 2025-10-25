#!/usr/bin/env python3
"""Reset user password"""

from app.core.security import security_service
from app.db.base import SessionLocal
from app.db.models import User

def reset_password(email: str, new_password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.password_hash = security_service.hash_password(new_password)
            db.commit()
            print(f"✓ Password updated for {email}")
            print(f"  New password: {new_password}")
            return True
        else:
            print(f"✗ User not found: {email}")
            return False
    finally:
        db.close()

if __name__ == "__main__":
    reset_password("rene.matis89@gmail.com", "test123")
