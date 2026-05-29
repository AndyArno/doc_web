<template>
  <div class="min-h-screen bg-slate-50 flex flex-col font-sans">
    <!-- 顶部导航栏 -->
    <AppHeader 
      mode="reader" 
      :user="user" 
      :books="textbooks"
      @logout="handleLogout"
      @select-book="handleBookSelect"
    />

    <!-- 主体区域 -->
    <main class="flex-1 container mx-auto px-4 py-12">
      <!-- 英雄板块 (Hero Section) -->
      <section class="mb-16 text-center">
        <h1 class="text-4xl md:text-5xl font-extrabold text-gray-900 mb-6 tracking-tight">
          <span class="text-brand-600">ROS小车</span> 教学资源中心
        </h1>
        <p class="text-lg text-gray-600 max-w-2xl mx-auto leading-relaxed">
          这里有最全的 ROS 小车学习教材，从入门到精通，助你掌握机器人操作系统的核心技术。
        </p>
      </section>

      <!-- 教材列表 -->
      <section>
        <div class="flex items-center justify-between mb-8">
          <div class="flex items-center gap-3">
            <div class="w-1.5 h-6 bg-brand-600 rounded-full"></div>
            <h2 class="text-2xl font-bold text-gray-900">精选教材</h2>
          </div>
          <div class="text-sm text-gray-500 font-medium">共 {{ textbooks.length }} 本</div>
        </div>

        <!-- 加载中 -->
        <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <div v-for="i in 3" :key="i" class="bg-white rounded-3xl border border-gray-100 p-6 animate-pulse">
            <div class="w-full aspect-video bg-gray-100 rounded-2xl mb-6"></div>
            <div class="h-6 bg-gray-100 rounded-full w-3/4 mb-4"></div>
            <div class="h-4 bg-gray-100 rounded-full w-full mb-2"></div>
            <div class="h-4 bg-gray-100 rounded-full w-2/3"></div>
          </div>
        </div>

        <!-- 空状态 -->
        <EmptyState 
          v-else-if="textbooks.length === 0"
          title="暂无教材"
          description="系统管理员还没有发布任何教材，请稍后再来。"
          icon="library"
        />

        <!-- 教材网格 -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <div 
            v-for="book in textbooks" 
            :key="book.id"
            class="group bg-white rounded-3xl border border-gray-100 overflow-hidden shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300"
          >
            <!-- 封面图 -->
            <div class="aspect-video relative overflow-hidden bg-brand-50 flex items-center justify-center group-hover:bg-brand-100 transition-colors">
              <img 
                v-if="book.cover_image" 
                :src="book.cover_image" 
                :alt="book.title"
                class="w-full h-full object-cover"
                @error="handleImageError($event)"
              />
              <BookOpen v-else class="w-16 h-16 text-brand-300 group-hover:scale-110 transition-transform duration-500" />
              <div class="absolute top-4 right-4 bg-white/80 backdrop-blur px-3 py-1 rounded-full text-[10px] font-bold text-brand-700 uppercase tracking-widest border border-brand-100">
                Textbook
              </div>
            </div>

            <!-- 教材信息 -->
            <div class="p-6">
              <h3 class="text-xl font-bold text-gray-900 mb-3 group-hover:text-brand-600 transition-colors">
                {{ book.title }}
              </h3>
              <p class="text-gray-500 text-sm leading-relaxed mb-6 line-clamp-2">
                {{ book.description || '暂无详细介绍，快来开启你的 ROS 学习之旅吧！' }}
              </p>
              
              <div class="flex items-center justify-between mt-auto pt-6 border-t border-gray-50">
                <div class="flex items-center gap-2 text-xs text-gray-400 font-medium">
                  <User class="w-3.5 h-3.5" />
                  <span>管理员</span>
                </div>
                <router-link 
                  :to="`/textbook/${book.id}`"
                  class="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-600 text-white text-sm font-bold hover:bg-brand-500 transition-all shadow-brand hover:shadow-brand-lg"
                >
                  开始阅读
                  <ArrowRight class="w-4 h-4" />
                </router-link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- 页脚 -->
    <footer class="bg-white border-t border-gray-200 py-12">
      <div class="container mx-auto px-4 text-center">
        <p class="text-sm text-gray-400">© 2026 ROS小车教学网站. All rights reserved.</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
/**
 * @file Home.vue
 * @description 应用首页，展示可用教材列表及入口
 * 
 * 功能：
 * - 获取并展示所有已发布教材
 * - 用户登录/登出管理
 * - 教材卡片式展示，支持跳转阅读
 */
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { 
  BookOpen, 
  ArrowRight, 
  User, 
} from 'lucide-vue-next'
import AppHeader from '@/components/AppHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import { useUserStore } from '@/stores/user'
import { getTextbooks } from '@/api/textbook'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(true)
const textbooks = ref([])
const user = computed(() => userStore.userInfo)

/**
 * 加载教材列表
 */
const loadTextbooks = async () => {
  loading.value = true
  try {
    // 首页只显示已发布的教材 (由后端 API 负责过滤或通过参数控制)
    const data = await getTextbooks({ page_size: 100 })
    textbooks.value = data.items
  } catch (error) {
    // API 拦截器已处理错误 toast
  } finally {
    loading.value = false
  }
}

/**
 * 处理退出登录
 */
const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}

/**
 * 处理教材切换
 */
function handleBookSelect(book) {
  router.push({ path: `/textbook/${book.id}` })
}

/**
 * 处理图片加载失败
 * 隐藏图片，显示占位图
 */
function handleImageError(event) {
  event.target.style.display = 'none'
}

onMounted(() => {
  loadTextbooks()
  // 如果已登录但没有用户信息，尝试获取一次
  if (userStore.token && !userStore.userInfo) {
    userStore.getUserInfo()
  }
})
</script>

<style scoped>
.shadow-brand {
  box-shadow: 0 4px 14px 0 rgba(var(--brand-600-rgb, 59, 130, 246), 0.39);
}
.shadow-brand-lg {
  box-shadow: 0 10px 25px -3px rgba(var(--brand-600-rgb, 59, 130, 246), 0.45);
}
</style>
