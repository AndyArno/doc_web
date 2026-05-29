<template>
  <header class="h-16 border-b border-gray-200 bg-white sticky top-0 z-50">
    <div class="container mx-auto h-full px-4 flex items-center justify-between">
      <!-- 左侧：Logo 与 菜单 -->
      <div class="flex items-center gap-4 lg:gap-8 h-full">
        <!-- Logo -->
        <router-link to="/" class="flex items-center gap-2 group shrink-0">
          <div class="bg-brand-600 p-1.5 rounded-xl text-white group-hover:bg-brand-500 transition-colors shadow-brand">
            <BookOpen class="w-5 h-5" />
          </div>
          <span class="text-xl font-extrabold text-gray-900 hidden sm:block tracking-tight">ROS小车教学</span>
        </router-link>

        <!-- 分隔线 (桌面端) -->
        <div class="hidden lg:block h-6 w-px bg-gray-200" v-if="mode === 'reader' || (mode === 'admin' && adminMenus.length > 0)"></div>

        <!-- 阅读模式：教材选择器 (桌面端) -->
        <div v-if="mode === 'reader'" class="relative hidden lg:block">
          <button 
            @click.stop="toggleBookSelector"
            class="flex items-center gap-2 px-3 py-2 rounded-xl border border-gray-200 hover:border-brand-400 hover:text-brand-600 transition-all text-sm font-semibold text-gray-700 bg-gray-50/50"
          >
            <Library class="w-4 h-4 text-gray-400" />
            <span class="max-w-[150px] truncate">{{ currentBook?.title || '选择教材' }}</span>
            <ChevronDown class="w-4 h-4 transition-transform duration-200" :class="{ 'rotate-180': isBookSelectorOpen }" />
          </button>
          
          <!-- 教材选择下拉菜单 -->
          <transition name="zoom">
            <div v-if="isBookSelectorOpen" class="absolute left-0 mt-2 w-72 bg-white rounded-2xl shadow-xl border border-gray-100 py-2 z-50">
              <div class="px-4 py-2 text-xs font-bold text-gray-400 uppercase tracking-wider">可用教材</div>
              <div class="max-height-[400px] overflow-y-auto">
                <button
                  v-for="book in books"
                  :key="book.id"
                  @click="selectBook(book)"
                  class="w-full text-left px-4 py-3 text-sm flex items-center justify-between hover:bg-brand-50 transition-colors"
                  :class="[currentBook?.id === book.id ? 'text-brand-600 font-bold bg-brand-50/50' : 'text-gray-700']"
                >
                  <span class="truncate">{{ book.title }}</span>
                  <div v-if="currentBook?.id === book.id" class="w-1.5 h-1.5 rounded-full bg-brand-600"></div>
                </button>
              </div>
              <div v-if="books.length === 0" class="px-4 py-8 text-center text-gray-400 text-sm">
                暂无可用教材
              </div>
            </div>
          </transition>
        </div>

        <!-- 管理模式：功能模块菜单 (桌面端) -->
        <nav v-if="mode === 'admin'" class="hidden md:flex items-center gap-1 h-full">
          <router-link 
            v-for="menu in adminMenus" 
            :key="menu.path"
            :to="getAdminPath(menu)"
            class="px-4 py-2 rounded-xl text-sm font-semibold transition-all"
            :class="[
              isRouteActive(getAdminPath(menu)) 
                ? 'bg-brand-600 text-white shadow-brand' 
                : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
            ]"
          >
            {{ menu.meta.title }}
          </router-link>
        </nav>
      </div>

      <!-- 右侧：搜索框、功能按钮与用户头像 -->
      <div class="flex items-center gap-2 sm:gap-4">
        <!-- 搜索框 (桌面端) -->
        <div class="hidden md:block w-64 lg:w-80">
          <SearchBox 
            @search="handleSearch"
            @select="handleSearchSelect"
          />
        </div>

        <!-- 模式切换按钮 -->
        <router-link 
          v-if="canAccessAdmin && mode === 'reader'"
          to="/admin"
          class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold text-brand-600 hover:bg-brand-50 transition-all border border-transparent hover:border-brand-100"
        >
          <LayoutDashboard class="w-4 h-4" />
          <span class="hidden lg:inline">管理后台</span>
        </router-link>

        <router-link 
          v-if="mode === 'admin'"
          to="/"
          class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold text-brand-600 hover:bg-brand-50 transition-all border border-transparent hover:border-brand-100"
        >
          <BookOpen class="w-4 h-4" />
          <span class="hidden lg:inline">阅读模式</span>
        </router-link>

        <!-- 用户信息与头像 -->
        <div class="relative" v-if="user">
          <button 
            @click.stop="toggleUserMenu"
            class="flex items-center gap-2 p-1 pr-2 sm:pr-3 rounded-full hover:bg-gray-100 transition-all border border-gray-200"
          >
            <div class="w-8 h-8 rounded-full bg-brand-100 flex items-center justify-center text-brand-600 font-bold text-xs border border-brand-200 overflow-hidden shadow-sm">
              <img v-if="user.avatar" :src="user.avatar" class="w-full h-full object-cover" :alt="user.username" />
              <User v-else class="w-4 h-4" />
            </div>
            <span class="text-sm font-bold text-gray-700 hidden sm:block">{{ user.username }}</span>
            <ChevronDown class="w-3.5 h-3.5 text-gray-400 hidden sm:block" />
          </button>
          
          <!-- 用户下拉菜单 -->
          <transition name="zoom">
            <div v-if="isUserMenuOpen" class="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-xl border border-gray-100 py-2 z-50">
              <div class="px-4 py-3 border-b border-gray-50 mb-1">
                <p class="text-sm font-bold text-gray-900 truncate">{{ user.username }}</p>
                <p class="text-xs text-gray-500 truncate">{{ user.role }}</p>
              </div>
              <button 
                @click="logout"
                class="w-full text-left px-4 py-2.5 text-sm text-red-500 font-semibold flex items-center gap-2 hover:bg-red-50 transition-colors"
              >
                <LogOut class="w-4 h-4" />
                退出登录
              </button>
            </div>
          </transition>
        </div>

        <!-- 未登录显示 -->
        <router-link 
          v-else 
          to="/login"
          class="px-5 py-2 rounded-xl bg-brand-600 text-white text-sm font-bold hover:bg-brand-500 transition-all shadow-brand hover:shadow-brand-lg"
        >
          登录
        </router-link>
        
        <!-- 移动端菜单触发器 (侧边栏) -->
        <button 
          v-if="showSidebarToggle && (mode === 'reader' || mode === 'admin')"
          @click="$emit('toggle-sidebar')"
          class="lg:hidden p-2 text-gray-600 hover:bg-gray-100 rounded-xl transition-colors"
        >
          <Menu class="w-6 h-6" />
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
/**
 * AppHeader 组件 - 应用顶部导航栏
 * 支持阅读模式和管理模式，响应式布局。
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { 
  BookOpen, 
  ChevronDown, 
  Library, 
  LayoutDashboard, 
  User, 
  LogOut, 
  Menu 
} from 'lucide-vue-next'
import SearchBox from './SearchBox.vue'
import type { Role } from '@/types/api'

/** 用户信息（简化版，用于 header 显示） */
interface HeaderUser {
  id: number
  username: string
  role: Role
  avatar?: string
}

