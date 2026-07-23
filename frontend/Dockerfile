# ---- build ----
FROM node:20-alpine AS build

WORKDIR /app

ARG VITE_API_URL=/api/v1
ARG VITE_WS_URL=/api/v1/ws
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_WS_URL=$VITE_WS_URL

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---- serve ----
FROM nginx:1.27-alpine

RUN apk add --no-cache curl

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD curl -fsS http://localhost:8080/ >/dev/null || exit 1