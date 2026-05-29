# AGENTS.md — Frontend API Layer

**Generated:** 2026-04-19  
**Parent:** `/AGENTS.md`

## OVERVIEW

Axios 请求封装层。所有 API 调用通过此层，返回解包后的数据（`data.data`），非 AxiosResponse。

## STRUCTURE

```
api/
├── index.ts         # Axios 实例、拦截器、响应解包
├── auth.ts          # 认证：login, register, password
├── user.ts          # 用户 CRUD
├── textbook.ts      # 教材 CRUD、发布
├── chapter.ts       # 章节树操作
├── media.ts         # 媒体管理
├── version.ts       # 版本历史
├── search.ts        # 全文搜索
└── upload.ts        # 文件上传
```

## WHERE TO LOOK

| 任务 | 文件 | 函数 |
|------|------|------|
| 登录/注册 | `auth.ts` | `login()`, `register()` |
| 用户管理 | `user.ts` | `getUsers()`, `createUser()` |
| 教材管理 | `textbook.ts` | `getTextbooks()`, `updateTextbook()` |
| 章节树 | `chapter.ts` | `getChapterTree()`, `reorderChapters()` |
| 文件上传 | `upload.ts` | `uploadImage()`, `uploadMarkdownZip()` |

## CONVENTIONS

### 函数命名
```typescript
// CRUD 命名
export async function getXxx(id: number): Promise<Xxx>
export async function getXxxList(params?): Promise<XxxListResponse>
export async function createXxx(data: XxxCreate): Promise<Xxx>
export async function updateXxx(id: number, data: XxxUpdate): Promise<Xxx>
export async function deleteXxx(id: number): Promise<void>
```

### 返回值（解包）
```typescript
// index.ts 拦截器
response => {
  const data = response.data
  if (data.code !== 200) {
    Toast.error(data.message)  // 自动显示错误 Toast
    return Promise.reject(data)
  }
  return data.data  // 返回解包后的数据
}

// API 函数
export async function getUser(id: number): Promise<User> {
  return request.get(`/users/${id}`)  // 直接返回 User，非 AxiosResponse
}
```

### 分页响应
```typescript
interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// 使用
const { items, total } = await getUsers({ page: 1, page_size: 20 })
```

### 文件上传
```typescript
export async function uploadImage(file: File): Promise<Media> {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/upload/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
```

## ANTI-PATTERNS

### 🚫 禁止
- 在 API 层处理业务逻辑
- 返回 AxiosResponse（返回 `data.data`）
- 硬编码 URL（使用 `BASE_URL` 配置）
- 捕获异常后静默处理（让拦截器处理）

### ⚠️ 注意
- 业务错误已由拦截器显示 Toast，调用方无需再处理
- 401 错误自动跳转登录页

## UNIQUE STYLES

### 自动 Token 注入
```typescript
// index.ts 请求拦截器
request.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

### 自动错误处理
```typescript
// index.ts 响应拦截器
// 业务错误（code !== 200）→ Toast.error → reject
// 401 未认证 → 清除 token → 跳转登录页
// 网络错误 → Toast.error
```

### 类型安全
```typescript
// types/api.ts 定义所有类型
// API 函数使用这些类型作为参数和返回值
export async function updateUser(id: number, data: UserUpdate): Promise<User> {
  return request.put(`/users/${id}`, data)
}
```

### 进度回调（上传）
```typescript
export async function uploadMarkdownZip(
  file: File,
  textbookId: number,
  onProgress?: (percent: number) => void
): Promise<Chapter[]> {
  return request.post('/upload/markdown', formData, {
    onUploadProgress: (e) => {
      if (e.total && onProgress) {
        onProgress(Math.round((e.loaded * 100) / e.total))
      }
    }
  })
}
```
