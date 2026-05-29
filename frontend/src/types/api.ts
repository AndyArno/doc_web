/**
 * API 类型定义
 *
 * 包含所有 API 请求和响应的 TypeScript 类型定义
 */

// ==================== 通用类型 ====================

/**
 * 分页查询参数
 */
export interface PaginationParams {
  page?: number
  page_size?: number
}

/**
 * 分页响应
 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// ==================== 用户角色 ====================

/**
 * 用户角色枚举
 */
export type Role = 'super_admin' | 'admin' | 'editor' | 'user'

/**
 * 章节节点类型
 */
export type NodeType = 'folder' | 'article'

// ==================== 用户相关类型 ====================

/**
 * 用户信息
 */
export interface User {
  id: number
  username: string
  email: string
  role: Role
  is_active: boolean
  must_change_password?: boolean
  created_at: string
  updated_at: string
}

/**
 * 用户详情（含权限列表）
 */
export interface UserDetail extends User {
  permissions: Permission[]
}

/**
 * 用户列表响应
 */
export type UserListResponse = PaginatedResponse<User>

/**
 * 登录请求参数
 */
export interface LoginParams {
  account: string
  password: string
}

/**
 * 注册请求参数
 */
export interface RegisterParams {
  username: string
  email: string
  password: string
}

/**
 * 登录响应
 */
export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

/**
 * 修改密码请求参数
 */
export interface ChangePasswordParams {
  old_password: string
  new_password: string
}

/**
 * 忘记密码请求参数
 */
export interface ForgotPasswordParams {
  account: string
  old_password: string
  new_password: string
}

/**
 * 创建用户请求参数（管理员）
 */
export interface CreateUserParams {
  username: string
  email: string
  password: string
  role: Role
}

/**
 * 更新用户请求参数
 */
export interface UpdateUserParams {
  username?: string
  email?: string
  is_active?: boolean
}

/**
 * 用户查询参数
 */
export interface UserQueryParams extends PaginationParams {
  role?: Role
  keyword?: string
  is_active?: boolean
}

// ==================== 权限相关类型 ====================

/**
 * 权限信息
 */
export interface Permission {
  id: number
  user_id: number
  textbook_id: number
  can_access: boolean
  created_at: string
  updated_at: string
}

/**
 * 分配权限请求参数
 */
export interface AssignPermissionParams {
  textbook_id: number
  can_access?: boolean
}

/**
 * 权限历史记录
 */
export interface PermissionHistoryItem {
  id: number
  action: string
  target_user_id: number
  operator_id: number
  details: {
    textbook_id?: number
    textbook_title?: string
    old_permissions?: Record<string, boolean>
    new_permissions?: Record<string, boolean>
  }
  created_at: string
  operator?: {
    id: number
    username: string
  }
}

/**
 * 权限历史响应
 */
export interface PermissionHistoryResponse {
  items: PermissionHistoryItem[]
  total: number
}

// ==================== 教材相关类型 ====================

/**
 * 教材状态枚举
 */
export type TextbookStatus = 'draft' | 'published'

/**
 * 教材信息
 */
export interface Textbook {
  id: number
  title: string
  description: string | null
  cover_image: string | null
  slug: string
  status: TextbookStatus
  created_at: string
  updated_at: string
}

/**
 * 教材列表响应
 */
export type TextbookListResponse = PaginatedResponse<Textbook>

/**
 * 创建教材请求参数
 */
export interface CreateTextbookParams {
  title: string
  description?: string
  cover_image?: string
}

/**
 * 更新教材请求参数
 */
export interface UpdateTextbookParams {
  title?: string
  description?: string
  cover_image?: string
}

/**
 * 教材查询参数
 */
export interface TextbookQueryParams extends PaginationParams {
  keyword?: string
  status?: TextbookStatus
  for_management?: boolean
}

// ==================== 章节相关类型 ====================

/**
 * 章节树节点
 */
export interface ChapterTreeNode {
  id: number
  title: string
  level: number
  order_index: number
  node_type: NodeType
  has_content: boolean
  parent_id: number | null
  children: ChapterTreeNode[]
}

/**
 * 章节树响应
 */
export interface ChapterTreeResponse {
  textbook_id: number
  textbook_title: string
  chapters: ChapterTreeNode[]
}

/**
 * 章节导航
 */
export interface ChapterNavigation {
  prev: { id: number; title: string } | null
  next: { id: number; title: string } | null
}

/**
 * 章节信息
 */
export interface Chapter {
  id: number
  textbook_id: number
  parent_id: number | null
  title: string
  slug: string
  level: number
  order_index: number
  node_type: NodeType
  content: string | null
  created_at: string
  updated_at: string
  navigation?: ChapterNavigation
}

/**
 * 创建章节请求参数
 */
export interface CreateChapterParams {
  textbook_id: number
  parent_id?: number | null
  title: string
  node_type?: NodeType
  content?: string
  order_index?: number
}

/**
 * 更新章节请求参数
 */
export interface UpdateChapterParams {
  title?: string
  content?: string
  parent_id?: number | null
}

/**
 * 章节排序项
 */
export interface ChapterReorderItem {
  id: number
  order_index: number
  parent_id?: number | null
}

/**
 * 排序项
 */
