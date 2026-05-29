<template>
  <div class="h-[calc(100vh-140px)] flex flex-col gap-6">
    <!-- 头部：教材信息与全局操作 -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div class="flex items-center gap-4">
        <router-link 
          to="/admin/textbooks" 
          class="p-2 text-gray-400 hover:text-brand-600 hover:bg-white rounded-xl transition-all border border-transparent hover:border-brand-100"
        >
          <ArrowLeft class="w-5 h-5" />
        </router-link>
        <div v-if="textbook">
          <h1 class="text-xl font-bold text-gray-900 line-clamp-1">{{ textbook.title }}</h1>
          <p class="text-xs text-gray-400 mt-0.5">教材 ID: {{ textbook.id }} · 共 {{ flattenedChapters.length }} 个章节</p>
        </div>
      </div>
      
      <!-- 移动端视图切换 (lg 以下显示) -->
      <div class="lg:hidden flex bg-gray-100 p-1 rounded-xl">
        <button 
          v-for="v in ['tree', 'preview']" 
          :key="v"
          @click="activeView = v"
          class="flex-1 px-4 py-1.5 rounded-lg text-sm font-bold transition-all"
          :class="[activeView === v ? 'bg-white text-brand-600 shadow-sm' : 'text-gray-500 hover:text-gray-700']"
        >
          {{ v === 'tree' ? '目录树' : '内容预览' }}
        </button>
      </div>

      <div class="hidden sm:flex items-center gap-2">
        <!-- 一键整理按钮（非排序模式） -->
        <button 
          v-if="!isSortMode"
          class="flex items-center gap-2 px-4 py-2 bg-white text-gray-700 border border-gray-200 rounded-xl text-sm font-bold hover:bg-gray-50 transition-all shadow-sm"
          @click="enterSortMode"
        >
          <ListOrdered class="w-4 h-4" />
          一键整理
        </button>
        
        <!-- 撤回排序按钮（有快照时显示） -->
        <button 
          v-if="hasSortSnapshot && !isSortMode"
          class="flex items-center gap-2 px-4 py-2 bg-white text-gray-700 border border-gray-200 rounded-xl text-sm font-bold hover:bg-gray-50 transition-all shadow-sm"
          @click="handleUndoSort"
        >
          <Undo2 class="w-4 h-4" />
          撤回排序
        </button>
        
        <!-- 排序模式下的按钮 -->
        <template v-if="isSortMode">
          <button 
            class="flex items-center gap-2 px-4 py-2 bg-white text-gray-700 border border-gray-200 rounded-xl text-sm font-bold hover:bg-gray-50 transition-all shadow-sm"
            @click="selectAll"
          >
            全选
          </button>
          <button 
            class="flex items-center gap-2 px-4 py-2 bg-white text-gray-700 border border-gray-200 rounded-xl text-sm font-bold hover:bg-gray-50 transition-all shadow-sm"
            @click="deselectAll"
          >
            反选
          </button>
          <button 
            class="flex items-center gap-2 px-4 py-2 bg-brand-600 text-white rounded-xl text-sm font-bold hover:bg-brand-500 transition-all shadow-brand"
            @click="confirmSort"
          >
            确认排序
          </button>
          <button 
            class="flex items-center gap-2 px-4 py-2 bg-white text-gray-700 border border-gray-200 rounded-xl text-sm font-bold hover:bg-gray-50 transition-all shadow-sm"
            @click="cancelSort"
          >
            取消
          </button>
        </template>

        <input
          ref="mdFileInput"
          type="file"
          accept=".md"
          class="hidden"
          @change="handleMdFileSelected"
        />
        <button
          class="flex items-center gap-2 px-4 py-2 bg-white text-gray-700 border border-gray-200 rounded-xl text-sm font-bold hover:bg-gray-50 transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="mdUploading"
          @click="triggerMdUpload"
        >
          <Loader2 v-if="mdUploading" class="w-4 h-4 animate-spin" />
          <FileUp v-else class="w-4 h-4" />
          {{ mdUploading ? '上传中...' : '上传 MD' }}
        </button>
        <button 
          class="flex items-center gap-2 px-4 py-2 bg-white text-gray-700 border border-gray-200 rounded-xl text-sm font-bold hover:bg-gray-50 transition-all shadow-sm"
          @click="handleZipUpload"
        >
          <UploadCloud class="w-4 h-4" />
          ZIP 上传
        </button>
        <button
          v-if="textbook && textbook.status !== 'published' && isAdmin"
          class="flex items-center gap-2 px-4 py-2 bg-brand-600 text-white rounded-xl text-sm font-bold hover:bg-brand-500 transition-all shadow-brand"
          @click="openPublishConfirm"
        >
          <UploadCloud class="w-4 h-4" />
          发布
        </button>
        <button
          v-if="textbook && textbook.status === 'published' && isAdmin"
          class="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-xl text-sm font-bold hover:bg-red-500 transition-all shadow-sm"
          @click="openUnpublishConfirm"
        >
          <XCircle class="w-4 h-4" />
          取消发布
        </button>
      </div>
    </div>

    <!-- 主内容区：分栏/切换布局 -->
    <div class="flex-1 flex gap-6 overflow-hidden min-h-0">
      <!-- 左侧：目录树 (桌面端常驻，移动端受控) -->
      <aside 
        class="flex-1 lg:flex-none lg:w-80 bg-white border border-gray-100 rounded-2xl flex flex-col shadow-sm overflow-hidden"
        v-show="isLargeScreen || activeView === 'tree'"
      >
        <div class="p-4 border-b border-gray-50 flex items-center justify-between">
          <h2 class="text-sm font-bold text-gray-900 uppercase tracking-wider">章节结构</h2>
          <button 
            @click="openAddChapter"
            class="p-1.5 text-brand-600 hover:bg-brand-50 rounded-lg transition-all"
            title="添加根章节"
          >
            <PlusCircle class="w-4 h-4" />
          </button>
        </div>
        
        <div class="flex-1 overflow-y-auto p-4 space-y-1">
          <div v-if="loading" class="py-12 flex flex-col items-center gap-2">
            <LoadingSpinner size="sm" />
            <span class="text-[10px] text-gray-400 font-medium">加载目录...</span>
          </div>
          
          <template v-else-if="rootChapters.length > 0">
            <!-- 桌面端使用拖拽 -->
            <draggable
              v-if="isLargeScreen"
              v-model="localRootChapters"
              item-key="id"
              handle=".drag-handle"
              ghost-class="opacity-50"
              animation="200"
              :group="{ name: 'chapters' }"
              :empty-insert-threshold="20"
              :swap-threshold="0.65"
              :fallback-on-body="true"
              @change="handleRootDragChange"
            >
              <template #item="{ element }">
                <div :data-chapter-id="element.id">
                  <TreeNode
                    :node="element"
                    :active-node-id="activeChapterId"
                    :editable="true"
                    :draggable="true"
                    :all-chapters="chapters"
                    :show-checkbox="isSortMode"
                    :selected-ids="selectedChapterIds"
                    @select="handleChapterClick"
                    @edit="handleChapterAction($event, 'edit')"
                    @delete="handleChapterAction($event, 'delete')"
                    @move-up="handleMoveUp"
                    @move-down="handleMoveDown"
                    @reorder="handleCrossLevelReorder"
                    @drag-preview="handleDragPreview"
                    @toggle-select="handleToggleSelect"
                  />
                </div>
              </template>
            </draggable>
            <!-- 移动端/平板端不使用拖拽 -->
            <template v-else>
              <TreeNode
                v-for="chapter in rootChapters"
                :key="chapter.id"
                :node="chapter"
                :active-node-id="activeChapterId"
                :editable="true"
                :all-chapters="chapters"
                :show-checkbox="isSortMode"
                :selected-ids="selectedChapterIds"
                @select="handleChapterClick"
                @edit="handleChapterAction($event, 'edit')"
                @delete="handleChapterAction($event, 'delete')"
                @move-up="handleMoveUp"
                @move-down="handleMoveDown"
                @reorder="handleCrossLevelReorder"
                @drag-preview="handleDragPreview"
                @toggle-select="handleToggleSelect"
              />
            </template>
          </template>
          
          <div v-else class="py-12 text-center">
            <p class="text-xs text-gray-400 italic">暂无章节内容</p>
          </div>
        </div>
      </aside>

      <!-- 右侧：预览区 (桌面端常驻，移动端受控) -->
      <section 
        class="flex-1 bg-white border border-gray-100 rounded-2xl flex flex-col shadow-sm overflow-hidden"
        v-show="isLargeScreen || activeView === 'preview'"
      >
        <template v-if="selectedChapter">
          <div class="p-4 border-b border-gray-50 flex items-center justify-between shrink-0">
            <h2 class="text-sm font-bold text-gray-900 truncate pr-4">{{ selectedChapter.title }}</h2>
            <div v-if="selectedChapter.node_type === 'article'" class="flex items-center gap-2">
              <router-link 
                :to="`/admin/textbooks/${textbook.id}/history/${selectedChapter.id}`"
                class="flex items-center gap-2 px-4 py-1.5 bg-gray-100 text-gray-700 rounded-lg text-xs font-bold hover:bg-gray-200 transition-all"
              >
                <History class="w-3.5 h-3.5" />
                版本历史
              </router-link>
              <router-link 
                :to="`/admin/textbooks/${textbook.id}/edit/${selectedChapter.id}`"
                class="flex items-center gap-2 px-4 py-1.5 bg-brand-600 text-white rounded-lg text-xs font-bold hover:bg-brand-500 transition-all shadow-brand"
              >
                <Edit3 class="w-3.5 h-3.5" />
                编辑此页
              </router-link>
            </div>
          </div>
          <div class="flex-1 overflow-y-auto p-6">
            <div v-if="loadingContent" class="py-20 flex flex-col items-center gap-4">
              <LoadingSpinner size="md" />
              <p class="text-xs text-gray-400 animate-pulse">正在获取详情...</p>
            </div>
            <MarkdownDisplay v-else :content="selectedChapter.content || '# 请添加内容'" />
          </div>
        </template>
        
        <div v-else class="flex-1 flex flex-col items-center justify-center p-12 text-center">
          <div class="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mb-6">
            <Eye class="w-10 h-10 text-gray-200" />
          </div>
          <h3 class="text-lg font-bold text-gray-900 mb-2">章节预览</h3>
          <p class="text-sm text-gray-400 max-w-xs">请从左侧目录树中选择一个章节，在此实时预览其 Markdown 渲染内容。</p>
        </div>
      </section>
    </div>

    <!-- 创建章节弹窗 -->
    <Modal 
      v-model:visible="createModalVisible" 
      title="添加章节"
      width="480px"
    >
      <div class="space-y-4">
        <FormInput
          v-model="createForm.title"
          label="章节标题"
          placeholder="请输入章节标题"
          :error="createErrors.title"
        />
        <FormSelect
          v-model="createForm.node_type"
          label="节点类型"
          :options="nodeTypeOptions"
        />
        <div class="space-y-1.5">
          <label class="text-sm font-medium text-gray-700">父章节（可选）</label>
          <CascadeSelect
            v-model="createForm.parent_id"
            :chapters="chapters"
            placeholder="无（根章节）"
          />
          <p class="text-xs text-gray-400">
            留空表示创建根章节，选择父章节后创建子章节
          </p>
        </div>
      </div>
      <template #footer>
        <button 
          @click="createModalVisible = false"
          class="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
        >
          取消
        </button>
        <button 
          @click="handleSubmitCreate"
          :disabled="createLoading"
          class="flex items-center gap-2 px-4 py-2 text-sm font-bold text-white bg-brand-600 hover:bg-brand-500 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Loader2 v-if="createLoading" class="w-4 h-4 animate-spin" />
          {{ createLoading ? '创建中...' : '创建' }}
        </button>
      </template>
    </Modal>

    <!-- 编辑章节弹窗 -->
    <Modal 
      v-model:visible="editModalVisible" 
      title="编辑章节"
      width="560px"
    >
      <div v-if="editLoading && !editForm.title" class="py-8 flex justify-center">
        <LoadingSpinner size="sm" />
      </div>
      <div v-else class="space-y-4">
        <FormInput
          v-model="editForm.title"
          label="章节标题"
          placeholder="请输入章节标题"
          :error="editErrors.title"
        />
        <div class="space-y-1.5">
          <label class="text-sm font-medium text-gray-700">父章节（可选）</label>
          <CascadeSelect
            v-model="editForm.parent_id"
            :chapters="chapters"
            placeholder="无（根章节）"
          />
          <p class="text-xs text-gray-400">
            留空表示根章节，选择父章节后移动为子章节
          </p>
        </div>
      </div>
      <template #footer>
        <button 
          @click="editModalVisible = false"
          class="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
        >
          取消
        </button>
        <button 
          @click="handleSubmitEdit"
          :disabled="editLoading"
          class="flex items-center gap-2 px-4 py-2 text-sm font-bold text-white bg-brand-600 hover:bg-brand-500 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Loader2 v-if="editLoading" class="w-4 h-4 animate-spin" />
          {{ editLoading ? '保存中...' : '保存' }}
        </button>
      </template>
    </Modal>

    <!-- ZIP 上传弹窗 -->
    <Modal 
      v-model:visible="zipModalVisible" 
      title="上传 Markdown ZIP"
      width="480px"
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            选择压缩文件
          </label>
          <input 
            type="file"
            accept=".zip,.tar,.tar.gz,.tgz,.tar.bz2,.tbz2,.tar.xz,.txz,.7z,.rar"
            @change="handleFileChange"
            class="block w-full text-sm text-gray-500
              file:mr-4 file:py-2 file:px-4
              file:rounded-lg file:border-0
              file:text-sm file:font-medium
              file:bg-brand-50 file:text-brand-700
              hover:file:bg-brand-100
              file:cursor-pointer file:transition-colors"
          />
          <p class="mt-1 text-xs text-gray-400">
            支持 ZIP / RAR / 7z / TAR / TAR.GZ / TAR.BZ2 / TAR.XZ，最大 100MB
          </p>
        </div>

        <!-- 上传进度区域 -->
        <div v-if="zipLoading" class="space-y-2">
          <div class="relative w-full h-2 bg-gray-200 rounded-full overflow-hidden">
            <div 
              class="absolute top-0 left-0 h-full rounded-full transition-all duration-300"
              :class="isProcessing ? 'bg-amber-500' : 'bg-brand-500'"
              :style="{ width: (isProcessing ? serverProgress : uploadProgress) + '%' }"
            />
          </div>
          <div class="flex items-center justify-between text-xs">
            <template v-if="!isProcessing">
              <span class="text-gray-600">上传中 {{ uploadProgress }}%</span>
              <span class="flex items-center gap-3 text-gray-400">
                <span v-if="uploadSpeed">{{ uploadSpeed }}</span>
                <span v-if="uploadEta">{{ uploadEta }}</span>
              </span>
            </template>
            <template v-else>
              <span class="flex items-center gap-1.5 text-amber-600">
                <Loader2 class="w-3 h-3 animate-spin" />
                {{ stageLabels[serverStage] || '处理中' }} {{ serverProgress }}%
              </span>
              <span></span>
            </template>
          </div>
        </div>
        
        <p class="text-xs text-gray-400">
          ZIP 内的 Markdown 文件将作为章节导入到当前教材「{{ textbook?.title }}」
        </p>
      </div>
      <template #footer>
        <button 
          @click="zipModalVisible = false"
          class="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
        >
          取消
        </button>
        <button 
          @click="handleZipSubmit"
          :disabled="zipLoading || !selectedFile"
          class="flex items-center gap-2 px-4 py-2 text-sm font-bold text-white bg-brand-600 hover:bg-brand-500 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Loader2 v-if="zipLoading" class="w-4 h-4 animate-spin" />
          {{ zipLoading ? '上传中...' : '确认上传' }}
        </button>
      </template>
    </Modal>

    <!-- 发布确认弹窗 -->
    <ConfirmDialog
      v-model:visible="publishConfirmVisible"
      title="发布教材"
      message="确定要发布此教材吗？发布后，教材将对所有用户可见。"
      type="warning"
      confirm-text="确认发布"
      @confirm="handlePublishConfirm"
    />

    <!-- 取消发布确认弹窗 -->
    <ConfirmDialog
      v-model:visible="unpublishConfirmVisible"
      title="取消发布"
      message="确定要取消发布此教材吗？取消后，教材将对普通用户不可见。"
      type="danger"
      confirm-text="确认取消发布"
      @confirm="handleUnpublishConfirm"
    />

    <!-- 排序预览弹窗 -->
    <SortPreviewModal
      v-if="sortPreviewData"
      :visible="showSortPreview"
      :preview-data="sortPreviewData"
      :current-tree="chapters"
      @confirm="handleSortConfirm"
      @cancel="handleSortCancel"
    />

    <!-- 拖拽预览确认横幅 -->
    <div 
      v-if="hasUnsavedChanges" 
      class="fixed bottom-4 right-4 bg-yellow-100 border border-yellow-300 rounded-lg p-4 shadow-lg z-40 max-w-sm"
    >
      <div class="flex items-start gap-3">
        <AlertCircle class="w-5 h-5 text-yellow-600 mt-0.5 shrink-0" />
        <div class="flex-1">
          <p class="text-sm font-medium text-yellow-800 mb-3">
            您修改了章节结构，是否保存？
          </p>
          <div class="flex gap-2">
            <button 
              @click="confirmDragChanges"
              class="px-3 py-1.5 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-500 transition-colors"
            >
              保存
            </button>
            <button 
              @click="cancelDragChanges"
              class="px-3 py-1.5 bg-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-300 transition-colors"
            >
              撤销
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @file ContentManager.vue
 * @description 教材内容管理，支持移动端单栏切换与桌面端双栏分屏
 */
