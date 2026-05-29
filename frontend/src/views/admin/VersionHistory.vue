<template>
  <div class="h-[calc(100vh-140px)] flex flex-col gap-6">
    <!-- 头部：返回和标题 -->
    <div class="flex items-center justify-between">
      <div>
        <div class="flex items-center gap-2 text-sm text-gray-400 mb-1">
          <router-link to="/admin/textbooks" class="hover:text-brand-600 transition-colors">
            教材管理
          </router-link>
          <ChevronRight class="w-4 h-4" />
          <span class="text-gray-600">版本历史</span>
        </div>
        <h1 class="text-2xl font-bold text-gray-900">版本历史</h1>
        <p class="text-sm text-gray-500 mt-1">查看章节的历史版本并恢复到任意版本</p>
      </div>
      <router-link
        v-if="chapterId"
        :to="`/admin/textbooks/${textbookId}/edit/${chapterId}`"
        class="flex items-center justify-center gap-2 px-4 py-2.5 bg-gray-100 text-gray-700 rounded-xl font-bold hover:bg-gray-200 transition-all"
      >
        <ArrowLeft class="w-4 h-4" />
        返回编辑
      </router-link>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex-1 py-20 flex flex-col items-center justify-center bg-white rounded-2xl border">
      <LoadingSpinner size="lg" />
      <p class="text-gray-400 text-sm mt-4 animate-pulse">正在加载版本历史...</p>
    </div>

    <!-- 主内容区：双栏布局 -->
    <div v-else class="flex-1 flex gap-6 overflow-hidden min-h-0">
      <!-- 左侧版本列表 (1/4 宽度) -->
      <aside class="w-1/4 min-w-[320px] bg-white rounded-2xl border overflow-hidden flex flex-col">
        <div class="p-4 border-b flex items-center justify-between">
          <h2 class="text-lg font-bold text-gray-900">版本列表</h2>
          <span
            v-if="selectedVersions.length > 0"
            class="text-sm text-gray-500"
          >
            已选 {{ selectedVersions.length }}/2
          </span>
        </div>

        <!-- 无数据 -->
        <div v-if="versions.length === 0" class="flex-1 flex flex-col items-center justify-center py-12 text-center">
          <div class="w-12 h-12 bg-gray-50 rounded-full flex items-center justify-center mb-3">
            <History class="w-6 h-6 text-gray-300" />
          </div>
          <p class="text-gray-400 text-sm font-medium">暂无版本记录</p>
        </div>

        <!-- 版本列表 -->
        <div v-else class="flex-1 overflow-y-auto">
          <div
            v-for="version in versions"
            :key="version.id"
            class="p-4 border-b last:border-b-0 hover:bg-gray-50/50 transition-colors cursor-pointer"
            :class="{
              'bg-brand-50/30': version.version_num === currentVersionNum,
              'bg-brand-50': selectedVersions.includes(version.id)
            }"
            @click="toggleVersionSelection(version.id)"
          >
            <div class="flex items-start gap-3">
              <!-- 选择框 -->
              <input
                type="checkbox"
                :checked="selectedVersions.includes(version.id)"
                :disabled="selectedVersions.length >= 2 && !selectedVersions.includes(version.id)"
                class="mt-1 w-4 h-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                @click.stop
                @change="toggleVersionSelection(version.id)"
              />

              <!-- 版本信息 -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <div
                    class="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold"
                    :class="version.version_num === currentVersionNum
                      ? 'bg-brand-600 text-white'
                      : 'bg-gray-100 text-gray-600'"
                  >
                    v{{ version.version_num }}
                  </div>
                  <span
                    v-if="version.version_num === currentVersionNum"
                    class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-brand-600 text-white"
                  >
                    当前
                  </span>
                </div>
                <div class="text-xs text-gray-400 mb-2">
                  {{ formatDateTime(version.created_at) }}
                </div>
                <div class="text-sm text-gray-600 line-clamp-2">
                  {{ getContentPreview(version.content) }}
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="flex items-center gap-1">
                <button
                  @click.stop="openDetailModal(version)"
                  class="p-1.5 text-gray-400 hover:text-brand-600 hover:bg-brand-50 rounded-lg transition-all"
                  title="查看详情"
                >
                  <Eye class="w-4 h-4" />
                </button>
                <button
                  v-if="version.version_num !== currentVersionNum"
                  @click.stop="openRestoreConfirm(version)"
                  class="p-1.5 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-all"
                  title="恢复此版本"
                >
                  <RotateCcw class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          <!-- 分页 -->
          <div v-if="total > queryParams.page_size" class="p-4 border-t flex items-center justify-center gap-3">
            <button
              :disabled="queryParams.page === 1"
              @click="changePage(queryParams.page - 1)"
              class="p-1.5 rounded-lg border border-gray-200 disabled:opacity-30 hover:bg-gray-50 transition-all"
            >
              <ChevronLeft class="w-4 h-4" />
            </button>
            <span class="text-xs font-bold text-gray-600">
              {{ queryParams.page }} / {{ Math.ceil(total / queryParams.page_size) }}
            </span>
            <button
              :disabled="queryParams.page * queryParams.page_size >= total"
              @click="changePage(queryParams.page + 1)"
              class="p-1.5 rounded-lg border border-gray-200 disabled:opacity-30 hover:bg-gray-50 transition-all"
            >
              <ChevronRight class="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      <!-- 右侧 DiffViewer 预览 (3/4 宽度) -->
      <section class="flex-1 bg-white rounded-2xl border overflow-hidden flex flex-col">
        <div class="p-4 border-b flex items-center justify-between">
          <h2 class="text-lg font-bold text-gray-900">版本对比</h2>
          <div v-if="selectedVersions.length === 2 && diffData" class="text-sm text-gray-500">
            版本 {{ diffData.from_version?.version_num }} → 版本 {{ diffData.to_version?.version_num }}
          </div>
        </div>

        <div class="flex-1 overflow-auto p-4">
          <!-- 单版本预览模式 -->
          <template v-if="previewVersion && selectedVersions.length < 2">
            <div class="mb-4 text-sm text-gray-500">
              预览：版本 {{ previewVersion.version_num }}
            </div>
            <MarkdownDisplay :content="previewVersion.content || '# 无内容'" />
          </template>
          
          <!-- 双版本对比模式 -->
          <template v-else-if="selectedVersions.length === 2">
            <!-- 加载中 -->
            <div
              v-if="loadingDiff"
              class="h-full flex flex-col items-center justify-center"
            >
              <LoadingSpinner size="lg" />
              <p class="text-gray-400 text-sm mt-4">正在加载版本差异...</p>
            </div>
            
            <!-- DiffViewer -->
            <DiffViewer
              v-else-if="diffData?.from_version && diffData?.to_version"
              :old-content="diffData.from_version.content || ''"
              :new-content="diffData.to_version.content || ''"
              :old-title="`版本 ${diffData.from_version.version_num}`"
              :new-title="`版本 ${diffData.to_version.version_num}`"
              mode="split"
            />
            
            <!-- 加载失败 -->
            <div v-else class="h-full flex items-center justify-center text-gray-400">
              <p class="text-sm">加载版本差异失败，请重新选择版本</p>
            </div>
          </template>
          
          <!-- 未选择提示 -->
          <div v-else class="h-full flex flex-col items-center justify-center text-gray-400">
            <GitCompare class="w-12 h-12 mb-4 opacity-30" />
            <p class="text-sm">点击预览按钮查看单个版本，或勾选两个版本进行对比</p>
          </div>
        </div>
      </section>
    </div>

    <!-- 恢复确认弹窗 -->
    <ConfirmDialog
      v-model:visible="restoreConfirmVisible"
      title="恢复版本"
      :message="`确定要将章节恢复到版本 ${restoreTarget?.version_num} 吗？当前版本将被保存为新版本。`"
      type="warning"
      confirm-text="确认恢复"
      @confirm="handleRestore"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  History,
  Eye,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  GitCompare
} from 'lucide-vue-next'
import { getVersionHistory, restoreVersion, compareVersions } from '@/api/version'
import { getChapterById } from '@/api/chapter'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import DiffViewer from '@/components/DiffViewer.vue'
import MarkdownDisplay from '@/components/MarkdownDisplay.vue'
import { useToast } from '@/composables/useToast'
import type { Version, VersionDiffResponse } from '@/types/api'

