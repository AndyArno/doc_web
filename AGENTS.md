# AGENTS.md — ROS小车教学网站

**Generated:** 2026-04-19  
**Commit:** f94ddf0  
**Branch:** main

> **交流语言：中文** | 技术术语保留英文（JWT, API, AsyncSession 等）

## OVERVIEW

ROS机器人操作系统教学内容管理平台，前后端分离架构。FastAPI 异步后端 + Vue 3 前端，支持三级章节结构、RBAC 权限、全文搜索。

## 项目概览

| 属性 | 内容 |
|------|------|
| 类型 | 毕设项目（开发中） |
| 架构 | 前后端分离 |
| 后端 | Python 3.13+ + uv + FastAPI + SQLAlchemy 2.x + PostgreSQL 17 (async) + JWT |
| 前端 | Vue 3 + Vite + Tailwind CSS v4 + Pinia + Vue Router + Axios + markdown-it |
| 图标 | Lucide Vue Next（不用 Element Plus） |
| 并发目标 | ~200 学生 |

## STRUCTURE

```
.
├── backend/               # FastAPI 后端
│   ├── app/
│   │   ├── api/          # 路由层 (endpoints + deps)
│   │   ├── core/         # 配置、JWT、异常处理
│   │   ├── db/           # 数据库会话、初始化
│   │   ├── models/       # SQLAlchemy 模型
│   │   ├── schemas/      # Pydantic 数据模型
│   │   ├── services/     # 业务逻辑层 ⚡ 复杂
│   │   └── utils/        # 工具函数
│   ├── migrations/       # Alembic 迁移
│   └── tests/            # pytest 测试
└── frontend/              # Vue 3 前端
    └── src/
        ├── api/          # Axios 请求封装
        ├── components/   # 公共组件 ⚡ 复杂
        ├── composables/  # 组合式函数
        ├── views/        # 页面组件 ⚡ 复杂
        ├── stores/       # Pinia 状态管理
        └── types/        # TypeScript 类型
```

## WHERE TO LOOK

| 任务 | 位置 | 说明 |
|------|------|------|
| 添加新 API 端点 | `backend/app/api/v1/endpoints/` | 参考 auth.py, users.py |
| 添加业务逻辑 | `backend/app/services/` | 见 `services/AGENTS.md` |
| 数据库模型变更 | `backend/app/models/` + `migrations/` | 修改后生成迁移 |
| 新增页面 | `frontend/src/views/` | 见 `views/AGENTS.md` |
| 新增组件 | `frontend/src/components/` | 见 `components/AGENTS.md` |
| 修改 API 类型 | `frontend/src/types/api.ts` | 与后端 schema 同步 |

## 常用命令

### 后端
```bash
cd backend
uv venv && uv sync                     # 初始化环境
uv run uvicorn app.main:app --reload   # 启动开发服务器
uv run pytest                          # 运行全部测试
uv run pytest tests/test_api/test_users.py              # 运行单个测试文件
uv run pytest tests/test_api/test_users.py -k "test_create_user"  # 运行单个测试用例
uv run pytest -v                       # 详细输出
uv run pytest --cov=app                # 带覆盖率
uv run python -m app.db.init_db        # 初始化数据库（建表+创建超级管理员）
```

### 前端
```bash
cd frontend
npm install                            # 安装依赖
npm run dev                            # 启动开发服务器
npm run build                          # 构建生产版本
npm run test                           # 运行测试（watch 模式）
npm run test:run                       # 运行测试（单次）
npm run type-check                     # TypeScript 类型检查
```

## 项目结构

```
backend/app/
├── main.py          # FastAPI 入口
├── api/v1/endpoints/  # 路由层（按模块划分）
├── models/          # SQLAlchemy 模型（异步模式）
├── schemas/         # Pydantic 数据模型
├── core/            # 配置、JWT、权限、异常处理
├── services/        # 业务逻辑层
├── db/              # 数据库会话
└── utils/           # 工具函数

frontend/src/
├── api/             # Axios 请求封装
├── router/          # 路由配置
├── stores/          # Pinia 状态管理
├── views/           # 页面组件
├── components/      # 公共组件
├── composables/     # 组合式函数
├── layouts/         # 布局组件
├── types/           # TypeScript 类型定义
└── mocks/           # Mock 数据
```