import { ref, reactive, onMounted, computed, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { 
  ArrowLeft, 
  UploadCloud, 
  PlusCircle, 
  Edit3, 
  Eye, 
  Loader2,
  FileUp,
  XCircle,
  History,
  ListOrdered,
  Undo2,
  AlertCircle,
} from 'lucide-vue-next'
import { getTextbookById, publishTextbook, unpublishTextbook } from '@/api/textbook'
import { getChapters, getChapterById, deleteChapter, createChapter, updateChapter, reorderChapters, undoSort, previewSort, applySort } from '@/api/chapter'
import { uploadMarkdown, uploadSingleMarkdown, pollUploadStatus } from '@/api/upload'
import TreeNode from '@/components/TreeNode.vue'
import Modal from '@/components/Modal.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import FormInput from '@/components/FormInput.vue'
import FormSelect from '@/components/FormSelect.vue'
import CascadeSelect from '@/components/CascadeSelect.vue'
import type { NodeType, SortPreviewResponse, OrderItem, ChapterReorderItem, ChapterTreeNode } from '@/types/api'
import MarkdownDisplay from '@/components/MarkdownDisplay.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import SortPreviewModal from '@/components/SortPreviewModal.vue'
import draggable from 'vuedraggable'
import { useToast } from '@/composables/useToast'
import { useUserStore } from '@/stores/user'

/**
 * 排序确认载荷
 */
interface SortConfirmPayload {
  orders: OrderItem[]
  deletedIds: number[]
  deletedFolderNumbers: number[]
}

const route = useRoute()
const toast = useToast()
const userStore = useUserStore()

const loading = ref(true)
const loadingContent = ref(false)
const textbook = ref(null)
const chapters = ref([])
const selectedChapter = ref(null)
const activeChapterId = computed(() => selectedChapter.value?.id ?? null)
const activeView = ref('tree') // tree | preview
const isLargeScreen = ref(window.innerWidth >= 1024)

// 创建章节弹窗状态
const createModalVisible = ref(false)
const createLoading = ref(false)
const createForm = reactive({
  title: '',
  parent_id: '' as string | null,
  node_type: 'folder' as NodeType
})
const createErrors = reactive({
  title: ''
})

// 编辑章节弹窗状态
const editModalVisible = ref(false)
const editLoading = ref(false)
const editingChapter = ref(null)
const editForm = reactive({
  title: '',
  content: '',
  node_type: 'folder',
  parent_id: '' as string | null
})
const editErrors = reactive({
  title: ''
})

// ZIP 上传弹窗状态
const zipModalVisible = ref(false)
const zipLoading = ref(false)
const selectedFile = ref(null)

// 上传进度状态
const uploadProgress = ref(0)
const uploadSpeed = ref('')
const uploadEta = ref('')
let uploadStartTime = 0
let lastLoaded = 0
let lastTime = 0

// 服务端处理状态
const serverStage = ref('')
const serverProgress = ref(0)
const isProcessing = ref(false)

function formatSpeed(bytesPerSecond: number): string {
  if (bytesPerSecond >= 1048576) return (bytesPerSecond / 1048576).toFixed(1) + ' MB/s'
  if (bytesPerSecond >= 1024) return (bytesPerSecond / 1024).toFixed(1) + ' KB/s'
  return bytesPerSecond.toFixed(0) + ' B/s'
}
function formatEta(seconds: number): string {
  if (seconds < 1) return '即将完成'
  if (seconds < 60) return `约 ${Math.ceil(seconds)} 秒`
  return `约 ${Math.ceil(seconds / 60)} 分钟`
}
const stageLabels: Record<string, string> = {
  extracting: '解压文件中',
  importing: '导入章节中',
  sorting: '生成预览中',
  done: '完成',
}

// 发布确认弹窗状态
const publishConfirmVisible = ref(false)
const publishLoading = ref(false)

// 取消发布确认弹窗状态
const unpublishConfirmVisible = ref(false)
const unpublishLoading = ref(false)

// 单 MD 上传状态
const mdUploading = ref(false)
const mdFileInput = ref(null)

// 排序模式状态
const isSortMode = ref(false)
const selectedChapterIds = ref<number[]>([])
const hasSortSnapshot = ref(false)

// 排序预览弹窗状态
const sortPreviewData = ref<SortPreviewResponse | null>(null)
const showSortPreview = ref(false)

// 本地章节树状态（用于拖拽预览）
const localChapterTree = ref<ChapterTreeNode[]>([])
const originalChapterTree = ref<ChapterTreeNode[]>([])

/**
 * 处理窗口缩放，同步屏幕状态
 */
const handleResize = () => {
  isLargeScreen.value = window.innerWidth >= 1024
}

/**
 * 处理浏览器关闭/导航事件
 * 当有未保存更改时提示用户
 */
const handleBeforeUnload = (e: BeforeUnloadEvent) => {
  if (hasUnsavedChanges.value) {
    e.preventDefault()
    e.returnValue = ''
    return ''
  }
}

/**
 * 平铺后的章节列表 (统计用)
 */
const flattenedChapters = computed(() => {
  const result = []
  const flatten = (list) => {
    for (const item of list) {
      result.push(item)
      if (item.children) flatten(item.children)
    }
  }
  flatten(chapters.value)
  return result
})

/**
 * 顶级章节列表（目录树入口）
 */
const rootChapters = computed(() => {
  return chapters.value.filter(chapter => !chapter.parent_id)
})

/**
 * 根级别章节的可写模型（用于 vuedraggable）
 * 绑定到 localChapterTree 以支持预览模式
 */
const localRootChapters = computed({
  get: () => {
    return localChapterTree.value.filter(node => node.parent_id === null)
  },
  set: (newValue) => {
    // 创建新根节点的 ID 集合
    const newRootIds = new Set(newValue.map(n => n.id))

    // 直接更新新根节点的 parent_id
    newValue.forEach(node => {
      node.parent_id = null
    })

    // 从原有的 localChapterTree 中过滤掉已经被移到根级别的节点
    const nonRootChapters = localChapterTree.value.filter(node => !newRootIds.has(node.id))
    localChapterTree.value = [...newValue, ...nonRootChapters]
  }
})

/**
 * 当前选中的父章节层级
 * 用于控制 node_type 选项的可用性
 */
const selectedParentLevel = computed(() => {
  if (!createForm.parent_id) return -1
  const parent = flattenedChapters.value.find(ch => String(ch.id) === createForm.parent_id)
  return parent?.level ?? -1
})

/**
 * 节点类型选项（选择二级目录时隐藏文件夹选项）
 */
const nodeTypeOptions = computed(() => {
  const options: Array<{ value: NodeType; label: string }> = [
    { value: 'folder', label: '文件夹（目录）' },
    { value: 'article', label: '文章' }
  ]
  
  // If parent is level 2+, exclude folder option (would create level 3+ folder, exceeds 3-level limit)
  if (selectedParentLevel.value >= 2) {
    return options.filter(opt => opt.value !== 'folder')
  }
  
  return options
})

/**
 * 当父章节改变时，自动切换节点类型
 * 如果当前选中的节点类型不在可用选项中，自动切换到第一个可用选项
 */
watch(selectedParentLevel, () => {
  const availableTypes = nodeTypeOptions.value.map(opt => opt.value)
  if (!availableTypes.includes(createForm.node_type)) {
    createForm.node_type = availableTypes[0] || 'article'
  }
})

/**
 * 深拷贝章节树，避免循环引用
 */
const deepCloneChapters = (chapters: ChapterTreeNode[]): ChapterTreeNode[] => {
  const seen = new WeakMap()
  
  const clone = (node: ChapterTreeNode): ChapterTreeNode => {
    if (seen.has(node)) {
      return seen.get(node)
    }
    
    const cloned: ChapterTreeNode = {
      ...node,
      children: node.children ? node.children.map(clone) : []
    }
    
    seen.set(node, cloned)
    return cloned
  }
  
  return chapters.map(clone)
}

/**
 * 同步章节树到本地状态
 */
watch(chapters, () => {
  if (chapters.value && chapters.value.length > 0) {
    localChapterTree.value = deepCloneChapters(chapters.value)
    originalChapterTree.value = deepCloneChapters(chapters.value)
  }
}, { immediate: true, deep: true })

/**
 * 用户是否是管理员（super_admin 或 admin）
 */
const isAdmin = computed(() => {
  return userStore.role === 'super_admin' || userStore.role === 'admin'
})

/**
 * 比较两个章节树是否相同
 */
const areTreesEqual = (tree1: ChapterTreeNode[], tree2: ChapterTreeNode[]): boolean => {
  if (tree1.length !== tree2.length) return false
  
  const compareNodes = (node1: ChapterTreeNode, node2: ChapterTreeNode): boolean => {
    if (node1.id !== node2.id) return false
    if (node1.title !== node2.title) return false
    if (node1.parent_id !== node2.parent_id) return false
    if (node1.order_index !== node2.order_index) return false
    
    const children1 = node1.children || []
    const children2 = node2.children || []
    
    if (children1.length !== children2.length) return false
    
    return children1.every((child, index) => compareNodes(child, children2[index]))
  }
  
  return tree1.every((node, index) => compareNodes(node, tree2[index]))
}

/**
 * 是否有未保存的章节结构更改
 */
const hasUnsavedChanges = computed(() => {
  return !areTreesEqual(localChapterTree.value, originalChapterTree.value)
})

/**
 * 刷新章节目录
 */
const loadChapters = async () => {
  const textbookId = Number(route.params.id)
  const cData = await getChapters(textbookId)
  chapters.value = cData.chapters || []

  if (selectedChapter.value) {
    const latest = flattenedChapters.value.find(ch => ch.id === selectedChapter.value.id)
    if (latest) {
      selectedChapter.value = { ...latest, content: selectedChapter.value.content }
      return
    }
  }

  if (chapters.value.length > 0) {
    await selectChapter(chapters.value[0])
  } else {
    selectedChapter.value = null
  }
}

/**
 * 加载教材与目录
 */
const loadData = async () => {
  loading.value = true
  try {
    const textbookId = Number(route.params.id)
    const tData = await getTextbookById(textbookId)
    textbook.value = tData
    await loadChapters()
  } catch (error) {
    // API 拦截器已处理错误 toast
  } finally {
    loading.value = false
  }
}

/**
 * 选择并加载章节内容
 */
const selectChapter = async (chapter) => {
  selectedChapter.value = chapter
  loadingContent.value = true
  try {
    const data = await getChapterById(chapter.id)
    selectedChapter.value = { ...chapter, content: data.content }
    // 移动端选择后切换到预览
    if (!isLargeScreen.value) {
      activeView.value = 'preview'
    }
  } catch (error) {
    // API 拦截器已处理错误 toast
  } finally {
    loadingContent.value = false
  }
}

/**
 * TreeNode 点击章节时的兼容入口
 */
const handleChapterClick = (chapter) => {
  selectChapter(chapter)
}

/**
 * 章节操作
 */
const openAddChapter = () => {
  createForm.title = ''
  createForm.parent_id = ''
  createForm.node_type = 'folder'
  createErrors.title = ''
  createModalVisible.value = true
}

/**
 * 验证创建表单
 */
const validateCreateForm = () => {
  let isValid = true
  createErrors.title = ''
  if (!createForm.title.trim()) {
    createErrors.title = '请输入章节标题'
    isValid = false
  }
  return isValid
}

/**
 * 提交创建章节
 */
const handleSubmitCreate = async () => {
  if (!validateCreateForm()) return
  
  createLoading.value = true
  try {
    await createChapter({
      textbook_id: Number(route.params.id),
      title: createForm.title.trim(),
      parent_id: createForm.parent_id ? Number(createForm.parent_id) : null,
      node_type: createForm.node_type
    })
    toast.success('章节创建成功')
    createModalVisible.value = false
    loadData()
  } catch (error) {
    // API 拦截器已处理错误 toast
  } finally {
    createLoading.value = false
  }
}

const handleChapterAction = async (chapter, action) => {
  if (action === 'delete') {
    if (confirm(`确定要删除章节《${chapter.title}》吗？`)) {
      try {
        await deleteChapter(chapter.id)
        toast.success('删除成功')
        loadData()
      } catch (error) {}
    }
  } else if (action === 'add') {
    // 添加子章节，预设父章节
    createForm.title = ''
    createForm.parent_id = String(chapter.id)
    createForm.node_type = 'folder'
    createErrors.title = ''
    createModalVisible.value = true
  } else if (action === 'edit') {
    openEditModal(chapter)
  }
}

/**
 * 打开编辑章节弹窗
 */
const openEditModal = async (chapter) => {
  editingChapter.value = chapter
  editErrors.title = ''
  editLoading.value = true
  editModalVisible.value = true
  
  try {
    // 获取完整章节数据
    const data = await getChapterById(chapter.id)
    editForm.title = data.title || ''
    editForm.content = data.content || ''
    editForm.node_type = data.node_type || 'folder'
    editForm.parent_id = String(data.parent_id || '')
  } catch (error) {
    // API 拦截器已处理错误 toast
    editModalVisible.value = false
  } finally {
    editLoading.value = false
  }
}

/**
 * 验证编辑表单
 */
const validateEditForm = () => {
  let isValid = true
  editErrors.title = ''
  if (!editForm.title.trim()) {
    editErrors.title = '请输入章节标题'
    isValid = false
  }
  return isValid
}

/**
 * 提交编辑章节
 */
const handleSubmitEdit = async () => {
  if (!validateEditForm()) return
  
  editLoading.value = true
  try {
    const updateData: { title: string; parent_id?: number | null } = {
      title: editForm.title.trim()
    }
    
    // 只在 parent_id 变更时提交该字段
    const originalParentId = String(editingChapter.value?.parent_id || '')
    if (editForm.parent_id !== originalParentId) {
      // 处理根章节（null 或空字符串都表示移到根级别）
      if (editForm.parent_id === '' || editForm.parent_id === null) {
        updateData.parent_id = null
      } else {
        updateData.parent_id = Number(editForm.parent_id)
      }
    }
    
    await updateChapter(editingChapter.value.id, updateData)
    toast.success('章节更新成功')
    editModalVisible.value = false
    loadData()
  } catch (error) {
    // API 拦截器已处理错误 toast
  } finally {
    editLoading.value = false
  }
}

/**
 * 处理 ZIP 上传按钮点击
 */
const handleZipUpload = () => {
  selectedFile.value = null
  zipModalVisible.value = true
}

/**
 * 处理文件选择变化
 */
const handleFileChange = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
  }
}

