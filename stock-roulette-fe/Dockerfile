# Development Dockerfile for Stock Roulette Frontend
FROM node:24-alpine

WORKDIR /app

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init curl

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodeuser -u 1001

# Copy package files
COPY package*.json ./

# Clean up any existing installations and install all dependencies
# This approach resolves the Alpine musl rollup dependency issue
RUN rm -rf node_modules package-lock.json && \
    npm cache clean --force && \
    npm install && \
    chown -R nodeuser:nodejs /app

# Copy source code
COPY --chown=nodeuser:nodejs . .

# Switch to non-root user
USER nodeuser

# Expose port
EXPOSE 5173

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:5173 || exit 1

# Default command
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
