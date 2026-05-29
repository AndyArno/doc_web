/**
 * Axios 实例配置
 *
 * 提供统一的 API 请求封装，包括：
 * - 自动添加 Authorization header
 * - 统一响应处理
 * - 错误处理和 Toast 提示
 */
import axios, {
  type AxiosInstance,
  type InternalAxiosRequestConfig,
  type AxiosResponse,
  type AxiosError
} from 'axios'
import { Toast } from '@/composables/useToast'
import router from '@/router'
import { useUserStore } from '@/stores/user'

/**
 * API 响应数据结构
 */
interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

/**
 * Axios 实例
 */
const configuredBaseURL = import.meta.env.VITE_API_BASE_URL?.trim()
const apiBaseURL =
  configuredBaseURL && !configuredBaseURL.includes(':8001/api/v1')
    ? configuredBaseURL
    : 'http://localhost:8000/api/v1'

const apiClient: AxiosInstance = axios.create({
  baseURL: apiBaseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

/**
 * 请求拦截器
 * 自动添加 Authorization header 和 X-Device-Id header
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    let deviceId = localStorage.getItem('x-device-id')
    if (!deviceId) {
      deviceId = typeof crypto !== 'undefined' && crypto.randomUUID
        ? crypto.randomUUID()
        : `${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 11)}`
      localStorage.setItem('x-device-id', deviceId)
    }
    config.headers['X-Device-Id'] = deviceId

    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

/**
 * 处理 401 未授权错误
 * 清除用户状态并跳转到登录页
 */
function handleUnauthorized(): void {
  const userStore = useUserStore()
  userStore.logout()
  Toast.error('登录已过期，请重新登录')
  router.push('/login')
}

/**
 * 响应拦截器
 * 处理业务状态码和 HTTP 错误
 */
apiClient.interceptors.response.use(
  <T>(response: AxiosResponse<ApiResponse<T>>): T => {
    const { data } = response

    if (data.code === 401) {
      if (localStorage.getItem('access_token')) {
        handleUnauthorized()
      } else {
        Toast.error(data.message || '请登录后继续')
      }
      throw new Error(data.message)
    }

    if (data.code !== 200) {
      Toast.error(data.message || '请求失败')
      throw new Error(data.message)
    }

    return data.data
  },
  (error: AxiosError<ApiResponse>) => {
    const { response } = error

    if (!response) {
      // 🔍 诊断日志：记录无响应错误的完整上下文
      console.error('[API] 请求失败-无响应', {
        url: error.config?.url,
        method: error.config?.method,
        baseURL: error.config?.baseURL,
        fullURL: `${error.config?.baseURL || ''}${error.config?.url || ''}`,
        message: error.message,
        code: error.code,
        name: error.name,
        requestReadyState: (error.request as XMLHttpRequest)?.readyState,
        requestStatus: (error.request as XMLHttpRequest)?.status,
        requestStatusText: (error.request as XMLHttpRequest)?.statusText,
        requestResponseURL: (error.request as XMLHttpRequest)?.responseURL,
        online: navigator.onLine,
        timeout: error.config?.timeout,
        headers: error.config?.headers,
      })
      if (error.message === 'Network Error') {
        Toast.error('网络连接失败，请检查网络')
      } else if (error.code === 'ECONNABORTED') {
        Toast.error('请求超时，请重试')
      } else {
        Toast.error('网络异常，请稍后重试')
      }
      return Promise.reject(error)
    }

    const { status, data } = response

    switch (status) {
      case 400:
        Toast.error(data?.message || '请求参数错误')
        break

      case 401:
        // 只有已登录用户才跳转登录页（游客静默处理）
        if (localStorage.getItem('access_token')) {
          handleUnauthorized()
        } else {
          Toast.error(data?.message || '请登录后继续')
        }
        break

      case 403:
        Toast.error('您没有权限执行此操作')
        break

      case 404:
        Toast.error('请求的资源不存在')
        break

      case 409:
        Toast.error(data?.message || '资源已存在')
        break

      case 422: {
        type ValidationErrorData = { errors?: Record<string, string[]> }
        const errorData = data?.data as ValidationErrorData | undefined
        const errors = errorData?.errors
        const messages = errors ? Object.values(errors).flat() : []
        Toast.error(messages[0] || '数据验证失败')
        break
      }

      case 500:
        Toast.error('服务器错误，请稍后重试')
        break

      default:
        Toast.error(data?.message || '请求失败')
    }

    return Promise.reject(error)
  }
)

export default apiClient
