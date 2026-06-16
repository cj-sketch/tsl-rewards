# TSL Rewards — гейт доступа: Python отдаёт статику только авторизованным сотрудникам
FROM python:3.12-alpine
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY auth_app.py /app/auth_app.py
COPY index.html /app/site/index.html
COPY assets /app/site/assets
RUN adduser -D -u 10001 app
USER app
EXPOSE 8080
CMD ["python", "auth_app.py"]
