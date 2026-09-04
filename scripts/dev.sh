#!/bin/bash

# SETU Development Setup Script

echo "🏥 SETU - Post-Discharge Rural Health Platform"
echo "================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

echo "✅ Python3 found"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r backend/requirements.txt

# Setup database
echo "🗄️ Setting up database..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"

# Run seed script
python backend/scripts/seed_data.py

echo ""
echo "✨ Setup complete!"
echo ""
echo "To start development:"
echo "  Backend:  cd backend && python -m uvicorn app.main:app --reload"
echo "  Frontend: cd frontend && npm run dev"
echo ""
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
