# Auto-generated Dockerfile for playwright-mcp-wrapper
FROM node:20-slim

WORKDIR /app

# Copy dependency files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Entry point
CMD ["node", "./index.js"]
