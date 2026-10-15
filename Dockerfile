FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x scripts/staging_entrypoint.sh
EXPOSE 8000
ENTRYPOINT ["/app/scripts/staging_entrypoint.sh"]
