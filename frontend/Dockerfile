# Frontend Dockerfile (Vite React + Tailwind + shadcn)

# Build stage
FROM node:20-alpine AS build
WORKDIR /app

# Install deps
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi

# Copy source
COPY . .

# Accept backend URL as build argument
ARG VITE_BACKEND_URL=https://vecinita-agent.onrender.com

# Build static assets with backend URL baked into bundle
RUN VITE_BACKEND_URL=${VITE_BACKEND_URL} npm run build

# Runtime stage using Nginx
FROM nginx:alpine AS runtime

# Copy nginx config for SPA routing
COPY <<EOF /etc/nginx/conf.d/default.conf
server {
  listen 80;
  server_name _;
  root /usr/share/nginx/html;
  index index.html;

  # SPA routing: redirect all non-file requests to index.html
  location / {
    try_files \$uri \$uri/ /index.html;
  }

  # Cache busting for assets
  location /assets/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
  }
}
EOF

COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]