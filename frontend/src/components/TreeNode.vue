<template>
  <div class="tree-node-container" :class="{ 'last-level': level >= 5 }">
    <!-- 节点项目：包含图标、标题和编辑按钮 -->
    <div
      class="group flex items-center py-2 px-3 cursor-pointer transition-colors duration-200 select-none"
      :class="[
        activeNodeId === node.id 
          ? 'bg-brand-50 text-brand-600 font-medium' 
          : 'text-gray-600 hover:bg-gray-100'
      ]"
      :style="{ paddingLeft: `${level * 14 + 12}px` }"
      @click="handleToggle"
    >
      <!-- 拖拽手柄（仅桌面端显示） -->
      <span 
        v-if="canDrag"
        class="drag-handle mr-1 cursor-grab active:cursor-grabbing text-gray-300 hover:text-gray-500 transition-colors"
        @click.stop
      >
        <GripVertical class="w-3.5 h-3.5" />
      </span>

      <!-- Checkbox（排序模式） -->
      <input
        v-if="showCheckbox"
        type="checkbox"
        :checked="selectedIds.includes(node.id)"
        @change="emit('toggle-select', node.id)"
        @click.stop
        class="w-4 h-4 mr-2 text-brand-600 border-gray-300 rounded focus:ring-brand-500 cursor-pointer"
      />

      <!-- 展开/收起图标或占位符 -->
      <span class="mr-1.5 w-4 h-4 flex items-center justify-center shrink-0">
        <template v-if="hasChildren">
          <ChevronDown v-if="isExpanded" class="w-3.5 h-3.5" />
          <ChevronRight v-else class="w-3.5 h-3.5" />
        </template>
        <span v-else class="w-1 h-1 rounded-full bg-gray-300"></span>
      </span>

      <!-- 节点类型图标 -->
      <Folder v-if="node.node_type === 'folder'" class="w-4 h-4 mr-1.5 text-brand-500 shrink-0" />
      <FileText v-else class="w-4 h-4 mr-1.5 text-gray-400 shrink-0" />

      <!-- 章节标题 -->
      <span class="flex-1 truncate text-sm">
        {{ node.title }}
      </span>

      <!-- 编辑操作按钮组（仅在 editable 模式且悬停时显示） -->
      <div 
        v-if="editable" 
        class="hidden group-hover:flex items-center space-x-1 ml-2"
        @click.stop
      >

        <button 
          class="p-1 hover:bg-gray-200 rounded text-gray-500 hover:text-brand-600 transition-colors" 
          title="上移"
          @click="$emit('move-up', node)"
        >
          <ArrowUp class="w-3.5 h-3.5" />
        </button>
        <button 
          class="p-1 hover:bg-gray-200 rounded text-gray-500 hover:text-brand-600 transition-colors" 
          title="下移"
          @click="$emit('move-down', node)"
        >
          <ArrowDown class="w-3.5 h-3.5" />
        </button>
        <button 
          class="p-1 hover:bg-gray-200 rounded text-gray-500 hover:text-brand-600 transition-colors" 
          title="编辑"
          @click="$emit('edit', node)"
        >
          <Pencil class="w-3.5 h-3.5" />
        </button>
        <button 
          class="p-1 hover:bg-gray-200 rounded text-gray-500 hover:text-red-500 transition-colors" 
          title="删除"
          @click="$emit('delete', node)"
        >
          <Trash2 class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>

    <!-- 递归渲染子节点 -->
    <!-- 拖拽模式：始终渲染 draggable 容器，以便可以拖入空文件夹/未展开文件夹 -->
    <div v-if="canReceiveChildren" v-show="isExpanded" class="tree-children">
      <draggable
        :list="childrenList"
        item-key="id"
        handle=".drag-handle"
        ghost-class="opacity-50"
        animation="200"
        :group="{ name: 'chapters' }"
        @change="handleDragChange"
      >
        <template #item="{ element }">
          <div :data-chapter-id="element.id">
            <TreeNode
              :node="element"
              :active-node-id="activeNodeId"
              :level="level + 1"
              :editable="editable"
              :draggable="isDraggable"
              :all-chapters="allChapters"
              :show-checkbox="showCheckbox"
              :selected-ids="selectedIds"
              @select="$emit('select', $event)"
              @edit="$emit('edit', $event)"
              @delete="$emit('delete', $event)"
              @move-up="$emit('move-up', $event)"
              @move-down="$emit('move-down', $event)"
              @reorder="$emit('reorder', $event)"
              @drag-preview="$emit('drag-preview', $event)"
              @update-children="$emit('update-children', $event)"
              @toggle-select="$emit('toggle-select', $event)"
            />
          </div>
        </template>
      </draggable>
    </div>
    <!-- 非拖拽模式：只在有子节点且展开时渲染 -->
    <div v-else-if="hasChildren && isExpanded" class="tree-children">
      <TreeNode
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :active-node-id="activeNodeId"
        :level="level + 1"
        :editable="editable"
        :draggable="isDraggable"
        :all-chapters="allChapters"
        :show-checkbox="showCheckbox"
        :selected-ids="selectedIds"
        @select="$emit('select', $event)"
        @edit="$emit('edit', $event)"
        @delete="$emit('delete', $event)"
        @move-up="$emit('move-up', $event)"
        @move-down="$emit('move-down', $event)"
        @reorder="$emit('reorder', $event)"
        @drag-preview="$emit('drag-preview', $event)"
        @update-children="$emit('update-children', $event)"
        @toggle-select="$emit('toggle-select', $event)"
      />
    </div>
  </div>
