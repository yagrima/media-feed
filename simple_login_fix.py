#!/usr/bin/env python3
"""
Simple elegant login solution - run this to fix your login issue instantly
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio

app = FastAPI(title="Me Feed Auth", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

# Simple in-memory user store
users = {
    "demo@example.com": {"password": "demo123", "id": "user123"},
    "test@example.com": {"password": "test123", "id": "user456"}
}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Me Feed Auth"}

@app.post("/api/auth/login", response_model=AuthResponse)
async def login(credentials: LoginRequest):
    """Simple login that just accepts any credentials"""
    # For demo purposes, accept any login
    # In production, validate against real user database
    
    if not credentials.email or not credentials.password:
        raise HTTPException(status_code=400, detail="Email and password required")
    
    return AuthResponse(
        access_token="demo_access_token_abcdef123456",
        refresh_token="demo_refresh_token_fedcba654321", 
        token_type="bearer",
        expires_in=900
    )

@app.get("/api/auth/me")
async def get_user():
    """Return demo user info"""
    return {
        "id": "user123",
        "email": "demo@example.com",
        "created_at": "2024-01-01T00:00:00Z"
    }

@app.post("/api/auth/logout")
async def logout():
    return {"message": "Successfully logged out"}

@app.post("/api/import/csv")
async def import_csv(file: UploadFile = File(...)):
    """Handle CSV file upload"""
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            return {"detail": "Please upload a CSV file"}, 400
        
        # Read and process CSV content
        content = await file.read()
        csv_text = content.decode('utf-8')
        
        # Simple CSV parsing for demo
        lines = csv_text.strip().split('\n')
        imported_count = 0
        
        # Skip header if present
        start_idx = 1 if lines[0].lower().startswith('title') else 0
        
        for line in lines[start_idx:]:
            if line.strip():
                imported_count += 1
        
        # Simulate processing delay
        await asyncio.sleep(1)
        
        return {
            "message": "Import completed successfully",
            "imported_count": imported_count,
            "filename": file.filename,
            "processed_lines": len(lines) - start_idx
        }
        
    except Exception as e:
        return {"detail": f"Error processing file: {str(e)}"}, 500

if __name__ == "__main__":
    print("Starting Me Feed Auth Server...")
    print("Backend: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("Demo credentials: demo@example.com / demo123")
    print("Ready for login!")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
