# Ubuntu EC2 Deployment Scripts

This directory contains deployment scripts for running the Stock Roulette Frontend on an Ubuntu VM in AWS EC2 free tier.

## Files

- `setup.sh` - One-time setup script that installs all system dependencies
- `deploy.sh` - Deployment script that installs project dependencies and runs the application

## Prerequisites

- Ubuntu 20.04+ VM on AWS EC2
- SSH access to the VM
- Git repository access

## Quick Start

### 1. Initial Setup (Run Once)

```bash
# Copy the setup script to your EC2 instance
scp setup.sh ubuntu@your-ec2-ip:~/

# SSH into your EC2 instance
ssh ubuntu@your-ec2-ip

# Make the script executable and run it
chmod +x setup.sh
./setup.sh

# Complete PM2 startup configuration (follow the instructions shown)
sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u ubuntu --hp /home/ubuntu
```

### 2. Deploy Application

```bash
# Copy the deployment script to your EC2 instance
scp deploy.sh ubuntu@your-ec2-ip:~/

# Make the script executable and run it
chmod +x deploy.sh
./deploy.sh
```

### 3. Access Your Application

After successful deployment, your application will be available at:
- `http://your-ec2-public-ip` (via nginx reverse proxy)
- `http://your-ec2-public-ip:5173` (direct access)

## What the Scripts Do

### setup.sh
- Updates system packages
- Installs Node.js (LTS version)
- Installs PM2 for process management
- Installs and configures nginx as reverse proxy
- Configures firewall (UFW)
- Creates application directory structure
- Sets up systemd service
- Optionally installs Docker

### deploy.sh
- Clones/updates the project repository
- Installs project dependencies
- Runs code quality checks (linting, type checking)
- Builds the application
- Configures PM2 for process management
- Starts the application with both PM2 and systemd
- Provides deployment status and management commands

## Management Commands

### PM2 Commands
```bash
pm2 list                          # List all processes
pm2 restart stock-roulette-fe     # Restart the application
pm2 stop stock-roulette-fe        # Stop the application
pm2 logs stock-roulette-fe        # View application logs
pm2 monit                         # Real-time monitoring dashboard
```

### Systemd Commands
```bash
sudo systemctl status stock-roulette-fe    # Check service status
sudo systemctl restart stock-roulette-fe   # Restart the service
sudo systemctl stop stock-roulette-fe      # Stop the service
sudo journalctl -u stock-roulette-fe -f    # View service logs
```

### Nginx Commands
```bash
sudo systemctl status nginx       # Check nginx status
sudo systemctl restart nginx      # Restart nginx
sudo nginx -t                     # Test nginx configuration
```

## Troubleshooting

### Check Application Status
```bash
# Check if the application is running
pm2 list
sudo systemctl status stock-roulette-fe

# Check logs
pm2 logs stock-roulette-fe
sudo journalctl -u stock-roulette-fe -f
```

### Check Network Connectivity
```bash
# Test if the application is responding locally
curl http://localhost:5173

# Check if nginx is proxying correctly
curl http://localhost
```

### Common Issues

1. **Port 5173 not accessible externally**
   - Ensure EC2 security group allows inbound traffic on port 5173
   - Check UFW firewall: `sudo ufw status`

2. **Application not starting**
   - Check Node.js version: `node --version`
   - Verify dependencies: `npm list`
   - Check PM2 logs: `pm2 logs stock-roulette-fe`

3. **Nginx configuration issues**
   - Test configuration: `sudo nginx -t`
   - Check nginx logs: `sudo tail -f /var/log/nginx/error.log`

## Security Considerations

- The scripts configure UFW firewall with basic rules
- Consider setting up SSL/TLS certificates for production use
- Review and harden nginx configuration as needed
- Consider using environment variables for sensitive configuration

## Resource Usage

This setup is optimized for AWS EC2 free tier:
- Single PM2 instance
- Memory limit set to 1GB
- Basic nginx configuration
- Minimal resource monitoring

## Updates

To update the application:
```bash
./deploy.sh
```

The deployment script will automatically pull the latest changes and restart the application.