</template>

<script setup>
/**
 * TreeNode - 树形目录节点组件
 * 
 * 功能：
 * - 递归展示三级目录（章 -> 节 -> 小节）
 * - 支持展开/收起（仅限含有子节点的节点）
 * - 支持选中态高亮（bg-brand-50 + 蓝色文字）
 * - 层级缩进：每层缩进 14px
 * - 管理模式下显示编辑、删除和排序按钮
 * 
 * @example
 * <TreeNode :node="chapter" :active-node-id="currentId" @select="onSelect" />
 */
import { ref, computed } from 'vue'
import { 
  ChevronDown, 
  ChevronRight, 
  Pencil, 
  Trash2, 
  ArrowUp, 
  ArrowDown,
  GripVertical,
  Folder,
  FileText
} from 'lucide-vue-next'
import draggable from 'vuedraggable'

const props = defineProps({
  /**
   * 节点数据
   * @type {Object}
   * @property {string|number} id - 节点ID
   * @property {string} title - 节点标题
   * @property {Array} [children] - 子节点列表
   */
  node: {
    type: Object,
    required: true
  },
  /**
   * 当前选中节点ID
   */
  activeNodeId: {
    type: [String, Number],
    default: null
  },
  /**
   * 当前层级 (0-2)
   */
  level: {
    type: Number,
    default: 0
  },
  /**
   * 是否处于编辑模式
   */
  editable: {
    type: Boolean,
    default: false
  },
  /**
   * 是否可拖拽
   */
  draggable: {
    type: Boolean,
    default: false
  },
  /**
   * 完整的章节树列表（用于跨分支循环引用检测）
   * 如果不传，则只在当前节点的子树中搜索
   */
  allChapters: {
    type: Array,
    default: () => []
  },
  /**
   * 是否显示 checkbox（排序模式）
   */
  showCheckbox: {
    type: Boolean,
    default: false
  },
  /**
   * 已选中的章节 ID 列表
   */
  selectedIds: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits([
  'select',
  'edit',
  'delete',
  'move-up',
  'move-down',
  'reorder',
  'drag-preview',
  'update-children',
  'toggle-select'
])

// 展开/收起状态，默认展开
const isExpanded = ref(true)

// 是否有子节点
const hasChildren = computed(() => {
  return props.node.children && props.node.children.length > 0
})

// 确保 draggable 是布尔值（防御 vuedraggable 传递 Object 类型）
const isDraggable = computed(() => Boolean(props.draggable))

// 是否处于可编辑拖拽模式
const canDrag = computed(() => isDraggable.value && props.editable)

// 是否渲染子节点拖放容器（article 不应接收子节点）
const canReceiveChildren = computed(() => 
  canDrag.value && 
  props.node.node_type !== 'article'
)

/**
 * 切换展开状态并触发选中事件
 */
const handleToggle = () => {
  if (hasChildren.value) {
    isExpanded.value = !isExpanded.value
  }
  emit('select', props.node)
}

/**
 * 子节点列表（用于 draggable）
 * 使用 computed 的 getter/setter 来支持 v-model 风格的双向绑定
 * 
 * 注意：vuedraggable 使用 :list 绑定时会：
 * 1. 直接修改数组内容（splice、push 等）
 * 2. 调用 setter 传入新的数组引用
 * 
 * 由于 props.node.children 是父组件响应式数据的引用，
 * 直接修改会触发父组件的响应式更新。
 * setter 发出 update-children 事件供父组件进行额外的状态同步。
 */
const childrenList = computed({
  get: () => props.node.children || [],
  set: (value) => {
    emit('update-children', {
      nodeId: props.node.id,
      children: value
    })
  }
})

/**
 * 计算节点的最大子孙深度
 * @param {Object} node - 要计算的节点
 * @returns {number} - 最大子孙深度（0 表示没有子节点）
 */
const getMaxDescendantDepth = (node) => {
  if (!node.children || node.children.length === 0) {
    return 0
  }
  let maxDepth = 0
  for (const child of node.children) {
    const childDepth = getMaxDescendantDepth(child)
    maxDepth = Math.max(maxDepth, childDepth + 1)
  }
  return maxDepth
}

/**
 * 检查某个节点是否是另一个节点的后代
 * @param {number} ancestorId - 祖先节点 ID
 * @param {number} descendantId - 可能的后代节点 ID
 * @returns {boolean} - 如果 descendantId 是 ancestorId 的后代，返回 true
 */
const isDescendant = (ancestorId, descendantId) => {
  // 递归查找节点
  const findNode = (nodeList, targetId) => {
    for (const node of nodeList) {
      if (node.id === targetId) return node
      if (node.children) {
        const found = findNode(node.children, targetId)
        if (found) return found
      }
    }
    return null
  }
  
  // 确定搜索范围：优先使用 allChapters，否则回退到 props.node
  const searchList = (props.allChapters && props.allChapters.length > 0)
    ? props.allChapters
    : [props.node]
  
  // 找到祖先节点
  const ancestorNode = findNode(searchList, ancestorId)
  if (!ancestorNode) return false
  
  // 检查 descendantId 是否在 ancestorNode 的子树中
  const checkDescendant = (node) => {
    if (!node.children) return false
    for (const child of node.children) {
      if (child.id === descendantId) return true
      if (checkDescendant(child)) return true
    }
    return false
  }
  
  return checkDescendant(ancestorNode)
}

/**
 * 处理拖拽变化事件
 * 使用 @change 事件处理跨容器拖拽和同级排序
 * @param {Object} event - vuedraggable 的 change 事件对象
 */
const handleDragChange = (event) => {
  // 非编辑模式或非拖拽模式不处理
  if (!canDrag.value) return
  
  // 处理节点添加到当前容器（跨容器拖入）
  if (event.added) {
    const { element, newIndex } = event.added
    
    // 当前节点作为父节点
    const newParentId = props.node.id
    
    // 检查目标父节点是否是 article 类型
    if (props.node.node_type === 'article') {
      emit('reorder', {
        chapterId: element.id,
        newParentId,
        newIndex,
        error: 'ARTICLE_CANNOT_HAVE_CHILDREN'
      })
      return
    }
    
    // 层级限制检查
    const newLevel = props.level + 1
    const maxDescendantDepth = getMaxDescendantDepth(element)
    const maxResultingLevel = newLevel + maxDescendantDepth
    
    if (maxResultingLevel > 5) {
      emit('reorder', {
        chapterId: element.id,
        newParentId: props.node.parent_id,
        newIndex,
        error: 'LEVEL_LIMIT_EXCEEDED'
      })
      return
    }
    
    // 循环引用检查
    if (isDescendant(element.id, props.node.id)) {
      emit('reorder', {
        chapterId: element.id,
        newParentId,
        newIndex,
        error: 'CIRCULAR_REFERENCE'
      })
      return
    }
    
    // 发送拖拽预览事件
    emit('drag-preview', {
      chapterId: element.id,
      newParentId,
      newIndex
    })
    return
  }
  
  // 处理同级排序（在同一个容器内移动）
  if (event.moved) {
    const { element, newIndex } = event.moved
    
    // 发送拖拽预览事件（parent_id 不变）
    emit('drag-preview', {
      chapterId: element.id,
      newParentId: props.node.id,
      newIndex
    })
    return
  }
}

/**
 * 处理拖放操作（供测试调用）
 * @param {Object} payload - { chapterId, newParentId, newIndex }
 */
const handleDrop = (payload) => {
  // 非编辑模式或非拖拽模式不处理
  if (!canDrag.value) return
  
  const { chapterId, newParentId, newIndex } = payload
  
  // 循环引用检查
  if (newParentId && isDescendant(chapterId, newParentId)) {
    emit('reorder', {
      ...payload,
      error: 'CIRCULAR_REFERENCE'
    })
    return
  }
  
  // 层级限制检查：系统最多支持 3 层（level 0, 1, 2）
  // level 2 的节点不能再有子节点
  if (newParentId !== null) {
    // 在 props.node 树中查找目标父节点及其层级
    const findNodeAndLevel = (node, targetId, currentLevel = 0) => {
      if (node.id === targetId) return { node, level: currentLevel }
      if (node.children) {
        for (const child of node.children) {
          const found = findNodeAndLevel(child, targetId, currentLevel + 1)
          if (found) return found
        }
      }
      return null
    }
    
    const targetInfo = findNodeAndLevel(props.node, newParentId)
    
    // 如果目标节点是 level 2（第三层），则不能作为父节点
    // 将 newParentId 调整为该节点的父节点
    if (targetInfo && targetInfo.level >= 5) {
      emit('reorder', {
        chapterId,
        newParentId: targetInfo.node.parent_id,
        newIndex
      })
      return
    }
  }
  
  // 发送重排序事件
  emit('reorder', {
    chapterId,
    newParentId,
    newIndex
  })
}

// 暴露方法供测试调用
defineExpose({
  handleDrop,
  isDescendant,
  handleDragChange
})
</script>

<script>
// 为递归调用显式指定组件名
export default {
  name: 'TreeNode'
}
</script>

<style scoped>
.tree-node-container {
  width: 100%;
}
</style>
