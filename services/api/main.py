from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter
from config import settings
from database import check_db_connection, engine
from models.models import Base
import logging

logger = logging.getLogger("sahay")

api_router = APIRouter()


@api_router.get("/health")
async def health():
    db_connected = await check_db_connection()
    return {
        "status": "ok",
        "backend": "connected",
        "database": "connected" if db_connected else "disconnected",
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    logger.info("%s %s %s", request.method, request.url.path, response.status_code)
    return response


from api.v1 import status as status_api
from api.v1 import alerts as alerts_api
from api.v1 import interventions as interventions_api
from api.v1 import demo as demo_api
from api.v1 import users as users_api
from api.v1 import counsellors as counsellors_api
from api.v1 import cases as cases_api
from api.v1 import counselling as counselling_api
from api.v1 import followups as followups_api
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(status_api.router, prefix=settings.API_V1_PREFIX)
app.include_router(alerts_api.router, prefix=settings.API_V1_PREFIX)
app.include_router(interventions_api.router, prefix=settings.API_V1_PREFIX)
app.include_router(demo_api.router, prefix=settings.API_V1_PREFIX)
app.include_router(users_api.router, prefix=settings.API_V1_PREFIX)
app.include_router(counsellors_api.router, prefix=settings.API_V1_PREFIX)
app.include_router(cases_api.router, prefix=f"{settings.API_V1_PREFIX}/cases")
app.include_router(counselling_api.router, prefix=settings.API_V1_PREFIX)
app.include_router(followups_api.router, prefix=settings.API_V1_PREFIX)
