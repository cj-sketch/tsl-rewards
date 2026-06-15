# TSL Rewards — статический сайт за nginx (non-root, изолированно)
FROM nginxinc/nginx-unprivileged:stable-alpine

# конфиг nginx: listen 8080, заголовки безопасности, gzip, кэш статики
COPY nginx.conf /etc/nginx/conf.d/default.conf

# статика проекта
COPY --chown=nginx:nginx index.html /usr/share/nginx/html/index.html
COPY --chown=nginx:nginx assets/     /usr/share/nginx/html/assets/

EXPOSE 8080
