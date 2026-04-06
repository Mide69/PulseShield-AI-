FROM python:3.11-alpine AS builder
WORKDIR /app
COPY requirements.txt .
RUN apk add --no-cache gcc musl-dev postgresql-dev && \
    pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-alpine
RUN apk add --no-cache libpq && \
    addgroup -g 1001 -S appuser && adduser -S appuser -u 1001
WORKDIR /app
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .
USER appuser
ENV PATH=/home/appuser/.local/bin:$PATH
EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"
CMD ["python", "main.py"]