## 设计文档

**编码前必须先读 `.sisyphus/drafts/` 下的设计文档。** 严格按文档定义的架构实现。
发现需求与文档冲突时：停止 → 指出冲突点 → 询问用户 → 获授权后继续。

## 代码风格指南

### 导入规范
- **Python**: 标准库 → 第三方库 → 本地模块（`app.*`）
- **TypeScript**: Vue 核心 → 第三方库 → 本地模块（`@/*` 别名）

### 命名约定

| 类型 | Python | TypeScript |
|------|--------|------------|
| 变量/函数 | snake_case | camelCase |
| 类/接口 | PascalCase | PascalCase |
| 常量 | UPPER_SNAKE | UPPER_SNAKE |
| 组件文件 | - | PascalCase.vue |
| API 函数 | - | get*, create*, update*, delete* |

### 类型定义
- **Python**: 类型注解 + Pydantic schema（`model_config = ConfigDict(from_attributes=True)`）
- **TypeScript**: interface 定义，统一导出到 `types/api.ts`

### 错误处理
- **后端**: `raise AppException(code=404, message="...", data=None)` → 统一响应格式
- **前端**: Axios 拦截器自动处理 → Toast 提示

### 代码注释
- Python: Google Style Docstring
- Vue/TS: JSDoc 注释解释"为什么"
- 禁止：注释掉的代码、`console.log`、无意义注释

## 核心规范

### API 响应格式
所有接口返回 `{code, message, data}`。使用自定义 ExceptionHandler 统一处理。
认证方式：Bearer Token（JWT）。
**重要**：业务错误返回 HTTP 200 + body.code，前端需检查 `response.data.code`。

### 数据库
- 使用 SQLAlchemy AsyncSession + `select()`（异步模式），通过 Depends 注入
- 章节层级：三级（章→节→小节），`parent_id` 自关联

### 权限系统（RBAC）
| 角色 | 权限 |
|------|------|
| super_admin | 所有权限 + 系统管理 |
| admin | 按教材授权，管理编辑 |
| editor | 按具体操作授权 |
| user | 只读公开内容 |

角色层级：高级可修改低级，低级不能修改高级。

## ANTI-PATTERNS (THIS PROJECT)

### 🚫 禁止使用
| 项目 | 禁止 | 替代方案 |
|------|------|----------|
| UI 组件库 | Element Plus | Tailwind CSS + Lucide Vue Next |
| 类型错误压制 | `as any`, `@ts-ignore` | 修复类型定义 |
| 空异常捕获 | `except: pass` | 处理或重新抛出 |

### 🚫 代码质量
- 注释掉的代码
- `console.log` 调试语句
- 无意义注释
- 删除测试用例以通过测试

### 🚫 Git 提交
- `.env` 文件、密钥、构建产物
- 测试文件夹（`backend/tests/` 不提交）
- 合并不相关的修改

### 🚫 业务约束
- 章节层级：**不能超过 3 层**
- 教材标题、章节标题：**不超过 200 字符**
- 文件上传：ZIP/单图片 **最大 100MB**
- 父节点拖入子孙节点：**禁止**（循环引用）

## UNIQUE STYLES

### 后端
- **HTTP 200 + 业务码**：所有响应（含错误）返回 HTTP 200，业务状态码在 `body.code`
- **角色数值层级**：用数字 1-4 比较权限（super_admin=4, user=1）
- **Type Alias DI**：`SessionDep = Annotated[AsyncSession, Depends(get_db)]`
- **AppException**：`raise AppException(code=404, message="...", data=None)`

### 前端
- **响应式策略**：桌面端表格 + 移动端卡片列表（`hidden md:block` / `md:hidden`）
- **Axios 响应解包**：API 函数返回 `data.data`，非 AxiosResponse
- **Toast 单例**：`useToast()` 和 `Toast.xxx()` 双模式
- **Tailwind CSS v4**：使用 `@tailwindcss/postcss` 插件（非 v3 配置方式）

## 测试规范

