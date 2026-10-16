from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import create_all
from . import models  # noqa: F401
from .schemas import HealthResponse
from .routers.v1 import router as v1_router
from .routers.tickets import router as tickets_router
from .routers.pods import router as pods_router
from .routers.modules import router as modules_router
from .routers.submissions import router as submissions_router
from .routers.outcomes import router as outcomes_router
from .routers.dashboard import router as dashboard_router
from .routers.sync import router as sync_router
from .routers.demo import router as demo_router

api_router = APIRouter(prefix="/api/v1")


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_all()
    yield


app = FastAPI(title="DemandLock API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=settings.cors_origins.strip() != "*",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


app.include_router(demo_router, prefix="/api/v1")
app.include_router(tickets_router, prefix="/api/v1")
app.include_router(pods_router, prefix="/api/v1")
app.include_router(modules_router, prefix="/api/v1")
app.include_router(submissions_router, prefix="/api/v1")
app.include_router(outcomes_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(sync_router, prefix="/api/v1")
app.include_router(v1_router, prefix="/api/v1")
