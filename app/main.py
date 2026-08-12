from fastapi import FastAPI
import logging

app = FastAPI()

logger = logging.getLogger("app_logger")
logging.basicConfig(level=logging.ERROR)

@app.get("/simulate-crash")
def simulate_crash():
    # Intentionally raising an unhandled exception for testing pipeline enrichment
    raise ConnectionRefusedError(
        "Failed to connect to PostgreSQL at db.production.internal:5432 (Timeout 3000ms)"
    )

@app.get("/")
def read_root():
    return {"status": "healthy", "service": "log-demo-app"}
