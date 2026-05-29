"""
应用配置模块

使用 pydantic-settings 管理环境变量配置。
"""
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类
    
    所有配置项从环境变量加载，支持 .env 文件。
    """
    
    model_config = SettingsConfigDict(
        env_file=('.env', '.env.local'),
        env_file_encoding='utf-8',
        extra='ignore',
    )
    
    # 应用配置
    APP_NAME: str = "ROS小车教学网站"
    DEBUG: bool = False
    
    # JWT 配置
    SECRET_KEY: str  # 必须从环境变量加载
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/document_web"

    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # 超级管理员初始密码
    FIRST_SUPERADMIN_PASSWORD: str = "changethis"  # 生产环境必须修改
    
    # CORS 配置（生产环境默认仅允许本地开发端口；部署时通过环境变量覆盖）
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:5174"


@lru_cache
def get_settings() -> Settings:
    """获取配置实例（缓存）"""
    return Settings()


# 依赖注入类型别名
SettingsDep = Annotated[Settings, Depends(get_settings)]
