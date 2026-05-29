"""认证 API 端点

提供用户注册、登录、登出、获取当前用户、修改密码等接口。
"""

from fastapi import APIRouter, Request

from app.api.deps import CurrentUser, SessionDep, SettingsDep
from app.core.limiter import limiter
from app.schemas.user import (
    ForgotPasswordRequest,
    PasswordChange,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=dict)
@limiter.limit("3/minute")
async def register(request: Request, user_in: UserCreate, session: SessionDep) -> dict:
    """用户注册

    创建新用户账户，默认角色为 user。

    Returns:
        包含新用户信息的响应
    """
    user = await auth_service.register_user(session, user_in)
    return {
        "code": 200,
        "message": "注册成功",
        "data": UserResponse.model_validate(user).model_dump(),
    }


@router.post("/login", response_model=dict)
@limiter.limit("5/minute")
async def login(request: Request, user_in: UserLogin, session: SessionDep, settings: SettingsDep) -> dict:
    """用户登录

    支持用户名或邮箱登录。

    Returns:
        包含 JWT token 和用户信息的响应
    """
    user, token = await auth_service.authenticate_user(
        session=session,
        account=user_in.account,
        password=user_in.password,
        settings=settings,
    )
    return {
        "code": 200,
        "message": "登录成功",
        "data": token.model_dump(),
    }


@router.post("/logout", response_model=dict)
async def logout() -> dict:
    """用户登出

    由于使用无状态 JWT，登出由客户端删除 token 完成。

    Returns:
        成功响应
    """
    return {"code": 200, "message": "登出成功", "data": None}


@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: CurrentUser) -> dict:
    """获取当前用户信息

    Returns:
        当前用户信息
    """
    return {
        "code": 200,
        "message": "success",
        "data": UserResponse.model_validate(current_user).model_dump(),
    }


@router.put("/me/password", response_model=dict)
async def change_password(
    password_in: PasswordChange,
    current_user: CurrentUser,
    session: SessionDep,
) -> dict:
    """修改密码

    验证原密码后更新为新密码。

    Returns:
        成功响应
    """
    await auth_service.change_user_password(session, current_user, password_in)
    return {"code": 200, "message": "密码修改成功", "data": None}


@router.post("/forgot-password", response_model=dict)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    password_in: ForgotPasswordRequest,
    session: SessionDep,
) -> dict:
    """忘记密码/修改密码（未登录用户）

    通过用户名/邮箱 + 原密码验证身份，然后修改密码。

    Returns:
        成功响应
    """
    await auth_service.forgot_password(session, password_in)
    return {"code": 200, "message": "密码修改成功", "data": None}
