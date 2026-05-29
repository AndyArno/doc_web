<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <!-- 顶部导航栏 -->
    <AppHeader 
      mode="admin" 
      :user="userStore.userInfo"
      @toggle-sidebar="isSidebarOpen = !isSidebarOpen"
      @logout="handleLogout"
    />

    <div class="flex-1 flex overflow-hidden">
      <!-- 移动端侧边栏遮罩 -->
      <transition name="fade">
        <div 
          v-if="isSidebarOpen" 
          class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm z-40 lg:hidden"
          @click="isSidebarOpen = false"
        ></div>
      </transition>

      <!-- 左侧侧边栏 (180px) - 仅在有子菜单时显示 -->
      <aside 
        v-if="currentSubMenus.length > 0"
        class="fixed inset-y-0 left-0 z-50 w-[180px] bg-white border-r border-gray-200 transform transition-transform duration-300 ease-in-out lg:relative lg:translate-x-0"
        :class="[isSidebarOpen ? 'translate-x-0' : '-translate-x-full']"
      >
        <!-- 移动端：侧边栏顶部的 Logo (因为顶部 Header 可能被遮挡或需要显示关闭按钮) -->
        <div class="lg:hidden flex items-center justify-between p-4 border-b border-gray-100">
          <span class="font-bold text-gray-900">管理菜单</span>
          <button @click="isSidebarOpen = false" class="p-1 hover:bg-gray-100 rounded-lg">
            <X class="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <div class="h-full overflow-y-auto py-4">
          <!-- 移动端专有：主模块切换 (在桌面端这些在顶部 Header) -->
          <nav class="lg:hidden px-3 mb-6 pb-6 border-b border-gray-100">
            <div class="px-3 mb-2 text-xs font-bold text-gray-400 uppercase tracking-wider">主要模块</div>
            <div class="space-y-1">
              <router-link 
                v-for="menu in topMenus" 
                :key="menu.path"
                :to="getAdminPath(menu)"
                class="flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-semibold transition-all"
                :class="[
                  isRouteActive(getAdminPath(menu)) 
                    ? 'bg-brand-50 text-brand-600' 
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                ]"
                @click="isSidebarOpen = false"
              >
                <component :is="getMenuIcon(menu.name)" class="w-4 h-4" />
                {{ menu.meta.title }}
              </router-link>
            </div>
          </nav>

          <!-- 子菜单区域 -->
          <nav v-if="currentSubMenus.length > 0" class="px-3">
            <div class="px-3 mb-2 text-xs font-bold text-gray-400 uppercase tracking-wider">
              {{ activeMenuTitle }}
            </div>
            <div class="space-y-1">
              <button
                v-for="item in currentSubMenus"
                :key="item.value"
                @click="handleSubMenuClick(item)"
                class="w-full flex items-center justify-between px-3 py-2 rounded-xl text-sm font-semibold transition-all group"
                :class="[
                  isSubMenuActive(item.value)
                    ? 'bg-brand-600 text-white shadow-brand-sm'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                ]"
              >
                <span>{{ item.label }}</span>
                <ChevronRight 
                  v-if="!isSubMenuActive(item.value)"
                  class="w-3.5 h-3.5 text-gray-400 opacity-0 group-hover:opacity-100 transition-all" 
                />
              </button>
            </div>
          </nav>

          <!-- 无子菜单时的提示 (可选) -->
          <div v-else-if="!isDashboardActive" class="px-6 py-8 text-center">
            <p class="text-xs text-gray-400 italic">当前模块无子项</p>
          </div>
        </div>
      </aside>

      <!-- 主内容区 -->
      <main class="flex-1 relative overflow-y-auto focus:outline-none bg-gray-50">
        <div class="py-6 px-4 sm:px-6 lg:px-8" :class="{ 'max-w-7xl mx-auto': !isEditorPage }">
          <router-view v-slot="{ Component }">
            <transition name="page" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
