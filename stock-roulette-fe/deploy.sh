#!/bin/bash

# Deployment script for Stock Roulette Frontend
# This script installs project dependencies and runs the application

set -e  # Exit on any error

APP_DIR="/var/www/stock-roulette-fe"
REPO_URL="https://github.com/Gautham-Nagaraj/Data608-Project.git"
FRONTEND_DIR="stock-roulette-fe"

echo "🚀 Starting deployment of Stock Roulette Frontend..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if required tools are installed
echo "🔍 Checking prerequisites..."
if ! command_exists node; then
    echo "❌ Node.js is not installed. Please run the setup script first."
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm is not installed. Please run the setup script first."
    exit 1
fi

if ! command_exists git; then
    echo "❌ git is not installed. Please run the setup script first."
    exit 1
fi

echo "✅ Prerequisites check passed!"

# Stop existing services
echo "🛑 Stopping existing services..."
sudo systemctl stop stock-roulette-fe 2>/dev/null || echo "Service not running"
pm2 stop stock-roulette-fe 2>/dev/null || echo "PM2 process not running"

# Create application directory if it doesn't exist
if [ ! -d "$APP_DIR" ]; then
    echo "📁 Creating application directory..."
    sudo mkdir -p "$APP_DIR"
    sudo chown -R $USER:$USER "$APP_DIR"
fi

# Navigate to application directory
cd "$APP_DIR"

# Clone or update repository
if [ ! -d ".git" ]; then
    echo "📥 Cloning repository..."
    git clone "$REPO_URL" .
else
    echo "🔄 Updating repository..."
    git fetch origin
    git reset --hard origin/main
fi

# Navigate to frontend directory
cd "$FRONTEND_DIR"

# Install dependencies
echo "📦 Installing project dependencies..."
npm ci --production=false

# Run linting and type checking
echo "🔍 Running code quality checks..."
npm run lint || echo "⚠️ Linting issues found, continuing deployment..."
npm run type-check || echo "⚠️ Type checking issues found, continuing deployment..."

# Build the application
echo "🔨 Building the application..."
npm run build

# Create PM2 ecosystem file
echo "⚙️ Creating PM2 ecosystem configuration..."
tee ecosystem.config.js > /dev/null <<EOF
module.exports = {
  apps: [{
    name: 'stock-roulette-fe',
    script: 'npm',
    args: 'run dev',
    cwd: '$APP_DIR/$FRONTEND_DIR',
    env: {
      NODE_ENV: 'production',
      PORT: 5173,
      HOST: '0.0.0.0'
    },
    env_development: {
      NODE_ENV: 'development',
      PORT: 5173,
      HOST: '0.0.0.0'
    },
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    log_date_format: 'YYYY-MM-DD HH:mm Z',
    error_file: '/var/log/stock-roulette-fe/error.log',
    out_file: '/var/log/stock-roulette-fe/out.log',
    log_file: '/var/log/stock-roulette-fe/combined.log'
  }]
};
EOF

# Update vite config to bind to all interfaces
echo "🔧 Updating Vite configuration for production..."
if [ ! -f "vite.config.prod.ts" ]; then
    cp vite.config.ts vite.config.prod.ts
    cat >> vite.config.prod.ts <<EOF

// Production server configuration
export default defineConfig({
  plugins: [
    vue(),
    // Disable devtools in production
    // vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    cors: true
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
    cors: true
  }
})
EOF
fi

# Update package.json to use production config
echo "📝 Updating package.json for production..."
npm pkg set scripts.dev="vite --config vite.config.prod.ts"
npm pkg set scripts.preview="vite preview --config vite.config.prod.ts"

# Start application with PM2
echo "🚀 Starting application with PM2..."
pm2 start ecosystem.config.js --env production
pm2 save

# Enable and start systemd service as backup
echo "⚙️ Configuring systemd service..."
sudo systemctl enable stock-roulette-fe
sudo systemctl start stock-roulette-fe

# Check application status
echo "🔍 Checking application status..."
sleep 5

if pm2 list | grep -q "stock-roulette-fe.*online"; then
    echo "✅ Application is running with PM2!"
else
    echo "⚠️ PM2 process may not be running correctly"
fi

if sudo systemctl is-active --quiet stock-roulette-fe; then
    echo "✅ Systemd service is active!"
else
    echo "⚠️ Systemd service may not be running correctly"
fi

# Test nginx configuration
echo "🌐 Testing nginx configuration..."
sudo nginx -t
sudo systemctl reload nginx

# Display deployment information
echo ""
echo "🎉 Deployment completed!"
echo ""
echo "📊 Application Status:"
echo "  PM2 Status: $(pm2 list | grep stock-roulette-fe | awk '{print $10}' || echo 'Not running')"
echo "  Systemd Status: $(sudo systemctl is-active stock-roulette-fe)"
echo "  Nginx Status: $(sudo systemctl is-active nginx)"
echo ""
echo "🌐 Access Information:"
echo "  Application URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'your-ec2-public-ip')"
echo "  Direct Port: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'your-ec2-public-ip'):5173"
echo ""
echo "🔧 Management Commands:"
echo "  pm2 restart stock-roulette-fe    # Restart with PM2"
echo "  pm2 logs stock-roulette-fe       # View PM2 logs"
echo "  pm2 monit                        # PM2 monitoring dashboard"
echo "  sudo systemctl restart stock-roulette-fe  # Restart systemd service"
echo "  sudo journalctl -u stock-roulette-fe -f   # View systemd logs"
echo ""
echo "📋 Log Files:"
echo "  PM2 Logs: /var/log/stock-roulette-fe/"
echo "  Nginx Logs: /var/log/nginx/"
echo "  System Logs: sudo journalctl -u stock-roulette-fe"
