<template>
  <div class="relative" ref="searchBoxRef">
    <!-- 搜索输入框 -->
    <div 
      class="relative flex items-center group"
      :class="[
        'rounded-xl border transition-all',
        isFocused 
          ? 'border-brand-500 ring-2 ring-brand-500/20 bg-white' 
          : 'border-gray-200 bg-gray-50/50 hover:border-gray-300 hover:bg-white'
      ]"
    >
      <!-- 搜索图标 -->
      <Search class="absolute left-3 w-4 h-4 text-gray-400 transition-colors" :class="{ 'text-brand-500': isFocused }" />
      
      <!-- 输入框 -->
      <input
        ref="inputRef"
        v-model="searchQuery"
        type="text"
        :placeholder="placeholder"
        class="w-full pl-10 pr-16 py-2.5 text-sm bg-transparent focus:outline-none text-gray-700 placeholder-gray-400"
        @focus="handleFocus"
        @blur="handleBlur"
        @input="handleInput"
        @keydown="handleKeydown"
      />
      
      <!-- 快捷键提示 -->
      <div 
        v-if="!searchQuery"
        class="absolute right-3 flex items-center gap-1 pointer-events-none"
      >
        <kbd class="hidden sm:inline-flex items-center px-2 py-0.5 text-xs font-medium text-gray-400 bg-gray-100 border border-gray-200 rounded">
          Ctrl
        </kbd>
        <kbd class="hidden sm:inline-flex items-center px-2 py-0.5 text-xs font-medium text-gray-400 bg-gray-100 border border-gray-200 rounded">
          K
        </kbd>
      </div>
      
      <!-- 清除按钮 -->
      <button
        v-else
        @click="clearSearch"
        class="absolute right-3 p-1 text-gray-400 hover:text-gray-600 transition-colors"
        type="button"
      >
        <X class="w-4 h-4" />
      </button>
    </div>
    
    <!-- 搜索建议下拉 -->
    <transition name="slide-down">
      <div 
        v-if="showSuggestions && (suggestions.length > 0 || isLoading)"
        class="absolute top-full left-0 right-0 mt-2 bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden z-50"
      >
        <!-- 加载状态 -->
        <div v-if="isLoading" class="px-4 py-8 text-center">
          <div class="inline-block w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin"></div>
          <span class="ml-2 text-sm text-gray-500">搜索中...</span>
        </div>
        
        <!-- 建议列表 -->
        <ul v-else class="max-h-80 overflow-y-auto">
          <li 
            v-for="(suggestion, index) in suggestions"
            :key="suggestion.id"
            @mousedown="selectSuggestion(suggestion)"
            class="px-4 py-3 cursor-pointer transition-colors flex items-start gap-3"
            :class="[
              index === activeIndex 
                ? 'bg-brand-50 text-brand-600' 
                : 'hover:bg-gray-50 text-gray-700'
            ]"
          >
            <FileText class="w-4 h-4 mt-0.5 text-gray-400 shrink-0" />
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium truncate" v-html="highlightMatch(suggestion.title, searchQuery)"></p>
              <p class="text-xs text-gray-400 truncate mt-0.5">
                {{ suggestion.textbookTitle }}
              </p>
            </div>
          </li>
        </ul>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
/**
 * SearchBox 搜索框组件
 * 
 * @description 提供全文搜索功能的输入框，支持搜索建议和快捷键
 * 
 * @property {string} [placeholder='搜索内容...'] - 占位文字
 * @property {boolean} [showSuggestions=true] - 是否显示搜索建议
 * @property {number} [debounceTime=300] - 防抖延迟时间(ms)
 * 
 * @emits search - 搜索事件，返回搜索关键词
 * @emits select - 选择建议事件，返回选中的建议项
 * 
 * @example
 * <SearchBox @search="handleSearch" @select="handleSelect" />
 */
import DOMPurify from 'dompurify'
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Search, X, FileText } from 'lucide-vue-next'
import { searchContent } from '@/api/search'

interface Props {
  placeholder?: string
  showSuggestions?: boolean
  debounceTime?: number
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '搜索内容...',
  showSuggestions: true,
  debounceTime: 300
})

const emit = defineEmits<{
  (e: 'search', query: string): void
  (e: 'select', suggestion: SearchSuggestion): void
}>()