/**
 * AdminLayout 组件 - 管理后台布局组件
 * 
 * 包含：
 * 1. 顶部导航 (AppHeader 管理模式)
 * 2. 左侧侧边栏 (180px，支持移动端抽屉式)
 * 3. 响应式布局
 * 4. 子菜单过滤逻辑
 */
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import AppHeader from '@/components/AppHeader.vue'
import { 
  X, 
  ChevronRight, 
  LayoutDashboard, 
  Users, 
  BookOpen, 
  FileText,
  Image
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isSidebarOpen = ref(false)

/**
 * 顶部导航主菜单配置（从路由动态读取）
 */
const topMenus = computed(() => {
  const adminRoute = router.options.routes.find(r => r.name === 'AdminLayout')
  if (!adminRoute || !adminRoute.children) return []
  
  // 过滤出具有 title 且不带动态参数的子路由作为主菜单模块
  // 同时根据角色过滤：无 roles 配置或有 roles 且包含当前用户角色
  return adminRoute.children.filter(r => 
    r.meta && r.meta.title && !r.path.includes(':') &&
    (!r.meta.roles || r.meta.roles.includes(userStore.role))
  )
})

/**
 * 获取子菜单配置
 */
const subMenuGroups = {
  'Users': [
    { label: '全部用户', value: '' },
    { label: '超级管理员', value: 'super_admin' },
    { label: '管理员', value: 'admin' },
    { label: '编辑', value: 'editor' },
    { label: '普通用户', value: 'user' }
  ],
  'Textbooks': [
    { label: '全部教材', value: '' },
    { label: '已发布', value: 'published' },
    { label: '草稿', value: 'draft' }
  ]
}

/**
 * 当前选中的子菜单项
 */
const currentSubMenus = computed(() => {
  // 根据当前路由名称返回对应的子菜单
  const currentRouteName = route.name
  if (currentRouteName === 'Users') return subMenuGroups.Users
  if (currentRouteName === 'Textbooks') return subMenuGroups.Textbooks
  return []
})

/**
 * 获取当前激活的顶级菜单标题
 */
const activeMenuTitle = computed(() => {
  const active = topMenus.value.find(menu => isRouteActive(getAdminPath(menu)))
  return active ? active.meta.title : '菜单'
})

/**
 * 是否是仪表盘页面
 */
const isDashboardActive = computed(() => route.name === 'AdminDashboard')

/**
 * 是否是编辑器页面（需要全宽布局）
 */
const isEditorPage = computed(() => route.name === 'Editor')

/**
 * 获取图标组件
 */
const getMenuIcon = (name) => {
  const icons = {
    'AdminDashboard': LayoutDashboard,
    'Users': Users,
    'Textbooks': BookOpen,
    'MediaLibrary': Image
  }
  return icons[name] || FileText
}

/**
 * 获取管理后台菜单的完整路径
 */
const getAdminPath = (menu) => {
  if (!menu.path) return '/admin'
  return `/admin/${menu.path}`
}

/**
 * 判断顶级路由是否激活
 */
const isRouteActive = (path) => {
  if (path === '/admin') return route.path === '/admin'
  return route.path.startsWith(path)
}

/**
 * 判断子菜单项是否激活 (基于 query)
 */
const isSubMenuActive = (value) => {
  const currentQueryValue = route.name === 'Users' ? route.query.role : route.query.status
  return (currentQueryValue || '') === value
}

/**
 * 处理子菜单点击
 */
const handleSubMenuClick = (item) => {
  const queryKey = route.name === 'Users' ? 'role' : 'status'
  router.push({
    query: { ...route.query, [queryKey]: item.value || undefined }
  })
  isSidebarOpen.value = false
}

/**
 * 退出登录
 */
const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.page-enter-active,
.page-leave-active {
  transition: all 0.2s ease-out;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.shadow-brand-sm {
  box-shadow: 0 4px 12px -2px rgba(37, 99, 235, 0.3);
}

/* 隐藏滚动条但保留滚动功能 */
.overflow-y-auto {
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.overflow-y-auto::-webkit-scrollbar {
  display: none;
}
</style>