/**
 * 提交 ZIP 上传
 */
const handleZipSubmit = async () => {
  if (!selectedFile.value) {
    toast.error('请选择 ZIP 文件')
    return
  }
  
  // 重置进度状态
  uploadProgress.value = 0
  uploadSpeed.value = ''
  uploadEta.value = ''
  serverStage.value = ''
  serverProgress.value = 0
  isProcessing.value = false
  uploadStartTime = Date.now()
  lastLoaded = 0
  lastTime = Date.now()
  
  zipLoading.value = true
  try {
    const { task_id } = await uploadMarkdown(
      selectedFile.value,
      textbook.value?.title || '未命名教材',
      Number(route.params.id),
      (percent, loaded, total) => {
        uploadProgress.value = percent
        const now = Date.now()
        const timeDiff = (now - lastTime) / 1000
        const bytesDiff = loaded - lastLoaded
        if (timeDiff > 0.3) {
          const speed = timeDiff > 0 ? bytesDiff / timeDiff : 0
          uploadSpeed.value = formatSpeed(speed)
          if (speed > 0) uploadEta.value = formatEta((total - loaded) / speed)
          lastLoaded = loaded
          lastTime = now
        }
      }
    )
    
    uploadProgress.value = 100
    isProcessing.value = true
    
    const status = await pollUploadStatus(task_id, (s) => {
      serverStage.value = s.stage
      serverProgress.value = s.progress
    })
    
    zipModalVisible.value = false
    
    // 如果有排序预览数据，显示预览弹窗
    if (status.result?.sort_preview) {
      sortPreviewData.value = status.result.sort_preview
      showSortPreview.value = true
    } else {
      toast.success('上传成功')
      await loadChapters()
    }
  } catch (error: any) {
    toast.error(error?.message || '上传处理失败，请重试')
  } finally {
    zipLoading.value = false
    uploadProgress.value = 0
    isProcessing.value = false
  }
}

