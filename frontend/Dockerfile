# Multi-stage Dockerfile for MIDINecromancer frontend
# Targets: dev (Vite dev server) and prod (static build with nginx)

# Dev target: Development with Vite
FROM node:20-alpine as dev

WORKDIR /app

# Copy package files
COPY package.json ./
COPY package-lock.json* ./

# Install dependencies
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy source (will be bind-mounted in compose)
COPY . .

# Expose Vite port
EXPOSE 5173

# Default command (overridden in compose)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Build stage: Build static assets
FROM node:20-alpine as build

WORKDIR /app

# Copy package files
COPY package.json ./
COPY package-lock.json* ./

# Install dependencies
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy source
COPY . .

# Build for production
RUN npm run build

# Prod target: Serve with nginx
FROM nginx:alpine as prod

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Create nginx config for SPA with API proxy
RUN cat > /etc/nginx/conf.d/default.conf << 'EOF'
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