const route = useRoute()
const toast = useToast()

const loading = ref(true)
const versions = ref<Version[]>([])
const total = ref(0)
const currentVersionNum = ref<number | null>(null)

const queryParams = reactive({
  page: 1,
  page_size: 20
})

/** 版本预览（单版本模式） */
const previewVersion = ref<Version | null>(null)

/** 恢复确认弹窗 */
const restoreConfirmVisible = ref(false)
const restoreTarget = ref<Version | null>(null)
const restoreLoading = ref(false)

/** 版本对比选择 */
const selectedVersions = ref<number[]>([])
const diffData = ref<VersionDiffResponse | null>(null)
const loadingDiff = ref(false)

/** 切换版本选择并自动加载对比 */
async function toggleVersionSelection(versionId: number) {
  const index = selectedVersions.value.indexOf(versionId)
  if (index > -1) {
    selectedVersions.value.splice(index, 1)
    diffData.value = null
  } else if (selectedVersions.value.length < 2) {
    selectedVersions.value.push(versionId)
  }

  // 选择两个版本后自动加载对比，并清除单版本预览
  if (selectedVersions.value.length === 2 && chapterId.value) {
    previewVersion.value = null
    await loadDiff()
  }
}

/** 加载版本差异 */
async function loadDiff() {
  if (selectedVersions.value.length !== 2 || !chapterId.value) return

  loadingDiff.value = true
  diffData.value = null

  try {
    const fromId = selectedVersions.value[0]
    const toId = selectedVersions.value[1]
    diffData.value = await compareVersions(chapterId.value, fromId, toId)
  } catch (error) {
    // API 拦截器已处理错误 toast
  } finally {
    loadingDiff.value = false
  }
}

