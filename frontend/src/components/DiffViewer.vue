<script setup lang="ts">
/**
 * DiffViewer - 差异对比组件
 *
 * @description 支持行级差异对比的组件，提供并排和统一两种视图模式。
 * 使用 LCS（最长公共子序列）算法实现差异计算。
 *
 * @example
 * <DiffViewer
 *   :old-content="oldText"
 *   :new-content="newText"
 *   mode="split"
 *   :show-line-numbers="true"
 * />
 */
import { computed, ref } from 'vue'
import { Columns, List, Copy, Check, AlertTriangle } from 'lucide-vue-next'

/** 性能限制：最大行数 */
const MAX_LINES = 1000

/** Diff 行类型 */
type DiffType = 'added' | 'removed' | 'unchanged'

/** Diff 行数据结构 */
interface DiffLine {
  type: DiffType
  content: string
  oldLineNumber: number | null
  newLineNumber: number | null
}

/** Props 类型定义 */
interface Props {
  /** 旧版本内容 */
  oldContent: string
  /** 新版本内容 */
  newContent: string
  /** 对比模式：split(并排) | unified(统一) */
  mode?: 'split' | 'unified'
  /** 是否显示行号 */
  showLineNumbers?: boolean
  /** 旧版本标题 */
  oldTitle?: string
  /** 新版本标题 */
  newTitle?: string
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'split',
  showLineNumbers: true,
  oldTitle: '旧版本',
  newTitle: '新版本'
})

/** 当前显示模式 */
const currentMode = ref<'split' | 'unified'>(props.mode)

/** 复制成功状态 */
const copySuccess = ref<string | null>(null)

/**
 * 计算 LCS（最长公共子序列）
 * 用于确定两段文本的差异
 */
function computeLCS(oldLines: string[], newLines: string[]): number[][] {
  const m = oldLines.length
  const n = newLines.length
  const dp: number[][] = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0))

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (oldLines[i - 1] === newLines[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1])
      }
    }
  }

  return dp
}

/**
 * 基于 LCS 生成差异行
 */
function generateDiffLines(oldLines: string[], newLines: string[], dp: number[][]): DiffLine[] {
  const result: DiffLine[] = []
  let i = oldLines.length
  let j = newLines.length

  // 从后向前遍历，构建 diff 结果
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && oldLines[i - 1] === newLines[j - 1]) {
      result.unshift({
        type: 'unchanged',
        content: oldLines[i - 1],
        oldLineNumber: i,
        newLineNumber: j
      })
      i--
      j--
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      result.unshift({
        type: 'added',
        content: newLines[j - 1],
        oldLineNumber: null,
        newLineNumber: j
      })
      j--
    } else if (i > 0) {
      result.unshift({
        type: 'removed',
        content: oldLines[i - 1],
        oldLineNumber: i,
        newLineNumber: null
      })
      i--
    }
  }

  return result
}

/**
 * 检查文件是否超过行数限制
 */
const isOversized = computed(() => {
  const oldLines = props.oldContent.split('\n')
  const newLines = props.newContent.split('\n')
  return oldLines.length > MAX_LINES || newLines.length > MAX_LINES
})

/**
 * 计算差异结果
 * 当文件超过 MAX_LINES 时，截断输入以避免性能问题
 */
const diffResult = computed(() => {
  const oldLines = props.oldContent.split('\n')
  const newLines = props.newContent.split('\n')

  // 性能保护：限制处理的行数
  const limitedOldLines = oldLines.slice(0, MAX_LINES)
  const limitedNewLines = newLines.slice(0, MAX_LINES)

  const dp = computeLCS(limitedOldLines, limitedNewLines)
  return generateDiffLines(limitedOldLines, limitedNewLines, dp)
})

/** 统计信息 */
const stats = computed(() => {
  const added = diffResult.value.filter(d => d.type === 'added').length
  const removed = diffResult.value.filter(d => d.type === 'removed').length
  const unchanged = diffResult.value.filter(d => d.type === 'unchanged').length
  return { added, removed, unchanged }
})

