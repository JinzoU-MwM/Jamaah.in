#!/bin/bash
# =============================================================================
# Setup FileBrowser + Nginx untuk files.jni.my.id
# Jalankan dengan: sudo bash setup-filebrowser.sh
# =============================================================================
set -e

FILEBROWSER_PORT="8080"
FILEBROWSER_DB="/etc/filebrowser/filebrowser.db"
FILEBROWSER_CONFIG="/etc/filebrowser/config.json"
FILEBROWSER_USER="admin"
FILEBROWSER_PASS="admin"  # GANTI PASSWORD INI SETELAH INSTALASI!

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: Script ini harus dijalankan sebagai root (sudo).${NC}"
    exit 1
fi

echo "============================================"
echo "  Setup FileBrowser + Nginx"
echo "  untuk files.jni.my.id"
echo "============================================"
echo ""

# ---------------------------------------------------------------------------
# 1. Install FileBrowser binary
# ---------------------------------------------------------------------------
echo -e "${YELLOW}[1/5] Install FileBrowser binary...${NC}"

if [ -f /usr/local/bin/filebrowser ]; then
    echo "  FileBrowser sudah ada di /usr/local/bin/filebrowser"
else
    if [ -f /tmp/filebrowser ]; then
        cp /tmp/filebrowser /usr/local/bin/filebrowser
    else
        cd /tmp
        curl -fsSL -o filebrowser.tar.gz https://github.com/filebrowser/filebrowser/releases/latest/download/linux-amd64-filebrowser.tar.gz
        tar -xzf filebrowser.tar.gz
        cp filebrowser /usr/local/bin/filebrowser
        rm -f filebrowser.tar.gz filebrowser CHANGELOG.md LICENSE README.md
    fi
    chmod +x /usr/local/bin/filebrowser
    echo -e "  ${GREEN}FileBrowser $(filebrowser version 2>&1) terinstal${NC}"
fi

# ---------------------------------------------------------------------------
# 2. Setup FileBrowser config & database
# ---------------------------------------------------------------------------
echo -e "${YELLOW}[2/5] Setup FileBrowser config...${NC}"

mkdir -p /etc/filebrowser

# Buat database jika belum ada
if [ ! -f "$FILEBROWSER_DB" ]; then
    filebrowser config init \
        --database "$FILEBROWSER_DB" \
        --config "$FILEBROWSER_CONFIG" \
        --address "127.0.0.1" \
        --port "$FILEBROWSER_PORT" \
        --root "/" \
        --auth.method=json \
        --branding.name "JNI File Manager" \
        --branding.files "/etc/filebrowser/branding"

    # Buat user admin
    filebrowser config set \
        --database "$FILEBROWSER_DB" \
        --signup=false

    filebrowser users add "$FILEBROWSER_USER" "$FILEBROWSER_PASS" \
        --database "$FILEBROWSER_DB" \
        --perm.admin

    echo -e "  ${GREEN}Database & user dibuat${NC}"
else
    echo "  Database sudah ada, skip init"
fi

# Buat file konfigurasi JSON
cat > "$FILEBROWSER_CONFIG" << 'EOF'
{
  "port": PORT_PLACEHOLDER,
  "address": "127.0.0.1",
  "database": "/etc/filebrowser/filebrowser.db",
  "root": "/",
  "baseURL": "",
  "auth.method": "json",
  "signup": false,
  "branding": {
    "name": "JNI File Manager",
    "disableExternal": false
  }
}
EOF
sed -i "s/PORT_PLACEHOLDER/$FILEBROWSER_PORT/" "$FILEBROWSER_CONFIG"

echo -e "  ${GREEN}Config file dibuat di $FILEBROWSER_CONFIG${NC}"

# ---------------------------------------------------------------------------
# 3. Create systemd service
# ---------------------------------------------------------------------------
echo -e "${YELLOW}[3/5] Create systemd service...${NC}"

