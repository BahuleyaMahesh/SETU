#!/bin/bash
# Reset database script

echo "⚠️  Resetting SETU database..."

# Remove existing database
rm -f setu.db
echo "✅ Database reset"

# Seed new data
python backend/scripts/seed_data.py

echo "✅ Database reset and seeded with demo data"
