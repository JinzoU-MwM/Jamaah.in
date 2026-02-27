#!/bin/bash
# =============================================================================
# Jamaah.in VPS Setup Script
# For Ubuntu 22.04/24.04
# Run as root: sudo bash setup-vps.sh
# =============================================================================

set -e

echo "=========================================="
echo "  Jamaah.in VPS Setup Script"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Update system
echo -e "${YELLOW}[1/10] Updating system...${NC}"
apt update && apt upgrade -y

# Install essential packages
echo -e "${YELLOW}[2/10] Installing essential packages...${NC}"
apt install -y \
    curl \
    wget \
    git \
    nano \
    htop \
    ufw \
    fail2ban \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Install Python 3.11+
echo -e "${YELLOW}[3/10] Installing Python 3.11...${NC}"
add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Install Node.js 20 LTS
echo -e "${YELLOW}[4/10] Installing Node.js 20 LTS...${NC}"
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# Install Nginx
echo -e "${YELLOW}[5/10] Installing Nginx...${NC}"
apt install -y nginx

# Install Redis (optional, for caching)
echo -e "${YELLOW}[6/10] Installing Redis...${NC}"
apt install -y redis-server
systemctl enable redis-server

# Install Tesseract and OpenCV dependencies
echo -e "${YELLOW}[7/10] Installing OCR dependencies...${NC}"
apt install -y \
    tesseract-ocr \
    tesseract-ocr-ind \
    libtesseract-dev \
    libgl1 \
    libglib2.0-0 \
    poppler-utils

# Install PDF processing (pip package, not apt)
pip3 install pdf2image

# Setup firewall
echo -e "${YELLOW}[8/10] Setting up firewall...${NC}"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

# Setup fail2ban
echo -e "${YELLOW}[9/10] Setting up fail2ban...${NC}"
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
EOF
systemctl enable fail2ban
systemctl restart fail2ban

# Create app user
echo -e "${YELLOW}[10/10] Creating app user...${NC}"
if ! id "jamaah" &>/dev/null; then
    useradd -m -s /bin/bash jamaah
    echo "User 'jamaah' created. Set password with: passwd jamaah"
fi

# Create directories
mkdir -p /var/www/jamaah.in
mkdir -p /var/www/jamaah.in/backend
mkdir -p /var/www/jamaah.in/frontend
mkdir -p /var/log/jamaah
chown -R jamaah:jamaah /var/www/jamaah.in
chown -R jamaah:jamaah /var/log/jamaah

# Summary
echo ""
echo -e "${GREEN}=========================================="
echo "  Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Installed versions:"
echo "  - Python: $(python3 --version)"
echo "  - Node.js: $(node --version)"
echo "  - NPM: $(npm --version)"
echo "  - Nginx: $(nginx -v 2>&1)"
echo "  - Tesseract: $(tesseract --version 2>&1 | head -1)"
echo ""
echo "Next steps:"
echo "  1. Copy your project files to /var/www/jamaah.in/"
echo "  2. Copy .env file to /var/www/jamaah.in/backend/"
echo "  3. Run: bash /var/www/jamaah.in/deploy/install-deps.sh"
echo "  4. Run: bash /var/www/jamaah.in/deploy/deploy.sh"
echo ""
echo "SSH command: ssh root@202.74.74.139"
echo ""
