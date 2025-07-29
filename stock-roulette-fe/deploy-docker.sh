#!/bin/bash

# Docker-based deployment script for Stock Roulette Frontend
# Alternative deployment method using Docker Compose

set -e  # Exit on any error

echo "🐳 Starting Docker-based deployment of Stock Roulette Frontend..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Docker and Docker Compose are installed
echo "🔍 Checking Docker prerequisites..."
if ! command_exists docker; then
    echo "❌ Docker is not installed. Please run the setup script first or install Docker manually."
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose is not installed. Please run the setup script first or install Docker Compose manually."
    exit 1
fi

# Check if user can run Docker commands
if ! docker info >/dev/null 2>&1; then
    echo "❌ Cannot connect to Docker daemon. You may need to:"
    echo "  1. Start Docker service: sudo systemctl start docker"
    echo "  2. Add user to docker group: sudo usermod -aG docker $USER"
    echo "  3. Log out and log back in"
    exit 1
fi

echo "✅ Docker prerequisites check passed!"

# Pull latest changes (if in git repository)
if [ -d ".git" ]; then
    echo "🔄 Pulling latest changes..."
    git pull origin main || echo "⚠️ Could not pull latest changes, continuing with current code"
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down || echo "No existing containers to stop"

# Remove old images (optional, saves space)
echo "🧹 Cleaning up old Docker images..."
docker system prune -f

# Build and start containers
echo "🔨 Building and starting containers..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check container status
echo "🔍 Checking container status..."
docker-compose ps

# Check if frontend is responding
echo "🌐 Testing frontend connectivity..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:5173 >/dev/null 2>&1; then
        echo "✅ Frontend is responding!"
        break
    elif [ $attempt -eq $max_attempts ]; then
        echo "❌ Frontend is not responding after $max_attempts attempts"
        echo "🔍 Container logs:"
        docker-compose logs frontend
        exit 1
    else
        echo "⏳ Attempt $attempt/$max_attempts - waiting for frontend..."
        sleep 2
        ((attempt++))
    fi
done

# Display deployment information
echo ""
echo "🎉 Docker deployment completed!"
echo ""
echo "📊 Container Status:"
docker-compose ps

echo ""
echo "🌐 Access Information:"
echo "  Application URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'your-ec2-public-ip')"
echo "  Direct Port: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'your-ec2-public-ip'):5173"
echo ""
echo "🔧 Management Commands:"
echo "  docker-compose logs frontend          # View application logs"
echo "  docker-compose logs -f                # Follow all logs"
echo "  docker-compose restart frontend       # Restart frontend container"
echo "  docker-compose down                   # Stop all containers"
echo "  docker-compose up -d                  # Start all containers"
echo "  docker-compose exec frontend sh       # Access frontend container shell"
echo ""
echo "📋 Useful Docker Commands:"
echo "  docker ps                             # List running containers"
echo "  docker images                         # List Docker images"
echo "  docker system df                      # Show Docker disk usage"
echo "  docker system prune                   # Clean up unused Docker resources"
