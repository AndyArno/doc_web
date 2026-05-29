<script setup lang="ts">
/**
 * SortPreviewModal - 排序预览弹窗组件
 *
 * @description 显示智能排序后的树结构预览，支持：
 * - 拖拽调整节点顺序
 * - 上下移动按钮微调
 * - 高亮变化的节点
 * - 显示变更统计
 *
 * @example
 * <SortPreviewModal
 *   :visible="showPreview"
 *   :preview-data="previewData"
 *   :current-tree="chapters"
 *   @confirm="handleConfirm"
 *   @cancel="handleCancel"
 * />
 */
import { ref, computed, watch } from 'vue'
import { ArrowUp, ArrowDown, X, Check, Folder, FileText, GripVertical, Trash2 } from 'lucide-vue-next'
import draggable from 'vuedraggable'
import type { SortPreviewResponse, SortPreviewNode, ChapterTreeNode, OrderItem } from '@/types/api'

/**
 * 组件 Props 定义
 */
interface Props {
  /** 是否显示弹窗 */
  visible: boolean
  /** 排序预览数据 */
  previewData: SortPreviewResponse
  /** 当前树结构（用于比较变化） */
  currentTree: ChapterTreeNode[]
}

const props = defineProps<Props>()

/**
 * 确认提交的载荷
 */
interface ConfirmPayload {
  /** 排序项列表（不包含已删除的节点） */
  orders: OrderItem[]
  /** 已删除的节点 ID 列表 */
  deletedIds: number[]
  /** 已删除的文件夹编号列表 */
  deletedFolderNumbers: number[]
}

/**
 * 组件 Emits 定义
 */
const emit = defineEmits<{
  /** 确认应用排序 */
  (e: 'confirm', payload: ConfirmPayload): void
  /** 取消排序 */
  (e: 'cancel'): void
}>()

/**
 * 本地树数据（用于拖拽操作）
 */
const localTree = ref<SortPreviewNode[]>([])

/**
 * 变化的节点 ID 集合
 */
const changedNodeIds = ref<Set<number | string>>(new Set())

/**
 * 已删除的节点 ID 集合
 */
const deletedNodeIds = ref<Set<number | string>>(new Set())

/**
 * 删除确认对话框状态
 */
const showDeleteConfirm = ref(false)
const nodeToDelete = ref<SortPreviewNode | null>(null)

/**
 * 初始化本地树数据
 */
const initLocalTree = () => {
  localTree.value = JSON.parse(JSON.stringify(props.previewData.preview_tree))
  detectChanges()
}

/**
 * 检测变化的节点
 * 通过比较 preview_tree 和 currentTree 判断哪些节点位置发生变化
 */
const detectChanges = () => {
  changedNodeIds.value.clear()
  
  // 构建当前树的位置映射 { id: { parentId, orderIndex } }
  const currentPositionMap = new Map<number, { parentId: number | null; orderIndex: number }>()
  const buildCurrentPositionMap = (nodes: ChapterTreeNode[], parentId: number | null = null) => {
    nodes.forEach((node, index) => {
      currentPositionMap.set(node.id, { parentId, orderIndex: index })
      if (node.children?.length) {
        buildCurrentPositionMap(node.children, node.id)
      }
    })
  }
  buildCurrentPositionMap(props.currentTree)
  
  // 构建预览树的位置映射并比较
  const comparePositions = (nodes: SortPreviewNode[], parentId: number | null = null) => {
    nodes.forEach((node, index) => {
      // 如果是临时ID（string），表示新建节点，直接标记为变化
      if (typeof node.id === 'string') {
        changedNodeIds.value.add(node.id)
      } else {
        const currentPos = currentPositionMap.get(node.id)
        if (currentPos) {
          // 比较父节点和顺序
          if (currentPos.parentId !== parentId || currentPos.orderIndex !== index) {
            changedNodeIds.value.add(node.id)
          }
        } else {
          // 新创建的节点（如文件夹）
          changedNodeIds.value.add(node.id)
        }
      }
      if (node.children?.length) {
        comparePositions(node.children, typeof node.id === 'number' ? node.id : null)
      }
    })
  }
  comparePositions(localTree.value)
}

