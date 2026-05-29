<template>
  <div class="h-[calc(100vh-140px)] flex flex-col gap-4">
    <!-- 头部工具栏 -->
    <header class="w-[95%] mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0 bg-white p-4 rounded-2xl border border-gray-100 shadow-sm">
      <div class="flex items-center gap-4">
        <router-link 
          :to="`/admin/textbooks/${$route.params.id}`" 
          class="p-2 text-gray-400 hover:text-brand-600 hover:bg-gray-50 rounded-xl transition-all border border-transparent hover:border-brand-100"
        >
          <ArrowLeft class="w-5 h-5" />
        </router-link>
        <div v-if="chapter">
          <h1 class="text-sm font-bold text-gray-900 line-clamp-1">正在编辑：{{ chapter.title }}</h1>
          <p class="text-[10px] text-gray-400 mt-0.5">教材 ID: {{ $route.params.id }} · 章节 ID: {{ $route.params.chapterId }}</p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <!-- 移动端视图切换 -->
        <div class="lg:hidden flex bg-gray-100 p-1 rounded-xl">
          <button 
            v-for="v in ['edit', 'preview']" 
            :key="v"
            @click="activeView = v"
            class="px-4 py-1.5 rounded-lg text-xs font-bold transition-all"
            :class="[activeView === v ? 'bg-white text-brand-600 shadow-sm' : 'text-gray-500 hover:text-gray-700']"
          >
            {{ v === 'edit' ? '源码编辑' : '效果预览' }}
          </button>
        </div>
        
        <!-- 版本历史按钮 -->
        <router-link 
          :to="`/admin/textbooks/${$route.params.id}/history/${$route.params.chapterId}`"
          class="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-bold text-gray-500 hover:text-brand-600 hover:bg-gray-50 transition-all"
          title="查看版本历史"
        >
          <History class="w-4 h-4" />
          <span class="hidden sm:inline">版本历史</span>
        </router-link>
        
        <!-- 保存版本按钮 -->
        <button 
          @click="handleSaveVersion"
          :disabled="savingVersion"
          class="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-bold text-gray-500 hover:text-brand-600 hover:bg-gray-50 transition-all disabled:opacity-50"
          title="保存当前内容为新版本"
        >
          <GitCommit v-if="!savingVersion" class="w-4 h-4" />
          <Loader2 v-else class="w-4 h-4 animate-spin" />
          <span class="hidden sm:inline">保存版本</span>
        </button>
        
        <!-- 同步滚动开关 -->
        <button 
          @click="syncScrollEnabled = !syncScrollEnabled"
          class="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-bold transition-all"
          :class="[
            syncScrollEnabled 
              ? 'text-brand-600' 
              : 'text-gray-500'
          ]"
          :title="syncScrollEnabled ? '点击关闭同步滚动' : '点击开启同步滚动'"
        >
          <!-- 勾选框 -->
          <span 
            class="w-5 h-5 rounded border-2 flex items-center justify-center transition-all"
            :class="[
              syncScrollEnabled 
                ? 'bg-brand-600 border-brand-600' 
                : 'bg-white border-gray-300'
            ]"
          >
            <Check v-if="syncScrollEnabled" class="w-3 h-3 text-white" />
          </span>
          <span>同步滚动</span>
        </button>
        
        <button 
          @click="handleSave"
          :disabled="saving"
          class="flex items-center gap-2 px-6 py-2 bg-brand-600 text-white rounded-xl text-sm font-bold hover:bg-brand-500 transition-all shadow-brand hover:shadow-brand-lg disabled:opacity-50"
        >
          <Save v-if="!saving" class="w-4 h-4" />
          <Loader2 v-else class="w-4 h-4 animate-spin" />
          {{ saving ? '正在保存...' : '保存修改' }}
        </button>
      </div>
    </header>

    <!-- Markdown 工具栏 -->
    <div class="w-[95%] mx-auto bg-white border border-gray-100 rounded-2xl p-2 shadow-sm flex items-center justify-between shrink-0 overflow-hidden">
      <!-- 核心工具集 -->
      <div class="flex items-center gap-1 overflow-x-auto no-scrollbar">
        <button v-for="btn in coreTools" :key="btn.id" @click="handleToolClick(btn)" class="p-2 hover:bg-brand-50 text-gray-500 hover:text-brand-600 rounded-lg transition-all" :title="btn.label">
          <component :is="btn.icon" class="w-4 h-4" />
        </button>
        
        <!-- 分隔符 -->
        <div class="h-6 w-px bg-gray-100 mx-1 hidden sm:block"></div>
        
        <!-- 扩展工具集 (桌面端显示，移动端折叠) -->
        <div class="hidden sm:flex items-center gap-1">
          <button v-for="btn in extraTools" :key="btn.id" @click="handleToolClick(btn)" class="p-2 hover:bg-brand-50 text-gray-500 hover:text-brand-600 rounded-lg transition-all" :title="btn.label">
            <component :is="btn.icon" class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- 移动端折叠菜单 (sm 以下显示) -->
      <div class="sm:hidden relative">
        <button 
          @click="showMoreTools = !showMoreTools"
          class="p-2 hover:bg-gray-100 text-gray-400 rounded-lg transition-all"
        >
          <MoreVertical class="w-4 h-4" />
        </button>
        <transition name="zoom">
          <div v-if="showMoreTools" class="absolute right-0 top-full mt-2 w-48 bg-white rounded-2xl shadow-xl border border-gray-100 p-2 z-50">
            <button 
              v-for="btn in extraTools" 
              :key="btn.id" 
              @click="handleToolClick(btn); showMoreTools = false" 
              class="w-full text-left px-3 py-2 text-xs flex items-center gap-3 text-gray-600 hover:bg-brand-50 hover:text-brand-600 rounded-lg transition-all"
            >
              <component :is="btn.icon" class="w-4 h-4" />
              {{ btn.label }}
            </button>
          </div>
        </transition>
      </div>

      <!-- 快捷操作 -->
      <div class="hidden lg:flex items-center gap-2 pr-2">
        <span class="text-[10px] text-gray-400 font-bold uppercase tracking-widest">Markdown Editor</span>
      </div>
    </div>

    <!-- 编辑/预览 容器 -->
    <div class="w-[95%] mx-auto flex-1 flex gap-4 overflow-hidden min-h-0">
      <!-- 源码编辑区 -->
      <div 
        class="flex-1 bg-white border border-gray-100 rounded-2xl flex flex-col shadow-sm overflow-hidden"
        v-show="isLargeScreen || activeView === 'edit'"
      >
        <div class="flex-1 flex overflow-hidden">
          <!-- 行号列 -->
          <div 
            ref="lineNumbersRef"
            class="w-12 shrink-0 bg-gray-50/50 border-r border-gray-100 overflow-hidden select-none"
          >
            <div class="py-6 pr-2 text-right font-mono text-xs text-gray-400 leading-[24px]">
              <div v-for="line in lineCount" :key="line" class="h-6">{{ line }}</div>
            </div>
          </div>
          <!-- 文本编辑区 -->
          <textarea
            ref="editorRef"
            v-model="content"
            class="flex-1 p-6 pl-4 text-sm font-mono text-slate-700 bg-white focus:outline-none resize-none leading-[24px]"
            placeholder="# 在此输入 Markdown 内容..."
            @scroll="handleEditorScroll"
          ></textarea>
        </div>
        <div class="px-6 py-3 border-t border-gray-50 flex items-center justify-between shrink-0 bg-gray-50/30">
          <div class="text-[10px] text-gray-400 font-bold tracking-widest uppercase">Source Code</div>
          <div class="text-[10px] text-gray-400 font-bold uppercase">{{ content.length }} 字符 · {{ lineCount }} 行</div>
        </div>
      </div>

      <!-- 效果预览区 -->
      <div 
        class="flex-1 bg-white border border-gray-100 rounded-2xl flex flex-col shadow-sm overflow-hidden"
        v-show="isLargeScreen || activeView === 'preview'"
      >
        <div ref="previewRef" class="flex-1 overflow-y-auto p-6 scroll-smooth" @scroll="handlePreviewScroll">
          <MarkdownDisplay :content="content || '*预览内容为空*'" />
        </div>
        <div class="px-6 py-3 border-t border-gray-50 shrink-0 bg-gray-50/30">
          <div class="text-[10px] text-gray-400 font-bold tracking-widest uppercase">Live Preview</div>
        </div>
      </div>
    </div>

    <MediaPickerModal
      :visible="showMediaPicker"
      @close="showMediaPicker = false"
      @select="handleMediaSelected"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * @file Editor.vue
 * @description 响应式 Markdown 编辑器，支持工具栏折叠与分屏模式
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  ArrowLeft, 
  Save, 
  Loader2, 
  Bold, 
  Italic, 
  Heading1, 
  Heading2, 
  List, 
  ListOrdered, 
  Link, 
  Image as ImageIcon,
  Images, 
  Code, 
  Quote, 
  MoreVertical,
  Check,
  History,
  GitCommit 
} from 'lucide-vue-next'
import { getChapterById, updateChapter } from '@/api/chapter'
import { saveVersion } from '@/api/version'
import MarkdownDisplay from '@/components/MarkdownDisplay.vue'
import { useToast } from '@/composables/useToast'
import MediaPickerModal from '@/components/MediaPickerModal.vue'
import type { Media } from '@/types/api'

