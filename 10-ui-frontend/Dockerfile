# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Copy version file if it exists
COPY src/version.json* public/ || true

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Create healthcheck endpoint
RUN printf '200 OK\n' > /usr/share/nginx/html/healthz

# Copy built app
COPY --from=build /app/dist/ /usr/share/nginx/html/

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/healthz || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
