# AGENTS.md — Frontend Components Layer

**Generated:** 2026-04-08  
**Parent:** `/AGENTS.md`

## OVERVIEW

可复用 UI 组件层。使用 Vue 3 Composition API + TypeScript + Tailwind CSS。图标使用 Lucide Vue Next。

## STRUCTURE

```
components/
├── AppHeader.vue            # 顶部导航（reader/admin 模式）
├── Modal.vue                # 基础弹窗（Teleport + Transition）
├── ConfirmDialog.vue        # 确认对话框（warning/danger）
├── Toast.vue                # Toast 通知（defineExpose 服务模式）
├── LoadingSpinner.vue       # 加载指示器
├── EmptyState.vue           # 空状态展示
├── FormInput.vue            # 表单输入（v-model 封装）
├── FormSelect.vue           # 表单下拉（泛型 Option 接口）
├── CascadeSelect.vue        # 级联选择（Teleport 逃逸）
├── TreeNode.vue             # 树节点（递归组件）⚠️ 518行
├── DiffViewer.vue           # 代码对比（LCS 算法）
├── MarkdownDisplay.vue      # Markdown 渲染
├── PageTOC.vue              # 页面目录
├── SearchBox.vue            # 搜索框
├── SortPreviewModal.vue     # 排序预览 ⚠️ 799行
└── ErrorBoundary.vue        # 错误边界
```

## WHERE TO LOOK

| 任务 | 组件 | 特性 |
|------|------|------|
| 弹窗 | `Modal.vue` | Teleport 到 body，Transition 动画 |
| 确认框 | `ConfirmDialog.vue` | warning/danger 类型 |
| 表单控件 | `FormInput.vue`, `FormSelect.vue` | v-model 双向绑定 |
| 树形结构 | `TreeNode.vue` | 递归渲染、拖拽 |
| 代码对比 | `DiffViewer.vue` | LCS 算法、行号同步 |
| Markdown | `MarkdownDisplay.vue` | markdown-it + highlight.js |
| 下拉逃逸 | `CascadeSelect.vue` | Teleport 解决 overflow 裁剪 |

## CONVENTIONS

### 组件结构
```vue
<script setup lang="ts">
/**
 * ComponentName - 简短描述
 * 
 * @description 详细说明
 * @example <Component prop="value" />
 */
import { ref, computed } from 'vue'
import { Icon1, Icon2 } from 'lucide-vue-next'

// 1. Props（TypeScript 接口）
interface Props {
  modelValue: string
  disabled?: boolean
}
const props = withDefaults(defineProps<Props>(), {
  disabled: false
})

// 2. Emits（类型签名）
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'change', value: string): void
}>()

// 3. 响应式状态
const isOpen = ref(false)

// 4. 计算属性
const displayValue = computed(() => ...)

// 5. 方法
function handleChange() { ... }

// 6. 生命周期
onMounted(() => { ... })

// 7. defineExpose（服务组件）
defineExpose({ open, close })
</script>

<template>
  <!-- Tailwind CSS -->
</template>
```

### Props 定义
```typescript
// 推荐：TypeScript 接口
interface Props {
  modelValue: string | null  // 支持 null
  placeholder?: string
  disabled?: boolean
}
const props = withDefaults(defineProps<Props>(), {
  disabled: false
})

// 简单组件：运行时 Props
const props = defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: '' }
})
```

### v-model 模式
```typescript
// 标准 v-model
interface Props {
  modelValue: string
}
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

// 模板
<input :value="modelValue" @input="emit('update:modelValue', $event.target.value)" />
```

### 事件发射
```typescript
// 类型安全的事件
const emit = defineEmits<{
  (e: 'select', node: TreeNode): void
  (e: 'reorder', payload: ReorderPayload): void
}>()

// 调用
emit('select', node)
```

## ANTI-PATTERNS

### 🚫 禁止
- 使用 Element Plus 组件
- 在组件中直接调用 `axios`（通过 props/callback 传递）
- 类型错误压制（`as any`, `@ts-ignore`）

### ⚠️ 注意
- `TreeNode.vue` 递归组件需要双 script 块：
  ```vue
  <script setup>...</script>
  <script>
  export default { name: 'TreeNode' }  // 递归名称解析
  </script>
  ```