### 后端测试
- 框架：`pytest + pytest-asyncio + httpx`
- 配置：`asyncio_mode = "auto"`
- 位置：`tests/test_api/`，按模块划分
- 数据库：默认 in-memory SQLite，可切换 PostgreSQL
- 断言：检查 HTTP status + `data["code"]`（双重验证）
- 每个接口至少成功+失败两个用例
- 测试文件夹不要提交到 git

### 前端测试
- 框架：`vitest + @vue/test-utils + jsdom`
- 配置：`globals: true`（describe/it/expect 全局可用）
- 位置：`src/**/*.test.ts`，与源文件同级
- 测试文件命名：`*.test.ts`

## Git 提交

格式：`<type>(scope): <description>`
- type: feat/fix/docs/refactor/test/chore
- scope: backend/frontend
- description: 中文描述

每次完成一个功能点立即提交，禁止合并不相关的修改。不提交 .env、密钥、构建产物。

## 关键约束

1. 文件上传限制：ZIP 100MB，单图片 100MB
2. 教材创建和删除仅限 super_admin
3. 数据库使用异步模式（AsyncSession + select）
4. 错误响应统一 `{code, message, data}` 格式
5. 前端 UI 用 Tailwind CSS，不用 Element Plus

## 前端约束

### 章节拖拽限制
- 不能将节点拖到第 3 层节点下（会创建第 4 层，超出三级限制）
- 不能将父节点拖入自己的子孙节点（循环引用检查）

### 输入限制
- 教材标题：不超过 200 个字符
- 章节标题：不超过 200 个字符

## 测试配置

### 后端测试
- 默认使用 **in-memory SQLite**（`sqlite+aiosqlite:///:memory:`）快速执行
- 可通过环境变量 `TEST_DATABASE_URL` 切换到 PostgreSQL（时区测试等场景）

### 前端测试
- Vitest + jsdom 环境
- 测试文件与源文件同级（`*.test.ts`）

## NOTES

### 设计文档
**编码前必须先读 `.sisyphus/drafts/` 下的设计文档。** 严格按文档定义的架构实现。
发现需求与文档冲突时：停止 → 指出冲突点 → 询问用户 → 获授权后继续。

### 配置特点
- Tailwind CSS v4（配置方式与 v3 不同，使用 `@tailwindcss/postcss` 插件）
- TypeScript 非严格模式（`strict: false`）
- 无 ESLint/Prettier 配置（依赖开发者自觉）

### 大文件警示

**后端（需要拆分）：**
| 文件 | 行数 | 建议 |
|------|------|------|
| `backend/app/services/chapter_service.py` | 721 | 拆分为 CRUD + Tree + Move + Validation |
| `backend/app/services/chapter_sort_service.py` | 715 | 拆分为 Core + Preview + Apply + FolderMatcher |
| `backend/app/services/upload_service.py` | 632 | 拆分为 ImageUpload + MarkdownImport |
| `backend/app/utils/archive_extractor.py` | 527 | 复杂度合理（7种格式支持） |

**前端（急需重构）：**
| 文件 | 行数 | 建议 |
|------|------|------|
| `frontend/src/views/admin/ContentManager.vue` | 1467 | **最高优先级** - 拆分 composables 和 modals |
| `frontend/src/views/admin/MediaLibrary.vue` | 1146 | 拆分 MediaTable + MediaCard + MultiSelectBar |
| `frontend/src/views/admin/Users.vue` | 1005 | 拆分 UserTable + UserCard + UserEditModal |
| `frontend/src/components/SortPreviewModal.vue` | 799 | 提取递归 SortPreviewNode 组件 |
| `frontend/src/components/TreeNode.vue` | 518 | 提取验证逻辑到 useTreeValidation |
| `frontend/src/views/admin/Textbooks.vue` | 551 | 可选拆分 TextbookRow |

**测试文件（>500行，复杂度可接受）：**
- `backend/tests/test_integration.py` (1047)
- `backend/tests/test_services/test_chapter_service.py` (1020)
- `backend/tests/test_api/test_chapters.py` (843)

### 缺失的 CI/CD
项目无 CI/CD 配置、无 Docker、无自动化测试流程。部署前需手动运行测试。
