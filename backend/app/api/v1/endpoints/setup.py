"""系统初始化 API 端点

提供系统安装状态查询和初始安装接口。
"""

from fastapi import APIRouter
from passlib.context import CryptContext
from sqlalchemy import select

from app.api.deps import SessionDep, SettingsDep
from app.core.exceptions import AppException
from app.core.setup_state import is_initialized, mark_initialized
from app.models.system_config import SystemConfig
from app.models.user import Role, User
from app.schemas.setup import SetupInitializeRequest

router = APIRouter(prefix="/setup", tags=["系统初始化"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/status", response_model=dict)
async def get_setup_status(session: SessionDep) -> dict:
    """查询系统初始化状态

    Returns:
        包含 initialized 布尔值的响应
    """
    initialized = await is_initialized(session)
    return {
        "code": 200,
        "message": "系统状态查询成功",
        "data": {"initialized": initialized},
    }


@router.post("/initialize", response_model=dict)
async def initialize_system(
    data: SetupInitializeRequest,
    session: SessionDep,
    settings: SettingsDep,
) -> dict:
    """系统初始化

    创建超级管理员账户、保存 CORS 配置、标记系统为已初始化。
    仅未初始化状态可调用，初始化后此接口返回 403。

    Args:
        data: 初始化请求参数（管理员用户名、邮箱、密码、CORS 域名）
        session: 数据库会话
        settings: 应用配置

    Returns:
        初始化成功响应

    Raises:
        AppException: 系统已初始化时返回 403
    """
    if await is_initialized(session):
        raise AppException(
            code=403,
            message="系统已初始化完成，此接口不可用",
            data=None,
        )

    existing = await session.execute(
        select(User).where(User.username == data.admin_username)
    )
    if existing.scalar_one_or_none() is not None:
        raise AppException(
            code=409,
            message=f"用户名 '{data.admin_username}' 已存在",
            data=None,
        )

    existing_email = await session.execute(
        select(User).where(User.email == data.admin_email)
    )
    if existing_email.scalar_one_or_none() is not None:
        raise AppException(
            code=409,
            message=f"邮箱 '{data.admin_email}' 已被注册",
            data=None,
        )

    hashed_password = pwd_context.hash(data.admin_password)
    admin = User(
        username=data.admin_username,
        email=data.admin_email,
        hashed_password=hashed_password,
        role=Role.SUPER_ADMIN,
        is_active=True,
    )
    session.add(admin)

    cors_config = SystemConfig(key="allowed_origins", value=data.cors_origins)
    session.add(cors_config)

    await mark_initialized(session)

    return {
        "code": 200,
        "message": "系统初始化成功，请使用管理员账户登录",
        "data": {"message": "初始化完成"},
    }