/**
 * 获取行的样式类
 */
function getLineClasses(type: DiffType): string {
  const baseClasses = 'font-mono text-sm leading-6 whitespace-pre-wrap break-all'
  const typeClasses: Record<DiffType, string> = {
    added: 'bg-green-50 text-green-800 border-l-4 border-green-500',
    removed: 'bg-red-50 text-red-800 border-l-4 border-red-500 line-through',
    unchanged: 'text-gray-700'
  }
  return `${baseClasses} ${typeClasses[type]}`
}

/**
 * 获取行号单元格样式
 */
function getLineNumberClasses(type: DiffType): string {
  const baseClasses = 'text-right px-2 py-0.5 text-xs select-none font-mono w-12 shrink-0'
  const typeClasses: Record<DiffType, string> = {
    added: 'bg-green-100 text-green-600',
    removed: 'bg-red-100 text-red-400',
    unchanged: 'bg-gray-50 text-gray-400'
  }
  return `${baseClasses} ${typeClasses[type]}`
}

/**
 * 切换显示模式
 */
function toggleMode() {
  currentMode.value = currentMode.value === 'split' ? 'unified' : 'split'
}

/**
 * 复制内容到剪贴板
 */
async function copyToClipboard(text: string, label: string) {
  try {
    await navigator.clipboard.writeText(text)
    copySuccess.value = label
    setTimeout(() => {
      copySuccess.value = null
    }, 2000)
  } catch {
    // 复制失败，静默处理
  }
}

/**
 * 获取并排模式的旧版本行
 */
const splitOldLines = computed(() => {
  const result: DiffLine[] = []
  diffResult.value.forEach(line => {
    if (line.type === 'removed' || line.type === 'unchanged') {
      result.push(line)
    } else if (line.type === 'added') {
      // 为添加的行在旧版本中插入占位符
      result.push({
        type: 'unchanged',
        content: '',
        oldLineNumber: null,
        newLineNumber: null
      })
    }
  })
  return result
})

/**
 * 获取并排模式的新版本行
 */
const splitNewLines = computed(() => {
  const result: DiffLine[] = []
  diffResult.value.forEach(line => {
    if (line.type === 'added' || line.type === 'unchanged') {
      result.push(line)
    } else if (line.type === 'removed') {
      // 为删除的行在新版本中插入占位符
      result.push({
        type: 'unchanged',
        content: '',
        oldLineNumber: null,
        newLineNumber: null
      })
    }
  })
  return result
})
</script>

