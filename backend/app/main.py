"""AI Payments Control Tower - FastAPI Application."""

from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.payments_v2 import router as payments_router
from .api.control_tower_v2 import router as control_tower_router
from .api.ai_v3 import router as ai_router
from .seed.generator_v2 import seed_data

app = FastAPI(
    title="AI Payments Control Tower",
    description="Cross-border payments operations intelligence platform — AI-enabled exception management",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payments_router, tags=["Payments"])
app.include_router(control_tower_router, tags=["Control Tower"])
app.include_router(ai_router, tags=["AI Intelligence"])


@app.on_event("startup")
def on_startup():
    print("[STARTUP] Seeding payment data...")
    seed_data(num_payments=100)
    print("[STARTUP] Seed complete. Server ready.")


@app.get("/health")
def health_check():
    from .repositories.memory_store import store
    return {
        "status": "healthy",
        "payments_count": store.payment_count(),
        "anomalies_count": store.anomaly_count(),
        "nodes_count": len(store.list_nodes()),
    }
