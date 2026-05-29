<script setup lang="ts">
/**
 * LoadingSpinner - 加载动画组件
 *
 * 显示加载状态的旋转动画，支持三种尺寸和可选文字。
 * 使用 CSS 动画实现旋转效果，不依赖外部动画库。
 *
 * @example
 * ```vue
 * <LoadingSpinner size="md" text="加载中..." />
 * ```
 */
import { computed } from 'vue'
import { Loader2 } from 'lucide-vue-next'

/** 组件 Props 类型定义 */
interface Props {
  /** 尺寸：sm(小) | md(中) | lg(大)，默认 md */
  size?: 'sm' | 'md' | 'lg'
  /** 加载文字，显示在图标下方 */
  text?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  text: ''
})

/** 根据尺寸计算图标大小 */
const iconSize = computed(() => {
  const sizes = {
    sm: 16,
    md: 24,
    lg: 32
  }
  return sizes[props.size]
})

/** 根据尺寸计算文字大小 */
const textSizeClass = computed(() => {
  const classes = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base'
  }
  return classes[props.size]
})
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-2">
    <!-- 旋转动画图标 -->
    <Loader2
      :size="iconSize"
      class="animate-spin text-blue-500"
    />
    <!-- 加载文字 -->
    <span
      v-if="text"
      :class="textSizeClass"
      class="text-gray-500"
    >
      {{ text }}
    </span>
  </div>
</template>
