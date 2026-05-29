# AGENTS.md — Frontend Views Layer

**Generated:** 2026-04-08  
**Parent:** `/AGENTS.md`

## OVERVIEW

页面组件层，负责路由级别的页面。管理后台页面使用 `AdminLayout` 布局，公开页面使用 `AppHeader` + 自定义布局。

## STRUCTURE

```
views/
├── Home.vue                  # 首页：教材卡片网格
├── Login.vue                 # 登录
├── Register.vue              # 注册
├── ForgotPassword.vue        # 忘记密码
├── ChangePassword.vue        # 强制修改密码
├── TextbookReader.vue        # 教材阅读器（三栏布局）
├── SearchResults.vue         # 搜索结果
├── NotFound.vue              # 404 页面
└── admin/
    ├── Dashboard.vue         # 管理后台首页
    ├── Users.vue             # 用户管理 ⚠️ 1005行
    ├── Textbooks.vue         # 教材管理
    ├── ContentManager.vue    # 内容管理 ⚠️ 1467行，急需重构
    ├── Editor.vue            # Markdown 编辑器
    ├── MediaLibrary.vue      # 媒体库 ⚠️ 1146行
    ├── VersionHistory.vue    # 版本历史
    └── PermissionManager.vue # 权限管理
```

## WHERE TO LOOK

| 任务 | 文件 | 关键特性 |
|------|------|----------|
| 添加公开页面 | `views/*.vue` | 使用 `AppHeader` 组件 |
| 添加管理页面 | `views/admin/*.vue` | 使用 `AdminLayout` 布局 |
| 表格+卡片响应式 | `Users.vue`, `Textbooks.vue` | `hidden md:block` / `md:hidden` |
| 树形拖拽 | `ContentManager.vue` | `vuedraggable` |
| 文件上传 | `MediaLibrary.vue`, `ContentManager.vue` | `FormData` + progress |
| 版本对比 | `VersionHistory.vue` | `DiffViewer` 组件 |

## CONVENTIONS

### 路由配置
```typescript
// router/index.ts
{
  path: '/admin/users',
  name: 'Users',
  component: () => import('@/views/admin/Users.vue'),
  meta: {
    title: '用户管理',
    requiresAuth: true,
    roles: ['super_admin', 'admin']  // 角色限制
  }
}
```

### 页面结构（管理后台）
```vue
<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between">
      <h1>页面标题</h1>
      <button @click="handleCreate">新建</button>
    </div>
    
    <!-- 搜索/筛选 -->
    <div class="flex gap-4">
      <input v-model="search" />
      <select v-model="filter" />
    </div>
    
    <!-- 桌面端表格 -->
    <table class="hidden md:block">...</table>
    
    <!-- 移动端卡片 -->
    <div class="md:hidden space-y-4">...</div>
  </div>
</template>
```

### 响应式模式
```vue
<!-- 模式1：表格 vs 卡片 -->
<table class="hidden md:block">...</table>
<div class="md:hidden space-y-4">...</div>

<!-- 模式2：双栏 vs 单栏切换 -->
<div class="hidden md:block md:w-1/3">目录</div>
<div class="md:hidden">
  <button @click="showTree = !showTree">切换</button>
  <div v-if="showTree">目录</div>
</div>
```

### 表单验证
```typescript
const form = reactive({ username: '', email: '' })
const errors = reactive({ username: '', email: '' })

function validate(): boolean {
  let isValid = true
  errors.username = ''
  if (!form.username.trim()) {
    errors.username = '用户名不能为空'
    isValid = false
  }
  return isValid
}
```

### API 调用
```typescript
const loading = ref(true)
const data = ref([])

onMounted(async () => {
  try {
    data.value = await getXxxList()
  } catch (error) {
    // Axios 拦截器已处理 Toast
  } finally {
    loading.value = false
  }
})
```

## ANTI-PATTERNS

### 🚫 禁止
- 在视图中直接调用 `axios`（使用 `@/api/*` 封装）
- 使用 `Element Plus` 组件（用 Tailwind CSS + Lucide）
- 硬编码 API URL（使用 `@/api/*`）

### ⚠️ 注意
- 状态管理：认证用 Pinia (`useUserStore`)，其他用组件本地状态

## REFACTORING PRIORITY

### ContentManager.vue (1467行) — 最高优先级
```
ContentManager.vue (orchestrator ~300行) →
├── composables/
│   ├── useChapterTree.ts      # Tree state, loading, selection
│   ├── useChapterDrag.ts      # Drag-drop logic, validation
│   ├── useChapterSort.ts      # Sort mode, preview, apply
│   └── useChapterUpload.ts    # MD/ZIP upload
└── components/
    ├── ChapterTreePanel.vue   # Left sidebar tree
    ├── ChapterPreview.vue     # Right preview panel
    └── modals/                # Extract each modal
```

### MediaLibrary.vue (1146行)
```
MediaLibrary.vue →
├── MediaTable.vue         # Desktop table view
├── MediaCardList.vue      # Mobile card list
├── MediaPreviewModal.vue  # Image preview
└── MultiSelectBar.vue     # Batch action bar
```

### Users.vue (1005行)
```
Users.vue →
├── UserTable.vue          # Desktop table
├── UserCard.vue           # Mobile card
└── UserEditModal.vue      # Edit modal with tabs
```

## UNIQUE STYLES

### 强制修改密码流程
```typescript
// router/index.ts - 路由守卫
if (userStore.userInfo?.must_change_password && to.path !== '/change-password') {
  next('/change-password')
  return
}
```

### 角色层级 UI 过滤
```typescript
// Users.vue - 根据当前角色过滤可选角色
const roleOptions = computed(() => {
  if (userStore.isSuperAdmin) {
    return allRoles  // super_admin 可创建所有角色
  }
  if (userStore.role === 'admin') {
    return allRoles.filter(r => r !== 'super_admin')  // admin 不能创建超管
  }
  return []
})
```

### 拖拽预览 + 确认模式
```typescript
// ContentManager.vue
const localTree = ref([])  // 本地预览状态
const hasChanges = ref(false)

async function handleDrop(event) {
  // 修改本地状态
  localTree.value = applyDrag(localTree.value, event)
  hasChanges.value = true
}

async function confirmChanges() {
  await applySortChanges(localTree.value)
  hasChanges.value = false
}

// 页面离开前提醒
onBeforeRouteLeave((to, from, next) => {
  if (hasChanges.value) {
    if (confirm('有未保存的更改，确定离开？')) {
      next()
    } else {
      next(false)
    }
  } else {
    next()
  }
})
```

### 同步滚动编辑器
```typescript
// Editor.vue
const syncScrollEnabled = ref(true)

function handleEditorScroll() {
  if (!syncScrollEnabled.value) return
  const line = getFirstVisibleLine()
  scrollToPreviewLine(line)
}

function handlePreviewScroll() {
  if (!syncScrollEnabled.value) return
  const element = getFirstVisibleElement()
  scrollToEditorLine(element.dataset.sourceLine)
}
```

## TESTING

视图测试位于 `views/**/*.test.ts`：

```typescript
describe('Users.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })
  
  it('应该显示用户列表', async () => {
    const wrapper = mount(Users)
    await wrapper.vm.$nextTick()
    expect(wrapper.find('table').exists()).toBe(true)
  })
})
```
