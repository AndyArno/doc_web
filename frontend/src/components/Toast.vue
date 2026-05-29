/**
 * Toast 消息提示组件
 * 
 * 提供 success/error/warning/info 四种类型的消息提示。
 * 支持方法调用方式：Toast.success('msg')
 * 自动 3 秒消失，右上角定位，滑入/滑出动画。
 * 
 * @example
 * import { Toast } from '@/components/Toast'
 * Toast.success('操作成功')
 * Toast.error('操作失败')
 */
<template>
  <Teleport to="body">
    <Transition name="toast">
      <div
        v-if="visible"
        :class="toastClasses"
        role="alert"
        aria-live="polite"
      >
        <span class="flex-shrink-0">
          <component :is="currentIcon" class="h-5 w-5" />
        </span>
        <span class="flex-1 text-sm font-medium">{{ message }}</span>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, type Component } from 'vue'
import { CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-vue-next'

/** Toast 消息类型 */
type ToastType = 'success' | 'error' | 'warning' | 'info'

/** Toast 实例接口 */
interface ToastInstance {
  success: (msg: string, duration?: number) => void
  error: (msg: string, duration?: number) => void
  warning: (msg: string, duration?: number) => void
  info: (msg: string, duration?: number) => void
}

const visible = ref(false)
const message = ref('')
const type = ref<ToastType>('info')
let timer: ReturnType<typeof setTimeout> | null = null

/** 图标映射表 */
const iconMap: Record<ToastType, Component> = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
}

/** 当前显示的图标 */
const currentIcon = computed(() => iconMap[type.value])

/** 根据类型返回对应的样式类 */
const toastClasses = computed(() => {
  const baseClasses = [
    'fixed top-5 right-5 z-[9999]',
    'flex items-center gap-3',
    'px-5 py-4 rounded-xl',
    'shadow-lg',
    'min-w-[280px] max-w-md',
  ]

  const typeClasses: Record<ToastType, string[]> = {
    success: ['bg-green-500 text-white'],
    error: ['bg-red-500 text-white'],
    warning: ['bg-yellow-500 text-white'],
    info: ['bg-blue-500 text-white'],
  }

  return [...baseClasses, ...typeClasses[type.value]]
})

/**
 * 显示 Toast 消息
 * 
 * @param msg - 消息内容
 * @param toastType - 消息类型
 * @param duration - 显示时长（毫秒），默认 3000ms
 */
function show(msg: string, toastType: ToastType = 'info', duration = 3000): void {
  if (timer) {
    clearTimeout(timer)
    timer = null
  }

  message.value = msg
  type.value = toastType
  visible.value = true

  timer = setTimeout(() => {
    visible.value = false
    timer = null
  }, duration)
}

defineExpose<ToastInstance>({
  /** 显示成功消息（绿色） */
  success: (msg: string, duration?: number) => show(msg, 'success', duration),
  /** 显示错误消息（红色） */
  error: (msg: string, duration?: number) => show(msg, 'error', duration),
  /** 显示警告消息（黄色） */
  warning: (msg: string, duration?: number) => show(msg, 'warning', duration),
  /** 显示信息消息（蓝色） */
  info: (msg: string, duration?: number) => show(msg, 'info', duration),
})
</script>

<style scoped>
.toast-enter-active {
  transition: all 0.3s ease-out;
}

.toast-leave-active {
  transition: all 0.3s ease-in;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