/**
 * 监听 previewData 变化，重新初始化
 */
watch(
  () => props.previewData,
  () => {
    if (props.visible) {
      initLocalTree()
    }
  },
  { immediate: true, deep: true }
)

/**
 * 监听 visible 变化
 */
watch(
  () => props.visible,
  (newVal) => {
    if (newVal) {
      initLocalTree()
    }
  }
)

/**
 * 检查节点是否发生变化
 */
const isNodeChanged = (nodeId: number | string): boolean => {
  return changedNodeIds.value.has(nodeId)
}

/**
 * 检查节点是否已被删除
 */
const isDeleted = (nodeId: number | string): boolean => {
  return deletedNodeIds.value.has(nodeId)
}

/**
 * 检查节点是否可以删除
 */
const canDelete = (_node: SortPreviewNode): boolean => {
  // 所有节点都可以删除
  return true
}

/**
 * 处理删除按钮点击
 */
const handleDeleteClick = (node: SortPreviewNode) => {
  nodeToDelete.value = node
  showDeleteConfirm.value = true
}

/**
 * 取消删除
 */
const cancelDelete = () => {
  showDeleteConfirm.value = false
  nodeToDelete.value = null
}

/**
 * 确认删除
 */
const confirmDelete = () => {
  if (nodeToDelete.value) {
    deletedNodeIds.value.add(nodeToDelete.value.id)
    // 如果是文件夹，同时标记所有子节点
    markChildrenAsDeleted(nodeToDelete.value)
  }
  showDeleteConfirm.value = false
  nodeToDelete.value = null
}

/**
 * 递归标记子节点为删除
 */
const markChildrenAsDeleted = (node: SortPreviewNode) => {
  if (node.children) {
    for (const child of node.children) {
      deletedNodeIds.value.add(child.id)
      markChildrenAsDeleted(child)
    }
  }
}

/**
 * 获取同级兄弟节点
 */
const getSiblings = (parentId: number | string | null): SortPreviewNode[] => {
  if (parentId === null) {
    return localTree.value
  }
  
  const findChildren = (nodes: SortPreviewNode[]): SortPreviewNode[] | null => {
    for (const node of nodes) {
      if (node.id === parentId) {
        return node.children || []
      }
      if (node.children?.length) {
        const found = findChildren(node.children)
        if (found) return found
      }
    }
    return null
  }
  
  return findChildren(localTree.value) || []
}

/**
 * 查找节点的父节点 ID
 */
const findParentId = (targetId: number | string, nodes: SortPreviewNode[], parentId: number | string | null = null): number | string | null => {
  for (const node of nodes) {
    if (node.id === targetId) {
      return parentId
    }
    if (node.children?.length) {
      const found = findParentId(targetId, node.children, node.id)
      if (found !== undefined) return found
    }
  }
  return undefined as unknown as number | string | null
}

/**
 * 在指定父节点下移动节点
 */
const moveNodeInParent = (
  parentId: number | string | null,
  nodeId: number | string,
  direction: 'up' | 'down'
) => {
  const siblings = getSiblings(parentId)
  const currentIndex = siblings.findIndex(s => s.id === nodeId)
  
  if (currentIndex === -1) return
  
  let targetIndex: number
  if (direction === 'up') {
    if (currentIndex === 0) return
    targetIndex = currentIndex - 1
  } else {
    if (currentIndex === siblings.length - 1) return
    targetIndex = currentIndex + 1
  }
  
  // 交换位置
  const temp = siblings[currentIndex]
  siblings[currentIndex] = siblings[targetIndex]
  siblings[targetIndex] = temp
  
  // 标记变化的节点
  changedNodeIds.value.add(nodeId)
  changedNodeIds.value.add(siblings[currentIndex].id)
}

