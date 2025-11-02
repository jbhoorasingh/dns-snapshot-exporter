"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import Base, engine
from app.api.routes import zones, snapshots, exports, comparisons, jobs
from app.services.scheduler import scheduler_service
from app.api.schemas import HealthResponse

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting DNS Snapshot Exporter API")

    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

    # Load scheduled jobs
    scheduler_service.load_jobs_from_database()

    yield

    # Shutdown
    logger.info("Shutting down DNS Snapshot Exporter API")
    scheduler_service.shutdown()


# Create FastAPI app
app = FastAPI(
    title="DNS Snapshot Exporter",
    description="API for backing up and exporting DNS zones from multiple providers",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(zones.router, prefix=settings.API_V1_PREFIX)
app.include_router(snapshots.router, prefix=settings.API_V1_PREFIX)
app.include_router(exports.router, prefix=settings.API_V1_PREFIX)
app.include_router(comparisons.router, prefix=settings.API_V1_PREFIX)
app.include_router(jobs.router, prefix=settings.API_V1_PREFIX)


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0"
    )


@app.get("/", tags=["root"])
def root():
    """Root endpoint."""
    return {
        "message": "DNS Snapshot Exporter API",
        "version": "1.0.0",
        "docs": "/docs"
    }