/** 教材信息（简化版，用于选择器） */
interface HeaderBook {
  id: number
  title: string
}

/** 管理后台菜单项 */
interface AdminMenuItem {
  path: string
  meta: {
    title: string
  }
}

interface Props {
  /** 当前模式：reader (阅读模式) 或 admin (管理模式) */
  mode?: 'reader' | 'admin'
  /** 当前登录用户信息 */
  user?: HeaderUser | null
  /** 当前选中的教材 */
  currentBook?: HeaderBook | null
  /** 可选教材列表 (用于阅读模式选择器) */
  books?: HeaderBook[]
  /** 是否显示移动端侧边栏按钮 */
  showSidebarToggle?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'reader',
  user: null,
  currentBook: null,
  books: () => [],
  showSidebarToggle: true
})

const emit = defineEmits<{
  /** 选择教材事件 */
  (e: 'select-book', book: HeaderBook): void
  /** 登出事件 */
  (e: 'logout'): void
  /** 切换侧边栏事件 (移动端) */
  (e: 'toggle-sidebar'): void
  /** 搜索事件 */
  (e: 'search', query: string): void
  /** 搜索选择事件 */
  (e: 'search-select', suggestion: unknown): void
}>()

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isBookSelectorOpen = ref(false)
const isUserMenuOpen = ref(false)

