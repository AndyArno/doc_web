<template>
  <ReadingLayout
    :user="user"
    :books="books"
    :current-book="currentBook"
    :chapters="chapters"
    :active-chapter-id="activeChapterId"
    :headings="headings"
    @select-book="handleBookSelect"
    @select-chapter="handleChapterSelect"
    @logout="handleLogout"
  >
    <!-- 内容加载状态 -->
    <div v-if="loadingContent" class="py-20 flex flex-col items-center justify-center space-y-4">
      <LoadingSpinner size="lg" />
      <p class="text-gray-400 text-sm animate-pulse">正在加载内容...</p>
    </div>

    <!-- 章节内容展示 -->
    <template v-else-if="currentChapter">
      <div class="mb-8">
        <h1 class="text-4xl font-extrabold text-gray-900 mb-4 tracking-tight leading-tight">
          {{ currentChapter.title }}
        </h1>
        <div class="flex items-center gap-4 text-xs text-gray-400 font-medium">
          <span class="flex items-center gap-1">
            <Calendar class="w-3.5 h-3.5" />
            {{ formatDate(currentChapter.updated_at) }}
          </span>
          <span class="w-1 h-1 bg-gray-300 rounded-full"></span>
          <span class="flex items-center gap-1 text-brand-600">
            <BookOpen class="w-3.5 h-3.5" />
            阅读中
          </span>
        </div>
      </div>

      <!-- Markdown 内容渲染 -->
      <MarkdownDisplay 
        :content="currentChapter.content || ''" 
        @toc-update="handleTocUpdate"
      />

      <!-- 翻页导航 -->
      <div class="mt-16 pt-8 border-t border-gray-100 flex flex-col sm:flex-row items-center justify-between gap-6">
        <button
          v-if="prevChapter"
          @click="handleChapterSelect(prevChapter)"
          class="w-full sm:w-auto group flex flex-col items-start p-4 rounded-2xl border border-gray-100 hover:border-brand-200 hover:bg-brand-50/30 transition-all text-left"
        >
          <span class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1 flex items-center gap-1 group-hover:text-brand-500 transition-colors">
            <ArrowLeft class="w-3 h-3" />
            上一页
          </span>
          <span class="text-sm font-bold text-gray-700 group-hover:text-brand-700 transition-colors line-clamp-1">
            {{ prevChapter.title }}
          </span>
        </button>
        <div v-else class="hidden sm:block flex-1"></div>

        <button
          v-if="nextChapter"
          @click="handleChapterSelect(nextChapter)"
          class="w-full sm:w-auto group flex flex-col items-end p-4 rounded-2xl border border-gray-100 hover:border-brand-200 hover:bg-brand-50/30 transition-all text-right"
        >
          <span class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1 flex items-center gap-1 group-hover:text-brand-500 transition-colors">
            下一页
            <ArrowRight class="w-3 h-3" />
          </span>
          <span class="text-sm font-bold text-gray-700 group-hover:text-brand-700 transition-colors line-clamp-1">
            {{ nextChapter.title }}
          </span>
        </button>
        <div v-else class="hidden sm:block flex-1"></div>
      </div>
    </template>

    <!-- 空状态 -->
    <div v-else class="py-32 flex flex-col items-center justify-center">
      <EmptyState 
        title="选择一个章节开始阅读"
        description="请从左侧目录中选择您感兴趣的章节进行学习。"
        icon="book-open"
      />
    </div>
  </ReadingLayout>
</template>

<script setup>
/**
 * @file TextbookReader.vue
 * @description 教材阅读核心页面，采用三栏布局，集成目录、内容与 TOC
 * 
 * 功能：
 * - 动态加载教材目录树
 * - Markdown 渲染与语法高亮
 * - 自动提取并展示页内目录 (TOC)
 * - 响应式三栏布局切换
 * - 教材间快速切换与章节翻页
 */
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  ArrowLeft, 
  ArrowRight, 
  Calendar, 
  BookOpen 
} from 'lucide-vue-next'
import ReadingLayout from '@/layouts/ReadingLayout.vue'
import MarkdownDisplay from '@/components/MarkdownDisplay.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import EmptyState from '@/components/EmptyState.vue'
import { useUserStore } from '@/stores/user'
import { getTextbooks, getTextbookById } from '@/api/textbook'
import { getChapters, getChapterById } from '@/api/chapter'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 状态定义
const loadingContent = ref(false)
const books = ref([])
const currentBook = ref(null)
const chapters = ref([])
const activeChapterId = ref(null)
const currentChapter = ref(null)
const headings = ref([])

