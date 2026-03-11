# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files and install dependencies
# Note: package-lock.json might not exist yet, so we copy only package.json first
COPY frontend/package.json ./
RUN npm install

# Copy the rest of the source
COPY frontend/.env ./
COPY frontend/index.html ./
COPY frontend/vite.config.ts ./
COPY frontend/tailwind.config.js ./
COPY frontend/postcss.config.js ./
COPY frontend/tsconfig.json ./
COPY frontend/src ./src

# Build the production bundle
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy custom nginx config
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
