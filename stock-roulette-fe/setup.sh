#!/bin/bash

# Setup script for Ubuntu VM on EC2 free tier
# This script installs all system dependencies and is meant to run once

set -e  # Exit on any error

echo "🚀 Starting setup for Ubuntu VM on EC2 free tier..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential packages
echo "🔧 Installing essential packages..."
sudo apt install -y curl wget git unzip software-properties-common build-essential

# Install Node.js (using NodeSource repository for latest LTS)
echo "📗 Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# Verify Node.js and npm installation
echo "✅ Verifying Node.js installation..."
node_version=$(node --version)
npm_version=$(npm --version)
echo "Node.js version: $node_version"
echo "npm version: $npm_version"

# Install PM2 for production process management
echo "⚙️ Installing PM2 for process management..."
sudo npm install -g pm2

# Configure PM2 to start on boot
echo "🔄 Configuring PM2 to start on boot..."
pm2 startup
echo "Note: Follow the instructions above to complete PM2 startup configuration"

# Install nginx for reverse proxy (optional but recommended for production)
echo "🌐 Installing nginx..."
sudo apt install -y nginx

# Configure firewall (UFW)
echo "🔒 Configuring firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw allow 5173  # Vite dev server port
sudo ufw allow 4173  # Vite preview port
sudo ufw --force enable

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /var/www/stock-roulette-fe
sudo chown -R $USER:$USER /var/www/stock-roulette-fe

# Create nginx configuration for the application
echo "📝 Creating nginx configuration..."
sudo tee /etc/nginx/sites-available/stock-roulette-fe > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# Enable the nginx site
sudo ln -sf /etc/nginx/sites-available/stock-roulette-fe /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload nginx
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl enable nginx

# Install Docker (optional, if you want to use containerization)
echo "🐳 Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
rm get-docker.sh

# Install Docker Compose
echo "🔧 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Set up log directory
echo "📋 Setting up log directory..."
sudo mkdir -p /var/log/stock-roulette-fe
sudo chown -R $USER:$USER /var/log/stock-roulette-fe

# Create systemd service file for the application
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/stock-roulette-fe.service > /dev/null <<EOF
[Unit]
Description=Stock Roulette Frontend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/var/www/stock-roulette-fe
ExecStart=/usr/bin/npm run dev -- --host 0.0.0.0 --port 5173
Restart=always
RestartSec=10
Environment=NODE_ENV=production
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload

echo "✅ Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Run the deployment script to deploy your application"
echo "2. Complete PM2 startup configuration by running the command shown above"
echo "3. Your application will be available at http://your-ec2-public-ip"
echo ""
echo "🔧 Useful commands:"
echo "  sudo systemctl status stock-roulette-fe  # Check service status"
echo "  sudo systemctl start stock-roulette-fe   # Start the service"
echo "  sudo systemctl stop stock-roulette-fe    # Stop the service"
echo "  sudo journalctl -u stock-roulette-fe -f  # View service logs"
echo "  pm2 list                                  # List PM2 processes"
echo "  pm2 logs                                  # View PM2 logs"
