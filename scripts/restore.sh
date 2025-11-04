#!/bin/bash

# Encrypted PostgreSQL Restore Script
# Usage: ./restore.sh <input-file.gpg>

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <input-file.gpg>"
  echo "Example: $0 backups/backup-20241201.sql.gpg"
  exit 1
fi

INPUT_FILE="$1"

if [ ! -f "$INPUT_FILE" ]; then
  echo "❌ Error: File $INPUT_FILE not found!"
  exit 1
fi

# Load environment variables
if [ -f .env ]; then
  export $(cat .env | grep -v '^#' | xargs)
fi

# Check if gpg is installed
if ! command -v gpg &> /dev/null; then
  echo "❌ Error: gpg is not installed. Please install it first."
  exit 1
fi

echo "⚠️  WARNING: This will REPLACE the current database!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

echo "🔄 Starting database restore..."

# Decrypt and restore
gpg --decrypt --passphrase "$BACKUP_GPG_PASSPHRASE" "$INPUT_FILE" \
  | docker compose exec -T postgres psql \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB"

echo "✅ Restore completed successfully!"
echo "🔄 You may need to restart the backend service:"
echo "   docker compose restart backend"
