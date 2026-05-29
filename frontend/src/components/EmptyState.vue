<script setup lang="ts">
/**
 * EmptyState - 空状态组件
 *
 * 显示空数据状态的占位界面，包含图标、标题、描述和可选的操作按钮。
 * 适用于列表为空、搜索无结果等场景。
 *
 * @example
 * ```vue
 * <EmptyState
 *   icon="inbox"
 *   title="暂无数据"
 *   description="当前没有相关内容"
 * >
 *   <template #action>
 *     <button>添加数据</button>
 *   </template>
 * </EmptyState>
 * ```
 */
import { computed } from 'vue'
import {
  Inbox,
  FileX,
  SearchX,
  FolderX,
  Library,
  BookOpen,
  type LucideIcon
} from 'lucide-vue-next'

/** 组件 Props 类型定义 */
interface Props {
  /** 图标名称，默认 inbox */
  icon?: 'inbox' | 'file-x' | 'search-x' | 'folder-x' | 'library' | 'book-open'
  /** 标题，默认"暂无数据" */
  title?: string
  /** 描述文字 */
  description?: string
}

const props = withDefaults(defineProps<Props>(), {
  icon: 'inbox',
  title: '暂无数据',
  description: ''
})

/** 图标映射表 */
const iconMap: Record<string, LucideIcon> = {
  'inbox': Inbox,
  'file-x': FileX,
  'search-x': SearchX,
  'folder-x': FolderX,
  'library': Library,
  'book-open': BookOpen
}

/** 当前显示的图标组件 */
const IconComponent = computed(() => iconMap[props.icon] || Inbox)
</script>

<template>
  <div class="flex flex-col items-center justify-center py-12 px-4">
    <!-- 图标 -->
    <div class="mb-4 text-gray-300">
      <component :is="IconComponent" :size="64" />
    </div>
    <!-- 标题 -->
    <h3 class="text-lg font-medium text-gray-600 mb-2">
      {{ title }}
    </h3>
    <!-- 描述 -->
    <p
      v-if="description"
      class="text-sm text-gray-400 mb-4 text-center max-w-sm"
    >
      {{ description }}
    </p>
    <!-- 操作按钮插槽 -->
    <div v-if="$slots.action" class="mt-2">
      <slot name="action" />
    </div>
  </div>
</template>
