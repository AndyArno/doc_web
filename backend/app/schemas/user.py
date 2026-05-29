"""用户相关的 Pydantic schemas"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import Role


def _validate_password_complexity(v: str) -> str:
    """验证密码复杂度：至少8位，包含大写字母和数字"""
    if not any(c.isupper() for c in v):
        raise ValueError("密码必须包含至少一个大写字母")
    if not any(c.isdigit() for c in v):
        raise ValueError("密码必须包含至少一个数字")
    return v


class UserBase(BaseModel):
    """用户基础 schema"""

    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr


class UserCreate(UserBase):
    """用户注册 schema"""

    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def _check_complexity(cls, v):
        return _validate_password_complexity(v)


class UserLogin(BaseModel):
    """用户登录 schema"""

    account: str  # 用户名或邮箱
    password: str


class UserResponse(BaseModel):
    """用户响应 schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: Role
    is_active: bool = True
    must_change_password: bool = False
    created_at: datetime
    updated_at: datetime


class Token(BaseModel):
    """Token 响应 schema"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 秒
    user: UserResponse


class PasswordChange(BaseModel):
    """修改密码 schema"""

    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def _check_complexity(cls, v):
        return _validate_password_complexity(v)


class ForgotPasswordRequest(BaseModel):
    """忘记密码请求（未登录用户修改密码）"""

    account: str = Field(..., description="用户名或邮箱")
    old_password: str = Field(..., min_length=8, max_length=100, description="原密码")
    new_password: str = Field(..., min_length=8, max_length=100, description="新密码")

    @field_validator("new_password")
    @classmethod
    def _check_complexity(cls, v):
        return _validate_password_complexity(v)


class UserUpdate(BaseModel):
    """用户更新 schema"""

    username: str | None = Field(
        None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$"
    )
    email: EmailStr | None = None
    is_active: bool | None = None


class UserCreateByAdmin(UserBase):
    """管理员创建用户 schema"""

    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def _check_complexity(cls, v):
        return _validate_password_complexity(v)

    role: Role = Role.USER


class UserRoleUpdate(BaseModel):
    """用户角色更新 schema"""

    role: Role


class PasswordReset(BaseModel):
    """重置密码 schema"""

    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def _check_complexity(cls, v):
        return _validate_password_complexity(v)


class PasswordResetResponse(BaseModel):
    """密码重置响应 schema"""

    must_change_password: bool = True


class UserListResponse(BaseModel):
    """用户列表响应 schema"""

    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PermissionCreate(BaseModel):
    """权限创建 schema"""

    textbook_id: int
    can_access: bool


class PermissionResponse(BaseModel):
    """权限响应 schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    textbook_id: int
    can_access: bool = False
    created_at: datetime
    updated_at: datetime


class UserDetailResponse(BaseModel):
    """用户详情响应 schema（含权限列表）"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: Role
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    permissions: list[PermissionResponse] = []


class PermissionHistoryResponse(BaseModel):
    """权限变更历史响应 schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    target_user_id: int | None = None
    operator_id: int | None = None
    details: dict | None = None
    created_at: datetime