const triggerMdUpload = () => {
  mdFileInput.value?.click()
}

const handleMdFileSelected = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  event.target.value = ''

  mdUploading.value = true
  try {
    await uploadSingleMarkdown(file, Number(route.params.id))
    toast.success('Markdown 上传成功')
    loadData()
  } catch {
    // API 拦截器已处理错误 toast
  } finally {
    mdUploading.value = false
  }
}

/**
 * 打开发布确认弹窗
 */
const openPublishConfirm = () => {
  publishConfirmVisible.value = true
}

/**
 * 确认发布教材
 */
const handlePublishConfirm = async () => {
  if (!textbook.value) return
  
  publishLoading.value = true
  try {
    const updatedTextbook = await publishTextbook(textbook.value.id)
    textbook.value = updatedTextbook
    toast.success('教材发布成功')
    publishConfirmVisible.value = false
  } catch (error) {
    // API 拦截器已处理错误 toast
  } finally {
    publishLoading.value = false
  }
}

/**
 * 打开取消发布确认弹窗
 */
const openUnpublishConfirm = () => {
  unpublishConfirmVisible.value = true
}

/**
 * 确认取消发布教材
 */
const handleUnpublishConfirm = async () => {
  if (!textbook.value) return
  
  unpublishLoading.value = true
  try {
    const updatedTextbook = await unpublishTextbook(textbook.value.id)
    textbook.value = updatedTextbook
    toast.success('已取消发布')
    unpublishConfirmVisible.value = false
  } catch (error) {
    // API 拦截器已处理错误 toast
  } finally {
    unpublishLoading.value = false
  }
}

