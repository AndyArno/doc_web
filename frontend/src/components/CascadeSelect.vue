<template>
  <div class="relative" ref="containerRef">
    <!-- Trigger Button -->
    <button
      ref="triggerRef"
      type="button"
      data-testid="cascade-trigger"
      role="combobox"
      :aria-haspopup="'listbox'"
      :aria-expanded="isOpen"
      :disabled="disabled"
      :class="[
        'w-full flex items-center justify-between rounded-lg border px-3.5 py-2.5 text-sm text-left transition-all focus:outline-none',
        disabled
          ? 'cursor-not-allowed bg-gray-100 text-gray-400 border-gray-200'
          : isOpen
            ? 'border-brand-500 ring-2 ring-brand-500/50 bg-white'
            : 'border-gray-200 bg-white hover:border-gray-300 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/50'
      ]"
      @click="toggleDropdown"
      @keydown.enter.prevent="handleTriggerEnter"
      @keydown.escape.prevent="closeDropdown"
    >
      <span class="truncate">
        <template v-if="displayLabel">
          {{ displayLabel }}
        </template>
        <template v-else-if="placeholder">
          {{ placeholder }}
        </template>
        <template v-else>
          请选择父章节
        </template>
      </span>
      <ChevronDown
        :size="16"
        :class="[
          'ml-2 shrink-0 text-gray-400 transition-transform',
          isOpen && !disabled ? 'rotate-180' : ''
        ]"
      />
    </button>

    <!-- Dropdown Menu (teleported to body to escape overflow clipping) -->
    <Teleport to="body">
      <div
        v-if="isOpen"
        ref="dropdownRef"
        data-testid="cascade-dropdown"
        role="listbox"
        tabindex="-1"
        class="fixed z-[9999] bg-white border border-gray-200 rounded-lg shadow-lg max-h-80 overflow-auto"
        :style="{
          top: `${dropdownPosition.top}px`,
          left: `${dropdownPosition.left}px`,
          width: `${dropdownPosition.width}px`
        }"
        @keydown.escape.prevent="closeDropdown"
      >
      <!-- "无（根章节）" option - always visible -->
      <div
        data-testid="cascade-root-option"
        :class="[
          'flex items-center justify-between py-2.5 px-3 text-sm cursor-pointer transition-colors border-b border-gray-100',
          modelValue === null
            ? 'bg-brand-50 text-brand-600 font-medium'
            : 'text-gray-700 hover:bg-gray-50'
        ]"
        @click.stop="selectRoot"
      >
        <span>无（根章节）</span>
        <button
          type="button"
          data-testid="select-root-btn"
          class="px-2 py-0.5 text-xs text-brand-600 hover:text-brand-700 hover:bg-brand-100 rounded transition-colors"
          @click.stop="selectRoot"
        >
          选择
        </button>
      </div>

      <!-- Breadcrumb Navigation with Back Button -->
      <div
        v-if="currentPath.length > 0"
        data-testid="cascade-breadcrumb"
        class="flex items-center gap-2 py-2 px-3 text-xs border-b border-gray-100 bg-gray-50"
      >
        <!-- Back Button -->
        <button
          type="button"
          data-testid="cascade-back-btn"
          class="flex items-center gap-1 px-2 py-1 text-brand-600 hover:bg-brand-100 rounded transition-colors font-medium"
          @click.stop="navigateTo(currentPath.length - 2)"
        >
          <ChevronLeft :size="14" />
          返回上一级
        </button>
        
        <!-- Breadcrumb Path -->
        <div class="flex items-center gap-1 text-gray-500 ml-2">
          <button
            type="button"
            data-testid="breadcrumb-item"
            class="hover:text-brand-600 transition-colors"
            @click.stop="navigateTo(-1)"
          >
            根目录
          </button>
          <template v-for="(node, index) in currentPath" :key="node.id">
            <ChevronRight :size="12" class="text-gray-400" />
            <button
              type="button"
              :data-testid="`breadcrumb-item-${index}`"
              :class="[
                'hover:text-brand-600 transition-colors',
                index === currentPath.length - 1 ? 'text-gray-700 font-medium' : ''
              ]"
              @click.stop="navigateTo(index)"
            >
              {{ node.title }}
            </button>
          </template>
        </div>
      </div>

      <!-- Current Level Nodes -->
      <template v-if="currentNodes.length > 0">
        <div
          v-for="node in currentNodes"
          :key="node.id"
          data-testid="cascade-node"
          :data-node-id="node.id"
          :class="[
            'flex items-center justify-between py-2.5 px-3 text-sm cursor-pointer transition-colors',
            modelValue === String(node.id)
              ? 'bg-brand-50 text-brand-600 font-medium'
              : 'text-gray-700 hover:bg-gray-50'
          ]"
          @click.stop="handleNodeClick(node)"
        >
          <span class="truncate flex-1 cursor-pointer">{{ node.title }}</span>
          <div class="flex items-center gap-2 shrink-0">
            <!-- Always show "选择" button so user can select this node -->
            <button
              type="button"
              data-testid="select-node-btn"
              class="px-2 py-0.5 text-xs text-brand-600 hover:text-brand-700 hover:bg-brand-100 rounded transition-colors"
              @click.stop="selectNode(node)"
            >
              选择
            </button>
            <!-- Has navigable children: also show arrow indicating user can navigate into -->
            <ChevronRight
              v-if="hasFilteredChildren(node)"
              :size="16"
              class="text-gray-400 cursor-pointer"
              @click.stop="navigateInto(node)"
            />
          </div>
        </div>
      </template>
      <div v-else class="px-3 py-4 text-sm text-gray-400 text-center">
        当前目录下没有章节
      </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ChevronDown, ChevronRight, ChevronLeft } from 'lucide-vue-next'
