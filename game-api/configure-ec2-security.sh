#!/bin/bash

# EC2 Security Configuration Guide for Stock Roulette Game API
# This script provides guidance and tools for configuring EC2 security

echo "☁️  EC2 Security Configuration for Stock Roulette Game API"
echo "=========================================================="

# Check if running on EC2
if ! curl -s --max-time 3 http://169.254.169.254/latest/meta-data/instance-id > /dev/null 2>&1; then
    echo "❌ This script is designed for EC2 instances"
    echo "Current server does not appear to be an EC2 instance"
    exit 1
fi

# Get EC2 metadata
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
PUBLIC_DNS=$(curl -s http://169.254.169.254/latest/meta-data/public-hostname)
AVAILABILITY_ZONE=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)
REGION=$(echo $AVAILABILITY_ZONE | sed 's/[a-z]$//')

echo "📍 EC2 Instance Information:"
echo "  - Instance ID: $INSTANCE_ID"
echo "  - Public IP: $PUBLIC_IP"
echo "  - Public DNS: $PUBLIC_DNS"
echo "  - Region: $REGION"
echo "  - Availability Zone: $AVAILABILITY_ZONE"
echo ""

# Check if AWS CLI is installed
if command -v aws &> /dev/null; then
    echo "✅ AWS CLI is installed"
    
    # Try to get security group info
    echo "🔍 Checking current security groups..."
    
    # Get instance security groups
    if aws sts get-caller-identity &> /dev/null; then
        echo "✅ AWS CLI is configured"
        
        SECURITY_GROUPS=$(aws ec2 describe-instances \
            --instance-ids $INSTANCE_ID \
            --region $REGION \
            --query 'Reservations[0].Instances[0].SecurityGroups[*].GroupId' \
            --output text 2>/dev/null)
        
        if [ -n "$SECURITY_GROUPS" ]; then
            echo "📋 Current Security Groups: $SECURITY_GROUPS"
            
            for sg in $SECURITY_GROUPS; do
                echo ""
                echo "Security Group: $sg"
                aws ec2 describe-security-groups \
                    --group-ids $sg \
                    --region $REGION \
                    --query 'SecurityGroups[0].IpPermissions[*].[IpProtocol,FromPort,ToPort,IpRanges[*].CidrIp]' \
                    --output table 2>/dev/null || echo "  Unable to describe security group"
            done
        else
            echo "❌ Unable to retrieve security group information"
        fi
    else
        echo "⚠️  AWS CLI is not configured with credentials"
    fi
else
    echo "⚠️  AWS CLI is not installed"
fi

echo ""
echo "🔧 MANUAL SECURITY GROUP CONFIGURATION:"
echo "============================================="
echo ""
echo "1. 📱 Go to AWS Console → EC2 Dashboard"
echo "2. 🔍 Navigate to 'Security Groups' in the left sidebar"
echo "3. 🎯 Find and select the security group for instance: $INSTANCE_ID"
echo "4. ✏️  Click 'Edit inbound rules'"
echo "5. ➕ Add the following rules:"
echo ""
echo "   REQUIRED RULES:"
echo "   ┌─────────────┬──────┬─────────────┬─────────────────┐"
echo "   │ Type        │ Port │ Protocol    │ Source          │"
echo "   ├─────────────┼──────┼─────────────┼─────────────────┤"
echo "   │ SSH         │ 22   │ TCP         │ Your IP/32      │"
echo "   │ Custom TCP  │ 8000 │ TCP         │ 0.0.0.0/0       │"
echo "   └─────────────┴──────┴─────────────┴─────────────────┘"
echo ""
echo "   OPTIONAL RULES (for production with reverse proxy):"
echo "   ┌─────────────┬──────┬─────────────┬─────────────────┐"
echo "   │ HTTP        │ 80   │ TCP         │ 0.0.0.0/0       │"
echo "   │ HTTPS       │ 443  │ TCP         │ 0.0.0.0/0       │"
echo "   └─────────────┴──────┴─────────────┴─────────────────┘"
echo ""
echo "6. 💾 Click 'Save rules'"
echo ""

echo "🔗 DIRECT LINKS:"
echo "=================="
echo "AWS Console Security Groups: https://$REGION.console.aws.amazon.com/ec2/v2/home?region=$REGION#SecurityGroups:"
echo "EC2 Instance: https://$REGION.console.aws.amazon.com/ec2/v2/home?region=$REGION#InstanceDetails:instanceId=$INSTANCE_ID"
echo ""

echo "🧪 TESTING CONNECTIVITY:"
echo "========================="
echo ""
echo "Once security group is configured, test these URLs:"
echo "  - API Health: http://$PUBLIC_IP:8000/"
echo "  - API Docs: http://$PUBLIC_IP:8000/docs"
echo "  - Admin Panel: http://$PUBLIC_IP:8000/admin"
echo ""
if [ -n "$PUBLIC_DNS" ]; then
    echo "Or using DNS name:"
    echo "  - API Health: http://$PUBLIC_DNS:8000/"
    echo "  - API Docs: http://$PUBLIC_DNS:8000/docs"
    echo "  - Admin Panel: http://$PUBLIC_DNS:8000/admin"
    echo ""
fi

echo "🔧 TESTING FROM COMMAND LINE:"
echo "=============================="
echo ""
echo "# Test from another machine:"
echo "curl -I http://$PUBLIC_IP:8000/"
echo ""
echo "# Test from this instance (should work):"
echo "curl -I http://localhost:8000/"
echo ""

# Offer to test connectivity
echo "🏃 Test connectivity now? (requires security group to be configured)"
read -p "Test API connectivity? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧪 Testing local connectivity..."
    
    if curl -s --max-time 10 http://localhost:8000/ > /dev/null; then
        echo "✅ Local API is responding"
        
        echo "🧪 Testing public connectivity..."
        echo "Note: This test checks if the port is accessible from outside"
        echo "If this fails, check your security group configuration"
        
        # Test public connectivity (this might fail if security group isn't configured)
        if timeout 10 bash -c "</dev/tcp/$PUBLIC_IP/8000" 2>/dev/null; then
            echo "✅ Public port 8000 is accessible"
            echo "🎉 Your API should be publicly accessible!"
        else
            echo "❌ Public port 8000 is not accessible"
            echo "⚠️  Check your security group configuration"
        fi
    else
        echo "❌ Local API is not responding"
        echo "Make sure your application is running with: ./deploy.sh"
    fi
fi

echo ""
echo "🔐 SECURITY REMINDERS:"
echo "======================"
echo "✅ Only open port 8000 if needed for direct API access"
echo "✅ For production, consider using a reverse proxy (nginx) on ports 80/443"
echo "✅ Never expose PostgreSQL port 5432 to 0.0.0.0/0"
echo "✅ Restrict SSH access to your IP address only"
echo "✅ Use HTTPS in production with proper SSL certificates"
echo "✅ Regularly update your instance and Docker images"
echo ""
echo "💡 For production deployment, consider:"
echo "   - Using Application Load Balancer (ALB)"
echo "   - Setting up SSL/TLS certificates with ACM"
echo "   - Using RDS for managed PostgreSQL"
echo "   - Implementing proper logging and monitoring"