## REFACTORING RECOMMENDATIONS

### SortPreviewModal.vue (799行)
**问题**: 模板中三级树结构代码重复（root → child → grandchild 相同代码重复3次）

**建议**: 提取递归 `SortPreviewNode.vue` 组件
```vue
<!-- SortPreviewNode.vue -->
<template>
  <div class="group flex items-center...">
    <GripVertical />
    <component :is="NodeTypeIcon..." />
    <span>{{ node.title }}</span>
    <!-- move buttons -->
  </div>
  <div v-if="node.children">
    <SortPreviewNode
      v-for="child in node.children"
      :node="child"
      :level="level + 1"
    />
  </div>
</template>
```

### TreeNode.vue (518行)
**问题**: 复杂的拖拽验证逻辑（循环引用、层级限制）

**建议**: 提取验证逻辑到 `composables/useTreeValidation.ts`
```typescript
// composables/useTreeValidation.ts
export function useTreeValidation(maxDepth: number = 3) {
  function wouldCreateCycle(nodeId: number, targetParentId: number, tree: TreeNode[]): boolean
  function wouldExceedDepth(node: TreeNode, targetParent: TreeNode): boolean
  return { wouldCreateCycle, wouldExceedDepth }
}
```

## UNIQUE STYLES

### Teleport 逃逸模式
```vue
<!-- CascadeSelect.vue - 解决父容器 overflow 裁剪 -->
<div ref="containerRef">
  <button ref="triggerRef">...</button>
  <Teleport to="body">
    <div v-if="isOpen" :style="{
      position: 'fixed',
      top: `${position.top}px`,
      left: `${position.left}px`,
      width: `${position.width}px`
    }">
      <!-- 下拉内容 -->
    </div>
  </Teleport>
</div>
```

### 服务组件模式（Toast）
```typescript
// useToast.ts - 单例模式
let toastInstance: ToastMethods | null = null

export function useToast(): ToastMethods {
  if (!toastInstance) {
    const app = createApp(Toast)
    toastInstance = app.mount('#toast-mount-point')
  }
  return toastInstance
}

// 双导出模式
export const Toast: ToastMethods = {
  success: (msg) => useToast().success(msg),
  error: (msg) => useToast().error(msg)
}

// 使用
const toast = useToast()
toast.success('操作成功')

// 或直接
Toast.error('操作失败')
```

### 图标映射模式
```typescript
// EmptyState.vue
const iconMap: Record<string, LucideIcon> = {
  'inbox': Inbox,
  'file-x': FileX,
  'search-x': SearchX,
}

const IconComponent = computed(() => iconMap[props.icon] || Inbox)

// 模板
<component :is="IconComponent" :size="64" />
```

### 递归组件事件转发
```vue
<!-- TreeNode.vue -->
<template>
  <div>
    <!-- 当前节点 -->
    <div @click="emit('select', node)">{{ node.title }}</div>
    
    <!-- 递归子节点，转发所有事件 -->
    <TreeNode
      v-for="child in node.children"
      :key="child.id"
      :node="child"
      @select="emit('select', $event)"
      @edit="emit('edit', $event)"
      @delete="emit('delete', $event)"
    />
  </div>
</template>
```

### 计算属性 getter/setter（vuedraggable）
```typescript
const childrenList = computed({
  get: () => props.node.children || [],
  set: (value) => {
    emit('update-children', {
      nodeId: props.node.id,
      children: value
    })
  }
})

// 模板
<draggable v-model="childrenList">...</draggable>
```

## TESTING

组件测试位于 `components/**/*.test.ts`：

```typescript
describe('TreeNode', () => {
  it('应该渲染节点标题', () => {
    const node = { id: 1, title: '测试节点', children: [] }
    const wrapper = mount(TreeNode, {
      props: { node },
      global: { stubs: { TreeNode: false } }  // 不 stub 递归组件
    })
    expect(wrapper.text()).toContain('测试节点')
  })
  
  it('应该发射 select 事件', async () => {
    const wrapper = mount(TreeNode, { props: { node } })
    await wrapper.find('[data-testid="node"]').trigger('click')
    expect(wrapper.emitted('select')).toBeTruthy()
  })
})
```
