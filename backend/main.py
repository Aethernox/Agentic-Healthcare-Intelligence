from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path

from routers import search, hospitals, dashboard, eval
from config import settings
from database import init_db, SessionLocal
from models import Hospital

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("medmap")


def auto_seed_if_empty():
    """Ensure database has data from dataset.csv on startup."""
    session = SessionLocal()
    try:
        count = session.query(Hospital).count()
        if count == 0:
            logger.info("Database is empty. Searching for dataset.csv to auto-ingest...")
            possible_paths = [
                Path(__file__).parent.parent / "dataset.csv",
                Path(__file__).parent / "dataset.csv",
                Path("dataset.csv"),
            ]
            csv_path = None
            for p in possible_paths:
                if p.exists():
                    csv_path = str(p)
                    break

            if csv_path:
                logger.info(f"Found dataset at {csv_path}. Running auto-ingestion...")
                from pipelines.ingest import ingest_dataset
                # Ingest initial 2,500 records quickly for immediate responsive startup, or full if specified
                ingest_dataset(csv_path, batch_size=200, limit=2500, clear_existing=False)
                logger.info("Auto-ingestion complete!")
            else:
                logger.warning("dataset.csv not found for auto-seeding.")
        else:
            logger.info(f"MedMap database ready with {count} facilities indexed.")
    except Exception as e:
        logger.error(f"Error during auto-seeding check: {e}")
    finally:
        session.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("MedMap backend starting up…")
    try:
        auto_seed_if_empty()
    except Exception as e:
        logger.warning(f"Auto-seed exception: {e}")
    yield
    logger.info("MedMap backend shutting down.")


app = FastAPI(
    title="MedMap API",
    description="Agentic Healthcare Intelligence System for Indian Healthcare (PS-03)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(hospitals.router, prefix="/api/hospitals", tags=["Hospitals"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(eval.router, prefix="", tags=["Eval"])


@app.get("/health")
async def health():
    session = SessionLocal()
    count = 0
    try:
        count = session.query(Hospital).count()
    except Exception:
        pass
    finally:
        session.close()
    return {"status": "ok", "service": "medmap-api", "facilities_indexed": count}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
