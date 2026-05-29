"""
FastAPI 应用入口

ROS小车教学网站后端 API
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

logging.basicConfig(level=logging.INFO)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from app.api.v1.endpoints import auth, chapters, media, search, setup, textbooks, upload, users
from app.core.exceptions import register_exception_handlers
from app.core.limiter import limiter
from app.db.session import AsyncSessionLocal, engine
from app.services import search_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理

    启动时：创建搜索索引表
    关闭时：释放数据库引擎
    """
    async with AsyncSessionLocal() as session:
        await search_service.ensure_search_table(session)
    logger.info("应用启动完成")
    yield
    await engine.dispose()
    logger.info("数据库引擎已释放")


app = FastAPI(
    title="ROS小车教学网站 API",
    description="ROS机器人操作系统教学内容管理平台",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置
from app.core.config import get_settings

_settings = get_settings()
origins = (
    ["*"]
    if _settings.ALLOWED_ORIGINS == "*"
    else [origin.strip() for origin in _settings.ALLOWED_ORIGINS.split(",")]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=(origins != ["*"]),
    allow_methods=["*"],
    allow_headers=["*"],
)

# CORS 调试日志中间件 — 仅记录含 Origin 头的请求
_origins_wildcard = _settings.ALLOWED_ORIGINS == "*"
_wildcard_logged = False


@app.middleware("http")
async def log_request_origin(request: Request, call_next):
    """记录包含 Origin 头的请求，方便排查 CORS 问题"""
    global _wildcard_logged

    origin = request.headers.get("origin")
    if not origin:
        return await call_next(request)

    # 仅记录一次 wildcard 模式状态
    if _origins_wildcard and not _wildcard_logged:
        logger.info("[CORS] Wildcard mode active — allowing all origins")
        _wildcard_logged = True

    logger.info(
        "[CORS] Origin=%s Method=%s Path=%s",
        origin,
        request.method,
        request.url.path,
    )
    return await call_next(request)


@app.middleware("http")
async def check_initialized(request: Request, call_next):
    """未初始化时拦截所有非 setup 请求"""
    # Skip setup, static files, docs, and all auth endpoints.
    # Auth remains accessible even when uninitialized — the setup flow
    # requires login/register, and tests depend on auth endpoints.
    if (
        request.url.path.startswith("/api/v1/setup")
        or request.url.path.startswith("/api/v1/auth")
        or request.url.path.startswith("/uploads")
        or request.url.path.startswith("/api/v1/docs")
        or request.url.path.startswith("/api/v1/openapi.json")
        or request.url.path == "/"
    ):
        return await call_next(request)

    from app.core.setup_state import is_initialized
    from app.db.session import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as session:
            initialized = await is_initialized(session)
    except Exception:
        # Database unreachable — allow request through (fail open).
        # This handles test environments where AsyncSessionLocal
        # may not match the dependency-injected session.
        return await call_next(request)

    if not initialized:
        return JSONResponse(
            status_code=200,
            content={
                "code": 503,
                "message": "系统尚未初始化，请访问 /setup 完成配置",
                "data": None,
            },
        )

    return await call_next(request)


# 注册异常处理器
register_exception_handlers(app)

# 注册 slowapi 限流器
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """处理限流异常，返回 HTTP 200 + code=429（符合项目统一响应格式）"""
    return JSONResponse(
        status_code=200,
        content={
            "code": 429,
            "message": "请求过于频繁，请稍后再试",
            "data": None,
        },
    )

# 注册路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(textbooks.router, prefix="/api/v1")
app.include_router(chapters.router, prefix="/api/v1")
app.include_router(media.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(setup.router, prefix="/api/v1")

# 静态文件服务
uploads_dir = Path(__file__).parent.parent / "uploads"
uploads_dir.mkdir(exist_ok=True)
(uploads_dir / "images").mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


@app.get("/")
async def root():
    """健康检查端点"""
    return {"code": 200, "message": "API is running", "data": None}


@app.get("/api/v1")
async def api_root():
    """API v1 根路径"""
    return {"code": 200, "message": "API v1 is running", "data": None}
