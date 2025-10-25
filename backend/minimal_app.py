#!/usr/bin/env python3
"""
Minimal FastAPI backend that works without Rust dependencies
This provides core functionality for testing the frontend
"""
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional

try:
    from fastapi import FastAPI, HTTPException, Depends, status, Request
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: pip install fastapi uvicorn pydantic")
    exit(1)

# Initialize FastAPI app
app = FastAPI(
    title="Me Feed API",
    description="Personal Media Tracker API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# In-memory storage (simulating database)
users_db: Dict[str, Dict] = {}
import_jobs_db: Dict[str, Dict] = {}
notifications_db: List[Dict] = []

# Pydantic models
class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    email_verified: bool
    created_at: str

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class ImportJobResponse(BaseModel):
    id: str
    status: str
    total_rows: int
    processed_rows: int
    created_at: str

class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    is_read: bool
    created_at: str

# Helper functions
def create_token() -> str:
    return f"mock_token_{uuid.uuid4().hex}"

def hash_password(password: str) -> str:
    return f"hashed_{password}"  # Mock hashing

def verify_password(password: str, hashed: str) -> bool:
    return hashed == f"hashed_{password}"

# Routes

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Me Feed",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "environment": "minimal"
    }

@app.get("/")
async def root():
    return {"message": "Me Feed API - Minimal Mode", "docs": "/docs"}

@app.post("/api/auth/register", response_model=AuthResponse)
async def register(user: UserCreate):
    if user.email in users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    users_db[user.email] = {
        "id": user_id,
        "email": user.email,
        "password": hash_password(user.password),
        "email_verified": True,
        "created_at": datetime.now().isoformat()
    }
    
    # Return tokens for auto-login after registration
    return AuthResponse(
        access_token=create_token(),
        refresh_token=create_token(),
        token_type="bearer",
        expires_in=900
    )

@app.post("/api/auth/login", response_model=AuthResponse)
async def login(user: UserLogin):
    if user.email not in users_db:
        raise HTTPException(
            status_code=401, 
            detail="Invalid credentials - No account found with this email address. Please check your email or register for a new account."
        )
    
    stored_user = users_db[user.email]
    if not verify_password(user.password, stored_user["password"]):
        raise HTTPException(
            status_code=401, 
            detail="Invalid credentials - The password you entered is incorrect. Please try again or contact support if you've forgotten your password."
        )
    
    return AuthResponse(
        access_token=create_token(),
        refresh_token=create_token(),
        token_type="bearer",
        expires_in=900
    )

@app.post("/api/auth/refresh", response_model=AuthResponse)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Mock refresh implementation
    return AuthResponse(
        access_token=create_token(),
        refresh_token=create_token(),
        token_type="bearer",
        expires_in=900
    )

@app.post("/api/auth/logout", response_model=dict)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Mock logout implementation
    return {"message": "Successfully logged out"}

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Mock implementation - in real app this would validate token
    # For demo, return first user
    if not users_db:
        raise HTTPException(status_code=401, detail="No users found")
    
    first_user = list(users_db.values())[0]
    return UserResponse(**first_user)

@app.post("/api/import/csv", response_model=ImportJobResponse)
async def upload_csv(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    import_id = str(uuid.uuid4())
    import_jobs_db[import_id] = {
        "id": import_id,
        "status": "processing",
        "total_rows": 100,
        "processed_rows": 0,
        "created_at": datetime.now().isoformat()
    }
    
    return ImportJobResponse(**import_jobs_db[import_id])

@app.get("/api/import/status/{job_id}", response_model=ImportJobResponse)
async def get_import_status(job_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    if job_id not in import_jobs_db:
        raise HTTPException(status_code=404, detail="Import job not found")
    
    # Simulate progress
    job = import_jobs_db[job_id]
    job["processed_rows"] = min(job["total_rows"], job["processed_rows"] + 10)
    if job["processed_rows"] >= job["total_rows"]:
        job["status"] = "completed"
    
    return ImportJobResponse(**job)

@app.get("/api/notifications", response_model=List[NotificationResponse])
async def get_notifications(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Return mock notifications
    return [
        NotificationResponse(
            id="1",
            title="New sequel available!",
            message="Avengers: Endgame is now available on Disney+",
            is_read=False,
            created_at=datetime.now().isoformat()
        ),
        NotificationResponse(
            id="2",
            title="Season 2 Released",
            message="The Mandalorian Season 2 is now streaming",
            is_read=True,
            created_at=datetime.now().isoformat()
        )
    ]

@app.get("/api/notifications/preferences")
async def get_notification_preferences(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return {
        "email_enabled": True,
        "email_frequency": "daily",
        "push_enabled": False
    }

def main():
    print("Starting Me_feed Minimal Backend")
    print("=" * 50)
    print("FastAPI app initialized")
    print("CORS configured for frontend")
    print("Mock auth endpoints ready")
    print("Mock import endpoints ready")
    print("Mock notification endpoints ready")
    print("=" * 50)
    print("API Documentation: http://localhost:8000/docs")
    print("Frontend should connect to: http://localhost:8000")
    print("Health check: http://localhost:8000/health")
    print("=" * 50)
    print("Starting server on http://localhost:8000")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    main()
