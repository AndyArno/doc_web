<template>
  <div class="space-y-6">
    <!-- 页面标题与操作 -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">教材管理</h1>
        <p class="text-sm text-gray-500 mt-1">管理系统中的所有教材及其发布状态</p>
      </div>
      <button 
        v-if="userStore.isSuperAdmin"
        @click="openCreateModal"
        class="flex items-center justify-center gap-2 px-4 py-2.5 bg-brand-600 text-white rounded-xl font-bold hover:bg-brand-500 transition-all shadow-brand hover:shadow-brand-lg"
      >
        <Plus class="w-4 h-4" />
        创建新教材
      </button>
    </div>

    <!-- 搜索与筛选 -->
    <div class="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm flex flex-col md:flex-row gap-4">
      <div class="flex-1 relative">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input 
          v-model="queryParams.keyword"
          type="text"
          placeholder="搜索教材标题或描述..."
          class="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-100 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
          @keyup.enter="handleSearch"
        />
      </div>
      <div class="flex gap-2">
        <select 
          v-model="queryParams.status"
          class="px-4 py-2 bg-gray-50 border border-gray-100 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 appearance-none cursor-pointer"
          @change="handleSearch"
        >
          <option value="">全部状态</option>
          <option value="published">已发布</option>
          <option value="draft">草稿</option>
        </select>
        <button 
          @click="handleSearch"
          class="px-4 py-2 bg-gray-100 text-gray-700 rounded-xl text-sm font-bold hover:bg-gray-200 transition-all"
        >
          筛选
        </button>
      </div>
    </div>

    <!-- 数据列表 -->
    <div v-if="loading" class="py-20 flex flex-col items-center justify-center">
      <LoadingSpinner size="lg" />
      <p class="text-gray-400 text-sm mt-4 animate-pulse">正在加载教材数据...</p>
    </div>

    <template v-else>
      <!-- 桌面端表格 (md 以上显示) -->
      <div class="hidden md:block bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-gray-50/50 border-b border-gray-100">
              <th class="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider w-1/3">教材信息</th>
              <th class="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">状态</th>
              <th class="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">更新时间</th>
              <th class="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider text-right">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="book in textbooks" :key="book.id" class="hover:bg-gray-50/50 transition-colors group">
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-xl bg-brand-50 flex items-center justify-center text-brand-600 border border-brand-100">
                    <BookOpen class="w-5 h-5" />
                  </div>
                  <div class="max-w-[200px] lg:max-w-xs">
                    <div class="text-sm font-bold text-gray-900 truncate" :title="book.title">{{ book.title }}</div>
                    <div class="text-xs text-gray-400 mt-0.5 line-clamp-1">{{ book.description || '暂无描述' }}</div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4">
                <span 
                  class="px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider border"
                  :class="book.status === 'published' ? 'bg-green-50 text-green-600 border-green-100' : 'bg-gray-50 text-gray-400 border-gray-100'"
                >
                  {{ book.status === 'published' ? '已发布' : '草稿' }}
                </span>
              </td>
              <td class="px-6 py-4 text-sm text-gray-500 whitespace-nowrap">
                {{ formatDate(book.updated_at) }}
              </td>
              <td class="px-6 py-4 text-right">
                <div class="flex items-center justify-end gap-2">
                  <router-link 
                    :to="`/admin/textbooks/${book.id}`"
                    class="p-2 text-gray-400 hover:text-brand-600 hover:bg-brand-50 rounded-lg transition-all"
                    title="内容管理"
                  >
                    <Settings class="w-4 h-4" />
                  </router-link>
                  <button 
                    v-if="userStore.isSuperAdmin"
                    @click="openEditModal(book)"
                    class="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all"
                    title="编辑"
                  >
                    <Pencil class="w-4 h-4" />
                  </button>
                  <button 
                    v-if="userStore.role === 'admin' || userStore.isSuperAdmin"
                    @click="book.status === 'published' ? handleUnpublish(book) : handlePublish(book)"
                    :class="book.status === 'published' ? 'p-2 text-gray-400 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition-all' : 'p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-all'"
                    :title="book.status === 'published' ? '取消发布' : '发布'"
                  >
                    <component :is="book.status === 'published' ? 'EyeOff' : 'Eye'" class="w-4 h-4" />
                  </button>
                  <button 
                    v-if="userStore.isSuperAdmin"
                    @click="handleDelete(book)"
                    class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                    title="删除"
                  >
                    <Trash2 class="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 移动端卡片列表 (md 以下显示) -->
      <div class="md:hidden space-y-4">
        <div 
          v-for="book in textbooks" 
          :key="book.id"
          class="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm space-y-4"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex items-center gap-3 min-w-0">
              <div class="w-12 h-12 rounded-xl bg-brand-50 shrink-0 flex items-center justify-center text-brand-600 border border-brand-100">
                <BookOpen class="w-6 h-6" />
              </div>
              <div class="min-w-0">
                <div class="text-base font-bold text-gray-900 truncate">{{ book.title }}</div>
                <div class="text-xs text-gray-400 mt-0.5 line-clamp-2">{{ book.description || '暂无描述' }}</div>
              </div>
            </div>
            <span 
              class="shrink-0 px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider border"
              :class="book.status === 'published' ? 'bg-green-50 text-green-600 border-green-100' : 'bg-gray-50 text-gray-400 border-gray-100'"
            >
              {{ book.status === 'published' ? '已发布' : '草稿' }}
            </span>
          </div>
          
          <div class="pt-4 border-t border-gray-50 flex items-center justify-between">
            <div class="text-xs text-gray-400">
              更新于 {{ formatDate(book.updated_at) }}
            </div>
            <div class="flex items-center gap-2">
              <router-link 
                :to="`/admin/textbooks/${book.id}`"
                class="px-3 py-1.5 text-brand-600 bg-brand-50 rounded-lg text-sm font-bold transition-all"
              >
                管理内容
              </router-link>
              <button 
                v-if="userStore.isSuperAdmin"
                @click="openEditModal(book)"
                class="px-3 py-1.5 text-blue-600 bg-blue-50 rounded-lg text-sm font-bold transition-all"
              >
                编辑
              </button>
              <button 
                v-if="userStore.role === 'admin' || userStore.isSuperAdmin"
                @click="book.status === 'published' ? handleUnpublish(book) : handlePublish(book)"
                :class="book.status === 'published' ? 'px-3 py-1.5 text-orange-600 bg-orange-50 rounded-lg text-sm font-bold transition-all' : 'px-3 py-1.5 text-green-600 bg-green-50 rounded-lg text-sm font-bold transition-all'"
              >
                {{ book.status === 'published' ? '取消发布' : '发布' }}
              </button>
              <button 
                v-if="userStore.isSuperAdmin"
                @click="handleDelete(book)"
                class="px-3 py-1.5 text-red-600 bg-red-50 rounded-lg text-sm font-bold transition-all"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 无数据 -->
      <div v-if="textbooks.length === 0" class="py-20 text-center bg-white rounded-2xl border border-dashed border-gray-200">
        <div class="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
          <BookOpen class="w-8 h-8 text-gray-300" />
        </div>
        <p class="text-gray-400 font-medium">暂无教材数据</p>
      </div>
    </template>

    <!-- 创建教材弹窗 -->
    <Modal v-model:visible="createModalVisible" title="创建新教材" width="500px">
      <form @submit.prevent="handleSubmitCreate" class="space-y-4">
        <FormInput
          v-model="createForm.title"
          label="教材标题"
          placeholder="请输入教材标题"
          :error="createErrors.title"
        />
        <FormInput
          v-model="createForm.description"
          label="教材描述"
          placeholder="请输入教材描述（选填）"
        />
        <FormInput
          v-model="createForm.cover_image"
          label="封面图片"
          placeholder="请输入封面图片URL（选填）"
        />
      </form>
      <template #footer>
        <button
          type="button"
          @click="createModalVisible = false"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
        >
          取消
        </button>
        <button
          type="button"
          @click="handleSubmitCreate"
          :disabled="createLoading"
          class="px-4 py-2 text-sm font-medium text-white bg-brand-600 rounded-lg hover:bg-brand-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <Loader2 v-if="createLoading" class="w-4 h-4 animate-spin" />
          {{ createLoading ? '创建中...' : '创建' }}
        </button>
      </template>
    </Modal>

    <!-- 编辑教材弹窗 -->
    <Modal v-model:visible="editModalVisible" title="编辑教材" width="500px">
      <form @submit.prevent="handleSubmitEdit" class="space-y-4">
        <FormInput
          v-model="editForm.title"
          label="教材标题"
          placeholder="请输入教材标题"
          :error="editErrors.title"
        />
        <FormInput
          v-model="editForm.description"
          label="教材描述"
          placeholder="请输入教材描述（选填）"
        />
        <FormInput
          v-model="editForm.cover_image"
          label="封面图片"
          placeholder="请输入封面图片URL（选填）"
        />
      </form>
      <template #footer>
        <button
          type="button"
          @click="editModalVisible = false"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
        >
          取消
        </button>
        <button
          type="button"
          @click="handleSubmitEdit"
          :disabled="editLoading"
          class="px-4 py-2 text-sm font-medium text-white bg-brand-600 rounded-lg hover:bg-brand-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <Loader2 v-if="editLoading" class="w-4 h-4 animate-spin" />
          {{ editLoading ? '保存中...' : '保存' }}
        </button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