const route = useRoute()
const router = useRouter()
const toast = useToast()

const chapter = ref(null)
const content = ref('')
const loading = ref(true)
const saving = ref(false)
const savingVersion = ref(false)
const activeView = ref('edit') // edit | preview
const showMoreTools = ref(false)
const isLargeScreen = ref(window.innerWidth >= 1024)
const editorRef = ref<HTMLTextAreaElement | null>(null)
const lineNumbersRef = ref<HTMLDivElement | null>(null)
const previewRef = ref<HTMLDivElement | null>(null)
const isSyncing = ref(false)
const syncScrollEnabled = ref(true)  // 同步滚动开关，默认开启
const showMediaPicker = ref(false)

// Route change guard: close media picker when navigating between chapters
watch(() => route.params.chapterId, () => {
  showMediaPicker.value = false
})

/** 工具定义 */
const coreTools = [
  { id: 'bold', label: '加粗', icon: Bold, template: '**加粗文字**' },
  { id: 'italic', label: '斜体', icon: Italic, template: '*斜体文字*' },
  { id: 'h1', label: '一级标题', icon: Heading1, template: '# 一级标题\n' },
  { id: 'h2', label: '二级标题', icon: Heading2, template: '## 二级标题\n' },
]

const extraTools = [
  { id: 'list', label: '无序列表', icon: List, template: '- 列表项\n' },
  { id: 'ordered-list', label: '有序列表', icon: ListOrdered, template: '1. 列表项\n' },
  { id: 'link', label: '插入链接', icon: Link, template: '[链接名称](https://)' },
  { id: 'image', label: '插入图片链接', icon: ImageIcon, template: '![图片说明](https://)' },
  { id: 'code', label: '代码块', icon: Code, template: '```\n代码块\n```' },
  { id: 'quote', label: '引用', icon: Quote, template: '> 引用内容' },
  { id: 'media-picker', label: '从媒体库选择', icon: Images, action: 'image-picker' },
]

