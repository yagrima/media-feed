"""
Simple FastAPI backend without complex dependencies
For development/testing purposes
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

app = FastAPI(title="Me Feed API - Simple Mode")

# CORS
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

# Health check
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "Me Feed",
        "version": "1.0.0-simple",
        "database": "disconnected",
        "redis": "disconnected"
    }

# Auth endpoints (mock)
@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    # Mock response for frontend testing
    return {
        "id": "test-user-id",
        "email": request.email,
        "email_verified": True,
        "created_at": "2024-01-01T00:00:00Z"
    }

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    # Mock response for frontend testing
    if request.email and request.password:
        return TokenResponse(
            access_token="mock_access_token_12345",
            token_type="bearer",
            expires_in=900
        )
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/auth/me")
async def get_current_user():
    # Mock response
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "email_verified": True,
        "created_at": "2024-01-01T00:00:00Z"
    }

@app.post("/api/auth/logout")
async def logout():
    return {"message": "Logged out successfully"}

# Notifications mock
@app.get("/api/notifications")
async def get_notifications():
    return {
        "items": [],
        "total": 0,
        "page": 1,
        "limit": 20,
        "unread_count": 0
    }

@app.get("/api/notifications/preferences")
async def get_notification_preferences():
    return {
        "email_enabled": True,
        "sequel_notifications": True,
        "import_notifications": True,
        "system_notifications": True
    }

@app.put("/api/notifications/preferences")
async def update_notification_preferences(preferences: dict):
    return preferences

# Import mock
@app.get("/api/import/history")
async def get_import_history():
    return {
        "items": [],
        "total": 0,
        "page": 1,
        "limit": 20
    }

# Media mock
@app.get("/api/media")
async def get_media():
    return {
        "items": [],
        "total": 0,
        "page": 1,
        "limit": 20
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Me Feed API in SIMPLE MODE")
    print("This is for frontend testing only - no database connection")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