/**
 * 处理节点上移
 */
const handleMoveUp = (node: SortPreviewNode) => {
  const parentId = findParentId(node.id, localTree.value)
  moveNodeInParent(parentId, node.id, 'up')
}

/**
 * 处理节点下移
 */
const handleMoveDown = (node: SortPreviewNode) => {
  const parentId = findParentId(node.id, localTree.value)
  moveNodeInParent(parentId, node.id, 'down')
}

/**
 * 处理拖拽变化
 */
const handleDragChange = (event: { moved?: { element: SortPreviewNode; oldIndex: number; newIndex: number } }) => {
  if (event.moved) {
    changedNodeIds.value.add(event.moved.element.id)
  }
}

/**
 * 递归更新子节点拖拽
 */
const handleChildDragChange = (
  event: { moved?: { element: SortPreviewNode; oldIndex: number; newIndex: number } },
  parentId: number | string
) => {
  if (event.moved) {
    changedNodeIds.value.add(event.moved.element.id)
  }
}

/**
 * 构建排序顺序数组
 */
const buildOrders = (): OrderItem[] => {
  const orders: OrderItem[] = []
  
  const traverse = (nodes: SortPreviewNode[], parentId: number | string | null = null) => {
    nodes.forEach((node, index) => {
      // 跳过已删除的节点
      if (isDeleted(node.id)) return
      
      orders.push({
        id: node.id,
        type: node.node_type as 'folder' | 'article',
        folder_number: node.folder_number,
        order_index: index,
        parent_id: parentId,
        is_new: node.is_new
      })
      if (node.children?.length) {
        traverse(node.children, node.id)
      }
    })
  }
  
  traverse(localTree.value)
  return orders
}

/**
 * 获取已删除节点的信息
 */
const getDeletedInfo = (): { deletedIds: number[], deletedFolderNumbers: number[] } => {
  const deletedIds: number[] = []
  const deletedFolderNumbers: number[] = []
  
  // 遍历 localTree 查找已删除的真实节点
  const findDeletedNodes = (nodes: SortPreviewNode[]) => {
    for (const node of nodes) {
      if (isDeleted(node.id)) {
        // 只处理真实ID（数字类型），临时ID（字符串）不需要处理
        if (typeof node.id === 'number') {
          deletedIds.push(node.id)
          // 如果是文件夹且有 folder_number，记录编号
          if (node.node_type === 'folder' && node.folder_number) {
            deletedFolderNumbers.push(node.folder_number)
          }
        }
      }
      if (node.children?.length) {
        findDeletedNodes(node.children)
      }
    }
  }
  
  findDeletedNodes(localTree.value)
  
  return { deletedIds, deletedFolderNumbers }
}

/**
 * 处理确认应用
 */
const handleConfirm = () => {
  const orders = buildOrders()
  const { deletedIds, deletedFolderNumbers } = getDeletedInfo()
  
  emit('confirm', {
    orders,
    deletedIds,
    deletedFolderNumbers
  })
}

/**
 * 处理取消
 */
const handleCancel = () => {
  emit('cancel')
}

/**
 * 节点类型图标
 */
