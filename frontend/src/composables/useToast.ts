/**
 * Toast 消息提示 Composable
 * 
 * 提供全局 Toast 消息提示功能，支持 success/error/warning/info 四种类型。
 * 
 * @example
 * import { useToast } from '@/composables/useToast'
 * 
 * const toast = useToast()
 * toast.success('操作成功')
 * toast.error('操作失败')
 */
import { createApp, type App } from 'vue'
import ToastComponent from '@/components/Toast.vue'

/** Toast 消息类型 */
type ToastType = 'success' | 'error' | 'warning' | 'info'

/** Toast 方法接口 */
interface ToastMethods {
  success: (msg: string, duration?: number) => void
  error: (msg: string, duration?: number) => void
  warning: (msg: string, duration?: number) => void
  info: (msg: string, duration?: number) => void
}

let toastInstance: ToastMethods | null = null

/**
 * 创建 Toast 实例
 * 
 * 使用 Vue 的 createApp 创建一个独立的 Toast 组件实例，
 * 并挂载到 body 上，确保 Toast 可以在任何地方使用。
 */
function createToastInstance(): ToastMethods {
  const app: App = createApp(ToastComponent)
  const mountPoint = document.createElement('div')
  mountPoint.id = 'toast-mount-point'
  document.body.appendChild(mountPoint)
  const vm = app.mount(mountPoint)
  return vm as unknown as ToastMethods
}

/**
 * 获取 Toast 实例
 * 
 * 单例模式，确保全局只有一个 Toast 实例。
 */
function getToastInstance(): ToastMethods {
  if (!toastInstance) {
    toastInstance = createToastInstance()
  }
  return toastInstance
}

/**
 * Toast 消息提示 Hook
 * 
 * @returns Toast 方法对象
 */
export function useToast(): ToastMethods {
  return getToastInstance()
}

// 导出单例实例，支持直接使用 Toast.success() 语法
export const Toast: ToastMethods = {
  success: (msg: string, duration?: number) => getToastInstance().success(msg, duration),
  error: (msg: string, duration?: number) => getToastInstance().error(msg, duration),
  warning: (msg: string, duration?: number) => getToastInstance().warning(msg, duration),
  info: (msg: string, duration?: number) => getToastInstance().info(msg, duration),
}

export default Toast
