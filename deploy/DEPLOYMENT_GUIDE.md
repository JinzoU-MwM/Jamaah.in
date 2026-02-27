# Jamaah.in VPS Deployment Guide

VPS IP: `202.74.74.139`

---

## Step 1: Initial Server Setup

SSH into your VPS as root:
```bash
ssh root@202.74.74.139
```

Create the deploy directory and upload setup script:
```bash
mkdir -p /root/deploy
```

Copy the setup script content to `/root/deploy/setup-vps.sh`, then run:
```bash
chmod +x /root/deploy/setup-vps.sh
bash /root/deploy/setup-vps.sh
```

This will install:
- Python 3.11
- Node.js 20 LTS
- Nginx
- Redis
- Tesseract OCR
- Firewall (UFW)
- Fail2ban

---

## Step 2: Upload Project Files

From your local machine, upload the project:
```bash
# Option A: Using scp
scp -r backend frontend-svelte deploy .env root@202.74.74.139:/var/www/jamaah.in/

# Option B: Using rsync (recommended)
rsync -avz --exclude 'node_modules' --exclude '__pycache__' --exclude '.git' \
  backend frontend-svelte deploy .env root@202.74.74.139:/var/www/jamaah.in/
```

On the VPS, rename frontend-svelte to frontend:
```bash
mv /var/www/jamaah.in/frontend-svelte /var/www/jamaah.in/frontend
```

---

## Step 3: Install Dependencies

```bash
cd /var/www/jamaah.in
chmod +x deploy/*.sh
bash deploy/install-deps.sh
```

---

## Step 4: Configure Environment

Edit the `.env` file:
```bash
nano /var/www/jamaah.in/backend/.env
```

Update these values:
```env
# Change CORS to your domain
ALLOWED_ORIGINS=https://jamaah.in,https://www.jamaah.in

# Update frontend URL for payment callback
FRONTEND_URL=https://jamaah.in
```

---

## Step 5: Setup Nginx

```bash
# Copy nginx config
cp /var/www/jamaah.in/deploy/nginx/jamaah.in /etc/nginx/sites-available/

# Enable site
ln -s /etc/nginx/sites-available/jamaah.in /etc/nginx/sites-enabled/

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Test config
nginx -t

# Reload nginx
systemctl reload nginx
```

---

## Step 6: Setup Systemd Service

```bash
# Copy systemd service
cp /var/www/jamaah.in/deploy/systemd/jamaah-backend.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable and start service
systemctl enable jamaah-backend
systemctl start jamaah-backend

# Check status
systemctl status jamaah-backend
```

---

## Step 7: Setup SSL (Let's Encrypt)

```bash
# Install certbot
apt install -y certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d jamaah.in -d www.jamaah.in

# Auto-renewal test
certbot renew --dry-run
```

---

## Step 8: Update DNS

In your domain registrar (where you bought jamaah.in), add A records:

| Type | Name | Value |
|------|------|-------|
| A | @ | 202.74.74.139 |
| A | www | 202.74.74.139 |

---

## Quick Commands Reference

```bash
# View backend logs
journalctl -u jamaah-backend -f

# Restart backend
systemctl restart jamaah-backend

# Reload nginx
systemctl reload nginx

# View nginx logs
tail -f /var/log/nginx/error.log

# Deploy updates
cd /var/www/jamaah.in && bash deploy/deploy.sh

# Check disk usage
df -h

# Check memory
free -h

# Check running processes
htop
```

---

## Troubleshooting

### Backend won't start
```bash
# Check logs
journalctl -u jamaah-backend -n 50

# Check if port is in use
lsof -i :8000

# Manual test
cd /var/www/jamaah.in/backend
source venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000
```

### 502 Bad Gateway
- Backend is not running: `systemctl start jamaah-backend`
- Check if port 8000 is listening: `curl http://127.0.0.1:8000/`

### SSL issues
```bash
# Check certificate
certbot certificates

# Renew manually
certbot renew
```

---

## Security Checklist

- [ ] Change SSH port (optional): Edit `/etc/ssh/sshd_config`
- [ ] Disable root login: `PermitRootLogin no` in sshd_config
- [ ] Setup automatic updates: `apt install unattended-upgrades`
- [ ] Check fail2ban: `fail2ban-client status`
- [ ] Check firewall: `ufw status`
