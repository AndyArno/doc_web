"""系统初始化相关的 Pydantic schemas"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _validate_password_complexity(v: str) -> str:
    """验证密码复杂度：至少8位，包含大写字母和数字"""
    if not any(c.isupper() for c in v):
        raise ValueError("密码必须包含至少一个大写字母")
    if not any(c.isdigit() for c in v):
        raise ValueError("密码必须包含至少一个数字")
    return v


class SetupStatusResponse(BaseModel):
    """系统安装状态响应 schema"""

    model_config = ConfigDict(from_attributes=True)

    initialized: bool


class SetupInitializeRequest(BaseModel):
    """系统初始化请求 schema"""

    admin_username: str = Field(
        ..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$"
    )
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8, max_length=100)
    cors_origins: str = Field(
        ..., description="允许的 CORS 域名，多个域名用逗号分隔"
    )

    @field_validator("admin_password")
    @classmethod
    def _check_complexity(cls, v):
        return _validate_password_complexity(v)


class SetupInitializeResponse(BaseModel):
    """系统初始化响应 schema"""

    model_config = ConfigDict(from_attributes=True)

    message: str