/** 路由参数 */
const chapterId = computed(() => {
  const id = route.params.chapterId
  return id ? Number(id) : null
})

const textbookId = computed(() => {
  const id = route.params.id
  return id ? Number(id) : null
})

/** 加载版本历史 */
const loadData = async () => {
  if (!chapterId.value) {
    loading.value = false
    return
  }

  loading.value = true
  try {
    const [versionData] = await Promise.all([
      getVersionHistory(chapterId.value, queryParams)
    ])

    versions.value = versionData.versions
    total.value = versionData.total

    // 从版本列表推断当前版本号（最新版本）
    if (versions.value.length > 0) {
      currentVersionNum.value = Math.max(...versions.value.map(v => v.version_num))
    }
  } catch {
    // API 拦截器已处理错误 toast
  } finally {
    loading.value = false
  }
}

/** 分页处理 */
const changePage = (newPage: number) => {
  queryParams.page = newPage
  loadData()
}

/** 格式化日期时间 */
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/** 获取内容预览 */
const getContentPreview = (content: string | null) => {
  if (!content) return '（无内容）'
  // 移除 Markdown 标记，取前 80 字符
  const plainText = content
    .replace(/#{1,6}\s/g, '')
    .replace(/\*\*/g, '')
    .replace(/\*/g, '')
    .replace(/`/g, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/\n/g, ' ')
    .trim()

  return plainText.length > 80 ? plainText.slice(0, 80) + '...' : plainText
}

/** 预览版本（在右侧显示） */
const openDetailModal = (version: Version) => {
  // 清除版本选择
  selectedVersions.value = []
  diffData.value = null
  // 设置预览版本
  previewVersion.value = version
}

/** 打开恢复确认弹窗 */
const openRestoreConfirm = (version: Version) => {
  restoreTarget.value = version
  restoreConfirmVisible.value = true
}

/** 执行恢复 */
const handleRestore = async () => {
  if (!chapterId.value || !restoreTarget.value) return

  restoreLoading.value = true
  try {
    await restoreVersion(chapterId.value, restoreTarget.value.id)
    toast.success(`已恢复到版本 ${restoreTarget.value.version_num}`)
    restoreConfirmVisible.value = false
    // 重新加载数据
    await loadData()
  } catch {
    // API 拦截器已处理错误 toast
  } finally {
    restoreLoading.value = false
  }
}

/** 监听路由参数变化 */
watch(() => route.params.chapterId, () => {
  queryParams.page = 1
  selectedVersions.value = []
  diffData.value = null
  previewVersion.value = null
  loadData()
})

onMounted(loadData)
</script>
