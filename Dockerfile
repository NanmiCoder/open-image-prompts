FROM node:22-bookworm-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

FROM base AS verification

COPY web/package.json web/package-lock.json ./web/
RUN npm --prefix web ci

COPY . .

RUN npm test \
    && npm run lint \
    && npm run build \
    && rm -rf /app/.oip

FROM base AS runtime

ENV NODE_ENV=production \
    OIP_WEB_HOST=0.0.0.0 \
    OIP_WEB_PORT=4173

COPY --from=verification --chown=node:node /app /app

RUN mkdir -p /app/.oip \
    && chown node:node /app/.oip

USER node

EXPOSE 4173

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["node", "-e", "fetch('http://127.0.0.1:4173/health').then((response) => process.exit(response.ok ? 0 : 1)).catch(() => process.exit(1))"]

CMD ["npm", "--prefix", "web", "run", "preview"]
