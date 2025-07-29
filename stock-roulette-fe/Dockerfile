# Multi-stage Dockerfile for Stock Roulette Frontend
# Build stage
FROM node:24-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:24-alpine AS production

WORKDIR /app

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodeuser -u 1001

# Copy package files
COPY package*.json ./

# Install only production dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy built application from builder stage
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/public ./public

# Copy source for development mode
COPY --chown=nodeuser:nodejs . .

# Create necessary directories and set permissions
RUN mkdir -p /app/logs && \
    chown -R nodeuser:nodejs /app

# Switch to non-root user
USER nodeuser

# Expose port
EXPOSE 5173

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD node -e "const http = require('http'); \
    const options = { host: '0.0.0.0', port: 5173, path: '/', timeout: 2000 }; \
    const req = http.request(options, (res) => { \
      console.log('Health check passed'); process.exit(0); \
    }); \
    req.on('error', () => { console.log('Health check failed'); process.exit(1); }); \
    req.end();"

# Default command (can be overridden)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
