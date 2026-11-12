import os
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from authentication.get_current_user import get_current_user
from authentication.routers import router as auth_router
from Services.routers import router as services_router
from utilities import models
from utilities.database import Base, engine

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Application Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database connected successfully")
        logger.info("Database tables created successfully")
    except SQLAlchemyError:
        logger.exception("Database initialization failed")
        raise

    yield

    # Shutdown
    await engine.dispose()
    logger.info("Database connections closed")


# FastAPI Application
app = FastAPI(
    title="Authentication System",
    description="Authentication System API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
origins = [
    o.strip()
    for o in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:3000,http://localhost:5173",
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",   # har origin allow
    allow_credentials=True,  # cookies ke liye zaroori
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(services_router)


# Root Endpoint
@app.get("/")
async def read_root():
    return {"message": "Authentication System API"}


# Health Check
@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/me")
async def me(user: models.User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "is_verified": user.is_verified,
    }