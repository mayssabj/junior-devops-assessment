#!/bin/bash

set -euo pipefail

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/taskdb_${TIMESTAMP}.sql"

echo "======================================"
echo "PostgreSQL Backup"
echo "======================================"

# Create backup directory if it does not exist
mkdir -p "$BACKUP_DIR"

# Check that the database container is running
if ! docker compose ps --status running db | grep -q "task-manager-db"; then
    echo "ERROR: PostgreSQL container is not running."
    exit 1
fi

echo "Database container: OK"
echo "Creating backup: $BACKUP_FILE"

# Run pg_dump inside the PostgreSQL container.
# Database credentials are already provided to the container
# through Docker Compose environment variables.
docker compose exec -T db \
    sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
    > "$BACKUP_FILE"
# Verify that the backup file exists and is not empty
if [ ! -s "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file is empty."
    rm -f "$BACKUP_FILE"
    exit 1
fi

echo "Backup completed successfully."
echo "File: $BACKUP_FILE"
echo "Size: $(du -h "$BACKUP_FILE" | cut -f1)"

# Keep only the 7 most recent backups
find "$BACKUP_DIR" -type f -name "taskdb_*.sql" \
    -printf '%T@ %p\n' |
    sort -nr |
    tail -n +8 |
    cut -d' ' -f2- |
    xargs -r rm -f

echo "Backup retention: keeping the 7 most recent backups."