/** 行数计算 */
const lineCount = computed(() => {
  return (content.value || '').split('\n').length
})

/** 根据行号找到最接近的元素 */
const findClosestElementByLine = (targetLine: number): HTMLElement | null => {
  if (!previewRef.value) return null
  
  const allElements = previewRef.value.querySelectorAll('[data-source-line]')
  let closestElement: HTMLElement | null = null
  let closestDistance = Infinity
  
  allElements.forEach((el) => {
    const line = parseInt((el as HTMLElement).dataset.sourceLine || '0')
    const distance = Math.abs(line - targetLine)
    if (distance < closestDistance) {
      closestDistance = distance
      closestElement = el as HTMLElement
    }
  })
  
  return closestElement
}

/** 找到预览区当前可见的第一个块元素 */
const findFirstVisibleBlock = (): HTMLElement | null => {
  if (!previewRef.value) return null
  
  const containerRect = previewRef.value.getBoundingClientRect()
  const allElements = previewRef.value.querySelectorAll('[data-source-line]')
  
  for (const el of allElements) {
    const rect = (el as HTMLElement).getBoundingClientRect()
    // 元素顶部在容器可视范围内
    if (rect.top >= containerRect.top && rect.top <= containerRect.bottom) {
      return el as HTMLElement
    }
  }
  
  return (allElements[0] as HTMLElement) || null
}

