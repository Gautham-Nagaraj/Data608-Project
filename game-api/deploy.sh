#!/bin/bash

# Stock Roulette Game API Deployment Script
# This script handles the deployment of the game-api: migrations, building, and starting containers

set -e  # Exit on any error

echo "🎮 Starting Stock Roulette Game API deployment..."

# Check if we're in the correct directory
if [ ! -f "docker-compose.yaml" ]; then
    echo "❌ Error: docker-compose.yaml not found in current directory"
    echo "Please run this script from the game-api directory"
    echo "Usage: cd Data608-Project/game-api && ./deploy.sh"
    exit 1
fi

# Check if Docker is running
echo "🐳 Checking Docker status..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Starting Docker..."
    sudo systemctl start docker
    sleep 5
    
    # Check again
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Failed to start Docker. Please check Docker installation."
        exit 1
    fi
fi

echo "✅ Docker is running"

# Check if user is in docker group
if ! groups $USER | grep -q '\bdocker\b'; then
    echo "⚠️  Warning: User $USER is not in the docker group."
    echo "You may need to run: sudo usermod -aG docker $USER"
    echo "Then logout and login again."
    echo "Continuing with sudo for now..."
    DOCKER_CMD="sudo docker"
    DOCKER_COMPOSE_CMD="sudo docker-compose"
else
    DOCKER_CMD="docker"
    DOCKER_COMPOSE_CMD="docker-compose"
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
$DOCKER_COMPOSE_CMD down 2>/dev/null || true

# Pull latest changes (optional)
if [ -d ".git" ]; then
    read -p "Pull latest changes from git? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📥 Pulling latest changes..."
        git pull
    fi
fi

# Check if .env file exists, create from template if not
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from template..."
    cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql+psycopg://stockroulette_user:ChangeMe123!@db:5432/stockroulette

# API Configuration
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=true
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Admin Configuration
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure-admin-password

# WebSocket Configuration
WS_HEARTBEAT_INTERVAL=30

EOF
    echo "📝 Created .env file with default values"
    echo "⚠️  Please edit .env file with your actual configuration before production use"
fi

# Build the Docker images
echo "🏗️ Building Docker images..."
$DOCKER_COMPOSE_CMD build

# Start the database first and wait for it to be ready
echo "🗄️ Starting database..."
$DOCKER_COMPOSE_CMD up -d db

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for database to be ready..."
for i in {1..30}; do
    if $DOCKER_CMD exec db pg_isready -U stockroulette_user -d stockroulette > /dev/null 2>&1; then
        echo "✅ Database is ready!"
        break
    fi
    echo "Waiting for database... ($i/30)"
    sleep 2
done

# Check if database is ready
if ! $DOCKER_CMD exec db pg_isready -U stockroulette_user -d stockroulette > /dev/null 2>&1; then
    echo "❌ Database failed to start within 60 seconds"
    echo "📋 Database logs:"
    $DOCKER_COMPOSE_CMD logs db
    exit 1
fi

# Run database migrations
echo "🔄 Running Alembic migrations..."
if ! $DOCKER_COMPOSE_CMD run --rm game-api uv run -- alembic upgrade head; then
    echo "❌ Migration failed"
    echo "📋 Checking if this is a fresh setup..."
    
    # Try to initialize the database with the first migration
    echo "🔧 Attempting to initialize database..."
    $DOCKER_COMPOSE_CMD run --rm game-api uv run -- alembic stamp head || true
    $DOCKER_COMPOSE_CMD run --rm game-api uv run -- alembic upgrade head
fi

echo "✅ Migrations completed successfully"

# Start all services
echo "🚀 Starting all services..."
$DOCKER_COMPOSE_CMD up -d

# Wait a moment for services to start
sleep 5

# Check if services are running
echo "🔍 Checking service status..."
if $DOCKER_COMPOSE_CMD ps | grep -q "Up"; then
    echo "✅ Services are running!"
else
    echo "❌ Some services may have failed to start"
    echo "📋 Service status:"
    $DOCKER_COMPOSE_CMD ps
    echo ""
    echo "📋 Recent logs:"
    $DOCKER_COMPOSE_CMD logs --tail=20
    exit 1
fi

