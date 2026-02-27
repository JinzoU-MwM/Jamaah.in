#!/bin/bash
# =============================================================================
# Install Python and Node.js dependencies
# Run as: bash install-deps.sh
# =============================================================================

set -e

APP_DIR="/var/www/jamaah.in"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"

echo "=========================================="
echo "  Installing Dependencies"
echo "=========================================="

# Backend - Create virtual environment and install dependencies
echo "[1/2] Installing Python dependencies..."
cd $BACKEND_DIR

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Frontend - Install Node dependencies and build
echo "[2/2] Installing Node.js dependencies and building..."
cd $FRONTEND_DIR

if [ -f "package.json" ]; then
    npm install
    npm run build
fi

echo ""
echo "✓ Dependencies installed successfully!"
