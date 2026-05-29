import apiClient from './index'
import type {
  LoginParams,
  LoginResponse,
  RegisterParams,
  User,
  ChangePasswordParams,
  ForgotPasswordParams
} from '@/types/api'

/**
 * 用户登录
 */
export function login(data: LoginParams): Promise<LoginResponse> {
  return apiClient.post('/auth/login', data)
}

/**
 * 用户注册
 */
export function register(data: RegisterParams): Promise<User> {
  return apiClient.post('/auth/register', data)
}

/**
 * 用户登出
 */
export function logout(): Promise<void> {
  return apiClient.post('/auth/logout')
}

/**
 * 获取当前用户信息
 */
export function getCurrentUser(): Promise<User> {
  return apiClient.get('/auth/me')
}

/**
 * 修改密码
 */
export function changePassword(data: ChangePasswordParams): Promise<void> {
  return apiClient.put('/auth/me/password', data)
}

/**
 * 忘记密码
 */
export function forgotPassword(data: ForgotPasswordParams): Promise<void> {
  return apiClient.post('/auth/forgot-password', data)
}
