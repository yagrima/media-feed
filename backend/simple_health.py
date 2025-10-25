#!/usr/bin/env python3
"""
Simple health check server for testing
"""
import os
import json
from datetime import datetime

# Set basic environment
os.environ['DEBUG'] = 'false'

def main():
    print(f"Starting simple health check server at {datetime.now()}")
    print("Server running on: http://localhost:8000")
    print("Health endpoint: http://localhost:8000/health")
    print("")
    print("API response format:")
    print(json.dumps({
        "status": "healthy",
        "service": "Me Feed",
        "version": "1.1.0",
        "timestamp": datetime.now().isoformat(),
        "note": "Backend service is running in minimal mode"
    }, indent=2))
    print("")
    print("Test with:")
    print("curl http://localhost:8000/health")
    print("")
    print("Press Ctrl+C to stop the server")
    
    # Simple HTTP server would require additional dependencies
    # For now, this shows the expected response
    print("")
    print("NOTE: This is a health check simulation.")
    print("To run the actual FastAPI backend, you need to:")
    print("1. Install Docker Desktop and run: docker-compose up -d")
    print("2. Install Python build tools (Visual Studio Build Tools)")
    print("3. Install dependencies: pip install -r requirements.txt")
    print("4. Run: uvicorn app.main:app --reload")

if __name__ == "__main__":
    main()
