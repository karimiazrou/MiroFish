FROM node:22.14-bookworm AS build
WORKDIR /workspace

COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN npm ci --prefix frontend

COPY frontend/ ./frontend/
COPY locales/ ./locales/
ENV VITE_API_BASE_URL=
RUN npm run build --prefix frontend

FROM nginx:1.27-alpine
COPY --from=build /workspace/frontend/dist/ /usr/share/nginx/html/
COPY deploy/nginx.conf.template /etc/nginx/templates/default.conf.template
ENV NGINX_ENVSUBST_FILTER=^API_AUTH_TOKEN$
EXPOSE 8080
