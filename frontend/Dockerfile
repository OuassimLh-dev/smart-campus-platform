FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ENV VITE_API_BASE_URL=/api/v1
RUN npm run build

FROM nginx:stable-alpine
ENV PORT=80 BACKEND_HOST=backend BACKEND_PORT=8000
ENV NGINX_ENVSUBST_FILTER="^(PORT|BACKEND_HOST|BACKEND_PORT|NGINX_RESOLVERS)$"
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY docker/15-resolvers.envsh /docker-entrypoint.d/15-resolvers.envsh
RUN chmod +x /docker-entrypoint.d/15-resolvers.envsh
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
