from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from authentication.get_current_user import get_current_user
from authentication.routers import router as auth_router
from Services.routers import router as services_router
from utilities import models
from utilities.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()

app = FastAPI(
    title="AI-Powered Job Portal API",
    description="Backend API for AI-Powered Job Portal",
    version="1.0.0",
    lifespan=lifespan,
)


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(services_router)


@app.get("/")
async def read_root():
    return {"message": "AI-Powered Job Portal API"}


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