/**
 * 获取同级兄弟章节列表
 */
const getSiblings = (chapter) => {
  const parentId = chapter.parent_id
  const siblings = flattenedChapters.value.filter(ch => ch.parent_id === parentId)
  // 按 order_index 排序
  return siblings.sort((a, b) => (a.order_index || 0) - (b.order_index || 0))
}

/**
 * 处理章节上移
 */
const handleMoveUp = async (chapter) => {
  const siblings = getSiblings(chapter)
  const currentIndex = siblings.findIndex(s => s.id === chapter.id)
  
  // 如果是第一个，无法上移
  if (currentIndex <= 0) {
    toast.error('已经是第一个章节，无法上移')
    return
  }
  
  // 交换 order_index
  const prevChapter = siblings[currentIndex - 1]
  const orders = [
    { id: chapter.id, order_index: prevChapter.order_index || currentIndex - 1, parent_id: chapter.parent_id },
    { id: prevChapter.id, order_index: chapter.order_index || currentIndex, parent_id: prevChapter.parent_id }
  ]
  
  try {
    await reorderChapters(Number(route.params.id), orders)
    toast.success('移动成功')
    await loadChapters()
  } catch (error) {
    // API 拦截器已处理错误 toast
  }
}

/**
 * 处理章节下移
 */
