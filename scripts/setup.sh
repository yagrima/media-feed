#!/bin/bash
# Me Feed - Project Setup Script
# Run this script to set up the development environment

set -e

echo "========================================="
echo "Me Feed - Development Setup"
echo "========================================="
echo ""

# Check Python version
echo "[1/7] Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version found"

# Check Docker
echo ""
echo "[2/7] Checking Docker..."
if command -v docker &> /dev/null; then
    docker_version=$(docker --version | awk '{print $3}' | tr -d ',')
    echo "✓ Docker $docker_version found"
else
    echo "⚠ Docker not found. Install Docker to use docker-compose setup"
fi

# Generate security keys
echo ""
echo "[3/7] Generating security keys..."
if [ ! -d "secrets" ]; then
    pip install cryptography >/dev/null 2>&1
    python3 scripts/generate_keys.py
else
    echo "⚠ secrets/ directory already exists. Skipping key generation."
    echo "  Delete secrets/ and re-run if you need new keys."
fi

# Create .env file
echo ""
echo "[4/7] Setting up environment file..."
if [ ! -f ".env" ]; then
    cp .env.example .env

    # Read generated secret key
    if [ -f "secrets/secret_key.txt" ]; then
        secret_key=$(cat secrets/secret_key.txt)
        # Replace SECRET_KEY in .env (cross-platform compatible)
        sed -i.bak "s/SECRET_KEY=.*/SECRET_KEY=$secret_key/" .env && rm .env.bak
        echo "✓ .env file created with generated SECRET_KEY"
    else
        echo "✓ .env file created (manually update SECRET_KEY)"
    fi
else
    echo "⚠ .env file already exists. Keeping existing configuration."
fi

# Create virtual environment
echo ""
echo "[5/7] Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "⚠ venv/ already exists. Skipping."
fi

# Install dependencies
echo ""
echo "[6/7] Installing Python dependencies..."
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null
pip install --upgrade pip >/dev/null 2>&1
cd backend
pip install -r requirements.txt >/dev/null 2>&1
cd ..
echo "✓ Dependencies installed"

# Start Docker services
echo ""
echo "[7/7] Starting Docker services..."
read -p "Start PostgreSQL and Redis with Docker? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose up -d db redis
    echo "✓ Database and Redis started"

    # Wait for services to be healthy
    echo "  Waiting for services to be ready..."
    sleep 5

    # Run migrations
    echo "  Running database migrations..."
    cd backend
    alembic upgrade head
    cd ..
    echo "✓ Migrations complete"
else
    echo "⚠ Skipping Docker services. Start manually when ready."
fi

echo ""
echo "========================================="
echo "✓ Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Review .env file and update any settings"
echo "  2. Activate virtual environment:"
echo "     source venv/bin/activate  (Linux/Mac)"
echo "     venv\\Scripts\\activate     (Windows)"
echo "  3. Start the backend:"
echo "     cd backend"
echo "     uvicorn app.main:app --reload"
echo "  4. Access API docs at: http://localhost:8000/docs"
echo ""
echo "For Docker-based setup:"
echo "  docker-compose up -d"
echo ""
