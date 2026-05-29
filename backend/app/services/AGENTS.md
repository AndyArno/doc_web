# AGENTS.md — Backend Services Layer

**Generated:** 2026-04-08  
**Parent:** `/AGENTS.md`

## OVERVIEW

业务逻辑层，处理所有核心业务规则。端点只负责 HTTP 交互，Service 负责数据验证、业务规则、数据库操作。

## STRUCTURE

```
services/
├── __init__.py              # 模块导出
├── auth_service.py          # 认证：登录、注册、Token 管理
├── user_service.py          # 用户 CRUD、角色管理、权限分配
├── textbook_service.py      # 教材管理、发布控制
├── chapter_service.py       # 章节 CRUD、树操作、导航 ⚠️ 721行
├── chapter_sort_service.py  # 自动排序算法 ⚠️ 715行
├── permission_service.py    # RBAC 权限检查
├── media_service.py         # 媒体管理、软删除、回收站
├── search_service.py        # 全文搜索（FTS5 + jieba）
├── upload_service.py        # 文件上传、ZIP 导入 ⚠️ 632行
└── version_service.py       # 版本历史、恢复
```

## WHERE TO LOOK

| 任务 | 文件 | 关键函数 |
|------|------|----------|
| 用户登录/注册 | `auth_service.py` | `authenticate_user()`, `register_user()` |
| 权限检查 | `permission_service.py` | `check_textbook_permission()`, `has_permission()` |
| 章节树操作 | `chapter_service.py` | `build_chapter_tree()`, `get_chapter_navigation()` |
| 自动排序 | `chapter_sort_service.py` | `preview_sort()`, `apply_sort()` |
| ZIP 导入 | `upload_service.py` | `process_markdown_zip()` |
| 搜索索引 | `search_service.py` | `index_chapter()`, `search_content()` |

## CONVENTIONS

### 函数签名模式
```python
async def function_name(
    session: AsyncSession,     # 总是第一个参数
    user: User,                # 需要认证时
    ...business_params...,     # 业务参数
) -> ReturnType:
```

### 错误处理
```python
# 统一使用 AppException
raise AppException(
    code=404,              # HTTP-like 状态码
    message="用户不存在",   # 中文用户友好消息
    data=None              # 可选附加数据
)
```

### 状态码约定
| Code | 含义 | 使用场景 |
|------|------|----------|
| 400 | 请求错误 | 验证失败、无效操作 |
| 401 | 未认证 | Token 无效/过期 |
| 403 | 无权限 | RBAC 检查失败 |
| 404 | 未找到 | 资源不存在 |
| 409 | 冲突 | 用户名/邮箱重复 |
| 500 | 服务器错误 | 文件写入失败等 |

### 权限检查两种模式
```python
# 模式1：抛异常（用于端点）
await check_textbook_permission(session, user, textbook_id, "edit")

# 模式2：返回布尔（用于条件判断）
if await has_permission(session, user, textbook_id, "edit"):
    # 执行操作
```

### 分页响应模式
```python
async def get_xxx_paginated(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
) -> XxxListResponse:
    # 查询总数
    total = (await session.execute(count_query)).scalar() or 0
    
    # 分页查询
    query = query.offset((page - 1) * page_size).limit(page_size)
    items = (await session.execute(query)).scalars().all()
    
    # 返回 Schema
    return XxxListResponse(
        items=[XxxResponse.model_validate(x) for x in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size),
    )
```

## ANTI-PATTERNS

### 🚫 禁止
- 在 Service 层直接返回 HTTP 响应（那是端点的事）
- 使用同步 Session（必须用 AsyncSession）
- 捕获异常后静默忽略（要么处理，要么重新抛出）
- 在 Service 中处理 JWT/Token（那是 auth_service 的职责）

### ⚠️ 注意
- 次要操作失败不应中断主流程（如搜索索引失败）

## REFACTORING RECOMMENDATIONS

### chapter_service.py (721行) → 拆分
```
chapter_service.py →
├── chapter_crud_service.py      # Basic CRUD
├── chapter_tree_service.py      # Tree operations (navigation, descendants)
├── chapter_move_service.py      # Move/reorder with validation
└── chapter_validation.py        # Shared validation helpers
```

### chapter_sort_service.py (715行) → 拆分
```
chapter_sort_service.py →
├── chapter_sort_core.py         # calculate_sort_orders (core algorithm)
├── chapter_sort_preview.py      # preview_sort, _build_preview_tree
├── chapter_sort_apply.py        # apply_sort, undo_sort
└── chapter_folder_matcher.py    # match_folder, create_folder_if_needed
```

### upload_service.py (632行) → 拆分
```
upload_service.py →
├── image_upload_service.py      # upload_image
└── markdown_import_service.py   # upload_markdown_zip, upload_single_markdown
```

## UNIQUE STYLES

### 角色层级数值化
```python
ROLE_HIERARCHY = {
    Role.SUPER_ADMIN: 4,
    Role.ADMIN: 3,
    Role.EDITOR: 2,
    Role.USER: 1,
}

# 单一比较判断权限
if ROLE_HIERARCHY[user.role] < ROLE_HIERARCHY[required_role]:
    raise AppException(code=403, ...)
```

### 最佳努力模式（Best-Effort）
次要操作失败时记录日志但不中断主流程：
```python
try:
    await search_service.index_chapter(session, chapter.id)
except Exception as e:
    logger.error(f"Failed to index chapter {chapter.id}: {e}")
    # 不重新抛出，主操作已成功
```

### 软删除模式
```python
# 在 Model 中定义方法
class Media:
    def soft_delete(self) -> None:
        self.is_deleted = True
        self.deleted_at = datetime.now(UTC)

# 在 Service 中调用
media.soft_delete()
await session.commit()
```

### 审计日志内置
```python
# 权限变更自动记录
audit_log = AuditLog(
    action="permission_update",
    target_user_id=user_id,
    operator_id=operator.id,
    details={
        "old_permissions": old,
        "new_permissions": new,
    },
)
session.add(audit_log)
```

## TESTING

Service 测试位于 `backend/tests/test_services/`，使用 `@pytest.mark.asyncio` 装饰器：

```python
@pytest.mark.asyncio
async def test_create_user_duplicate_username(test_session: AsyncSession):
    # 先创建一个用户
    await user_service.create_user(test_session, user_data)
    
    # 尝试创建同名用户
    with pytest.raises(AppException) as exc_info:
        await user_service.create_user(test_session, same_username_data)
    
    assert exc_info.value.code == 409
```
