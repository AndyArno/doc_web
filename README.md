# ROS小车教学网站 - 生产环境部署指南

> **适用系统**: Debian 12+ / Ubuntu 22.04+
> **部署方式**: 手动部署（非 Docker）
> **最后更新**: 2026-05-11

---

## 目录

1. [环境要求](#1-环境要求)
2. [安装 Python 3.13+](#2-安装-python-313)
3. [安装和配置 PostgreSQL](#3-安装和配置-postgresql)
4. [安装 Redis](#4-安装-redis)
5. [克隆代码并安装后端依赖](#5-克隆代码并安装后端依赖)
6. [配置环境变量](#6-配置环境变量)
7. [数据库迁移](#7-数据库迁移)
8. [构建前端](#8-构建前端)
9. [配置 Nginx](#9-配置-nginx)
10. [配置 systemd 服务](#10-配置-systemd-服务)
11. [启动服务](#11-启动服务)
12. [运行初始化向导](#12-运行初始化向导)
13. [配置 HTTPS](#13-配置-https)
14. [常见问题排查](#14-常见问题排查)
15. [更新部署](#15-更新部署)

---

## 1. 环境要求

部署前请确保服务器满足以下条件：

| 组件 | 最低版本 | 说明 |
|------|----------|------|
| 操作系统 | Debian 12 / Ubuntu 22.04 LTS | 其他 Linux 发行版可参考对应命令 |
| Python | 3.13+ | 项目 `requires-python = ">=3.13"`（`pyproject.toml`） |
| PostgreSQL | 16+ | 使用 `asyncpg` 异步驱动连接 |
| Redis | 7+ | 用于 SlowAPI 请求频率限制 |
| Nginx | 任意稳定版 | 反向代理 + 静态文件服务 |
| Node.js | 20+ LTS | 前端构建和 npm 包管理 |
| git | 任意版本 | 代码克隆 |
| 内存 | 建议 1GB+ | 后端异步模式，内存占用较低 |
| 磁盘 | 建议 10GB+ | 包含代码、数据库、上传文件 |

> **注意**: 本项目使用 Python 3.13+ 语法特性（`requires-python = ">=3.13"`）。请勿使用更低版本的 Python，否则可能出现语法错误。

---

## 2. 安装 uv（Python 版本管理器）

项目使用 [uv](https://docs.astral.sh/uv/) 管理 Python 版本和依赖。`uv` 会自动下载 Python 3.13+，无需通过系统包管理器安装。

```bash
# 安装 uv（官方脚本，Ubuntu / Debian 通用）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 重新加载 shell 环境（或重新登录）
source ~/.bashrc

# 验证 uv 安装
uv --version
# 应输出: uv x.x.x
```

> **说明**: `uv` 由 Astral 开发（Ruff 同团队），是一个极速的 Python 包管理器和版本管理器。它会自动下载并管理项目所需的 Python 3.13+，无需手动安装 Python 或配置 deadsnakes PPA。详见 [uv 官方文档](https://docs.astral.sh/uv/)。

---

## 3. 安装和配置 PostgreSQL

### 3.1 安装 PostgreSQL

```bash
# 安装 PostgreSQL
sudo apt install postgresql postgresql-client -y

# 启动并设置开机自启
sudo systemctl enable postgresql
sudo systemctl start postgresql

# 验证运行状态
sudo systemctl status postgresql
# 应显示 active (running)
```

### 3.2 创建数据库和用户

```bash
# 以 postgres 用户身份进入 PostgreSQL Shell
sudo -u postgres psql
```

在 PostgreSQL Shell 中执行以下 SQL：

```sql
-- 创建数据库用户（请将 'your_db_password' 替换为强密码）
CREATE USER document_web WITH PASSWORD 'your_db_password';

-- 创建数据库，指定所有者
CREATE DATABASE document_web OWNER document_web;

-- 授予所有权限
GRANT ALL PRIVILEGES ON DATABASE document_web TO document_web;

-- 退出
\q
```

验证数据库连接：

```bash
# 测试能否连接
psql -h localhost -U document_web -d document_web -c "SELECT 1;"
# 输入密码后应返回 ?column? = 1
```

> **注意**: 如果连接被拒绝，检查 `pg_hba.conf` 中的认证方式。对于本地连接，确保使用 `md5` 或 `scram-sha-256` 密码认证：
> ```bash
> sudo nano /etc/postgresql/*/main/pg_hba.conf
> # 找到 local all all 所在行，确认认证方式为 md5 或 scram-sha-256
> sudo systemctl reload postgresql
> ```

### 3.3 安装 pg_jieba 中文分词扩展

项目使用 PostgreSQL 的 `pg_jieba` 扩展进行中文全文搜索。该扩展不在 Debian 官方仓库中，需要源码编译。

```bash
# 安装编译依赖
sudo apt install postgresql-server-dev-15 git build-essential cmake -y

# 克隆源码（含 cppjieba 子模块）
git clone --recurse-submodules https://github.com/jaiminpan/pg_jieba.git /tmp/pg_jieba
cd /tmp/pg_jieba
mkdir build && cd build
cmake .. -DPostgreSQL_TYPE_INCLUDE_DIR=/usr/include/postgresql/15/server
make
sudo make install

# 在项目数据库中启用扩展
sudo -u postgres psql -d document_web -c "CREATE EXTENSION IF NOT EXISTS pg_jieba;"

# 验证
sudo -u postgres psql -d document_web -c "SELECT cfgname FROM pg_ts_config WHERE cfgname LIKE '%jieba%';"
# 应输出 jiebacfg, jiebaqry, jiebamp, jiebahmm
```

> **说明**：此扩展仅影响全文搜索功能。如果编译失败，上传和章节管理仍可正常使用，搜索功能会降级为简单模式。

---

## 4. 安装 Redis

本项目使用 Redis 存储 SlowAPI 请求限流计数。

```bash
# 安装 Redis
sudo apt install redis-server -y

# 启动并设置开机自启
sudo systemctl enable redis-server
sudo systemctl start redis-server

# 验证运行状态
sudo systemctl status redis-server
# 应显示 active (running)

# 测试 Redis 连接
redis-cli ping
# 应返回 PONG
```

默认配置即可满足需求。Redis 监听 `127.0.0.1:6379`，无密码认证（仅本地访问，安全）—— 项目配置中的默认 `REDIS_URL` 正是 `redis://localhost:6379/0`。

---

## 5. 克隆代码并安装后端依赖

### 5.1 创建部署目录并克隆代码

```bash
# 创建部署目录
sudo mkdir -p /opt/document_web
sudo chown $USER:$USER /opt/document_web

# 克隆代码（将 <repository-url> 替换为你的 Git 仓库地址）
cd /opt/document_web
git clone <repository-url> .

# 确认文件结构
ls -la
# 应该看到 backend/ 和 frontend/ 目录
```

### 5.2 创建虚拟环境并安装依赖

```bash
cd /opt/document_web/backend

# uv 自动下载 Python 3.13+ 并创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate

# 安装生产依赖
uv pip install -r requirements.txt

# 验证关键包已安装
uv pip list | grep -E "fastapi|uvicorn|sqlalchemy|asyncpg|redis|slowapi"
```

> **提示**: 安装 `bcrypt` 等包可能需要编译 C 扩展。如果报错，请确保已安装系统编译工具：
> ```bash
> sudo apt install build-essential libffi-dev -y
> ```

`requirements.txt` 包含以下生产依赖：

| 包名 | 用途 |
|------|------|
| fastapi | Web 框架 |
| uvicorn[standard] | ASGI 服务器 |
| sqlalchemy[asyncio] | 异步 ORM |
| asyncpg | PostgreSQL 异步驱动 |
| python-jose[cryptography] | JWT 生成与验证 |
| passlib[bcrypt] / bcrypt | 密码哈希 |
| pydantic-settings | 环境变量配置 |
| alembic[asyncio] | 数据库迁移 |
| python-multipart | 表单/文件上传解析 |
| aiofiles | 异步文件 I/O |
| email-validator | 邮箱格式校验 |
| jieba | 中文分词（全文搜索） |
| py7zr / rarfile | 压缩包解析 |
| pypinyin | 拼音转换（搜索辅助） |
| redis | Redis 客户端（限流） |
| slowapi | 请求频率限制 |

---

## 6. 配置环境变量

### 6.1 从模板复制 .env 文件

```bash
cd /opt/document_web/backend
cp .env.example .env
```

### 6.2 编辑 .env 文件

```bash
nano .env
```

下面是一个完整的生产环境 `.env` 配置示例：

```bash
# ============================================================
# ROS小车教学网站 - 生产环境配置
# ============================================================

# 应用配置
APP_NAME=ROS小车教学网站
DEBUG=false

# JWT 配置
# SECRET_KEY: 用 openssl rand -hex 32 生成，切勿使用默认值
SECRET_KEY=a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 数据库配置
# DATABASE_URL 格式: postgresql+asyncpg://用户名:密码@主机:端口/数据库名
DATABASE_URL=postgresql+asyncpg://document_web:your_db_password@localhost:5432/document_web

# Redis 配置
# 默认本地 Redis 即可，生产环境建议设置密码
REDIS_URL=redis://localhost:6379/0

# 文件上传配置
# 100MB = 104857600 字节
MAX_UPLOAD_SIZE=104857600

# CORS 配置
# 生产环境设置为实际域名（多个域名用逗号分隔）
# 例如: http://your-domain.com,https://your-domain.com
# 注意：初始化向导可以帮你在系统内记录 CORS 域名
ALLOWED_ORIGINS=*

# 超级管理员初始密码
# 初始化向导（/setup）会要求重新设置，这里用作备选
FIRST_SUPERADMIN_PASSWORD=TempPass123!
```

关键配置说明：

| 变量 | 说明 | 注意事项 |
|------|------|----------|
| `SECRET_KEY` | JWT 签名密钥 | **必须修改**，用 `openssl rand -hex 32` 生成强随机字符串 |
| `DATABASE_URL` | PostgreSQL 连接串 | 填写第 3 步创建的数据库用户名和密码 |
| `REDIS_URL` | Redis 连接地址 | 默认值通常无需修改 |
| `ALLOWED_ORIGINS` | 跨域允许的来源 | 部署时建议先设为 `*`，等配置完域名后再改为实际域名 |
| `FIRST_SUPERADMIN_PASSWORD` | 备用管理员密码 | 初始化向导会创建新的管理员账户，这个值作为系统降级备选 |

生成强随机密钥：

```bash
openssl rand -hex 32
# 输出: a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0
```

---

## 7. 数据库迁移

使用 Alembic 执行数据库表创建。

```bash
cd /opt/document_web/backend

# 确保虚拟环境已激活
source .venv/bin/activate

# 执行所有待处理的迁移
alembic upgrade head
```

成功输出应包含类似信息：

```
INFO  [alembic.runtime.migration] Running upgrade ... -> xxxxx, create tables
```

### 验证迁移结果

```bash
# 连接数据库查看表
psql -h localhost -U document_web -d document_web -c "\dt"
```

应该看到 `users`、`textbooks`、`chapters`、`media`、`system_configs` 等表。

> **注意**: Alembic 只负责创建表结构，不会创建初始数据。管理员账户通过初始化向导（第 12 步）创建。

---

## 8. 构建前端

### 8.1 安装 Node.js 20+

```bash
# 使用 NodeSource 官方脚本安装 Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y

# 验证版本
node --version   # 应输出 v20.x.x
npm --version    # 应输出 10.x.x 或更高
```

### 8.2 安装前端依赖

```bash
cd /opt/document_web/frontend

# 安装依赖
npm install
```

### 8.3 配置前端环境变量

```bash
# 复制环境变量模板
cp .env.example .env.production
```

编辑 `.env.production`：

```bash
nano .env.production
```

内容如下：

```bash
# 生产环境 API 地址
# 如果是同域名反向代理，使用相对路径即可
VITE_API_BASE_URL=/api/v1

# 禁用 Mock 数据
VITE_USE_MOCK=false
```

> **注意**: Nginx 将 `/api` 反向代理到后端，因此前端使用相对路径 `/api/v1` 即可。如果你的前端和后端不在同一域名下，请设置为完整的 URL（例如 `https://api.your-domain.com/api/v1`），并确保后端 `ALLOWED_ORIGINS` 包含前端域名。

### 8.4 构建生产版本

```bash
# 构建前端静态文件
npm run build
```

构建产物输出到 `frontend/dist/` 目录：

```
dist/
├── index.html
├── assets/
│   ├── index-xxxxxxxx.css
│   └── index-xxxxxxxx.js
└── ...
```

### 8.5 设置文件权限

```bash
# 确保 Nginx 可以读取静态文件
sudo chmod -R 755 /opt/document_web/frontend/dist
```

---

## 9. 配置 Nginx

Nginx 同时负责：
- 提供前端静态文件（SPA 单页应用）
- 反向代理 API 请求到后端（uvicorn 端口 8000）
- 转发上传文件请求

### 9.1 安装 Nginx

```bash
sudo apt install nginx -y

# 启动并启用开机自启
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 9.2 创建站点配置文件

```bash
sudo nano /etc/nginx/sites-available/document-web
```

粘贴以下完整配置（包含详细注释）：

```nginx
# ==================================================================
# ROS小车教学网站 - Nginx 站点配置
# 文件路径: /etc/nginx/sites-available/document-web
# 功能: SPA 静态文件 + API 反向代理
# ==================================================================

server {
    # 监听端口
    listen 80;
    # 替换为你的实际域名（如 ros-teaching.example.com）
    server_name your-domain.com;

    # ================================================================
    # 日志配置
    # ================================================================
    access_log /var/log/nginx/document-web-access.log;
    error_log /var/log/nginx/document-web-error.log;

    # ================================================================
    # 上传文件大小限制（与后端 MAX_UPLOAD_SIZE 保持一致: 100MB）
    # ================================================================
    client_max_body_size 100m;

    # ================================================================
    # 前端静态文件（SPA 模式）
    # - try_files: 找不到文件时回退到 index.html
    #   Vue Router 在浏览器端处理路由，因此所有路径都应由 index.html 响应
    # ================================================================
    location / {
        root /opt/document_web/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;

        # 浏览器缓存策略
        # 带哈希的 JS/CSS 资源可长期缓存（文件名变化即更新）
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # HTML 文件不缓存（确保用户始终获得最新版本）
        location ~* \.html$ {
            expires -1;
            add_header Cache-Control "no-cache";
        }
    }

    # ================================================================
    # API 反向代理
    # 将 /api/ 路径的请求转发到后端 FastAPI 服务（127.0.0.1:8000）
    # ================================================================
    location /api/ {
        proxy_pass http://127.0.0.1:8000;

        # 传递客户端真实信息
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置
        # proxy_read_timeout: 处理大文件上传时需要更长超时
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;

        # 缓冲设置（适用于大文件上传）
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # ================================================================
    # 上传文件服务
    # /uploads/ 路径下的文件由后端直接提供（存储在 backend/uploads/ 目录）
    # ================================================================
    location /uploads/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # ================================================================
    # acme.sh HTTP 验证目录（用于 Let's Encrypt 证书签发）
    # 配置 HTTPS 时需要此路径
    # ================================================================
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
}
```

### 9.3 启用站点并重载 Nginx

```bash
# 创建软链接启用站点
sudo ln -s /etc/nginx/sites-available/document-web /etc/nginx/sites-enabled/

# 删除默认站点（可选，避免冲突）
sudo rm -f /etc/nginx/sites-enabled/default

# 测试 Nginx 配置语法
sudo nginx -t
# 应输出: syntax is ok / test is successful

# 重载 Nginx
sudo systemctl reload nginx
```

### 9.4 验证 Nginx 是否工作

```bash
# 检查 Nginx 运行状态
sudo systemctl status nginx

# 测试静态文件访问（替换为你的服务器 IP 或域名）
curl -I http://your-server-ip/
# 应返回 HTTP/1.1 200 OK
```

---

## 10. 配置 systemd 服务

使用 systemd 管理后端 API 进程，实现开机自启和崩溃自动重启。

### 10.1 创建服务文件

```bash
sudo nano /etc/systemd/system/document-web.service
```

粘贴以下完整配置：

```ini
# ==================================================================
# ROS小车教学网站 - 后端 API systemd 服务
# 文件路径: /etc/systemd/system/document-web.service
# 管理命令:
#   启动: sudo systemctl start document-web
#   停止: sudo systemctl stop document-web
#   重启: sudo systemctl restart document-web
#   状态: sudo systemctl status document-web
#   日志: sudo journalctl -u document-web -f
# ==================================================================

[Unit]
Description=ROS小车教学网站 Backend API
Documentation=https://github.com/your-org/document-web
After=network.target postgresql.service redis-server.service
Requires=postgresql.service redis-server.service
Wants=network-online.target

[Service]
# 服务类型: simple 表示 ExecStart 启动的进程即为主进程
Type=simple

# 运行用户和组
# 注意: 确保 www-data 用户有权限读取 /opt/document_web/backend/
User=www-data
Group=www-data

# 工作目录
WorkingDirectory=/opt/document_web/backend

# 环境变量
Environment="PYTHONUNBUFFERED=1"

# 从 .env 文件加载环境变量
EnvironmentFile=/opt/document_web/backend/.env

# 启动命令
# --host 127.0.0.1: 仅监听本地回环，由 Nginx 对外暴露（安全）
# --port 8000: FastAPI 默认端口
# 如需更多 worker，可添加 --workers N 参数（默认 1 worker）
ExecStart=/opt/document_web/backend/.venv/bin/uvicorn app.main:app \
    --host 127.0.0.1 \
    --port 8000

# 崩溃后自动重启
Restart=always
# 重启前等待 5 秒（避免快速重启循环）
RestartSec=5

# 限制重启频率（30 秒内最多重启 3 次，超过则停止尝试）
StartLimitIntervalSec=30
StartLimitBurst=3

# 安全加固（可选）
NoNewPrivileges=yes
PrivateTmp=yes

# 日志配置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=document-web

[Install]
# 随系统启动（multi-user.target 即服务器正常运行模式）
WantedBy=multi-user.target
```

### 10.2 设置目录权限

systemd 服务以 `www-data` 用户运行，需要确保该用户有权限访问后端目录和上传目录：

```bash
# 设置后端目录所有者
sudo chown -R www-data:www-data /opt/document_web/backend

# 确保上传目录可写
sudo mkdir -p /opt/document_web/backend/uploads/images
sudo chown -R www-data:www-data /opt/document_web/backend/uploads

# 确保 .env 文件可读（但不要设为全局可读，因为包含密码）
sudo chown www-data:www-data /opt/document_web/backend/.env
sudo chmod 600 /opt/document_web/backend/.env

# 恢复代码文件为 root 所有（防止通过 Web 进程修改源码）
sudo chown -R root:root /opt/document_web/backend/app
sudo chmod -R 755 /opt/document_web/backend/app
```

### 10.3 启用服务

```bash
# 重载 systemd 配置（识别新服务）
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable document-web

# 验证服务文件是否正确
sudo systemctl show document-web | grep -E "ExecStart|User|Group|Restart"
```

---

## 11. 启动服务

### 11.1 启动后端

```bash
# 启动后端 API 服务
sudo systemctl start document-web

# 查看运行状态
sudo systemctl status document-web
# 应显示 active (running)

# 查看实时日志（确认没有错误）
sudo journalctl -u document-web -f
# 按 Ctrl+C 退出日志
```

健康检查：

```bash
# 通过 Nginx 代理访问 API 根路径
curl http://localhost/api/v1
# 应返回: {"code":200,"message":"API v1 is running","data":null}

# 如果系统未初始化，非 setup 接口会返回:
# {"code":503,"message":"系统尚未初始化，请访问 /setup 完成配置","data":null}
# 这是正常的，继续下一步初始化即可
```

### 11.2 确保 Nginx 正常运行

```bash
# 重载 Nginx（如果之前启动过）
sudo systemctl reload nginx

# 验证
sudo systemctl status nginx
```

---

## 12. 运行初始化向导

系统首次部署后，需要运行初始化向导来创建超级管理员账户并完成系统配置。

### 12.1 通过浏览器访问

在浏览器中访问（替换为你的服务器 IP 或域名）：

```
http://your-server-ip/setup
```

### 12.2 填写初始化表单

初始化页面会要求填写以下信息：

| 字段 | 说明 | 示例 |
|------|------|------|
| 管理员用户名 | 超级管理员登录用户名 | `admin` |
| 管理员邮箱 | 管理员联系邮箱 | `admin@example.com` |
| 管理员密码 | 必须包含大写字母和数字，至少 8 位 | `MyPass123` |
| CORS 允许域名 | 前端访问域名，多个用逗号分隔 | `http://your-domain.com,https://your-domain.com` |

> **密码要求**: 至少 8 位，必须包含大写字母和数字（与 `user.py` 中的 `_validate_password_complexity` 一致）。

### 12.3 提交并完成

点击提交后，系统会：
1. 创建超级管理员账户（角色：`super_admin`）
2. 将 CORS 域名保存到 `system_configs` 表
3. 标记系统为"已初始化"状态

成功后，自动跳转到登录页面。使用刚才创建的管理员账户登录即可。

### 12.4 命令行验证初始化状态

```bash
# 通过 API 查询初始化状态
curl http://127.0.0.1:8000/api/v1/setup/status
# 初始化完成后应返回: {"code":200,"data":{"initialized":true}}
```

---

## 13. 配置 HTTPS

使用 [acme.sh](https://github.com/acmesh-official/acme.sh) 签发免费的 Let's Encrypt SSL 证书。

### 13.1 安装 acme.sh

```bash
# 普通用户安装
curl https://get.acme.sh | sh

# 重新加载 shell 环境
source ~/.bashrc
```

### 13.2 签发证书

使用 HTTP 验证方式（确保域名已解析到服务器 IP，且 Nginx 的 `/.well-known/acme-challenge/` 路径可正常访问）。

```bash
# 替换 your-domain.com 为你的域名
# -w: 指定 Web 根目录（与 Nginx 配置中的 root 路径一致）
~/.acme.sh/acme.sh --issue -d your-domain.com -w /var/www/html

# 如果成功，输出类似:
# [Tue May 11 10:00:00 CST 2026] Your cert is in: /home/user/.acme.sh/your-domain.com/
```

### 13.3 安装证书到指定目录

```bash
# 创建 SSL 证书存放目录
sudo mkdir -p /etc/nginx/ssl

# 安装证书（替换 your-domain.com 为你的域名）
~/.acme.sh/acme.sh --install-cert -d your-domain.com \
  --key-file /etc/nginx/ssl/your-domain.key \
  --fullchain-file /etc/nginx/ssl/your-domain.crt \
  --reloadcmd "systemctl reload nginx"
```

### 13.4 更新 Nginx 配置支持 HTTPS

编辑 Nginx 站点配置：

```bash
sudo nano /etc/nginx/sites-available/document-web
```

在现有 `server` 块之外，添加以下 HTTPS 配置（完整替换方案见下方）：

```nginx
# ==================================================================
# HTTP → HTTPS 重定向
# ==================================================================
server {
    listen 80;
    server_name your-domain.com;

    # acme.sh 验证路径（续签需要）
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # 其他所有请求重定向到 HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

# ==================================================================
# HTTPS 站点（主要配置）
# ==================================================================
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书
    ssl_certificate /etc/nginx/ssl/your-domain.crt;
    ssl_certificate_key /etc/nginx/ssl/your-domain.key;

    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS (可选，强制 HTTPS)
    add_header Strict-Transport-Security "max-age=63072000" always;

    # 日志
    access_log /var/log/nginx/document-web-access.log;
    error_log /var/log/nginx/document-web-error.log;

    # 上传文件大小限制
    client_max_body_size 100m;

    # 前端静态文件
    location / {
        root /opt/document_web/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # 上传文件服务
    location /uploads/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

验证并重载：

```bash
# 测试配置语法
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

### 13.5 设置证书自动续签

acme.sh 安装证书时会自动添加续签 cron 任务。验证一下：

```bash
# 查看 acme.sh 安装的 cron 任务
crontab -l | grep acme.sh
# 应输出类似: 0 0 * * * "/home/user/.acme.sh"/acme.sh --cron --home "/home/user/.acme.sh" > /dev/null
```

证书将在到期前自动续签，无需手动操作。

---

## 14. 常见问题排查

### 14.1 后端无法启动

```bash
# 查看 systemd 服务日志
sudo journalctl -u document-web -f

# 查看最近的错误
sudo journalctl -u document-web -n 50 --no-pager
```

**可能原因**:

1. **`.env` 文件权限不对**: systemd 服务以 `www-data` 用户运行，但 `.env` 文件权限为 600 且属于 root 用户。
   ```bash
   sudo chown www-data:www-data /opt/document_web/backend/.env
   sudo chmod 600 /opt/document_web/backend/.env
   ```

2. **Python 虚拟环境损坏**: 重新创建虚拟环境并安装依赖。
   ```bash
   cd /opt/document_web/backend
   rm -rf .venv
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

3. **端口被占用**: 检查 8000 端口是否已被占用。
   ```bash
   sudo ss -tlnp | grep 8000
   ```

4. **依赖缺失**: `systemd` 无法找到 Python 模块。
   ```bash
   # 手动启动测试
   cd /opt/document_web/backend
   sudo -u www-data .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
   # 观察控制台输出的错误信息
   ```

### 14.2 前端页面 404

```bash
# 确认 dist 目录存在且有 index.html
ls -la /opt/document_web/frontend/dist/
```

**可能原因**:

1. **前端未构建**: 重新执行构建步骤。
   ```bash
   cd /opt/document_web/frontend
   npm install && npm run build
   ```

2. **Nginx root 路径不对**: 检查 Nginx 配置中 `root` 是否指向正确的 `dist/` 目录。

3. **文件权限问题**: Nginx 的 worker 进程（通常是 `www-data` 用户）无法读取文件。
   ```bash
   sudo chmod -R 755 /opt/document_web/frontend/dist
   ```

### 14.3 API 返回 503 "系统尚未初始化"

这是正常的错误提示。系统首次部署后，需要访问 `/setup` 完成初始化。如果初始化后仍然出现此错误：

```bash
# 检查初始化状态
curl http://localhost/api/v1/setup/status
```

如果返回 `{"initialized":false}`，重新运行初始化向导。

### 14.4 数据库连接失败

```bash
# 查看具体错误
sudo journalctl -u document-web -n 20 | grep -i "database\|connection\|postgres"
```

**检查清单**:

1. PostgreSQL 是否在运行：`sudo systemctl status postgresql`
2. `.env` 中的 `DATABASE_URL` 格式是否正确
3. 数据库用户和密码是否正确：`psql -h localhost -U document_web -d document_web -c "SELECT 1;"`
4. PostgreSQL 认证方式是否允许密码登录（检查 `pg_hba.conf`）

```sql
-- 在 PostgreSQL 中检查用户是否存在
sudo -u postgres psql -c "\du"
```

### 14.5 Redis 连接失败

```bash
# 检查 Redis 运行状态
sudo systemctl status redis-server

# 测试连接
redis-cli ping
```

如果 Redis 未运行：

```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 14.6 文件上传失败

1. 检查 `uploads/` 目录权限：
   ```bash
   sudo chown -R www-data:www-data /opt/document_web/backend/uploads
   sudo chmod 755 /opt/document_web/backend/uploads
   ```

2. 检查 Nginx `client_max_body_size` 和 `.env` 中的 `MAX_UPLOAD_SIZE`（默认 100MB）。

3. 如果通过 Nginx 上传超时，增加超时设置：
   ```nginx
   proxy_read_timeout 300s;
   proxy_send_timeout 300s;
   ```

### 14.7 密码登录失败 / JWT 令牌验证失败

1. 确保 `SECRET_KEY` 在部署期间未被修改（如果修改了，所有已签发的令牌都会失效）。

2. 检查 `ACCESS_TOKEN_EXPIRE_MINUTES` 设置（默认 30 分钟，登录后 30 分钟内无操作需要重新登录）。

### 14.8 性能问题

- **增加 uvicorn worker 数**: 编辑 systemd 服务文件，在 `ExecStart` 后添加 `--workers 4`（建议 worker 数 = CPU 核数），然后 `sudo systemctl daemon-reload && sudo systemctl restart document-web`。
- **开启 PostgreSQL 查询日志**: 在 `postgresql.conf` 中设置 `log_min_duration_statement = 1000` 记录慢查询。

### 14.9 常规诊断命令速查

```bash
# 后端日志
sudo journalctl -u document-web -f

# Nginx 访问日志
sudo tail -f /var/log/nginx/document-web-access.log

# Nginx 错误日志
sudo tail -f /var/log/nginx/document-web-error.log

# PostgreSQL 日志
sudo journalctl -u postgresql -f

# Redis 日志
sudo journalctl -u redis-server -f

# 磁盘空间
df -h

# 内存使用
free -h

# 进程列表
sudo systemctl list-units --type=service | grep -E "document-web|nginx|postgres|redis"
```


---

## 15. 更新部署

当有新代码推送到 GitHub 仓库后，在服务器上执行以下命令拉取更新并重启服务：

```bash
# 拉取最新代码
cd /opt/document_web
git pull

# 如有数据库迁移，执行迁移
cd backend
source ../.venv/bin/activate
alembic upgrade head

# 如有前端变更，重新构建
cd ../frontend
npm install
npm run build

# 重启后端服务
sudo systemctl restart document-web

# 重载 Nginx（前端静态文件变更时需要）
sudo systemctl reload nginx
```

> **提示**: 如果只是后端代码变更（不涉及数据库迁移和前端），只需执行 `git pull` + `sudo systemctl restart document-web` 即可。

### 15.1 查看服务状态

```bash
# 确认服务正常运行
sudo systemctl status document-web

# 查看最新日志确认无报错
sudo journalctl -u document-web -n 20 --no-pager
```

---

> **本文档是纯手动部署指南。** 项目当前不包含 Docker 或 Docker Compose 支持。如需容器化部署，请参考官方 Docker 文档自行编写 Dockerfile。
>
> **遇到问题？** 查看后端日志（`journalctl -u document-web -f`）和 Nginx 错误日志（`tail -f /var/log/nginx/document-web-error.log`）通常能定位 90% 的问题。
