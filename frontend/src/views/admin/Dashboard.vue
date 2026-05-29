<template>
  <div class="space-y-6">
    <!-- 欢迎栏 -->
    <header class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 tracking-tight">管理后台概览</h1>
        <p class="text-sm text-gray-500 mt-1">欢迎回来，{{ userStore.userInfo?.username }}。这是系统的实时状态看板。</p>
      </div>
      <div class="flex items-center gap-2">
        <span class="flex items-center gap-1 text-[10px] font-bold text-gray-400 uppercase tracking-widest bg-gray-100 px-3 py-1.5 rounded-lg border border-gray-200">
          <Calendar class="w-3 h-3" />
          {{ currentDate }}
        </span>
      </div>
    </header>

    <!-- 统计指标 (响应式网格) -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
      <!-- 加载状态 -->
      <div 
        v-if="loading" 
        class="col-span-full flex items-center justify-center py-12"
      >
        <Loader2 class="w-8 h-8 text-brand-600 animate-spin" />
        <span class="ml-3 text-gray-500">加载中...</span>
      </div>
      
      <!-- 统计卡片 -->
      <template v-else>
        <div 
          v-for="stat in stats" 
          :key="stat.label"
          class="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm hover:shadow-brand transition-all group"
        >
          <div class="flex items-center justify-between mb-4">
            <div 
              class="w-12 h-12 rounded-2xl flex items-center justify-center transition-colors group-hover:scale-110 duration-500"
              :class="stat.bgClass"
            >
              <component :is="stat.icon" class="w-6 h-6" :class="stat.iconClass" />
            </div>
          </div>
          <div class="text-3xl font-extrabold text-gray-900 mb-1 tabular-nums">{{ stat.value }}</div>
          <div class="text-xs font-bold text-gray-400 uppercase tracking-widest">{{ stat.label }}</div>
        </div>
      </template>
    </div>

    <!-- 快速入门 -->
    <div class="bg-brand-600 rounded-3xl p-8 text-white shadow-brand-lg relative overflow-hidden group">
      <div class="relative z-10 h-full flex flex-col">
        <h2 class="text-xl font-bold mb-4">开始您的教学管理之旅</h2>
        <p class="text-brand-100 text-sm leading-relaxed mb-8">
          通过管理后台，您可以轻松地创建、编辑教材，管理用户权限，并实时跟踪学习进度。
        </p>
        
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-auto">
          <router-link 
            to="/admin/textbooks" 
            class="flex items-center justify-between px-5 py-3 bg-white/10 hover:bg-white/20 backdrop-blur rounded-2xl text-sm font-bold transition-all border border-white/10 group-hover:translate-x-1"
          >
            <span>管理教材库</span>
            <ArrowRight class="w-4 h-4" />
          </router-link>
          <router-link 
            to="/admin/users" 
            class="flex items-center justify-between px-5 py-3 bg-white/10 hover:bg-white/20 backdrop-blur rounded-2xl text-sm font-bold transition-all border border-white/10 group-hover:translate-x-1"
          >
            <span>查看全部用户</span>
            <ArrowRight class="w-4 h-4" />
          </router-link>
        </div>
      </div>
      
      <!-- 装饰背景 -->
      <BookOpen class="absolute -bottom-8 -right-8 w-48 h-48 text-white/5 rotate-12 group-hover:rotate-0 transition-transform duration-1000" />
    </div>
  </div>
</template>

<script setup>
/**
 * @file Dashboard.vue
 * @description 管理后台首页，响应式概览看板
 */
import { ref, computed, onMounted } from 'vue'
import { 
  Users, 
  BookOpen, 
  Calendar, 
  ArrowRight,
  Loader2
} from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import { getUsers } from '@/api/user'
import { getTextbooks } from '@/api/textbook'

const userStore = useUserStore()

/** 加载状态 */
const loading = ref(true)

/** 统计数据 */
const userCount = ref(0)
const textbookCount = ref(0)

/** 统计卡片配置 */
const stats = computed(() => [
  { 
    label: '注册用户', 
    value: userCount.value, 
    icon: Users,
    bgClass: 'bg-brand-50',
    iconClass: 'text-brand-600'
  },
  { 
    label: '教材总数', 
    value: textbookCount.value, 
    icon: BookOpen,
    bgClass: 'bg-green-50',
    iconClass: 'text-green-600'
  }
])

const currentDate = computed(() => {
  return new Date().toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
})

/** 加载统计数据 */
async function loadStats() {
  loading.value = true
  try {
    // 并行请求用户和教材总数
    const [usersRes, textbooksRes] = await Promise.all([
      getUsers({ page: 1, page_size: 1 }),
      getTextbooks({ page: 1, page_size: 1 })
    ])
    userCount.value = usersRes.total || 0
    textbookCount.value = textbooksRes.total || 0
  } catch (error) {
    // API 拦截器已处理错误 toast
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>
