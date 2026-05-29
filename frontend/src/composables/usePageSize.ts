/**
 * 页面大小选择器 Composable
 * 
 * 管理媒体库每页显示数量的 localStorage 持久化。
 * 
 * @example
 * import { usePageSize, PAGE_SIZE_OPTIONS } from '@/composables/usePageSize'
 * 
 * const { pageSize, setPageSize, pageSizeOptions } = usePageSize()
 * // pageSize.value = 10 (默认值)
 * setPageSize(20)
 * // localStorage 已更新
 */
import { ref, watch } from 'vue'

/** 可选的每页显示数量 */
export const PAGE_SIZE_OPTIONS = [10, 20, 30, 50, 100] as const

/** 每页显示数量类型 */
export type PageSizeOption = typeof PAGE_SIZE_OPTIONS[number]

/** localStorage 存储键名 */
const STORAGE_KEY = 'media-library-page-size'

/** 默认每页显示数量 */
const DEFAULT_PAGE_SIZE: PageSizeOption = 10

/**
 * 页面大小管理 Hook
 * 
 * 从 localStorage 读取已保存的每页显示数量，如果没有则使用默认值 10。
 * 设置新值时会自动持久化到 localStorage。
 * 
 * @returns 页面大小相关的响应式对象
 */
export function usePageSize() {
  // 从 localStorage 读取初始值
  const storedValue = localStorage.getItem(STORAGE_KEY)
  const initialSize = storedValue ? parseInt(storedValue, 10) : DEFAULT_PAGE_SIZE
  
  // 验证初始值是否有效，无效则使用默认值
  const isValidOption = PAGE_SIZE_OPTIONS.includes(initialSize as PageSizeOption)
  const pageSize = ref<PageSizeOption>(
    isValidOption ? (initialSize as PageSizeOption) : DEFAULT_PAGE_SIZE
  )

  /**
   * 设置新的每页显示数量
   * 
   * @param size - 新的每页显示数量，必须是 PAGE_SIZE_OPTIONS 中的一项
   */
  function setPageSize(size: PageSizeOption) {
    pageSize.value = size
    localStorage.setItem(STORAGE_KEY, String(size))
  }

  return {
    /** 当前每页显示数量 */
    pageSize,
    /** 设置新的每页显示数量 */
    setPageSize,
    /** 可选的每页显示数量列表 */
    pageSizeOptions: PAGE_SIZE_OPTIONS
  }
}