# Show running services
echo ""
echo "📋 Service Status:"
$DOCKER_COMPOSE_CMD ps

# Detect if running on EC2 and get public IP
echo ""
echo "🌐 Detecting server environment..."
EC2_PUBLIC_IP=""
EC2_PUBLIC_DNS=""

# Try to get EC2 metadata (this will only work on EC2 instances)
if curl -s --max-time 3 http://169.254.169.254/latest/meta-data/public-ipv4 > /dev/null 2>&1; then
    EC2_PUBLIC_IP=$(curl -s --max-time 3 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "")
    EC2_PUBLIC_DNS=$(curl -s --max-time 3 http://169.254.169.254/latest/meta-data/public-hostname 2>/dev/null || echo "")
    echo "✅ Running on EC2 instance"
    echo "📍 Public IP: $EC2_PUBLIC_IP"
    if [ -n "$EC2_PUBLIC_DNS" ]; then
        echo "📍 Public DNS: $EC2_PUBLIC_DNS"
    fi
else
    echo "📍 Running locally or on non-EC2 server"
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "🌐 Your application is now available at:"

# Show local URLs
echo "  LOCAL ACCESS:"
echo "  - API: http://localhost:8000"
echo "  - API Documentation: http://localhost:8000/docs"
echo "  - Interactive API Docs: http://localhost:8000/redoc"
echo "  - Admin Panel: http://localhost:8000/admin"

# Show public URLs if on EC2
if [ -n "$EC2_PUBLIC_IP" ]; then
    echo ""
    echo "  PUBLIC ACCESS (via EC2):"
    echo "  - API: http://$EC2_PUBLIC_IP:8000"
    echo "  - API Documentation: http://$EC2_PUBLIC_IP:8000/docs"
    echo "  - Interactive API Docs: http://$EC2_PUBLIC_IP:8000/redoc"
    echo "  - Admin Panel: http://$EC2_PUBLIC_IP:8000/admin"
    
    if [ -n "$EC2_PUBLIC_DNS" ]; then
        echo ""
        echo "  PUBLIC ACCESS (via DNS):"
        echo "  - API: http://$EC2_PUBLIC_DNS:8000"
        echo "  - API Documentation: http://$EC2_PUBLIC_DNS:8000/docs"
        echo "  - Interactive API Docs: http://$EC2_PUBLIC_DNS:8000/redoc"
        echo "  - Admin Panel: http://$EC2_PUBLIC_DNS:8000/admin"
    fi
    
    echo ""
    echo "⚠️  IMPORTANT EC2 SECURITY CONFIGURATION:"
    echo "  Make sure your AWS Security Group allows:"
    echo "  - Inbound rule: Custom TCP, Port 8000, Source: 0.0.0.0/0"
    echo "  - Inbound rule: SSH, Port 22, Source: Your IP"
    echo ""
    echo "  To configure Security Group:"
    echo "  1. Go to EC2 Dashboard → Security Groups"
    echo "  2. Select your instance's security group"
    echo "  3. Edit Inbound Rules → Add Rule:"
    echo "     - Type: Custom TCP"
    echo "     - Port Range: 8000"
    echo "     - Source: 0.0.0.0/0 (Anywhere-IPv4)"
    echo "  4. Save rules"
fi
echo ""
echo "📚 Useful commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop services: docker-compose down"
echo "  - Restart services: docker-compose restart"
echo "  - Rebuild and restart: docker-compose up --build"
echo "  - View specific service logs: docker-compose logs -f [service_name]"
echo ""
echo "🔧 Database connection:"
echo "  - Host: localhost"
echo "  - Port: 5432"
echo "  - Database: stockroulette"
echo "  - Username: stockroulette_user"
echo "  - Password: ChangeMe123!"
echo ""
echo "⚠️  Production reminders:"
echo "  - Change database passwords in .env and docker-compose.yaml"
echo "  - Update SECRET_KEY in .env"
echo "  - Set DEBUG=false in production"
echo "  - Configure proper CORS_ORIGINS"
echo "  - Use environment-specific .env files"

# Optionally show real-time logs
echo ""
read -p "Show real-time logs? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📋 Showing real-time logs (Ctrl+C to exit)..."
    $DOCKER_COMPOSE_CMD logs -f
fi
