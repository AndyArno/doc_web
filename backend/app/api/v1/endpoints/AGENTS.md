# AGENTS.md — API Endpoints Layer

**Generated:** 2026-04-19  
**Parent:** `/AGENTS.md`

## OVERVIEW

REST API 端点层，处理 HTTP 请求/响应。端点只负责：参数验证、调用 Service、返回响应。业务逻辑在 `services/` 层。

## STRUCTURE

```
endpoints/
├── __init__.py       # 路由注册
├── auth.py           # 登录、注册、密码重置
├── users.py          # 用户 CRUD、角色管理
├── textbooks.py      # 教材 CRUD、发布控制
├── chapters.py       # 章节树操作、排序
├── media.py          # 媒体管理、回收站
├── upload.py         # 文件上传
├── search.py         # 全文搜索
└── (version.py)      # 版本历史（通过 chapters 暴露）
```

## WHERE TO LOOK

| 任务 | 文件 | 端点 |
|------|------|------|
| 用户认证 | `auth.py` | `POST /auth/login`, `/auth/register` |
| 用户管理 | `users.py` | `GET/POST/PUT/DELETE /users` |
| 教材管理 | `textbooks.py` | `GET/POST/PUT/DELETE /textbooks` |
| 章节管理 | `chapters.py` | `GET/POST/PUT/DELETE /chapters` |
| 文件上传 | `upload.py` | `POST /upload/image`, `/upload/markdown` |
| 搜索 | `search.py` | `GET /search` |

## CONVENTIONS

### 端点结构
```python
@router.post("/users", response_model=UserResponse)
async def create_user(
    data: UserCreate,           # Pydantic schema
    session: SessionDep,        # 类型别名 DI
    current_user: CurrentUser,  # 认证用户
) -> UserResponse:
    user = await user_service.create_user(session, current_user, data)
    return UserResponse.model_validate(user)
```

### 依赖注入类型别名
```python
# 在 api/deps.py 定义
SessionDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]
SuperAdminUser = Annotated[User, Depends(require_super_admin)]
```

### 响应格式（统一）
```python
# 成功：HTTP 200 + body.code=200
return {"code": 200, "message": "操作成功", "data": result}

# 业务错误：HTTP 200 + body.code=4xx
raise AppException(code=404, message="资源不存在", data=None)
```

### 分页端点
```python
@router.get("/users", response_model=UserListResponse)
async def list_users(
    session: SessionDep,
    current_user: AdminUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    return await user_service.get_users_paginated(
        session, page, page_size, role, search
    )
```

## ANTI-PATTERNS

### 🚫 禁止
- 在端点中写业务逻辑（调用 service）
- 直接使用 `HTTPException`（用 `AppException`）
- 返回非标准响应格式
- 硬编码错误消息（统一中文）

### ⚠️ 注意
- 文件上传端点需要 `UploadFile` 类型
- 分页参数使用 `Query()` 定义默认值和范围

## UNIQUE STYLES

### 权限检查两种模式
```python
# 模式1：端点级别（依赖注入）
@router.delete("/users/{user_id}")
async def delete_user(session: SessionDep, current_user: SuperAdminUser):
    # SuperAdminUser 依赖自动验证角色

# 模式2：资源级别（service 层）
@router.put("/textbooks/{id}")
async def update_textbook(session: SessionDep, user: CurrentUser, ...):
    await textbook_service.update_textbook(session, user, ...)  # service 内检查权限
```

### 文件上传模式
```python
@router.post("/upload/image")
async def upload_image(
    session: SessionDep,
    user: CurrentUser,
    file: UploadFile = File(...),  # FastAPI 文件类型
):
    content = await file.read()
    return await upload_service.upload_image(session, user, content, file.filename)
```
