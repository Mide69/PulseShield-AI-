from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Inventory Service")

inventory_db = {
    "laptop": {"stock": 50, "price": 999.99},
    "phone": {"stock": 100, "price": 699.99},
    "tablet": {"stock": 75, "price": 499.99}
}

http_requests_total = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
http_request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])

@app.middleware("http")
async def metrics_middleware(request, call_next):
    with http_request_duration.labels(method=request.method, endpoint=request.url.path).time():
        response = await call_next(request)
        http_requests_total.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
        return response

@app.get("/inventory/{product}")
async def get_inventory(product: str):
    if product not in inventory_db:
        logger.warning(f"Product not found: {product}")
        raise HTTPException(status_code=404, detail="Product not found")
    logger.info(f"Inventory checked for: {product}")
    return inventory_db[product]

@app.post("/inventory/{product}/reduce")
async def reduce_inventory(product: str, quantity: int):
    if product not in inventory_db:
        raise HTTPException(status_code=404, detail="Product not found")
    if inventory_db[product]["stock"] < quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    inventory_db[product]["stock"] -= quantity
    logger.info(f"Reduced {quantity} units of {product}")
    return {"product": product, "remaining_stock": inventory_db[product]["stock"]}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "inventory-service"}

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