/** 编辑区滚动 → 预览区同步 */
const syncScrollToPreview = () => {
  if (!isLargeScreen.value || isSyncing.value || !editorRef.value || !previewRef.value) return
  if (!syncScrollEnabled.value) return
  
  isSyncing.value = true
  
  // 1. 获取 textarea 实际行高（从 CSS computed style）
  const computedStyle = window.getComputedStyle(editorRef.value)
  const lineHeight = parseFloat(computedStyle.lineHeight) || 24
  
  // 2. 计算当前可见的第一行行号（0-based）
  const scrollTop = editorRef.value.scrollTop
  const firstVisibleLine = Math.floor(scrollTop / lineHeight)
  
  // 3. 找到预览区对应的元素
  const targetElement = findClosestElementByLine(firstVisibleLine)
  
  // 4. 滚动预览区，使目标元素在顶部显示
  if (targetElement) {
    targetElement.scrollIntoView({ behavior: 'instant', block: 'start' })
  }
  
  requestAnimationFrame(() => {
    isSyncing.value = false
  })
}

/** 预览区滚动 → 编辑区同步 */
const syncScrollToEditor = () => {
  if (!isLargeScreen.value || isSyncing.value || !editorRef.value || !previewRef.value) return
  if (!syncScrollEnabled.value) return
  
  isSyncing.value = true
  
  // 1. 找到预览区当前可见的第一个块元素
  const visibleElement = findFirstVisibleBlock()
  
  if (visibleElement) {
    // 2. 读取行号
    const line = parseInt(visibleElement.dataset.sourceLine || '0')
    
    // 3. 获取 textarea 实际行高
    const computedStyle = window.getComputedStyle(editorRef.value)
    const lineHeight = parseFloat(computedStyle.lineHeight) || 24
    
    // 4. 计算滚动位置，使该行在顶部显示
    editorRef.value.scrollTop = line * lineHeight
    
    // 5. 同时更新行号列
    if (lineNumbersRef.value) {
      lineNumbersRef.value.scrollTop = editorRef.value.scrollTop
    }
  }
  
  requestAnimationFrame(() => {
    isSyncing.value = false
  })
}

/** 处理编辑器滚动同步到行号列和预览区 */
const handleEditorScroll = () => {
  // 同步行号列
  if (lineNumbersRef.value && editorRef.value) {
    lineNumbersRef.value.scrollTop = editorRef.value.scrollTop
  }
  // 同步预览区
  syncScrollToPreview()
}

/** 处理预览区滚动同步到编辑区 */
const handlePreviewScroll = () => {
  syncScrollToEditor()
}

/** 处理窗口缩放 */
const handleResize = () => {
  isLargeScreen.value = window.innerWidth >= 1024
}

/** 处理工具栏按钮点击 */
function handleToolClick(btn: { id: string; label: string; icon: any; template?: string; action?: string }) {
  if (btn.action === 'image-picker') {
    showMediaPicker.value = true
  } else if (btn.template) {
    insertMarkdown(btn.template)
  }
}

/** 处理媒体选择器选中图片 */
function handleMediaSelected(media: Media) {
  const alt = media.original_name || '图片'
  const markdown = `![${alt}](${media.url})`
  insertMarkdown(markdown)
}

/** 插入 Markdown 模板 */
const insertMarkdown = (template: string) => {
  const textarea = editorRef.value
  if (!textarea) return
  
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const text = content.value
  
  content.value = text.substring(0, start) + template + text.substring(end)
  
  // 插入后保持焦点并重置光标位置
  setTimeout(() => {
    textarea.focus()
    textarea.selectionStart = textarea.selectionEnd = start + template.length
  }, 0)
}

/** 加载数据 */
const loadData = async () => {
  loading.value = true
  try {
    const data = await getChapterById(Number(route.params.chapterId))
    chapter.value = data
    content.value = data.content || ''
  } catch (error) {
    // API 拦截器已处理错误 toast
  } finally {
    loading.value = false
  }
}

/** 保存修改 */
const handleSave = async () => {
  saving.value = true
  try {
    await updateChapter(Number(route.params.chapterId), { 
      content: content.value,
      title: chapter.value?.title || '' 
    })
    toast.success('保存成功')
  } catch (error) {
    // API 拦截器已处理错误 toast
  } finally {
    saving.value = false
  }
}

/** 保存版本 */
const handleSaveVersion = async () => {
  if (!chapter.value) return
  savingVersion.value = true
  try {
    await saveVersion(chapter.value.id)
    toast.success('版本保存成功')
  } catch (error) {
    // API 拦截器已处理错误 toast
  } finally {
    savingVersion.value = false
  }
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
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

.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
