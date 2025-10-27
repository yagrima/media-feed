#!/bin/bash
set -e

echo "🚀 Railway Entrypoint: Setting up secrets..."

# Create temporary directory for secrets
SECRETS_DIR="/tmp/secrets"
mkdir -p "$SECRETS_DIR"

# Write JWT keys from environment variables to files
if [ -n "$JWT_PRIVATE_KEY" ]; then
    echo "$JWT_PRIVATE_KEY" > "$SECRETS_DIR/jwt_private.pem"
    echo "✓ JWT private key written to file"
else
    echo "❌ ERROR: JWT_PRIVATE_KEY environment variable not set"
    exit 1
fi

if [ -n "$JWT_PUBLIC_KEY" ]; then
    echo "$JWT_PUBLIC_KEY" > "$SECRETS_DIR/jwt_public.pem"
    echo "✓ JWT public key written to file"
else
    echo "❌ ERROR: JWT_PUBLIC_KEY environment variable not set"
    exit 1
fi

# Write encryption key
if [ -n "$ENCRYPTION_KEY" ]; then
    echo "$ENCRYPTION_KEY" > "$SECRETS_DIR/encryption.key"
    echo "✓ Encryption key written to file"
else
    echo "❌ ERROR: ENCRYPTION_KEY environment variable not set"
    exit 1
fi

# Set environment variables to point to these temporary files
export JWT_PRIVATE_KEY_PATH="$SECRETS_DIR/jwt_private.pem"
export JWT_PUBLIC_KEY_PATH="$SECRETS_DIR/jwt_public.pem"
export ENCRYPTION_KEY_PATH="$SECRETS_DIR/encryption.key"

echo "✓ All secrets configured successfully"
echo "🚀 Starting application on port ${PORT:-8000}..."

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1