import type { ChapterTreeNode } from '@/types/api'

/**
 * CascadeSelect 级联选择器组件
 *
 * @description 用于选择层级数据的下拉选择器，支持单层展开+面包屑导航
 *
 * @property {string | null} modelValue - 绑定值，章节ID或null表示根章节
 * @property {ChapterTreeNode[]} chapters - 章节树数据
 * @property {string} [placeholder] - 占位文字
 * @property {boolean} [disabled=false] - 是否禁用
 *
 * @example
 * <CascadeSelect v-model="parentId" :chapters="chapterTree" placeholder="请选择父章节" />
 */

interface Props {
  modelValue: string | null
  chapters: ChapterTreeNode[]
  placeholder?: string
  disabled?: boolean
  /** Maximum level of folders that can be selected as parent (default: 3, allows levels 0-2) */
  maxLevel?: number
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  maxLevel: 3
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | null): void
}>()

// Refs
const containerRef = ref<HTMLElement | null>(null)
const triggerRef = ref<HTMLElement | null>(null)
const dropdownRef = ref<HTMLElement | null>(null)
const isOpen = ref(false)

// Computed: Dropdown position relative to viewport (for fixed positioning with Teleport)
const dropdownPosition = computed(() => {
  if (!triggerRef.value) return { top: 0, left: 0, width: 0 }
  const rect = triggerRef.value.getBoundingClientRect()
  return {
    top: rect.bottom + 4, // 4px gap (same as mt-1)
    left: rect.left,
    width: rect.width
  }
})

// Navigation state: path from root to current level
const currentPath = ref<ChapterTreeNode[]>([])

// Internal selected value for immediate display updates
const internalSelectedValue = ref<string | null>(null)

// Helper: Filter chapters tree by maxLevel (recursive)
function filterChaptersByLevel(nodes: ChapterTreeNode[], maxLevel: number): ChapterTreeNode[] {
  return nodes
    .filter(node => node.node_type === 'folder' && node.level < maxLevel)
    .map(node => ({
      ...node,
      children: node.children ? filterChaptersByLevel(node.children, maxLevel) : []
    }))
}

