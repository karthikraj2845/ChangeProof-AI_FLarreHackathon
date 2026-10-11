from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.db.seed import seed_database
from app.models.rule import Rule

from app.api.dashboard import router as dashboard_router
from app.api.rules import router as rules_router
from app.api.changes import router as changes_router
from app.api.workflows import router as workflows_router
from app.api.graph import router as graph_router
from app.api.verification import router as verification_router
from app.api.findings import router as findings_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("changeproof")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing ChangeProof AI backend database...")
    init_db()
    # Check if seed data exists; if not, seed automatically
    db = SessionLocal()
    try:
        existing_rule = db.query(Rule).first()
        if not existing_rule:
            logger.info("No existing rules found. Auto-seeding motor insurance demo dataset...")
            seed_database(db)
        else:
            logger.info("Database already initialized with existing rules.")
    finally:
        db.close()
    yield
    logger.info("Shutting down ChangeProof AI backend...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Insurance-native, multi-agent AI platform for change assurance and release verification.",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api
app.include_router(dashboard_router, prefix="/api")
app.include_router(rules_router, prefix="/api")
app.include_router(changes_router, prefix="/api")
app.include_router(workflows_router, prefix="/api")
app.include_router(graph_router, prefix="/api")
app.include_router(verification_router, prefix="/api")
app.include_router(findings_router, prefix="/api")


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_check": "/api/health",
    }