/**
 * @file Textbooks.vue
 * @description 教材管理列表页面，支持移动端卡片化展示
 */
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { 
  Plus, 
  Search, 
  BookOpen, 
  Settings, 
  Trash2, 
  ChevronLeft, 
  ChevronRight,
  Loader2,
  Eye,
  EyeOff,
  Pencil
} from 'lucide-vue-next'
import { getTextbooks, deleteTextbook, createTextbook, updateTextbook, publishTextbook, unpublishTextbook } from '@/api/textbook'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Modal from '@/components/Modal.vue'
import FormInput from '@/components/FormInput.vue'
import { useUserStore } from '@/stores/user'
import { useToast } from '@/composables/useToast'

const route = useRoute()
const userStore = useUserStore()
const toast = useToast()

const loading = ref(true)
const textbooks = ref([])
const total = ref(0)

// 创建教材弹窗状态
const createModalVisible = ref(false)
const createLoading = ref(false)
const createForm = reactive({
  title: '',
  description: '',
  cover_image: ''
})
const createErrors = reactive({
  title: ''
})

// 编辑教材弹窗状态
const editModalVisible = ref(false)
const editLoading = ref(false)
const editingBook = ref(null)
const editForm = reactive({
  title: '',
  description: '',
  cover_image: ''
})
const editErrors = reactive({
  title: ''
})

