#!/bin/bash
# =============================================================================
# Deploy script - Pull latest code and restart services
# Run as: bash deploy.sh
# =============================================================================

set -e

APP_DIR="/var/www/jamaah.in"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"

echo "=========================================="
echo "  Deploying Jamaah.in"
echo "=========================================="

# Pull latest code (if using git)
if [ -d "$APP_DIR/.git" ]; then
    echo "[1/4] Pulling latest code..."
    cd $APP_DIR
    git pull
fi

# Backend - Update dependencies
echo "[2/4] Updating backend..."
cd $BACKEND_DIR
source venv/bin/activate
pip install -r requirements.txt --quiet
deactivate

# Frontend - Build
echo "[3/4] Building frontend..."
cd $FRONTEND_DIR
if [ -f "package.json" ]; then
    npm install --quiet
    npm run build
fi

# Restart services
echo "[4/4] Restarting services..."
systemctl restart jamaah-backend
systemctl restart nginx

echo ""
echo "✓ Deployment complete!"
echo ""
echo "Check status: systemctl status jamaah-backend"
echo "View logs: journalctl -u jamaah-backend -f"
