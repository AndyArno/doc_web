<template>
  <div class="min-h-screen bg-slate-50 flex flex-col font-sans">
    <AppHeader
      mode="reader"
      :user="user"
      :books="textbooks"
      @logout="handleLogout"
    />

    <main class="flex-1 container mx-auto px-4 py-8">
      <div class="max-w-4xl mx-auto">
        <div class="mb-8">
          <h1 class="text-3xl font-extrabold text-gray-900 mb-2 tracking-tight">
            搜索结果
          </h1>
          <p v-if="query" class="text-gray-500">
            找到 <span class="font-bold text-gray-700">{{ total }}</span> 条与
            "<span class="font-bold text-brand-600">{{ query }}</span>" 相关的结果
          </p>
        </div>

        <div v-if="loading" class="py-20 flex flex-col items-center justify-center">
          <LoadingSpinner size="lg" />
          <p class="text-gray-400 text-sm mt-4 animate-pulse">正在搜索...</p>
        </div>

        <EmptyState
          v-else-if="results.length === 0 && query"
          icon="search-x"
          title="未找到相关内容"
          description="尝试使用其他关键词进行搜索"
        >
          <template #action>
            <router-link
              to="/"
              class="px-5 py-2.5 rounded-xl bg-brand-600 text-white text-sm font-bold hover:bg-brand-500 transition-all shadow-brand"
            >
              返回首页
            </router-link>
          </template>
        </EmptyState>

        <template v-else-if="results.length > 0">
          <div class="space-y-4">
            <router-link
              v-for="item in results"
              :key="item.doc_id"
              :to="`/textbook/${item.textbook_id}/chapter/${item.doc_id}`"
              class="block bg-white rounded-2xl border border-gray-100 p-6 hover:shadow-lg hover:border-brand-200 transition-all group"
            >
              <div class="flex items-start justify-between gap-4">
                <div class="flex-1 min-w-0">
                  <h3
                    class="text-lg font-bold text-gray-900 group-hover:text-brand-600 transition-colors mb-2"
                    v-html="highlightText(item.title, query)"
                  />
                  <div class="flex items-center gap-2 text-sm text-gray-500">
                    <BookOpen class="w-4 h-4" />
                    <span v-html="highlightText(item.textbook_title, query)" />
                  </div>
                </div>
                <ArrowRight class="w-5 h-5 text-gray-300 group-hover:text-brand-500 group-hover:translate-x-1 transition-all shrink-0" />
              </div>
            </router-link>
          </div>

          <div v-if="totalPages > 1" class="mt-10 flex items-center justify-center gap-2">
            <button
              :disabled="currentPage <= 1"
              @click="changePage(currentPage - 1)"
              class="px-4 py-2 rounded-xl border border-gray-200 text-sm font-semibold text-gray-600 hover:bg-gray-50 hover:border-gray-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              上一页
            </button>

            <div class="flex items-center gap-1">
              <button
                v-for="page in visiblePages"
                :key="page"
                @click="changePage(page)"
                class="w-10 h-10 rounded-xl text-sm font-bold transition-all"
                :class="[
                  page === currentPage
                    ? 'bg-brand-600 text-white shadow-brand'
                    : 'text-gray-600 hover:bg-gray-100'
                ]"
              >
                {{ page }}
              </button>
            </div>

            <button
              :disabled="currentPage >= totalPages"
              @click="changePage(currentPage + 1)"
              class="px-4 py-2 rounded-xl border border-gray-200 text-sm font-semibold text-gray-600 hover:bg-gray-50 hover:border-gray-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一页
            </button>
          </div>

          <p class="mt-6 text-center text-sm text-gray-400">
            第 {{ currentPage }} 页，共 {{ totalPages }} 页
          </p>
        </template>
      </div>
    </main>

    <footer class="bg-white border-t border-gray-200 py-8">
      <div class="container mx-auto px-4 text-center">
        <p class="text-sm text-gray-400">© 2026 ROS小车教学网站. All rights reserved.</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import DOMPurify from 'dompurify'
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { BookOpen, ArrowRight } from 'lucide-vue-next'
import AppHeader from '@/components/AppHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { useUserStore } from '@/stores/user'
import { getTextbooks } from '@/api/textbook'
import { searchContent } from '@/api/search'
import type { SearchResultItem, Textbook } from '@/types/api'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const query = ref('')
const results = ref<SearchResultItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const totalPages = ref(1)
const textbooks = ref<Textbook[]>([])

const user = computed(() => userStore.userInfo)

const visiblePages = computed(() => {
  const pages: number[] = []
  const start = Math.max(1, currentPage.value - 2)
  const end = Math.min(totalPages.value, currentPage.value + 2)

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }

  return pages
})

const loadTextbooks = async () => {
  try {
    const data = await getTextbooks({ page_size: 100 })
    textbooks.value = data.items
  } catch {
    // API 拦截器已处理错误
  }
}

const performSearch = async () => {
  const q = route.query.q as string
  const page = parseInt(route.query.page as string) || 1

  if (!q) {
    results.value = []
    return
  }

  query.value = q
  currentPage.value = page
  loading.value = true

  try {
    const data = await searchContent({
      q: q,
      page: page,
      page_size: pageSize.value
    })

    results.value = data.results
    total.value = data.total
    totalPages.value = data.total_pages
  } catch {
    // API 拦截器已处理错误
  } finally {
    loading.value = false
  }
}

const highlightText = (text: string, searchQuery: string): string => {
  if (!searchQuery || !text) return text

  const regex = new RegExp(`(${escapeRegExp(searchQuery)})`, 'gi')
  return DOMPurify.sanitize(text.replace(regex, '<mark class="bg-yellow-200 text-inherit rounded px-0.5">$1</mark>'), { ALLOWED_TAGS: ['mark'] })
}

const escapeRegExp = (string: string): string => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

const changePage = (page: number) => {
  if (page < 1 || page > totalPages.value) return

  router.push({
    path: '/search',
    query: {
      q: query.value,
      page: page.toString()
    }
  })
}

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}

watch(() => route.query, () => {
  performSearch()
}, { immediate: true })

onMounted(() => {
  loadTextbooks()
  if (userStore.token && !userStore.userInfo) {
    userStore.getUserInfo()
  }
})
</script>
