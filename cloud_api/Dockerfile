FROM python:3.12-slim

WORKDIR /app

COPY cloud_api/requirements.txt /app/cloud_api/requirements.txt
RUN pip install --no-cache-dir -r /app/cloud_api/requirements.txt

COPY cloud_api /app/cloud_api

ENV PORT=8090
EXPOSE 8090

CMD ["sh", "-c", "uvicorn cloud_api.app:app --host 0.0.0.0 --port ${PORT:-8090}"]
