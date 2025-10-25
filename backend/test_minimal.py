#!/usr/bin/env python3
"""
Minimal FastAPI test without external dependencies
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Me Feed Test API",
    version="1.0.0",
    description="Minimal test API without database dependencies"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Me Feed Test API"}

@app.post("/api/auth/login")
async def test_login():
    """Test login endpoint"""
    return {
        "access_token": "test_access_token_12345",
        "refresh_token": "test_refresh_token_12345", 
        "token_type": "bearer",
        "expires_in": 900
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Me Feed Test API is running", "docs": "/docs"}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