cat > /etc/systemd/system/filebrowser.service << 'EOF'
[Unit]
Description=File Browser - Web File Manager
Documentation=https://filebrowser.org
After=network.target

[Service]
Type=simple
User=root
Group=root
ExecStart=/usr/local/bin/filebrowser \
    --config /etc/filebrowser/config.json \
    --database /etc/filebrowser/filebrowser.db \
    --address 127.0.0.1 \
    --port PORT_PLACEHOLDER \
    --root /
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5
LimitNOFILE=65535

# Security hardening (minimal karena perlu akses full filesystem)
ReadWritePaths=/
NoNewPrivileges=false
PrivateTmp=false

[Install]
WantedBy=multi-user.target
EOF
sed -i "s/PORT_PLACEHOLDER/$FILEBROWSER_PORT/" /etc/systemd/system/filebrowser.service

systemctl daemon-reload
systemctl enable filebrowser
echo -e "  ${GREEN}systemd service dibuat & di-enable${NC}"

# ---------------------------------------------------------------------------
# 4. Install & configure Nginx
# ---------------------------------------------------------------------------
echo -e "${YELLOW}[4/5] Install & configure Nginx...${NC}"

# Install nginx jika belum ada
if ! command -v nginx &>/dev/null; then
    apt-get update -qq
    apt-get install -y -qq nginx
    echo -e "  ${GREEN}Nginx terinstal${NC}"
else
    echo "  Nginx sudah terinstal"
fi

# Hapus default config
rm -f /etc/nginx/sites-enabled/default

# Buat config untuk files.jni.my.id
cat > /etc/nginx/sites-available/files.jni.my.id << EOF
# =============================================================================
# files.jni.my.id - File Browser
# =============================================================================
server {
    listen 80;
    server_name files.jni.my.id;

    # Increase upload size limit
    client_max_body_size 500M;
    client_body_timeout 300s;

    location / {
        proxy_pass http://127.0.0.1:$FILEBROWSER_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_read_timeout 3600s;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/files.jni.my.id /etc/nginx/sites-enabled/files.jni.my.id

# Test nginx config
if nginx -t 2>&1; then
    echo -e "  ${GREEN}Nginx config OK${NC}"
else
    echo -e "  ${RED}Nginx config ERROR!${NC}"
    exit 1
fi

# ---------------------------------------------------------------------------
# 5. Start services
# ---------------------------------------------------------------------------
echo -e "${YELLOW}[5/5] Starting services...${NC}"

systemctl start filebrowser
systemctl restart nginx

sleep 2

# Verify services
if systemctl is-active --quiet filebrowser; then
    echo -e "  ${GREEN}FileBrowser: RUNNING on 127.0.0.1:$FILEBROWSER_PORT${NC}"
else
    echo -e "  ${RED}FileBrowser: FAILED! Cek: journalctl -u filebrowser${NC}"
fi

if systemctl is-active --quiet nginx; then
    echo -e "  ${GREEN}Nginx: RUNNING${NC}"
else
    echo -e "  ${RED}Nginx: FAILED! Cek: journalctl -u nginx${NC}"
fi

echo ""
echo "============================================"
echo -e "  ${GREEN}Setup Complete!${NC}"
echo "============================================"
echo ""
echo "  URL:        http://files.jni.my.id"
echo "  Username:   $FILEBROWSER_USER"
echo "  Password:   $FILEBROWSER_PASS"
echo ""
echo -e "  ${RED}!!! GANTI PASSWORD DENGAN:${NC}"
echo "  sudo filebrowser users update $FILEBROWSER_USER --password 'NEW_PASS' --database $FILEBROWSER_DB"
echo ""
echo "  Tips:"
echo "  - Cloudflare SSL mode: sebaiknya 'Full (strict)' atau 'Flexible'"
echo "  - Pastikan files.jni.my.id di Cloudflare DNS sudah pointing ke IP server ini"
echo "  - Jika ada firewall (UFW/iptables), buka port 80: sudo ufw allow 80/tcp"
echo "============================================"
