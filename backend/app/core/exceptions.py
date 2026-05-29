"""
异常处理模块

定义自定义异常类和统一异常处理器。
"""

from typing import Any, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppException(Exception):
    """自定义业务异常

    用于在业务逻辑中抛出可预期的错误，自动转换为标准响应格式。

    Attributes:
        code: 业务状态码
        message: 错误消息
        data: 附加数据

    Example:
        raise AppException(code=400, message="用户名已存在", data={"field": "username"})
    """

    def __init__(
        self,
        code: int = 400,
        message: str = "请求失败",
        data: Optional[Any] = None,
    ):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    """注册异常处理器

    Args:
        app: FastAPI 应用实例
    """

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request, exc: AppException
    ) -> JSONResponse:
        """处理自定义业务异常"""
        return JSONResponse(
            status_code=status.HTTP_200_OK,  # HTTP 200，业务状态码在 body 中
            content={
                "code": exc.code,
                "message": exc.message,
                "data": exc.data,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """处理 HTTP 异常"""
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "code": exc.status_code,
                "message": exc.detail or "请求失败",
                "data": None,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """处理请求验证错误"""
        # 格式化错误信息
        errors = {}
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
            errors[field] = error["msg"]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "code": 422,
                "message": "请求参数验证失败",
                "data": {"errors": errors},
            },
        )
