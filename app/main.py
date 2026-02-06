"""
Точка входа FastAPI.

lifespan: подключение/отключение MongoDB при старте/остановке.
CORS, exception handlers (структурированные ответы), подключение роутеров (health, items).
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers import auth, health, items, portfolios, resumes, uploads
from app.schemas.common import ErrorResponse, SuccessResponse

# Логирование
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл: при старте — подключение к Mongo, при остановке — отключение."""
    logger.info("Starting up: connecting to MongoDB...")
    connect_to_mongo()
    yield
    logger.info("Shutting down: closing MongoDB...")
    close_mongo_connection()


app = FastAPI(
    title="Backend Boilerplate API",
    description="Backend Boilerplate: core, schemas, routers. Структурированные ответы: success, data / error, message.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — список origins из конфига (добавляем первым, выполняется после rate limit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Rate limit по IP — выполняется первым (лимит из config: RATE_LIMIT, например "100/minute")
app.add_middleware(RateLimitMiddleware)


# Обработчик неожиданных исключений — структурированный ответ
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s: %s", request.url.path, exc)
    body = ErrorResponse(error="internal_server_error", message="An unexpected error occurred")
    return JSONResponse(status_code=500, content=body.model_dump())


# Обработчик HTTPException — структурированный ответ
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail and "message" in detail:
        body = ErrorResponse(error=detail["error"], message=detail["message"])
    else:
        body = ErrorResponse(error="request_failed", message=str(detail) if detail else "Request failed")
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


# Обработчик валидации (422) — структурированный ответ
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    msg = "; ".join(f"{e.get('loc', [])}: {e.get('msg', '')}" for e in errors[:3])
    body = ErrorResponse(error="validation_error", message=msg or "Validation failed")
    return JSONResponse(status_code=422, content=body.model_dump())


# Корень и документация — структурированный ответ
@app.get("/", response_model=SuccessResponse[dict])
def root():
    return SuccessResponse(data={"message": "Backend Boilerplate API", "docs": "/docs", "health": "/health"})


# Роутеры
app.include_router(health.router)
app.include_router(items.router)
app.include_router(auth.router)
app.include_router(resumes.router)
app.include_router(portfolios.router)
app.include_router(uploads.router)