const queryParams = reactive({
  page: 1,
  page_size: 10,
  status: route.query.status || '',
  keyword: ''
})

/**
 * 监听路由中的 status 参数变化
 */
watch(() => route.query.status, (newStatus) => {
  queryParams.status = newStatus || ''
  handleSearch()
})

/**
 * 加载数据
 */
const loadData = async () => {
  loading.value = true
  try {
    const params = {
      ...queryParams,
      // 如果 status 是空字符串，就不传这个参数给后端，表示查全部
      status: queryParams.status === '' ? undefined : queryParams.status,
      for_management: true
    }
    const data = await getTextbooks(params)
    textbooks.value = data.items
    total.value = data.total
  } catch (error) {
    // API 拦截器已处理错误 toast
  } finally {
    loading.value = false
  }
}

/**
 * 搜索处理
 */
const handleSearch = () => {
  queryParams.page = 1
  loadData()
}

/**
 * 格式化日期
 */
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 操作处理
 */
const openCreateModal = () => {
  createForm.title = ''
  createForm.description = ''
  createForm.cover_image = ''
  createErrors.title = ''
  createModalVisible.value = true
}

/**
 * 验证表单
 */
const validateForm = () => {
  let isValid = true
  createErrors.title = ''
  
  if (!createForm.title.trim()) {
    createErrors.title = '请输入教材标题'
    isValid = false
  } else if (createForm.title.length > 200) {
    createErrors.title = '标题不能超过200个字符'
    isValid = false
  }
  
  return isValid
}

/**
 * 提交创建教材
 */
const handleSubmitCreate = async () => {
  if (!validateForm()) return
  
  createLoading.value = true
  try {
    const data = {
      title: createForm.title.trim(),
      description: createForm.description.trim() || undefined,
      cover_image: createForm.cover_image.trim() || undefined
    }
    await createTextbook(data)
    toast.success('教材创建成功')
    createModalVisible.value = false
    loadData()
  } catch (error) {
    // API 拦截器已处理错误 toast
  } finally {
    createLoading.value = false
  }
}
const handleDelete = async (book) => {
  if (confirm(`确定要删除教材《${book.title}》吗？这将不可恢复！`)) {
    try {
      await deleteTextbook(book.id)
      toast.success('删除成功')
      loadData()
    } catch (error) {
      // API 拦截器已处理错误 toast
    }
  }
}

/**
 * 发布教材
 */
const handlePublish = async (book) => {
  if (!confirm(`确定要发布教材《${book.title}》吗？`)) return
  try {
    await publishTextbook(book.id)
    toast.success('教材发布成功')
    await loadData()
  } catch (error) {
    // API 拦截器已处理错误 toast
  }
}

/**
 * 取消发布教材
 */
const handleUnpublish = async (book) => {
  if (!confirm(`确定要取消发布教材《${book.title}》吗？`)) return
  try {
    await unpublishTextbook(book.id)
    toast.success('教材已取消发布')
    await loadData()
  } catch (error) {
    // API 拦截器已处理错误 toast
  }
}

/**
 * 打开编辑弹窗
 */
const openEditModal = (book) => {
  editingBook.value = book
  editForm.title = book.title || ''
  editForm.description = book.description || ''
  editForm.cover_image = book.cover_image || ''
  editErrors.title = ''
  editModalVisible.value = true
}

/**
 * 验证编辑表单
 */
const validateEditForm = () => {
  let isValid = true
  editErrors.title = ''
  
  if (!editForm.title.trim()) {
    editErrors.title = '请输入教材标题'
    isValid = false
  } else if (editForm.title.length > 200) {
    editErrors.title = '标题不能超过200个字符'
    isValid = false
  }
  
  return isValid
}

/**
 * 提交编辑教材
 */
const handleSubmitEdit = async () => {
  if (!validateEditForm()) return
  
  editLoading.value = true
  try {
    const data = {
      title: editForm.title.trim(),
      description: editForm.description.trim() || undefined,
      cover_image: editForm.cover_image.trim() || undefined
    }
    await updateTextbook(editingBook.value.id, data)
    toast.success('教材更新成功')
    editModalVisible.value = false
    loadData()
  } catch (error) {
    // API 拦截器已处理错误 toast
  } finally {
    editLoading.value = false
  }
}

onMounted(loadData)
</script>
