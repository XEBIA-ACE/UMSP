# ── Build stage ────────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install production dependencies only
COPY package*.json ./
RUN npm ci --only=production

# ── Runtime stage ───────────────────────────────────────────────────────────────
FROM node:20-alpine AS runtime

WORKDIR /app

# Copy installed node_modules from builder
COPY --from=builder /app/node_modules ./node_modules

# Copy application source
COPY package*.json ./
COPY src/ ./src/
COPY index.js ./

EXPOSE 3000

CMD ["node", "index.js"]
