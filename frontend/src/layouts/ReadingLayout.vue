<template>
  <div class="min-h-screen bg-slate-50 flex flex-col font-sans">
    <!-- 顶部导航栏 -->
    <AppHeader 
      mode="reader" 
      :user="user" 
      :current-book="currentBook" 
      :books="books"
      :show-sidebar-toggle="hasChapters"
      @select-book="$emit('select-book', $event)"
      @logout="$emit('logout')"
      @toggle-sidebar="isSidebarOpen = !isSidebarOpen"
    />

    <div class="flex-1 flex overflow-hidden relative">
      <!-- 移动端侧边栏遮罩层 (tablet/mobile) -->
      <transition name="fade">
        <div 
          v-if="isSidebarOpen" 
          class="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm lg:hidden"
          @click="isSidebarOpen = false"
        />
      </transition>

      <!-- 左侧目录栏 (桌面端固定 280px，平板/移动端抽屉) -->
      <aside 
        v-if="hasChapters"
        class="fixed top-16 bottom-0 left-0 z-50 w-[280px] bg-white border-r border-gray-100 flex flex-col shadow-xl lg:shadow-none transition-transform duration-300 lg:translate-x-0"
        :class="[isSidebarOpen ? 'translate-x-0' : '-translate-x-full']"
      >
        <!-- 平板/移动端：显示在抽屉顶部的教材选择器 (lg:hidden) -->
        <div class="lg:hidden p-4 border-b border-gray-50 bg-gray-50/50">
          <div class="text-[10px] font-extrabold text-gray-400 uppercase tracking-widest mb-3">切换教材</div>
          <div class="relative">
            <select 
              class="w-full bg-white border border-gray-200 rounded-xl px-3 py-2.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-brand-500/20 text-gray-700 appearance-none cursor-pointer"
              :value="currentBook?.id"
              @change="handleBookChange"
            >
              <option v-for="book in books" :key="book.id" :value="book.id">
                {{ book.title }}
              </option>
            </select>
            <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
              <ChevronDown class="w-4 h-4 text-gray-400" />
            </div>
          </div>
        </div>

        <!-- 目录树区域 -->
        <div class="flex-1 overflow-y-auto py-6 px-2 scroll-container">
          <div class="px-3 mb-6 flex items-center gap-2">
            <div class="w-1 h-4 bg-brand-500 rounded-full"></div>
            <h2 class="text-sm font-bold text-gray-900 tracking-wide uppercase">课程目录</h2>
          </div>
          <div class="space-y-0.5">
            <TreeNode 
              v-for="chapter in chapters" 
              :key="chapter.id" 
              :node="chapter"
              :active-node-id="activeChapterId"
              @select="handleChapterSelect"
            />
          </div>
        </div>
      </aside>

      <!-- 主内容区 -->
      <main class="flex-1 min-w-0 bg-white lg:bg-transparent overflow-y-auto scroll-smooth lg:ml-[280px] lg:mr-[280px]">
        <div class="max-w-4xl mx-auto px-4 py-8 lg:px-16 lg:py-12 bg-white min-h-full shadow-sm lg:shadow-none ring-1 ring-gray-100 lg:ring-0">
          <slot />
        </div>
      </main>

      <!-- 右侧页内导航 (仅桌面端显示) -->
      <aside class="hidden lg:block fixed top-16 right-0 w-[280px] h-[calc(100vh-64px)] overflow-hidden border-l border-gray-50">
        <PageTOC :headings="headings" />
      </aside>
    </div>
  </div>
</template>

<script setup>
/**
 * @file ReadingLayout.vue
 * @description 阅读模式主布局组件
 * 
 * 功能：
 * - 桌面端：三栏布局（左侧目录 280px + 主内容 + 右侧页内导航 280px）
 * - 平板/移动端：左侧栏折叠为抽屉，右侧栏隐藏
 * - 集成教材选择器在移动端抽屉顶部
 */
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ChevronDown } from 'lucide-vue-next'
import AppHeader from '../components/AppHeader.vue'
import TreeNode from '../components/TreeNode.vue'
import PageTOC from '../components/PageTOC.vue'

/**
 * @typedef {Object} User
 * @property {number} id
 * @property {string} username
 * @property {string} role
 */

/**
 * @typedef {Object} Book
 * @property {number} id
 * @property {string} title
 */

/**
 * @typedef {Object} Chapter
 * @property {number} id
 * @property {string} title
 * @property {Array} [children]
 */

/**
 * @typedef {Object} TOCItem
 * @property {string} id
 * @property {string} text
 * @property {number} level
 */

const props = defineProps({
  /** 当前登录用户信息 */
  user: {
    type: Object,
    default: null
  },
  /** 可选教材列表 */
  books: {
    type: Array,
    default: () => []
  },
  /** 当前选中的教材 */
  currentBook: {
    type: Object,
    default: null
  },
  /** 教材章节树 */
  chapters: {
    type: Array,
    default: () => []
  },
  /** 当前选中的章节ID */
  activeChapterId: {
    type: [String, Number],
    default: null
  },
  /** 当前页面的标题列表 (TOC) */
  headings: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits([
  /** 教材切换事件 */
  'select-book', 
  /** 章节选择事件 */
  'select-chapter', 
  /** 退出登录事件 */
  'logout'
])

const route = useRoute()
const isSidebarOpen = ref(false)
const hasChapters = computed(() => Array.isArray(props.chapters) && props.chapters.length > 0)

/**
 * 处理移动端教材切换
 * @param {Event} event 
 */
const handleBookChange = (event) => {
  const bookId = Number(event.target.value)
  const book = props.books.find(b => b.id === bookId)
  if (book) {
    emit('select-book', book)
  }
}

/**
 * 处理章节选择
 * @param {Object} chapter 
 */
const handleChapterSelect = (chapter) => {
  emit('select-chapter', chapter)
  // 移动端/平板端选中后自动关闭侧边栏
  if (window.innerWidth < 1024) {
    isSidebarOpen.value = false
  }
}

// 监听路由变化，关闭侧边栏
watch(() => route.fullPath, () => {
  isSidebarOpen.value = false
})
</script>

<style scoped>
@reference "../style.css";

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 优化侧边栏滚动条 */
.scroll-container::-webkit-scrollbar {
  width: 4px;
}

.scroll-container::-webkit-scrollbar-thumb {
  @apply bg-gray-200 rounded-full;
}

.scroll-container::-webkit-scrollbar-track {
  @apply bg-transparent;
}

.scroll-container:hover::-webkit-scrollbar-thumb {
  @apply bg-gray-300;
}

/* iOS 滚动优化 */
.scroll-container {
  -webkit-overflow-scrolling: touch;
}
</style>