<template>
  <div class="diff-viewer w-full rounded-xl border border-gray-200 bg-white overflow-hidden">
    <!-- 工具栏 -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-gray-50/50">
      <!-- 统计信息 -->
      <div class="flex items-center gap-4 text-sm">
        <span class="flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-green-500"></span>
          <span class="text-gray-600">+{{ stats.added }} 行</span>
        </span>
        <span class="flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-red-500"></span>
          <span class="text-gray-600">-{{ stats.removed }} 行</span>
        </span>
        <span v-if="stats.unchanged > 0" class="text-gray-400">
          · {{ stats.unchanged }} 行不变
        </span>
      </div>

      <!-- 模式切换 -->
      <div class="flex items-center gap-2">
        <button
          @click="toggleMode"
          class="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-lg transition-colors"
          :class="currentMode === 'split' ? 'bg-brand-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
        >
          <Columns class="w-4 h-4" />
          并排
        </button>
        <button
          @click="toggleMode"
          class="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-lg transition-colors"
          :class="currentMode === 'unified' ? 'bg-brand-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
        >
          <List class="w-4 h-4" />
          统一
        </button>
      </div>
    </div>

    <!-- 性能警告 -->
    <div
      v-if="isOversized"
      class="flex items-center gap-2 px-4 py-2 bg-amber-50 border-b border-amber-200 text-amber-700 text-sm"
    >
      <AlertTriangle class="w-4 h-4 flex-shrink-0" />
      <span>
        文件过大（超过 {{ MAX_LINES }} 行），已截断显示以保证性能。完整内容请下载查看。
      </span>
    </div>

    <!-- 并排模式 -->
    <div v-if="currentMode === 'split'" class="flex divide-x divide-gray-200">
      <!-- 旧版本 -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center justify-between px-4 py-2 bg-red-50/50 border-b border-gray-100">
          <span class="text-sm font-medium text-gray-700">{{ oldTitle }}</span>
          <button
            @click="copyToClipboard(oldContent, 'old')"
            class="p-1 rounded hover:bg-gray-200 transition-colors"
            :title="copySuccess === 'old' ? '已复制' : '复制'"
          >
            <Check v-if="copySuccess === 'old'" class="w-4 h-4 text-green-500" />
            <Copy v-else class="w-4 h-4 text-gray-400" />
          </button>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <tbody>
              <tr
                v-for="(line, index) in splitOldLines"
                :key="`old-${index}`"
                :class="line.type === 'removed' ? 'bg-red-50' : ''"
              >
                <td v-if="showLineNumbers" :class="getLineNumberClasses(line.type)">
                  {{ line.oldLineNumber || '' }}
                </td>
                <td :class="getLineClasses(line.type)">
                  {{ line.content || ' ' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 新版本 -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center justify-between px-4 py-2 bg-green-50/50 border-b border-gray-100">
          <span class="text-sm font-medium text-gray-700">{{ newTitle }}</span>
          <button
            @click="copyToClipboard(newContent, 'new')"
            class="p-1 rounded hover:bg-gray-200 transition-colors"
            :title="copySuccess === 'new' ? '已复制' : '复制'"
          >
            <Check v-if="copySuccess === 'new'" class="w-4 h-4 text-green-500" />
            <Copy v-else class="w-4 h-4 text-gray-400" />
          </button>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <tbody>
              <tr
                v-for="(line, index) in splitNewLines"
                :key="`new-${index}`"
                :class="line.type === 'added' ? 'bg-green-50' : ''"
              >
                <td v-if="showLineNumbers" :class="getLineNumberClasses(line.type)">
                  {{ line.newLineNumber || '' }}
                </td>
                <td :class="getLineClasses(line.type)">
                  {{ line.content || ' ' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 统一模式 -->
    <div v-else class="overflow-x-auto">
      <table class="w-full">
        <tbody>
          <tr
            v-for="(line, index) in diffResult"
            :key="`unified-${index}`"
            :class="{
              'bg-red-50': line.type === 'removed',
              'bg-green-50': line.type === 'added'
            }"
          >
            <td
              v-if="showLineNumbers"
              :class="getLineNumberClasses(line.type)"
            >
              {{ line.oldLineNumber || '' }}
            </td>
            <td
              v-if="showLineNumbers"
              :class="getLineNumberClasses(line.type)"
            >
              {{ line.newLineNumber || '' }}
            </td>
            <td class="px-2 py-0.5 text-xs font-mono text-center w-8 shrink-0">
              <span v-if="line.type === 'added'" class="text-green-600 font-bold">+</span>
              <span v-else-if="line.type === 'removed'" class="text-red-600 font-bold">-</span>
              <span v-else class="text-gray-300"> </span>
            </td>
            <td :class="getLineClasses(line.type)">
              {{ line.content || ' ' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 空状态 -->
    <div
      v-if="diffResult.length === 0"
      class="flex flex-col items-center justify-center py-12 text-gray-400"
    >
      <List class="w-12 h-12 mb-2 opacity-50" />
      <p class="text-sm">无内容差异</p>
    </div>
  </div>
</template>

<style scoped>
.diff-viewer {
  font-family: var(--font-family-mono, 'JetBrains Mono', 'Fira Code', monospace);
}

/* 代码高亮过渡效果 */
.diff-viewer tbody tr {
  transition: background-color 0.15s ease;
}

/* 滚动条样式 */
.diff-viewer ::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.diff-viewer ::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.diff-viewer ::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.diff-viewer ::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
