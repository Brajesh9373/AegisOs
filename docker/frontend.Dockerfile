# syntax=docker/dockerfile:1
# Multi-stage build for the aegisOS Vite/React frontend.

FROM node:20-slim AS builder
WORKDIR /app
RUN npm install -g pnpm@9.0.0

# Copy workspace root files for monorepo resolution
COPY frontend/pnpm-workspace.yaml frontend/package.json frontend/pnpm-lock.yaml frontend/tsconfig.base.json ./
COPY frontend/apps/web/package.json ./apps/web/package.json

# Copy packages that the web app depends on
COPY frontend/packages/ ./packages/

# Install dependencies
RUN pnpm install --no-frozen-lockfile

# Copy the web app source
COPY frontend/apps/web/ ./apps/web/

# Build the Vite app
WORKDIR /app/apps/web
RUN pnpm build

# Runtime: nginx to serve static files + proxy API
FROM nginx:alpine AS runtime

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built static files
COPY --from=builder /app/apps/web/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:80/health || exit 1
CMD ["nginx", "-g", "daemon off;"]
