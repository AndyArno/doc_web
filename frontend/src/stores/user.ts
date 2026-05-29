/**
 * 用户状态管理
 * 管理用户登录状态、Token 和用户信息
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getCurrentUser } from '@/api/auth'

/**
 * 用户信息接口
 */
export interface UserInfo {
  id: number
  username: string
  email: string
  role: UserRole
  must_change_password?: boolean
  created_at?: string
  updated_at?: string
}

/**
 * 用户角色类型
 */
export type UserRole = 'super_admin' | 'admin' | 'editor' | 'user'

/**
 * 用户 Store 返回类型
 */
export interface UserStore {
  /** 用户 Token */
  token: Ref<string | null>
  /** 用户信息 */
  userInfo: Ref<UserInfo | null>
  /** 是否已登录 */
  isLoggedIn: Readonly<Ref<boolean>>
  /** 用户角色 */
  role: Readonly<Ref<UserRole>>
  /** 是否为超级管理员 */
  isSuperAdmin: Readonly<Ref<boolean>>
  /** 是否正在加载用户信息 */
  isLoadingUserInfo: Ref<boolean>
  /** 设置 Token */
  setToken: (newToken: string) => void
  /** 设置用户信息 */
  setUserInfo: (info: UserInfo | null) => void
  /** 登出 */
  logout: () => void
  /** 获取用户信息 */
  getUserInfo: () => Promise<UserInfo | null>
}

import type { Ref } from 'vue'

export const useUserStore = defineStore('user', (): UserStore => {
  /** 用户 Token */
  const token = ref<string | null>(localStorage.getItem('access_token'))

  /** 用户信息 */
  const userInfo = ref<UserInfo | null>(getUserInfoFromStorage())

  /** 是否已登录 */
  const isLoggedIn = computed(() => !!token.value)

  /** 用户角色 */
  const role = computed<UserRole>(() => userInfo.value?.role || 'user')

  /** 是否为超级管理员 */
  const isSuperAdmin = computed(() => userInfo.value?.role === 'super_admin')

  /** 是否正在加载用户信息（防止并发调用） */
  const isLoadingUserInfo = ref(false)

  /**
   * 从 localStorage 解析用户信息
   * @returns 用户信息或 null
   */
  function getUserInfoFromStorage(): UserInfo | null {
    try {
      const stored = localStorage.getItem('user')
      return stored ? JSON.parse(stored) as UserInfo : null
    } catch {
      return null
    }
  }

  /**
   * 设置 Token
   * @param newToken - 新 Token
   */
  function setToken(newToken: string): void {
    token.value = newToken
    localStorage.setItem('access_token', newToken)
  }

  /**
   * 设置用户信息
   * @param info - 用户信息对象
   */
  function setUserInfo(info: UserInfo | null): void {
    userInfo.value = info
    if (info) {
      localStorage.setItem('user', JSON.stringify(info))
    } else {
      localStorage.removeItem('user')
    }
  }

  /**
   * 登出，清除用户状态
   */
  function logout(): void {
    token.value = null
    userInfo.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
  }

  /**
   * 从服务器获取当前用户信息
   * @returns 用户信息或 null
   */
  async function getUserInfo(): Promise<UserInfo | null> {
    if (!token.value) {
      return null
    }
    // 防止并发调用
    if (isLoadingUserInfo.value) {
      return null
    }
    isLoadingUserInfo.value = true
    try {
      const data = await getCurrentUser() as UserInfo
      setUserInfo(data)
      return data
    } catch {
      // Token 无效或请求失败，清除状态
      logout()
      return null
    } finally {
      isLoadingUserInfo.value = false
    }
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    role,
    isSuperAdmin,
    isLoadingUserInfo,
    setToken,
    setUserInfo,
    logout,
    getUserInfo,
  }
})
