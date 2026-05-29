<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">权限管理</h1>
        <p class="text-sm text-gray-500 mt-1">管理用户对教材的访问权限，查看权限继承关系</p>
      </div>
    </div>

    <!-- 用户选择区 -->
    <div class="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm">
      <div class="flex flex-col md:flex-row gap-4">
        <div class="flex-1 relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input 
            v-model="searchKeyword"
            type="text"
            placeholder="搜索用户名或邮箱..."
            class="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-100 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
            @keyup.enter="handleSearchUser"
          />
        </div>
        <button 
          @click="handleSearchUser"
          class="px-4 py-2 bg-brand-600 text-white rounded-xl text-sm font-bold hover:bg-brand-500 transition-all shadow-brand hover:shadow-brand-lg"
        >
          搜索用户
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="py-20 flex flex-col items-center justify-center">
      <LoadingSpinner size="lg" />
      <p class="text-gray-400 text-sm mt-4 animate-pulse">正在加载...</p>
    </div>

    <!-- 主内容区 -->
    <template v-else-if="selectedUser">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- 用户信息卡片 -->
        <div class="lg:col-span-1">
          <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <div class="p-6 border-b border-gray-100">
              <div class="flex items-center gap-4">
                <div class="w-14 h-14 rounded-full bg-brand-50 flex items-center justify-center text-brand-600 font-bold border border-brand-100">
                  <UserIcon class="w-7 h-7" />
                </div>
                <div>
                  <h3 class="text-lg font-bold text-gray-900">{{ selectedUser.username }}</h3>
                  <span 
                    class="px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider border"
                    :class="getRoleBadgeClass(selectedUser.role)"
                  >
                    {{ getRoleName(selectedUser.role) }}
                  </span>
                </div>
              </div>
            </div>
            <div class="p-6 space-y-3 text-sm">
              <div class="flex justify-between">
                <span class="text-gray-500">邮箱</span>
                <span class="text-gray-900">{{ selectedUser.email }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">状态</span>
                <span :class="selectedUser.is_active ? 'text-green-600' : 'text-red-600'">
                  {{ selectedUser.is_active ? '正常' : '已禁用' }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">用户ID</span>
                <span class="text-gray-900">{{ selectedUser.id }}</span>
              </div>
            </div>
            <!-- 权限继承说明 -->
            <div class="p-6 bg-gray-50 border-t border-gray-100">
              <h4 class="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
                <Shield class="w-4 h-4" />
                权限继承
              </h4>
              <div class="space-y-2 text-xs">
                <div v-if="selectedUser.role === 'super_admin'" class="flex items-start gap-2">
                  <CheckCircle class="w-4 h-4 text-purple-500 mt-0.5 flex-shrink-0" />
                  <span class="text-gray-600">超级管理员自动拥有所有权限，无需额外授权</span>
                </div>
                <div v-else-if="selectedUser.role === 'admin'" class="flex items-start gap-2">
                  <CheckCircle class="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                  <span class="text-gray-600">管理员自动拥有所有教材的操作权限</span>
                </div>
                <div v-else-if="selectedUser.role === 'editor'" class="flex items-start gap-2">
                  <AlertCircle class="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
                  <span class="text-gray-600">编辑需要显式授权具体权限</span>
                </div>
                <div v-else class="flex items-start gap-2">
                  <XCircle class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                  <span class="text-gray-600">普通用户仅可访问公开内容</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 权限列表 -->
        <div class="lg:col-span-2 space-y-6">
          <!-- 当前权限 -->
          <div class="bg-white rounded-2xl border border-gray-100 shadow-sm">
            <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <h3 class="font-bold text-gray-900 flex items-center gap-2">
                <Key class="w-5 h-5 text-brand-600" />
                当前权限
              </h3>
              <button 
                v-if="canAssignPermissions"
                @click="openAssignModal"
                class="flex items-center gap-2 px-3 py-1.5 text-sm font-bold text-brand-600 bg-brand-50 rounded-lg hover:bg-brand-100 transition-all"
              >
                <Plus class="w-4 h-4" />
                授予教材权限
              </button>
            </div>
            
            <div v-if="userPermissions.length === 0" class="p-8 text-center">
              <div class="w-12 h-12 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-3">
                <Key class="w-6 h-6 text-gray-300" />
              </div>
              <p class="text-gray-400 text-sm">暂无权限记录</p>
              <p class="text-gray-300 text-xs mt-1" v-if="selectedUser.role === 'super_admin' || selectedUser.role === 'admin'">
                角色权限已自动继承
              </p>
            </div>
            
            <div v-else class="divide-y divide-gray-50">
              <div 
                v-for="perm in userPermissions" 
                :key="perm.id"
                class="p-4 hover:bg-gray-50/50 transition-colors"
              >
                <div class="flex items-center justify-between">
                  <div class="flex-1">
                    <div class="flex items-center gap-3">
                      <BookOpen class="w-5 h-5 text-gray-400" />
                      <div>
                        <div class="font-medium text-gray-900">{{ getTextbookTitle(perm.textbook_id) }}</div>
                        <div class="text-xs text-gray-400 mt-0.5">教材ID: {{ perm.textbook_id }}</div>
                      </div>
                    </div>
                  </div>
                  <div class="flex items-center gap-4">
                    <div class="flex items-center gap-2">
                      <span 
                        v-if="perm.can_access"
                        class="px-2 py-0.5 text-xs font-bold bg-green-50 text-green-600 rounded"
                      >编辑权限</span>
                    </div>
                    <button 
                      v-if="canRevokePermissions"
                      @click="handleRevokePermission(perm)"
                      class="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                      title="撤销权限"
                    >
                      <Trash2 class="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 无选中用户提示 -->
    <div v-else class="py-20 text-center bg-white rounded-2xl border border-dashed border-gray-200">
      <div class="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
        <UserIcon class="w-8 h-8 text-gray-300" />
      </div>
      <p class="text-gray-400 font-medium">搜索并选择用户以管理权限</p>
    </div>

    <!-- 授予教材权限弹窗 -->
    <Modal v-model:visible="assignModalVisible" title="授予教材权限" width="500px">
      <form @submit.prevent="handleSubmitAssign" class="space-y-4">
        <FormSelect
          v-model="assignForm.textbook_id"
          label="选择教材"
          :options="textbookOptions"
          placeholder="请选择要授权的教材"
          :error="assignErrors.textbook_id"
        />
        <p class="text-sm text-gray-500">授予后，该用户将拥有此教材的访问权限。</p>
      </form>
      <template #footer>
        <button
          type="button"
          @click="assignModalVisible = false"
          class="px-4 py-2 text-sm font-bold text-gray-700 bg-gray-100 rounded-xl hover:bg-gray-200 transition-all"
        >
          取消
        </button>
        <button
          type="submit"
          @click="handleSubmitAssign"
          :disabled="assignLoading"
          class="flex items-center gap-2 px-4 py-2 text-sm font-bold text-white bg-brand-600 rounded-xl hover:bg-brand-500 transition-all disabled:opacity-50"
        >
          <Loader2 v-if="assignLoading" class="w-4 h-4 animate-spin" />
          {{ assignLoading ? '提交中...' : '确认授予' }}
        </button>
      </template>
    </Modal>

    <!-- 撤销权限确认对话框 -->
    <ConfirmDialog
      v-model:visible="revokeConfirmVisible"
      title="撤销权限"
      :message="revokeTargetPerm ? `确定要撤销该用户对「${getTextbookTitle(revokeTargetPerm.textbook_id)}」的权限吗？` : ''"
      type="danger"
      confirm-text="确认撤销"
      @confirm="confirmRevokePermission"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { 
  Search, 
  User as UserIcon, 
  Shield, 
  Key, 
  Plus, 
  Trash2, 
  CheckCircle,
  AlertCircle,
  XCircle,
  BookOpen,
  Loader2
} from 'lucide-vue-next'
import { getUsers, getUserById, assignUserPermissions, revokeUserPermission } from '@/api/user'
import { getTextbooks } from '@/api/textbook'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Modal from '@/components/Modal.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import FormSelect from '@/components/FormSelect.vue'
import { useToast } from '@/composables/useToast'
import type { User, UserDetail, Permission, Textbook, Role } from '@/types/api'

const toast = useToast()
const userStore = useUserStore()

const loading = ref(false)
const searchKeyword = ref('')
const selectedUser = ref<UserDetail | null>(null)
const userPermissions = ref<Permission[]>([])
const textbooks = ref<Textbook[]>([])

const assignModalVisible = ref(false)
const assignLoading = ref(false)
const assignForm = reactive({
  textbook_id: ''
})
const assignErrors = reactive({
  textbook_id: ''
})

// 撤销权限确认对话框状态
const revokeConfirmVisible = ref(false)
const revokeTargetPerm = ref<Permission | null>(null)

const textbookOptions = computed(() => 
  textbooks.value.map(t => ({ value: String(t.id), label: t.title }))
)

const canAssignPermissions = computed(() => {
  const role = userStore.role
  return role === 'super_admin' || role === 'admin'
})

const canRevokePermissions = computed(() => {
  const role = userStore.role
  return role === 'super_admin' || role === 'admin'
})

const handleSearchUser = async () => {
  if (!searchKeyword.value.trim()) {
    toast.warning('请输入搜索关键词')
    return
  }
  
  loading.value = true
  try {
    const data = await getUsers({ keyword: searchKeyword.value, page_size: 10 })
    if (data.items.length === 0) {
      toast.warning('未找到匹配的用户')
      selectedUser.value = null
    } else if (data.items.length === 1) {
      await selectUser(data.items[0])
    } else {
      // 多个结果时选择第一个
      await selectUser(data.items[0])
      toast.info(`找到 ${data.items.length} 个用户，显示第一个`)
    }
  } catch {
    // API 拦截器已处理错误
  } finally {
    loading.value = false
  }
}

const selectUser = async (user: User) => {
  try {
    const detail = await getUserById(user.id)
    selectedUser.value = detail
    userPermissions.value = detail.permissions || []
  } catch {
    // API 拦截器已处理错误
  }
}

const loadTextbooks = async () => {
  try {
    const data = await getTextbooks({ page_size: 100 })
    textbooks.value = data.items
  } catch {
    // API 拦截器已处理错误
  }
}

const getTextbookTitle = (textbookId: number): string => {
  const textbook = textbooks.value.find(t => t.id === textbookId)
  return textbook?.title || `教材 #${textbookId}`
}

const getRoleName = (role: Role): string => {
  const roles: Record<Role, string> = {
    'super_admin': '超级管理员',
    'admin': '管理员',
    'editor': '编辑',
    'user': '普通用户'
  }
  return roles[role] || role
}

const getRoleBadgeClass = (role: Role): string => {
  const classes: Record<Role, string> = {
    'super_admin': 'bg-purple-50 text-purple-600 border-purple-100',
    'admin': 'bg-blue-50 text-blue-600 border-blue-100',
    'editor': 'bg-amber-50 text-amber-600 border-amber-100',
    'user': 'bg-slate-50 text-slate-500 border-slate-100'
  }
  return classes[role] || 'bg-slate-50 text-slate-500 border-slate-100'
}

const openAssignModal = () => {
  assignForm.textbook_id = ''
  assignErrors.textbook_id = ''
  assignModalVisible.value = true
}

const validateAssignForm = (): boolean => {
  let isValid = true
  assignErrors.textbook_id = ''
  
  if (!assignForm.textbook_id) {
    assignErrors.textbook_id = '请选择教材'
    isValid = false
  }
  
  return isValid
}

const handleSubmitAssign = async () => {
  if (!validateAssignForm() || !selectedUser.value) return
  
  assignLoading.value = true
  try {
    await assignUserPermissions(selectedUser.value.id, {
      textbook_id: Number(assignForm.textbook_id),
      can_access: true
    })
    toast.success('权限授予成功')
    assignModalVisible.value = false
    
    // 刷新用户权限
    const detail = await getUserById(selectedUser.value.id)
    selectedUser.value = detail
    userPermissions.value = detail.permissions || []
  } catch {
    // API 拦截器已处理错误
  } finally {
    assignLoading.value = false
  }
}

const handleRevokePermission = (perm: Permission) => {
  if (!selectedUser.value) return
  // 显示确认对话框
  revokeTargetPerm.value = perm
  revokeConfirmVisible.value = true
}

const confirmRevokePermission = async () => {
  if (!selectedUser.value || !revokeTargetPerm.value) return
  
  try {
    await revokeUserPermission(selectedUser.value.id, revokeTargetPerm.value.textbook_id)
    toast.success('权限已撤销')
    
    // 刷新用户权限
    const detail = await getUserById(selectedUser.value.id)
    selectedUser.value = detail
    userPermissions.value = detail.permissions || []
  } catch {
    // API 拦截器已处理错误
  }
}

const formatTime = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadTextbooks()
})
</script>
