#!/bin/bash

# Ubuntu VM Setup Script for Stock Roulette Game API
# This script sets up a fresh Ubuntu VM with all dependencies needed to run the game-api on Docker

set -e  # Exit on any error

echo "🚀 Starting Ubuntu VM setup for Stock Roulette Game API..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential system packages
echo "🔧 Installing essential system packages..."
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    nano \
    htop \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    build-essential \
    libpq-dev \
    python3-dev \
    python3-pip

# Install Docker
echo "🐳 Installing Docker..."
# Remove any old Docker installations
sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add current user to docker group
sudo usermod -aG docker $USER

# Start and enable Docker service
sudo systemctl start docker
sudo systemctl enable docker

echo "✅ Docker installation completed!"

# Install Docker Compose (standalone version as backup)
echo "🐙 Installing Docker Compose standalone..."
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Python 3.12 (required by the project)
echo "🐍 Installing Python 3.12..."
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.12 python3.12-dev python3.12-venv python3.12-distutils

# Make Python 3.12 the default python3
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1

# Install pip for Python 3.12
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

# Install uv (modern Python package manager used by the project)
echo "⚡ Installing uv package manager..."
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# Add uv to PATH for current session and future sessions
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# Install Git (if not already installed)
echo "📁 Ensuring Git is installed..."
sudo apt install -y git

# Install PostgreSQL client tools (for debugging/management)
echo "🗄️ Installing PostgreSQL client tools..."
sudo apt install -y postgresql-client

# Create useful aliases
echo "⚙️ Setting up useful aliases..."
cat >> ~/.bashrc << 'EOF'

# Docker aliases
alias dps='docker ps'
alias dpa='docker ps -a'
alias di='docker images'
alias dcu='docker-compose up'
alias dcd='docker-compose down'
alias dcb='docker-compose build'
alias dcl='docker-compose logs'

# Project aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

EOF

# Install additional useful tools
echo "🛠️ Installing additional development tools..."
sudo apt install -y \
    tree \
    jq \
    httpie \
    netcat-openbsd

# Set up firewall rules
echo "🔥 Setting up firewall..."
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 8000/tcp  # FastAPI app
sudo ufw allow 5432/tcp  # PostgreSQL (if needed for external access)
sudo ufw allow 80/tcp    # HTTP (for potential reverse proxy)
sudo ufw allow 443/tcp   # HTTPS (for potential reverse proxy)

# Final system cleanup
echo "🧹 Cleaning up..."
sudo apt autoremove -y
sudo apt autoclean

echo ""
echo "🎉 Ubuntu VM setup completed successfully!"
echo ""
echo "📋 Summary of installed components:"
echo "  ✅ Docker & Docker Compose"
echo "  ✅ Python 3.12"
echo "  ✅ uv package manager"
echo "  ✅ PostgreSQL client tools"
echo "  ✅ Git"
echo "  ✅ Development tools (tree, jq, httpie, etc.)"
echo ""
echo "🚀 Next steps:"
echo "  1. Logout and login again (or run 'newgrp docker') to apply Docker group membership"
echo "  2. Clone your repository:"
echo "     git clone https://github.com/Gautham-Nagaraj/Data608-Project.git"
echo "  3. Run the deployment script to build and start the application"
echo ""
echo "☁️  For EC2 instances, configure AWS Security Group:"
echo "  - SSH (22): Your IP or 0.0.0.0/0"
echo "  - HTTP (80): 0.0.0.0/0 (if using reverse proxy)"
echo "  - HTTPS (443): 0.0.0.0/0 (if using reverse proxy)"
echo "  - Custom TCP (8000): 0.0.0.0/0 (for direct API access)"
echo "  - Custom TCP (5432): Your IP only (for database access, not recommended for public)"
echo ""
echo "📝 Don't forget to configure Git with your credentials:"
echo "  git config --global user.name 'Your Name'"
echo "  git config --global user.email 'your.email@example.com'"
echo ""
echo "🔐 Security notes:"
echo "  - Firewall has been configured to allow SSH, ports 80, 443, 8000, and 5432"
echo "  - Change default database passwords before production use"
echo "  - For production, use a reverse proxy (nginx) instead of direct port 8000 access"