const NodeTypeIcon = ({ nodeType }: { nodeType: string }) => {
  if (nodeType === 'folder') {
    return Folder
  }
  return FileText
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="visible"
        class="fixed inset-0 z-50 overflow-y-auto"
        role="dialog"
        aria-modal="true"
      >
        <!-- 遮罩层 -->
        <div
          class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm transition-opacity"
          @click="handleCancel"
        ></div>

        <!-- 弹窗容器 -->
        <div class="flex min-h-full items-center justify-center p-4 text-center">
          <Transition name="zoom" appear>
            <div
              v-if="visible"
              class="relative transform overflow-hidden rounded-2xl bg-white text-left shadow-xl transition-all w-full"
              style="max-width: 720px"
            >
              <!-- 头部 -->
              <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                <div class="flex items-center gap-3">
                  <h3 class="text-lg font-semibold text-gray-900">排序预览</h3>
                  <span
                    v-if="previewData.changes_count > 0"
                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800"
                  >
                    {{ previewData.changes_count }} 处变更
                  </span>
                </div>
                <button
                  type="button"
                  class="rounded-lg p-1 text-gray-400 hover:text-gray-500 hover:bg-gray-100 transition-colors focus:outline-none"
                  @click="handleCancel"
                >
                  <span class="sr-only">关闭</span>
                  <X class="h-5 w-5" />
                </button>
              </div>

              <!-- 统计信息 -->
              <div class="px-6 py-3 bg-gray-50 border-b border-gray-100">
                <div class="flex items-center gap-4 text-sm text-gray-600">
                  <span>
                    <strong class="text-gray-900">{{ previewData.changes_count }}</strong> 处位置变更
                  </span>
                  <span v-if="previewData.folders_created.length > 0">
                    <strong class="text-gray-900">{{ previewData.folders_created.length }}</strong> 个新文件夹
                  </span>
                </div>
                <p v-if="previewData.folders_created.length > 0" class="mt-1 text-xs text-gray-500">
                  新建文件夹：{{ previewData.folders_created.join('、') }}
                </p>
              </div>

              <!-- 内容区 - 树结构 -->
              <div class="px-6 py-4 max-h-[60vh] overflow-y-auto">
                <p class="text-xs text-gray-400 mb-3">
                  拖拽节点或使用上下移动按钮调整顺序，高亮节点表示位置发生变化
                </p>

                <!-- 树节点列表 -->
                <draggable
                  v-model="localTree"
                  item-key="id"
                  handle=".drag-handle"
                  ghost-class="opacity-50"
                  animation="200"
                  :group="{ name: 'sort-preview' }"
                  @change="handleDragChange"
                >
                  <template #item="{ element }">
                    <div>
                      <!-- 根级别节点 -->
                       <div
                        class="group flex items-center py-2 px-3 rounded-lg transition-colors mb-1"
                        :class="[
                          isDeleted(element.id)
                            ? 'bg-gray-100 opacity-50'
                            : isNodeChanged(element.id)
                              ? 'bg-yellow-50 border-l-2 border-yellow-400'
                              : 'hover:bg-gray-50'
                        ]"
                      >
                        <!-- 拖拽手柄 -->
                        <span
                          class="drag-handle mr-2 cursor-grab active:cursor-grabbing text-gray-300 hover:text-gray-500 transition-colors"
                        >
                          <GripVertical class="w-4 h-4" />
                        </span>

                        <!-- 节点类型图标 -->
                        <component
                          :is="NodeTypeIcon({ nodeType: element.node_type })"
                          class="w-4 h-4 mr-2 shrink-0"
                          :class="element.node_type === 'folder' ? 'text-brand-500' : 'text-gray-400'"
                        />

                        <!-- 标题 -->
                        <span 
                          class="flex-1 text-sm text-gray-700 truncate"
                          :class="{ 'line-through text-gray-400': isDeleted(element.id) }"
                        >
                          {{ element.title }}
                        </span>

                        <!-- 移动按钮 -->
                        <div class="hidden group-hover:flex items-center space-x-1 ml-2">
                          <button
                            class="p-1 hover:bg-gray-200 rounded text-gray-500 hover:text-brand-600 transition-colors"
                            title="上移"
                            @click.stop="handleMoveUp(element)"
                          >
                            <ArrowUp class="w-3.5 h-3.5" />
                          </button>
                          <button
                            class="p-1 hover:bg-gray-200 rounded text-gray-500 hover:text-brand-600 transition-colors"
                            title="下移"
                            @click.stop="handleMoveDown(element)"
                          >
                            <ArrowDown class="w-3.5 h-3.5" />
                          </button>
                          <!-- 删除按钮 -->
                          <button
                            v-if="canDelete(element) && !isDeleted(element.id)"
                            class="p-1 hover:bg-red-100 rounded text-gray-500 hover:text-red-600 transition-colors"
                            title="删除"
                            @click.stop="handleDeleteClick(element)"
                          >
                            <Trash2 class="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>

                      <!-- 子节点 -->
                      <div v-if="element.children?.length" class="ml-6">
                        <draggable
                          :list="element.children"
                          item-key="id"
                          handle=".drag-handle"
                          ghost-class="opacity-50"
                          animation="200"
                          :group="{ name: 'sort-preview' }"
                          @change="handleChildDragChange($event, element.id)"
                        >
                          <template #item="{ element: child }">
                            <div>
                              <!-- 二级节点 -->
                               <div
                                class="group flex items-center py-2 px-3 rounded-lg transition-colors mb-1"
                                :class="[
                                  isDeleted(child.id)
                                    ? 'bg-gray-100 opacity-50'
                                    : isNodeChanged(child.id)
                                      ? 'bg-yellow-50 border-l-2 border-yellow-400'
                                      : 'hover:bg-gray-50'
                                ]"
                              >
                                <span
                                  class="drag-handle mr-2 cursor-grab active:cursor-grabbing text-gray-300 hover:text-gray-500 transition-colors"
                                >
                                  <GripVertical class="w-4 h-4" />
                                </span>
                                <component
                                  :is="NodeTypeIcon({ nodeType: child.node_type })"
                                  class="w-4 h-4 mr-2 shrink-0"
                                  :class="child.node_type === 'folder' ? 'text-brand-500' : 'text-gray-400'"
                                />
                                <span 
                                  class="flex-1 text-sm text-gray-700 truncate"
                                  :class="{ 'line-through text-gray-400': isDeleted(child.id) }"
                                >
                                  {{ child.title }}
                                </span>
                                <div class="hidden group-hover:flex items-center space-x-1 ml-2">
                                  <button
                                    class="p-1 hover:bg-gray-200 rounded text-gray-500 hover:text-brand-600 transition-colors"
                                    title="上移"
                                    @click.stop="handleMoveUp(child)"
                                  >
                                    <ArrowUp class="w-3.5 h-3.5" />
                                  </button>
                                  <button
                                    class="p-1 hover:bg-gray-200 rounded text-gray-500 hover:text-brand-600 transition-colors"
                                    title="下移"
                                    @click.stop="handleMoveDown(child)"
                                  >
                                    <ArrowDown class="w-3.5 h-3.5" />
                                  </button>
                                  <!-- 删除按钮 -->
                                  <button
                                    v-if="canDelete(child) && !isDeleted(child.id)"
                                    class="p-1 hover:bg-red-100 rounded text-gray-500 hover:text-red-600 transition-colors"
                                    title="删除"
                                    @click.stop="handleDeleteClick(child)"
                                  >
                                    <Trash2 class="w-3.5 h-3.5" />
                                  </button>
                                </div>
                              </div>

                              <!-- 三级节点 -->
                               <div v-if="child.children?.length" class="ml-6">
                                <div
                                  v-for="grandchild in child.children"
                                  :key="grandchild.id"
                                  class="group flex items-center py-2 px-3 rounded-lg transition-colors mb-1"
                                  :class="[
                                    isDeleted(grandchild.id)
                                      ? 'bg-gray-100 opacity-50'
                                      : isNodeChanged(grandchild.id)
                                        ? 'bg-yellow-50 border-l-2 border-yellow-400'
                                        : 'hover:bg-gray-50'
                                  ]"
                                >
                                  <span
                                    class="drag-handle mr-2 cursor-grab active:cursor-grabbing text-gray-300 hover:text-gray-500 transition-colors"
                                  >
                                    <GripVertical class="w-4 h-4" />
                                  </span>
                                  <component
                                    :is="NodeTypeIcon({ nodeType: grandchild.node_type })"
                                    class="w-4 h-4 mr-2 shrink-0"
                                    :class="grandchild.node_type === 'folder' ? 'text-brand-500' : 'text-gray-400'"
                                  />
                                  <span 
                                    class="flex-1 text-sm text-gray-700 truncate"
                                    :class="{ 'line-through text-gray-400': isDeleted(grandchild.id) }"
                                  >
                                    {{ grandchild.title }}
                                  </span>
                                  <div class="hidden group-hover:flex items-center space-x-1 ml-2">
                                    <button
                                      class="p-1 hover:bg-gray-200 rounded text-gray-500 hover:text-brand-600 transition-colors"
                                      title="上移"
                                      @click.stop="handleMoveUp(grandchild)"
                                    >
                                      <ArrowUp class="w-3.5 h-3.5" />
                                    </button>
                                    <button
                                      class="p-1 hover:bg-gray-200 rounded text-gray-500 hover:text-brand-600 transition-colors"
                                      title="下移"
                                      @click.stop="handleMoveDown(grandchild)"
                                    >
                                      <ArrowDown class="w-3.5 h-3.5" />
                                    </button>
                                    <!-- 删除按钮 -->
                                    <button
                                      v-if="canDelete(grandchild) && !isDeleted(grandchild.id)"
                                      class="p-1 hover:bg-red-100 rounded text-gray-500 hover:text-red-600 transition-colors"
                                      title="删除"
                                      @click.stop="handleDeleteClick(grandchild)"
                                    >
                                      <Trash2 class="w-3.5 h-3.5" />
                                    </button>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </template>
                        </draggable>
                      </div>
                    </div>
                  </template>
                </draggable>

                <!-- 空状态 -->
                <div v-if="localTree.length === 0" class="py-8 text-center">
                  <p class="text-sm text-gray-400">暂无章节数据</p>
                </div>
              </div>

              <!-- 底部 -->
              <div class="px-6 py-4 border-t border-gray-100 bg-gray-50/50 flex justify-end gap-3">
                <button
                  type="button"
                  class="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                  @click="handleCancel"
                >
                  取消
                </button>
                <button
                  type="button"
                  class="flex items-center gap-2 px-4 py-2 text-sm font-bold text-white bg-brand-600 hover:bg-brand-500 rounded-lg transition-colors"
                  @click="handleConfirm"
                >
                  <Check class="w-4 h-4" />
                  确认应用
                </button>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </Transition>

    <!-- 删除确认对话框 -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showDeleteConfirm"
          class="fixed inset-0 z-[60] flex items-center justify-center"
          role="dialog"
          aria-modal="true"
        >
          <!-- 遮罩层 -->
          <div
            class="fixed inset-0 bg-black/50 backdrop-blur-sm"
            @click="cancelDelete"
          ></div>

          <!-- 对话框内容 -->
          <div class="relative bg-white rounded-lg p-6 max-w-sm shadow-xl">
            <h3 class="text-lg font-semibold text-gray-900 mb-2">确认删除</h3>
            <p class="text-gray-600 mb-4">
              确定要删除 "{{ nodeToDelete?.title }}" 吗？
              <span v-if="nodeToDelete?.children?.length" class="block text-sm text-red-600 mt-1">
                （将同时删除 {{ nodeToDelete.children.length }} 个子节点）
              </span>
            </p>
            <div class="flex justify-end gap-2">
              <button
                class="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                @click="cancelDelete"
              >
                取消
              </button>
              <button
                class="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
                @click="confirmDelete"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </Teleport>
</template>

<style scoped>
/* 淡入淡出动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 缩放动画 */
.zoom-enter-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.zoom-leave-active {
  transition: all 0.2s ease-in;
}

.zoom-enter-from {
  opacity: 0;
  transform: scale(0.95);
}

.zoom-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