/**
 * 计算管理后台菜单项（从路由配置动态读取）
 */
const adminMenus = computed<AdminMenuItem[]>(() => {
  const adminRoute = router.options.routes.find(r => r.name === 'AdminLayout')
  if (!adminRoute || !adminRoute.children) return []
  
  // 过滤出具有 title 且不带动态参数的子路由作为主菜单模块
  // 同时根据角色过滤：无 roles 配置或有 roles 且包含当前用户角色
  return adminRoute.children.filter(r => 
    r.meta && r.meta.title && !r.path.includes(':') &&
    (!r.meta.roles || r.meta.roles.includes(userStore.role))
  ) as AdminMenuItem[]
})

/**
 * 获取管理后台菜单的完整路径
 */
const getAdminPath = (menu: AdminMenuItem): string => {
  if (!menu.path) return '/admin'
  return `/admin/${menu.path}`
}

/**
 * 判断路由是否处于激活状态
 */
const isRouteActive = (path: string): boolean => {
  if (path === '/admin') {
    return route.path === '/admin'
  }
  return route.path.startsWith(path)
}

/**
 * 是否有权访问管理后台
 */
const canAccessAdmin = computed(() => {
  const adminRoles = ['super_admin', 'admin', 'editor']
  return props.user && adminRoles.includes(props.user.role)
})

/** 切换教材选择器显示状态 */
const toggleBookSelector = () => {
  isBookSelectorOpen.value = !isBookSelectorOpen.value
  isUserMenuOpen.value = false
}

/** 切换用户菜单显示状态 */
const toggleUserMenu = () => {
  isUserMenuOpen.value = !isUserMenuOpen.value
  isBookSelectorOpen.value = false
}

/** 选中教材 */
const selectBook = (book: HeaderBook): void => {
  emit('select-book', book)
  isBookSelectorOpen.value = false
}

/** 退出登录 */
const logout = (): void => {
  emit('logout')
  isUserMenuOpen.value = false
}

/** 处理搜索事件 */
const handleSearch = (query: string): void => {
  emit('search', query)
}

/** 处理搜索选择事件 */
const handleSearchSelect = (suggestion: unknown): void => {
  emit('search-select', suggestion)
  // 添加路由跳转
  const s = suggestion as { id: number; textbookId: number }
  if (s.id && s.textbookId) {
    router.push(`/textbook/${s.textbookId}/chapter/${s.id}`)
  }
}

/** 点击外部关闭所有下拉菜单 */
const handleClickOutside = () => {
  isBookSelectorOpen.value = false
  isUserMenuOpen.value = false
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.zoom-enter-active,
.zoom-leave-active {
  transition: all 0.2s ease-out;
}

.zoom-enter-from,
.zoom-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* 自定义滚动条样式 */
.max-height-\[400px\]::-webkit-scrollbar {
  width: 4px;
}
.max-height-\[400px\]::-webkit-scrollbar-track {
  background: transparent;
}
.max-height-\[400px\]::-webkit-scrollbar-thumb {
  background: #e5e7eb;
  border-radius: 10px;
}
.max-height-\[400px\]::-webkit-scrollbar-thumb:hover {
  background: #d1d5db;
}
</style>