interface SearchSuggestion {
  id: number
  title: string
  textbookId: number
  textbookTitle: string
  rank: number
}

// Refs
const searchBoxRef = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const searchQuery = ref('')
const isFocused = ref(false)
const isLoading = ref(false)
const suggestions = ref<SearchSuggestion[]>([])
const activeIndex = ref(-1)
const showSuggestions = computed(() => props.showSuggestions && isFocused.value && searchQuery.value.trim().length > 0)

// 防抖定时器
let debounceTimer: ReturnType<typeof setTimeout> | null = null

/**
 * 处理输入事件
 */
const handleInput = () => {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
  
  if (!searchQuery.value.trim()) {
    suggestions.value = []
    return
  }
  
  debounceTimer = setTimeout(() => {
    fetchSuggestions()
  }, props.debounceTime)
}

/**
 * 获取搜索建议
 */
const fetchSuggestions = async () => {
  const query = searchQuery.value.trim()
  if (!query) return
  
  isLoading.value = true
  
  try {
    const response = await searchContent({ q: query, page: 1, page_size: 5 })
    
    if (response.results) {
      suggestions.value = response.results.map(result => ({
        id: result.doc_id,
        title: result.title,
        textbookId: result.textbook_id,
        textbookTitle: result.textbook_title,
        rank: result.rank
      }))
    }
  } catch (error) {
    suggestions.value = []
  } finally {
    isLoading.value = false
  }
}

/**
 * 处理焦点事件
 */
const handleFocus = () => {
  isFocused.value = true
  activeIndex.value = -1
}

/**
 * 处理失焦事件
 */
const handleBlur = () => {
  isFocused.value = false
  activeIndex.value = -1
}

/**
 * 处理键盘事件
 */
const handleKeydown = (event: KeyboardEvent) => {
  // 回车键 - 搜索或选择
  if (event.key === 'Enter') {
    event.preventDefault()
    if (activeIndex.value >= 0 && suggestions.value[activeIndex.value]) {
      selectSuggestion(suggestions.value[activeIndex.value])
    } else if (searchQuery.value.trim()) {
      emit('search', searchQuery.value.trim())
      inputRef.value?.blur()
    }
  }
  
  // 上下箭头键 - 导航建议
  if (event.key === 'ArrowDown') {
    event.preventDefault()
    if (suggestions.value.length > 0) {
      activeIndex.value = Math.min(activeIndex.value + 1, suggestions.value.length - 1)
    }
  }
  
  if (event.key === 'ArrowUp') {
    event.preventDefault()
    activeIndex.value = Math.max(activeIndex.value - 1, -1)
  }
  
  // Escape键 - 关闭建议
  if (event.key === 'Escape') {
    inputRef.value?.blur()
  }
}

/**
 * 选择建议项
 */
const selectSuggestion = (suggestion: SearchSuggestion) => {
  emit('select', suggestion)
  searchQuery.value = suggestion.title
  suggestions.value = []
  inputRef.value?.blur()
}

/**
 * 清除搜索
 */
const clearSearch = () => {
  searchQuery.value = ''
  suggestions.value = []
  inputRef.value?.focus()
}

/**
 * 高亮匹配文本
 */
const highlightMatch = (text: string, query: string): string => {
  if (!query.trim()) return text
  
  const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi')
  return DOMPurify.sanitize(text.replace(regex, '<mark class="bg-brand-200 text-brand-700 px-0.5 rounded">$1</mark>'), { ALLOWED_TAGS: ['mark'] })
}

/**
 * 转义正则特殊字符
 */
const escapeRegExp = (string: string): string => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/**
 * 全局快捷键处理
 */
const handleGlobalKeydown = (event: KeyboardEvent) => {
  // Ctrl/Cmd + K - 聚焦搜索框
  if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
    event.preventDefault()
    inputRef.value?.focus()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleGlobalKeydown)
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
})
</script>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.2s ease-out;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* 自定义滚动条 */
ul::-webkit-scrollbar {
  width: 6px;
}

ul::-webkit-scrollbar-track {
  background: transparent;
}

ul::-webkit-scrollbar-thumb {
  background: #e5e7eb;
  border-radius: 10px;
}

ul::-webkit-scrollbar-thumb:hover {
  background: #d1d5db;
}
</style>