const handleMoveDown = async (chapter) => {
  const siblings = getSiblings(chapter)
  const currentIndex = siblings.findIndex(s => s.id === chapter.id)
  
  // 如果是最后一个，无法下移
  if (currentIndex >= siblings.length - 1) {
    toast.error('已经是最后一个章节，无法下移')
    return
  }
  
  // 交换 order_index
  const nextChapter = siblings[currentIndex + 1]
  const orders = [
    { id: chapter.id, order_index: nextChapter.order_index || currentIndex + 1, parent_id: chapter.parent_id },
    { id: nextChapter.id, order_index: chapter.order_index || currentIndex, parent_id: nextChapter.parent_id }
  ]
  
  try {
    await reorderChapters(Number(route.params.id), orders)
    toast.success('移动成功')
    await loadChapters()
  } catch (error) {
    // API 拦截器已处理错误 toast
  }
}

/**
 * 处理根级别拖拽变化
 * vuedraggable 会自动更新 localChapterTree，我们只需要确认是否有实际变化
 */
const handleRootDragChange = (event) => {
  // vuedraggable 已经通过 v-model 更新了 localChapterTree
  // hasUnsavedChanges 会自动检测变化并显示确认 UI
  
  // 这里不需要额外处理，用户会看到保存/撤销按钮
}

