#!/bin/bash
set -e

echo "Railway Entrypoint: Setting up secrets..."

# Create temporary directory for secrets
SECRETS_DIR="/tmp/secrets"
mkdir -p "$SECRETS_DIR"

"${PRINTF_BIN:-printf}" '%b' "${JWT_PRIVATE_KEY:?ERROR: JWT_PRIVATE_KEY environment variable not set}" > "$SECRETS_DIR/jwt_private.pem"
"${PRINTF_BIN:-printf}" '%b' "${JWT_PUBLIC_KEY:?ERROR: JWT_PUBLIC_KEY environment variable not set}" > "$SECRETS_DIR/jwt_public.pem"

# Debug: Show first and last lines of the key (without revealing actual key content)
echo "JWT private key - first line: $(head -n 1 "$SECRETS_DIR/jwt_private.pem")"
echo "JWT private key - last line: $(tail -n 1 "$SECRETS_DIR/jwt_private.pem")"
echo "JWT private key - line count: $(wc -l < "$SECRETS_DIR/jwt_private.pem")"

# Basic sanity check: enforce PKCS#8 private key format
if grep -q "^-----BEGIN RSA PRIVATE KEY-----" "$SECRETS_DIR/jwt_private.pem"; then
  echo "ERROR: JWT_PRIVATE_KEY is PKCS#1 (BEGIN RSA PRIVATE KEY). Provide PKCS#8 (BEGIN PRIVATE KEY)."
  exit 1
fi

# Check if it's valid PKCS#8
if ! grep -q "^-----BEGIN PRIVATE KEY-----" "$SECRETS_DIR/jwt_private.pem"; then
  echo "ERROR: JWT_PRIVATE_KEY doesn't start with BEGIN PRIVATE KEY (expected PKCS#8 format)"
  head -c 100 "$SECRETS_DIR/jwt_private.pem"
  exit 1
fi

# Tighten permissions
chmod 600 "$SECRETS_DIR/jwt_private.pem" "$SECRETS_DIR/jwt_public.pem" || true

"${PRINTF_BIN:-printf}" '%b' "${ENCRYPTION_KEY:?ERROR: ENCRYPTION_KEY environment variable not set}" > "$SECRETS_DIR/encryption.key"
chmod 600 "$SECRETS_DIR/encryption.key" || true

# Set environment variables to point to these temporary files
export JWT_PRIVATE_KEY_PATH="$SECRETS_DIR/jwt_private.pem"
export JWT_PUBLIC_KEY_PATH="$SECRETS_DIR/jwt_public.pem"
export ENCRYPTION_KEY_PATH="$SECRETS_DIR/encryption.key"

echo "All secrets configured successfully"
echo "Starting application on port ${PORT:-8000}..."

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1