export interface OrderItem {
  id: number | string
  type: 'folder' | 'article'
  folder_number?: number
  order_index: number
  parent_id?: number | string | null
  is_new?: boolean
}

/**
 * 智能排序预览节点
 */
export interface SortPreviewNode {
  id: number | string
  title: string
  node_type: string
  level: number
  order_index: number
  parent_id: number | string | null
  folder_number?: number
  is_new?: boolean
  can_delete?: boolean
  children: SortPreviewNode[]
}

/**
 * 智能排序预览响应
 */
export interface SortPreviewResponse {
  preview_tree: SortPreviewNode[]
  changes_count: number
  folders_created: string[]
  orders: OrderItem[]
}

/**
 * 智能排序顺序项
 */
export interface SortOrderItem {
  id: number | string
  order_index: number
  parent_id: number | string | null
}

/**
 * 智能排序应用响应
 */
export interface SortApplyResponse {
  success: boolean
  changes_count: number
  folders_created: number[]
}

/**
 * 智能排序应用请求
 */
export interface SortApplyRequest {
  textbook_id: number
  selected_ids?: number[]
  orders?: OrderItem[]
  deleted_ids?: number[]
  deleted_folder_numbers?: number[]
}

/**
 * 用户角色更新响应
 */
export interface UpdateUserRoleResponse {
  id: number
  username: string
  old_role: string
  new_role: string
}

/**
 * 清空回收站响应
 */
export interface ClearTrashResponse {
  deleted_count: number
}

// ==================== 媒体相关类型 ====================

/**
 * 媒体信息
 */
export interface Media {
  id: number
  textbook_id: number | null
  textbook_title?: string | null
  chapter_id: number | null
  filename: string
  original_name: string
  file_path: string
  file_size: number
  file_size_mb: number
  url: string
  file_type: string
  is_deleted: boolean
  deleted_at: string | null
  created_at: string
  updated_at: string
}

/**
 * 媒体列表响应
 */
export type MediaListResponse = PaginatedResponse<Media>

/**
 * 回收站列表响应
 */
export interface TrashListResponse {
  items: Media[]
  total: number
  total_size_mb: number
}

/**
 * 媒体查询参数
 */
export interface MediaQueryParams extends PaginationParams {
  textbook_id?: number
  chapter_id?: number
  file_type?: string
}

// ==================== 上传相关类型 ====================

/**
 * 上传响应
 */
export interface UploadResponse {
  id: number
  filename: string
  original_name: string
  file_path: string
  file_size: number
  file_type: string
  url: string
  warning?: string
}

/**
 * Markdown ZIP 上传响应
 */
export interface MarkdownUploadResponse {
  textbook_id: number
  title: string
  chapters_count: number
  task_id?: string
  message: string
  sort_preview?: SortPreviewResponse
}

/**
 * 上传任务状态
 */
export interface UploadStatus {
  task_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  message?: string
  result?: MarkdownUploadResponse
}

/**
 * 异步任务状态（用于服务端轮询）
 */
export interface TaskStatus {
  task_id: string
  status: 'processing' | 'done' | 'failed'
  stage: string
  progress: number
  result: MarkdownUploadResponse | null
  error: string | null
}

/**
 * 上传进度回调函数类型
 */
export type UploadProgressCallback = (percent: number, loaded: number, total: number) => void

// ==================== 搜索相关类型 ====================

/**
 * 搜索结果项
 */
export interface SearchResultItem {
  /** 文档ID（章节ID） */
  doc_id: number
  /** 文档类型 */
  doc_type: string
  /** 章节标题 */
  title: string
  /** 教材ID */
  textbook_id: number
  /** 教材标题 */
  textbook_title: string
  /** 相关度排名 */
  rank: number
}

/**
 * 搜索响应数据
 */
export interface SearchResponseData {
  /** 原始查询字符串 */
  query: string
  /** 搜索结果列表 */
  results: SearchResultItem[]
  /** 总结果数 */
  total: number
  /** 当前页码 */
  page: number
  /** 每页数量 */
  page_size: number
  /** 总页数 */
  total_pages: number
}

/**
 * 搜索查询参数
 */
export interface SearchQueryParams {
  /** 搜索关键词 */
  q: string
  /** 页码 */
  page?: number
  /** 每页数量 */
  page_size?: number
  /** 限定教材ID */
  textbook_id?: number
}

// ==================== 版本相关类型 ====================

/**
 * 版本信息
 */
export interface Version {
  id: number
  chapter_id: number
  content: string | null
  version_num: number
  created_by: number | null
  created_at: string
  updated_at: string
}

/**
 * 版本列表响应
 */
export interface VersionListResponse {
  chapter_id: number
  total: number
  versions: Version[]
}

/**
 * 版本查询参数
 */
export interface VersionQueryParams extends PaginationParams {}

/**
 * 版本差异行
 */
export interface VersionDiffLine {
  type: 'added' | 'removed' | 'unchanged'
  content: string
  old_line_num: number | null
  new_line_num: number | null
}

/**
 * 版本差异统计
 */
export interface VersionDiffSummary {
  added: number
  removed: number
  changed: number
}

/**
 * 版本对比响应
 */
export interface VersionDiffResponse {
  from_version: Version
  to_version: Version
  diff: VersionDiffLine[]
  summary: VersionDiffSummary
}