/**
 * 查找指定父节点的所有子节点
 * @param list - 章节列表
 * @param parentId - 父节点 ID，null 表示根级别
 * @returns 子节点数组
 */
const findChapterChildren = (list, parentId) => {
  if (parentId === null) {
    // 根级别章节
    return [...list]
  }
  // 查找父节点并返回其 children
  const findParent = (nodes) => {
    for (const node of nodes) {
      if (node.id === parentId) return node.children || []
      if (node.children) {
        const found = findParent(node.children)
        if (found) return found
      }
    }
    return []
  }
  return findParent(list)
}

/**
 * 处理跨层级拖拽重排序
 * @param payload - { chapterId, newParentId, newIndex, error? }
 * 
 * 注意：在预览模式下，此方法不调用 API，仅更新本地状态
 */
const handleCrossLevelReorder = async (payload) => {
  if (payload.error) {
    if (payload.error === 'ARTICLE_CANNOT_HAVE_CHILDREN') {
      toast.error('文章节点不能包含子节点')
    } else if (payload.error === 'LEVEL_LIMIT_EXCEEDED') {
      toast.error('层级超出限制，最多支持三级章节')
    } else if (payload.error === 'CIRCULAR_REFERENCE') {
      toast.error('不能将父节点拖入其子节点下')
    }
    await loadChapters()
    return
  }

  // 1. 刷新数据（确保数据一致性）
  await loadChapters()
  
  // 2. 找到目标父节点的所有子节点
  const targetChildren = findChapterChildren(chapters.value, payload.newParentId)
  
  // 3. 找到被拖拽的节点，移到正确位置
  const draggedIndex = targetChildren.findIndex(ch => ch.id === payload.chapterId)
  if (draggedIndex !== -1 && draggedIndex !== payload.newIndex) {
    const [dragged] = targetChildren.splice(draggedIndex, 1)
    targetChildren.splice(payload.newIndex, 0, dragged)
  }
  
  // 4. 构建 orders（只包含目标父节点的子节点）
  const orders = targetChildren.map((ch, i) => ({
    id: ch.id,
    order_index: i,
    parent_id: payload.newParentId
  }))
  
}