// Computed: Filtered chapters tree (only folders with level < maxLevel)
const filteredChapters = computed(() => {
  return filterChaptersByLevel(props.chapters, props.maxLevel)
})

// Computed: Root nodes (parent_id === null)
const rootNodes = computed(() => {
  return filteredChapters.value.filter(
    node => node.parent_id === null
  )
})

// Computed: Current level nodes
const currentNodes = computed(() => {
  if (currentPath.value.length === 0) {
    return rootNodes.value
  }
  // Children of the last node in path
  const lastNode = currentPath.value[currentPath.value.length - 1]
  return lastNode.children || []
})

// Computed: Display label for selected value
const displayLabel = computed(() => {
  const effectiveValue = internalSelectedValue.value ?? props.modelValue
  
  // null means root/no parent
  if (effectiveValue === null) {
    return ''
  }
  
  // Find the node and build path label (search in original chapters, not filtered)
  const path = findNodePath(props.chapters, effectiveValue)
  if (path.length === 0) {
    return ''
  }
  
  return path.map(n => n.title).join(' > ')
})

// Helper: Find node path by ID (recursive)
function findNodePath(nodes: ChapterTreeNode[], targetId: string): ChapterTreeNode[] {
  for (const node of nodes) {
    if (String(node.id) === targetId) {
      return [node]
    }
    if (node.children && node.children.length > 0) {
      const childPath = findNodePath(node.children, targetId)
      if (childPath.length > 0) {
        return [node, ...childPath]
      }
    }
  }
  return []
}

/**
 * Check if a node has any navigable children (folder type with level < maxLevel)
 * This ensures arrow display and click behavior use the same logic
 */
const hasFilteredChildren = (node: ChapterTreeNode): boolean => {
  if (!node.children || node.children.length === 0) return false
  return node.children.some(
    child => child.node_type === 'folder' && child.level < props.maxLevel
  )
}

// Methods
const toggleDropdown = () => {
  if (props.disabled) return
  isOpen.value = !isOpen.value
  // Reset path when opening
  if (isOpen.value) {
    currentPath.value = []
  }
}

const closeDropdown = () => {
  isOpen.value = false
  currentPath.value = []
}

const handleNodeClick = (node: ChapterTreeNode) => {
  // Clicking the row (title area) navigates into children if has any
  if (hasFilteredChildren(node)) {
    navigateInto(node)
  } else {
    // If no children, select the node
    selectNode(node)
  }
}

const navigateInto = (node: ChapterTreeNode) => {
  currentPath.value = [...currentPath.value, node]
}

const navigateTo = (index: number) => {
  // -1 means go to root (clear path)
  // 0, 1, 2... means go to specific level
  if (index < 0) {
    currentPath.value = []
  } else {
    currentPath.value = currentPath.value.slice(0, index + 1)
  }
}

const selectNode = (node: ChapterTreeNode) => {
  internalSelectedValue.value = String(node.id)
  emit('update:modelValue', String(node.id))
  closeDropdown()
}

const selectRoot = () => {
  internalSelectedValue.value = null
  emit('update:modelValue', null)
  closeDropdown()
}

// Handle click outside (must check both trigger container and teleported dropdown)
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as Node
  const clickedInsideTrigger = containerRef.value?.contains(target)
  const clickedInsideDropdown = dropdownRef.value?.contains(target)
  
  if (!clickedInsideTrigger && !clickedInsideDropdown) {
    closeDropdown()
  }
}

// Trigger key handlers
const handleTriggerEnter = () => {
  if (props.disabled) return
  if (isOpen.value) {
    closeDropdown()
  } else {
    isOpen.value = true
    currentPath.value = []
  }
}

// Lifecycle
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// Watch modelValue prop changes to sync internal state
watch(() => props.modelValue, (newVal) => {
  internalSelectedValue.value = newVal
}, { immediate: true })

// Close dropdown when disabled changes to true
watch(() => props.disabled, (newVal) => {
  if (newVal && isOpen.value) {
    closeDropdown()
  }
})
</script>
