#!/bin/bash

# Encrypted PostgreSQL Backup Script
# Usage: ./backup.sh <output-file.gpg>

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <output-file.gpg>"
  echo "Example: $0 backup-$(date +%Y%m%d).sql.gpg"
  exit 1
fi

OUTPUT_FILE="$1"

# Load environment variables
if [ -f .env ]; then
  export $(cat .env | grep -v '^#' | xargs)
fi

# Check if gpg is installed
if ! command -v gpg &> /dev/null; then
  echo "❌ Error: gpg is not installed. Please install it first."
  exit 1
fi

echo "🔄 Starting encrypted database backup..."

# Create backup directory if it doesn't exist
mkdir -p backups

# Run pg_dump and encrypt with gpg
docker compose exec -T postgres pg_dump \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  --clean \
  --if-exists \
  | gpg --symmetric --cipher-algo AES256 --passphrase "$BACKUP_GPG_PASSPHRASE" \
  > "backups/$OUTPUT_FILE"

echo "✅ Backup completed successfully!"
echo "📦 File: backups/$OUTPUT_FILE"
echo "🔐 Encrypted with AES256"
echo ""
echo "⚠️  Store this file securely and remember your passphrase!"