/**
 * 处理拖拽预览事件
 * 更新本地章节树状态，不立即调用 API
 */
const handleDragPreview = (payload: any) => {
  // payload 包含: { chapterId, newParentId, newIndex }
  
  // 找到被拖拽的章节节点
  const findAndRemoveChapter = (nodes: ChapterTreeNode[], chapterId: number): ChapterTreeNode | null => {
    for (let i = 0; i < nodes.length; i++) {
      if (nodes[i].id === chapterId) {
        const [removed] = nodes.splice(i, 1)
        return removed
      }
      if (nodes[i].children) {
        const found = findAndRemoveChapter(nodes[i].children!, chapterId)
        if (found) return found
      }
    }
    return null
  }
  
  // 移除被拖拽的节点
  const draggedNode = findAndRemoveChapter(localChapterTree.value, payload.chapterId)
  
  if (!draggedNode) {
    toast.error('找不到被拖拽的章节')
    return
  }
  
  // 更新 parent_id
  draggedNode.parent_id = payload.newParentId
  
  // 找到目标位置并插入
  if (payload.newParentId === null) {
    // 插入到根级别
    localChapterTree.value.splice(payload.newIndex, 0, draggedNode)
  } else {
    // 找到父节点
    const findParent = (nodes: ChapterTreeNode[], parentId: number): ChapterTreeNode | null => {
      for (const node of nodes) {
        if (node.id === parentId) return node
        if (node.children) {
          const found = findParent(node.children, parentId)
          if (found) return found
        }
      }
      return null
    }
    
    const parentNode = findParent(localChapterTree.value, payload.newParentId)
    if (parentNode) {
      if (!parentNode.children) {
        parentNode.children = []
      }
      parentNode.children.splice(payload.newIndex, 0, draggedNode)
    }
  }
  
  // hasUnsavedChanges 会自动检测变化并显示确认 UI
  toast.info('章节位置已更改，请点击保存按钮确认')
}

/**
 * 进入排序模式
 */
function enterSortMode() {
  isSortMode.value = true
  // 默认全选
  selectedChapterIds.value = flattenedChapters.value.map(ch => ch.id)
}

/**
 * 全选所有章节
 */
function selectAll() {
  selectedChapterIds.value = flattenedChapters.value.map(ch => ch.id)
}

/**
 * 反选所有章节
 */
function deselectAll() {
  selectedChapterIds.value = []
}

/**
 * 确认排序（预览排序结果）
 * 调用 previewSort API 获取排序预览数据，并打开预览弹窗
 */
async function confirmSort() {
  if (!textbook.value) return
  
  try {
    const result = await previewSort(
      textbook.value.id,
      selectedChapterIds.value.length > 0 ? selectedChapterIds.value : null
    )
    sortPreviewData.value = result
    showSortPreview.value = true
  } catch (error) {
    // API 拦截器已处理错误 toast
  }
}

/**
 * 取消排序模式
 */
function cancelSort() {
  isSortMode.value = false
  selectedChapterIds.value = []
}

/**
 * 处理排序预览确认
 * 应用用户在预览弹窗中调整后的排序
 * @param payload - 排序确认载荷，包含排序项和删除信息
 */
async function handleSortConfirm(payload: SortConfirmPayload) {
  if (!textbook.value) return
  
  try {
    await applySort(
      textbook.value.id,
      selectedChapterIds.value.length > 0 ? selectedChapterIds.value : null,
      payload.orders,
      payload.deletedIds,
      payload.deletedFolderNumbers
    )
    toast.success('排序应用成功')
    showSortPreview.value = false
    isSortMode.value = false
    selectedChapterIds.value = []
    hasSortSnapshot.value = true  // 有快照可撤回
    await loadChapters()
  } catch (error) {
    // API 拦截器已处理错误 toast
  }
}

/**
 * 处理排序预览取消
 */
function handleSortCancel() {
  showSortPreview.value = false
}

/**
 * 撤回智能排序
 */
async function handleUndoSort() {
  if (!textbook.value) return
  
  try {
    await undoSort(textbook.value.id)
    toast.success('撤回成功')
    await loadChapters()
    hasSortSnapshot.value = false
  } catch (error) {
    // API 拦截器已处理错误 toast
  }
}

/**
 * 处理章节选择切换
 * @param chapterId - 章节ID
 */
function handleToggleSelect(chapterId: number) {
  const index = selectedChapterIds.value.indexOf(chapterId)
  if (index > -1) {
    selectedChapterIds.value.splice(index, 1)
  } else {
    selectedChapterIds.value.push(chapterId)
  }
}

/**
 * 构建排序顺序数组
 */
const buildOrders = (tree: ChapterTreeNode[], parentId: number | null = null): ChapterReorderItem[] => {
  const orders: ChapterReorderItem[] = []
  tree.forEach((node, index) => {
    orders.push({
      id: node.id,
      order_index: index,
      parent_id: parentId
    })
    if (node.children && node.children.length > 0) {
      orders.push(...buildOrders(node.children, node.id))
    }
  })
  return orders
}

/**
 * 确认保存拖拽更改
 */
const confirmDragChanges = async () => {
  if (!textbook.value) return
  
  try {
    const orders = buildOrders(localChapterTree.value)
    await reorderChapters(Number(route.params.id), orders)
    toast.success('章节顺序已更新')
    // 更新快照
    originalChapterTree.value = deepCloneChapters(localChapterTree.value)
  } catch (error) {
    // API 拦截器已处理错误 toast
  }
}

/**
 * 取消拖拽更改
 */
const cancelDragChanges = () => {
  localChapterTree.value = deepCloneChapters(originalChapterTree.value)
  toast.info('已撤销更改')
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('beforeunload', handleBeforeUnload)
})
</script>