const user = computed(() => userStore.userInfo)

/**
 * 获取所有可用教材 (用于头部选择器)
 */
const loadBooks = async () => {
  try {
    const data = await getTextbooks({ page_size: 100 })
    books.value = data.items
  } catch (error) {
    // API 拦截器已处理错误 toast
  }
}

/**
 * 获取教材详情及目录
 * @param {number} textbookId 
 */
const loadTextbookData = async (textbookId) => {
  try {
    const [bookData, chaptersResponse] = await Promise.all([
      getTextbookById(textbookId),
      getChapters(textbookId)
    ])
    currentBook.value = bookData
    chapters.value = chaptersResponse.chapters || []

    // 如果当前路由没有指定章节，默认选中第一个有内容的章节
    if (!route.params.chapterId && chapters.value.length > 0) {
      const firstChapter = findFirstLeafChapter(chapters.value)
      if (firstChapter) {
        handleChapterSelect(firstChapter)
      }
    } else if (route.params.chapterId) {
      activeChapterId.value = Number(route.params.chapterId)
      loadChapterContent(activeChapterId.value)
    }
  } catch (error) {
    // API 拦截器已处理错误 toast
  }
}

/**
 * 加载特定章节的内容
 * @param {number} chapterId 
 */
const loadChapterContent = async (chapterId) => {
  if (!chapterId) return
  loadingContent.value = true
  try {
    const data = await getChapterById(chapterId)
    currentChapter.value = data
    activeChapterId.value = chapterId
    // 自动滚动到顶部
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (error) {
    // API 拦截器已处理错误 toast
  } finally {
    loadingContent.value = false
  }
}

/**
 * 递归查找第一个叶子节点章节
 * @param {Array} list 
 */
const findFirstLeafChapter = (list) => {
  for (const item of list) {
    if (!item.children || item.children.length === 0) {
      return item
    }
    const found = findFirstLeafChapter(item.children)
    if (found) return found
  }
  return null
}

/**
 * 获取平滑后的章节列表 (用于前后翻页)
 */
const flattenedChapters = computed(() => {
  const result = []
  const flatten = (list) => {
    for (const item of list) {
      result.push(item)
      if (item.children && item.children.length > 0) {
        flatten(item.children)
      }
    }
  }
  flatten(chapters.value)
  return result
})

/**
 * 上一章
 */
const prevChapter = computed(() => {
  if (!activeChapterId.value || flattenedChapters.value.length === 0) return null
  const index = flattenedChapters.value.findIndex(c => c.id === activeChapterId.value)
  if (index <= 0) return null
  // 向上寻找最近的一个非父节点或有内容的节点（这里简单处理，找上一个）
  return flattenedChapters.value[index - 1]
})

/**
 * 下一章
 */
const nextChapter = computed(() => {
  if (!activeChapterId.value || flattenedChapters.value.length === 0) return null
  const index = flattenedChapters.value.findIndex(c => c.id === activeChapterId.value)
  if (index === -1 || index >= flattenedChapters.value.length - 1) return null
  return flattenedChapters.value[index + 1]
})

/**
 * 处理教材切换
 */
const handleBookSelect = (book) => {
  router.push(`/textbook/${book.id}`)
}

/**
 * 处理章节切换
 */
const handleChapterSelect = (chapter) => {
  if (chapter.id === activeChapterId.value) return
  // 如果点击的是带有子章节的父章节，通常只展开不跳转，或者根据业务逻辑决定
  // 这里我们始终尝试跳转并加载
  router.push(`/textbook/${currentBook.value?.id}/chapter/${chapter.id}`)
}

/**
 * 处理 TOC 更新
 */
const handleTocUpdate = (newHeadings) => {
  headings.value = newHeadings
}

/**
 * 处理退出登录
 */
const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}

/**
 * 格式化日期
 */
const formatDate = (dateStr) => {
  if (!dateStr) return '未知时间'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// 监听教材 ID 变化
watch(() => route.params.id, (newId) => {
  if (newId) {
    loadTextbookData(Number(newId))
  }
}, { immediate: true })

// 监听章节 ID 变化
watch(() => route.params.chapterId, (newChapterId) => {
  if (newChapterId) {
    loadChapterContent(Number(newChapterId))
  }
})

onMounted(() => {
  loadBooks()
  if (userStore.token && !userStore.userInfo) {
    userStore.getUserInfo()
  }
})
</script>

<style scoped>
@reference "../style.css";

/* 针对 Markdown 内容的一些全局样式微调 */
:deep(.markdown-body) {
  @apply text-slate-700;
}
</style>
