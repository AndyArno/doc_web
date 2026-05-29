import apiClient from './index'
import type {
  User,
  UserDetail,
  UserListResponse,
  UserQueryParams,
  CreateUserParams,
  UpdateUserParams,
  Role,
  AssignPermissionParams,
  UpdateUserRoleResponse,
  PermissionHistoryResponse
} from '@/types/api'

/**
 * 获取用户列表
 */
export function getUsers(params: UserQueryParams = {}): Promise<UserListResponse> {
  const filteredParams = Object.fromEntries(
    Object.entries(params).filter(([_, v]) => v !== '' && v !== null && v !== undefined)
  )
  return apiClient.get('/users', { params: filteredParams })
}

/**
 * 获取用户详情
 */
export function getUserById(id: number): Promise<UserDetail> {
  return apiClient.get(`/users/${id}`)
}

/**
 * 创建用户（管理员）
 */
export function createUser(data: CreateUserParams): Promise<User> {
  return apiClient.post('/users', data)
}

/**
 * 更新用户信息
 */
export function updateUser(id: number, data: UpdateUserParams): Promise<User> {
  return apiClient.put(`/users/${id}`, data)
}

/**
 * 修改用户角色
 */
export function updateUserRole(id: number, role: Role): Promise<UpdateUserRoleResponse> {
  return apiClient.put(`/users/${id}/role`, { role })
}

/**
 * 删除用户
 */
export function deleteUser(id: number): Promise<void> {
  return apiClient.delete(`/users/${id}`)
}

export interface ResetPasswordResponse {
  password: string
  must_change_password: boolean
}

/**
 * 重置用户密码
 */
export function resetUserPassword(id: number): Promise<ResetPasswordResponse> {
  return apiClient.post(`/users/${id}/reset-password`)
}

/**
 * 分配用户教材权限
 */
export function assignUserPermissions(userId: number, permissions: AssignPermissionParams): Promise<void> {
  return apiClient.post(`/users/${userId}/permissions`, permissions)
}

/**
 * 撤销用户教材权限
 */
export function revokeUserPermission(userId: number, textbookId: number): Promise<void> {
  return apiClient.delete(`/users/${userId}/permissions/${textbookId}`)
}

/**
 * 获取用户权限变更历史
 */
export function getUserPermissionHistory(userId: number): Promise<PermissionHistoryResponse> {
  return apiClient.get(`/users/${userId}/permissions/history`)
}
