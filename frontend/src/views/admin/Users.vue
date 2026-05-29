<template>
  <div class="space-y-6">
    <!-- 页面标题与操作 -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">用户管理</h1>
        <p class="text-sm text-gray-500 mt-1">管理系统用户信息、角色及教材访问权限</p>
      </div>
      <button 
        @click="openCreateModal"
        class="flex items-center justify-center gap-2 px-4 py-2.5 bg-brand-600 text-white rounded-xl font-bold hover:bg-brand-500 transition-all shadow-brand hover:shadow-brand-lg"
      >
        <UserPlus class="w-4 h-4" />
        新增用户
      </button>
    </div>

    <!-- 搜索与筛选 -->
    <div class="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm flex flex-col md:flex-row gap-4">
      <div class="flex-1 relative">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input 
          v-model="queryParams.keyword"
          type="text"
          placeholder="搜索用户名或邮箱..."
          class="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-100 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
          @keyup.enter="handleSearch"
        />
      </div>
      <div class="flex gap-2">
        <select 
          v-model="queryParams.role"
          class="px-4 py-2 bg-gray-50 border border-gray-100 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 appearance-none cursor-pointer"
          @change="handleSearch"
        >
          <option value="">全部角色</option>
          <option value="super_admin">超级管理员</option>
          <option value="admin">管理员</option>
          <option value="editor">编辑</option>
          <option value="user">普通用户</option>
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
      <p class="text-gray-400 text-sm mt-4 animate-pulse">正在加载用户数据...</p>
    </div>

    <template v-else>
      <!-- 桌面端表格 (md 以上显示) -->
      <div class="hidden md:block bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-gray-50/50 border-b border-gray-100">
              <th class="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">用户信息</th>
              <th class="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">角色</th>
              <th class="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">邮箱</th>
              <th class="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider text-right">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="user in users" :key="user.id" class="hover:bg-gray-50/50 transition-colors group">
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-full bg-brand-50 flex items-center justify-center text-brand-600 font-bold border border-brand-100 overflow-hidden">
                    <img v-if="user.avatar" :src="user.avatar" class="w-full h-full object-cover" />
                    <UserIcon v-else class="w-5 h-5" />
                  </div>
                  <div>
                    <div class="text-sm font-bold text-gray-900">{{ user.username }}</div>
                    <div class="text-xs text-gray-400 mt-0.5">ID: {{ user.id }}</div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4">
                <span 
                  class="px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider border"
                  :class="getRoleBadgeClass(user.role)"
                >
                  {{ getRoleName(user.role) }}
                </span>
              </td>
              <td class="px-6 py-4 text-sm text-gray-500">{{ user.email }}</td>
              <td class="px-6 py-4 text-right">
                <div class="flex items-center justify-end gap-2">
                  <button 
                    @click="openEditModal(user)"
                    class="p-2 text-gray-400 hover:text-brand-600 hover:bg-brand-50 rounded-lg transition-all"
                    title="编辑"
                  >
                    <Edit2 class="w-4 h-4" />
                  </button>
                  <button 
                    @click="handleDelete(user)"
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
          v-for="user in users" 
          :key="user.id"
          class="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm space-y-4"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 rounded-full bg-brand-50 flex items-center justify-center text-brand-600 font-bold border border-brand-100 overflow-hidden">
                <img v-if="user.avatar" :src="user.avatar" class="w-full h-full object-cover" />
                <UserIcon v-else class="w-6 h-6" />
              </div>
              <div>
                <div class="text-base font-bold text-gray-900">{{ user.username }}</div>
                <div class="text-xs text-gray-400">ID: {{ user.id }}</div>
              </div>
            </div>
            <span 
              class="px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider border"
              :class="getRoleBadgeClass(user.role)"
            >
              {{ getRoleName(user.role) }}
            </span>
          </div>
          
          <div class="pt-4 border-t border-gray-50 flex items-center justify-between text-sm">
            <div class="text-gray-500">{{ user.email }}</div>
            <div class="flex items-center gap-2">
              <button 
                @click="openEditModal(user)"
                class="px-3 py-1.5 text-brand-600 bg-brand-50 rounded-lg font-bold transition-all"
              >
                编辑
              </button>
              <button 
                @click="handleDelete(user)"
                class="px-3 py-1.5 text-red-600 bg-red-50 rounded-lg font-bold transition-all"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 无数据 -->
      <div v-if="users.length === 0" class="py-20 text-center bg-white rounded-2xl border border-dashed border-gray-200">
        <div class="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
          <Users class="w-8 h-8 text-gray-300" />
        </div>
        <p class="text-gray-400 font-medium">没有找到符合条件的用户</p>
      </div>

      <!-- 分页 (简单实现) -->
      <div v-if="total > queryParams.page_size" class="mt-8 flex items-center justify-center gap-4">
        <button 
          :disabled="queryParams.page === 1"
          @click="changePage(queryParams.page - 1)"
          class="p-2 rounded-xl border border-gray-200 disabled:opacity-30 hover:bg-gray-50 transition-all"
        >
          <ChevronLeft class="w-5 h-5" />
        </button>
        <span class="text-sm font-bold text-gray-600">{{ queryParams.page }} / {{ Math.ceil(total / queryParams.page_size) }}</span>
        <button 
          :disabled="queryParams.page * queryParams.page_size >= total"
          @click="changePage(queryParams.page + 1)"
          class="p-2 rounded-xl border border-gray-200 disabled:opacity-30 hover:bg-gray-50 transition-all"
        >
          <ChevronRight class="w-5 h-5" />
        </button>
      </div>
    </template>

    <!-- 创建用户弹窗 -->
    <Modal v-model:visible="createModalVisible" title="新增用户" width="480px">
      <form @submit.prevent="handleSubmitCreate" class="space-y-4">
        <FormInput
          v-model="createForm.username"
          label="用户名"
          placeholder="请输入用户名"
          :error="createErrors.username"
        />
        <FormInput
          v-model="createForm.email"
          label="邮箱"
          type="email"
          placeholder="请输入邮箱"
          :error="createErrors.email"
        />
        <FormInput
          v-model="createForm.password"
          label="密码"
          type="password"
          placeholder="请输入密码（至少8位，包含大写字母和数字）"
          :error="createErrors.password"
        />
        <FormSelect
          v-model="createForm.role"
          label="角色"
          :options="roleOptions"
          placeholder="请选择角色"
          :error="createErrors.role"
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
          type="submit"
          @click="handleSubmitCreate"
          :disabled="createLoading"
          class="px-4 py-2 text-sm font-medium text-white bg-brand-600 rounded-lg hover:bg-brand-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <Loader2 v-if="createLoading" class="w-4 h-4 animate-spin" />
          {{ createLoading ? '创建中...' : '确认创建' }}
        </button>
      </template>
    </Modal>

    <!-- 编辑用户弹窗 -->
    <Modal v-model:visible="editModalVisible" :title="editingUser ? `编辑用户 - ${editingUser.username}` : '编辑用户'" width="600px">
      <!-- Tabs -->
      <div class="flex border-b border-gray-100 mb-4">
        <button
          @click="activeTab = 'basic'"
          class="px-4 py-2 text-sm font-medium border-b-2 transition-colors"
          :class="activeTab === 'basic' ? 'border-brand-600 text-brand-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
        >
          基本信息
        </button>
        <button
          @click="activeTab = 'password'"
          class="px-4 py-2 text-sm font-medium border-b-2 transition-colors"
          :class="activeTab === 'password' ? 'border-brand-600 text-brand-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
        >
          密码
        </button>
        <button
          v-if="editingUser && editingUser.role !== 'user'"
          @click="activeTab = 'permissions'"
          class="px-4 py-2 text-sm font-medium border-b-2 transition-colors"
          :class="activeTab === 'permissions' ? 'border-brand-600 text-brand-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
        >
          权限管理
        </button>
      </div>

      <!-- 基本信息 Tab -->
      <form v-show="activeTab === 'basic'" @submit.prevent="handleSubmitEdit" class="space-y-4">
        <FormInput
          v-model="editForm.username"
          label="用户名"
          placeholder="请输入用户名"
          :error="editErrors.username"
        />
        <FormInput
          v-model="editForm.email"
          label="邮箱"
          type="email"
          placeholder="请输入邮箱"
          :error="editErrors.email"
        />
        <div class="flex items-center gap-2">
          <input
            type="checkbox"
            id="edit-is-active"
            v-model="editForm.is_active"
            class="w-4 h-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
          />
          <label for="edit-is-active" class="text-sm text-gray-700">账号启用状态</label>
        </div>
        <FormSelect
          v-model="editForm.role"
          label="角色"
          :options="roleOptions"
          placeholder="请选择角色"
        />
      </form>

      <!-- 密码 Tab -->
      <div v-show="activeTab === 'password'" class="space-y-4">
        <!-- 重置密码 -->
        <div class="p-4 border border-gray-100 rounded-xl">
          <h4 class="text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
            <KeyRound class="w-4 h-4" />
            重置密码
          </h4>
          <p class="text-sm text-gray-500 mb-3">
            将密码重置为默认密码 <span class="font-mono font-bold text-gray-700">A12345678</span>，
            用户下次登录时必须修改密码。
          </p>
          <button 
            @click="handleResetPasswordInModal"
            :disabled="resetPasswordLoading"
            class="px-4 py-2 text-sm font-bold text-amber-600 bg-amber-50 rounded-xl hover:bg-amber-100 transition-all disabled:opacity-50"
          >
            <Loader2 v-if="resetPasswordLoading" class="w-4 h-4 animate-spin inline mr-2" />
            重置密码
          </button>
        </div>
      </div>

      <!-- 权限管理 Tab -->
      <div v-show="activeTab === 'permissions'" class="space-y-4">
        <!-- 权限继承说明 -->
        <div class="p-4 bg-gray-50 rounded-xl border border-gray-100">
          <h4 class="text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
            <Shield class="w-4 h-4" />
            权限继承
          </h4>
          <div class="space-y-1 text-xs">
            <div v-if="editingUser?.role === 'super_admin'" class="flex items-start gap-2">
              <CheckCircle class="w-4 h-4 text-purple-500 mt-0.5 flex-shrink-0" />
              <span class="text-gray-600">超级管理员自动拥有所有权限，无需额外授权</span>
            </div>
            <div v-else-if="editingUser?.role === 'admin'" class="flex items-start gap-2">
              <CheckCircle class="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
              <span class="text-gray-600">管理员自动拥有所有教材的操作权限</span>
            </div>
            <div v-else-if="editingUser?.role === 'editor'" class="flex items-start gap-2">
              <AlertCircle class="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
              <span class="text-gray-600">编辑需要显式授权具体权限</span>
            </div>
          </div>
        </div>

        <!-- 当前权限列表 -->
        <div class="border border-gray-100 rounded-xl overflow-hidden">
          <div class="px-4 py-3 bg-gray-50 border-b border-gray-100 flex items-center justify-between">
            <h3 class="font-bold text-gray-900 text-sm flex items-center gap-2">
              <Key class="w-4 h-4 text-brand-600" />
              当前权限
            </h3>
            <button 
              v-if="canAssignPermissions"
              @click="openAssignModal"
              class="flex items-center gap-1 px-2 py-1 text-xs font-bold text-brand-600 bg-brand-50 rounded hover:bg-brand-100 transition-all"
            >
              <Plus class="w-3 h-3" />
              添加权限
            </button>
          </div>
          
          <div v-if="permissionsLoading" class="p-8 flex justify-center">
            <Loader2 class="w-6 h-6 text-brand-600 animate-spin" />
          </div>
          <div v-else-if="userPermissions.length === 0" class="p-6 text-center">
            <p class="text-gray-400 text-sm">暂无权限记录</p>
          </div>
          <div v-else class="divide-y divide-gray-50 max-h-60 overflow-y-auto">
            <div 
              v-for="perm in userPermissions" 
              :key="perm.id"
              class="p-3 hover:bg-gray-50/50 transition-colors flex items-center justify-between"
            >
              <div class="flex items-center gap-2">
                <BookOpen class="w-4 h-4 text-gray-400" />
                <div class="text-sm font-medium text-gray-900">{{ getTextbookTitle(perm.textbook_id) }}</div>
              </div>
              <div class="flex items-center gap-3">
                <span v-if="perm.can_access" class="px-1.5 py-0.5 text-[10px] font-bold bg-green-50 text-green-600 rounded">编辑权限</span>
                <span v-else class="px-1.5 py-0.5 text-[10px] font-bold bg-gray-50 text-gray-400 rounded">无权限</span>
                <button 
                  v-if="canRevokePermissions"
                  @click="handleRevokePermission(perm)"
                  class="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-all"
                  title="撤销权限"
                >
                  <Trash2 class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <button
          type="button"
          @click="editModalVisible = false"
          class="px-4 py-2 text-sm font-bold text-gray-700 bg-gray-100 rounded-xl hover:bg-gray-200 transition-all"
        >
          取消
        </button>
        <button
          v-if="activeTab === 'basic'"
          type="button"
          @click="handleSubmitEdit"
          :disabled="editLoading"
          class="flex items-center gap-2 px-4 py-2 text-sm font-bold text-white bg-brand-600 rounded-xl hover:bg-brand-500 transition-all disabled:opacity-50"
        >
          <Loader2 v-if="editLoading" class="w-4 h-4 animate-spin" />
          {{ editLoading ? '保存中...' : '保存' }}
        </button>
      </template>
    </Modal>

    <!-- 添加权限弹窗 -->
    <Modal v-model:visible="assignModalVisible" title="添加权限" width="500px">
      <form @submit.prevent="handleSubmitAssign" class="space-y-4">
        <FormSelect
          v-model="assignForm.textbook_id"
          label="选择教材"
          :options="textbookOptions"
          placeholder="请选择教材"
          :error="assignErrors.textbook_id"
        />
        
        <div class="space-y-3">
          <label class="text-sm font-medium text-gray-700">权限类型</label>
          <label class="flex items-center gap-2 p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-all">
            <input type="checkbox" v-model="assignForm.can_access" class="w-4 h-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500" />
            <span class="text-sm text-gray-700">编辑权限</span>
          </label>
        </div>
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
          {{ assignLoading ? '提交中...' : '确认添加' }}
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

    <!-- 重置密码确认对话框 -->
    <ConfirmDialog
      v-model:visible="resetPasswordConfirmVisible"
      title="重置密码"
      :message="editingUser ? `确定要将用户「${editingUser.username}」的密码重置为默认密码吗？用户下次登录时需要修改密码。` : ''"
      type="warning"
      confirm-text="确认重置"
      @confirm="confirmResetPassword"
    />
  </div>
</template>

<script setup>
/**
 * @file Users.vue
 * @description 用户管理页面，实现响应式列表展示
 */
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  Users, 
  UserPlus, 
  Search, 
  User as UserIcon, 
  Edit2, 
  Trash2, 
  ChevronLeft, 
  ChevronRight,
  Loader2,
  Key,
  KeyRound,
  Plus,
  BookOpen,
  Shield,
  CheckCircle,
  AlertCircle,
  XCircle
} from 'lucide-vue-next'
import { 
  getUsers, 
  deleteUser, 
  createUser, 
  updateUser, 
  updateUserRole,
  getUserById,
  assignUserPermissions,
  revokeUserPermission,
  resetUserPassword
} from '@/api/user'
import { getTextbooks } from '@/api/textbook'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Modal from '@/components/Modal.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import FormInput from '@/components/FormInput.vue'
import FormSelect from '@/components/FormSelect.vue'
import { useToast } from '@/composables/useToast'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const toast = useToast()
const userStore = useUserStore()

const loading = ref(true)
const users = ref([])
const total = ref(0)

/** 创建用户弹窗相关 */
const createModalVisible = ref(false)
const createLoading = ref(false)
const createForm = reactive({
  username: '',
  email: '',
  password: '',
  role: 'user'
})
const createErrors = reactive({
  username: '',
  email: '',
  password: '',
  role: ''
})

/** 编辑用户弹窗相关 */
const editModalVisible = ref(false)
const editLoading = ref(false)
const editingUser = ref(null)
const activeTab = ref('basic')
const editForm = reactive({
  username: '',
  email: '',
  is_active: true,
  role: 'user'
})
const editErrors = reactive({
  username: '',
  email: ''
})
const originalEditRole = ref('user')

/** 权限管理相关 */
const permissionsLoading = ref(false)
const userPermissions = ref([])
const textbooks = ref([])

const assignModalVisible = ref(false)
const assignLoading = ref(false)
const assignForm = reactive({
  textbook_id: '',
  can_access: false
})
const assignErrors = reactive({
  textbook_id: ''
})

const revokeConfirmVisible = ref(false)
const revokeTargetPerm = ref(null)

/** 重置密码相关 */
const resetPasswordLoading = ref(false)
const resetPasswordConfirmVisible = ref(false)

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

const loadTextbooks = async () => {
  try {
    const data = await getTextbooks({ page_size: 100 })
    textbooks.value = data.items
  } catch (error) {
    // API 拦截器已处理错误
  }
}

const getTextbookTitle = (textbookId) => {
  const textbook = textbooks.value.find(t => t.id === textbookId)
  return textbook?.title || `教材 #${textbookId}`
}

const loadUserPermissions = async (userId) => {
  permissionsLoading.value = true
  try {
    const detail = await getUserById(userId)
    userPermissions.value = detail.permissions || []
  } catch (error) {
    // API 拦截器已处理错误
  } finally {
    permissionsLoading.value = false
  }
}

const openAssignModal = () => {
  assignForm.textbook_id = ''
  assignForm.can_access = false
  assignErrors.textbook_id = ''
  assignModalVisible.value = true
}

const validateAssignForm = () => {
  let isValid = true
  assignErrors.textbook_id = ''
  
  if (!assignForm.textbook_id) {
    assignErrors.textbook_id = '请选择教材'
    isValid = false
  }
  
  return isValid
}

const handleSubmitAssign = async () => {
  if (!validateAssignForm() || !editingUser.value) return
  
  assignLoading.value = true
  try {
    await assignUserPermissions(editingUser.value.id, {
      textbook_id: Number(assignForm.textbook_id),
      can_access: assignForm.can_access
    })
    toast.success('权限添加成功')
    assignModalVisible.value = false
    
    // 刷新用户权限
    await loadUserPermissions(editingUser.value.id)
  } catch (error) {
    // API 拦截器已处理错误
  } finally {
    assignLoading.value = false
  }
}

const handleRevokePermission = (perm) => {
  if (!editingUser.value) return
  revokeTargetPerm.value = perm
  revokeConfirmVisible.value = true
}

const confirmRevokePermission = async () => {
  if (!editingUser.value || !revokeTargetPerm.value) return
  
  try {
    await revokeUserPermission(editingUser.value.id, revokeTargetPerm.value.textbook_id)
    toast.success('权限已撤销')
    
    // 刷新用户权限
    await loadUserPermissions(editingUser.value.id)
  } catch (error) {
    // API 拦截器已处理错误
  }
}

/**
 * 点击重置密码按钮 -> 显示确认对话框
 */
const handleResetPasswordInModal = () => {
  if (!editingUser.value) return
  resetPasswordConfirmVisible.value = true
}

/**
 * 确认后执行重置密码
 */
const confirmResetPassword = async () => {
  if (!editingUser.value) return
  
  resetPasswordLoading.value = true
  try {
    const result = await resetUserPassword(editingUser.value.id)
    toast.success(`密码重置成功！新密码：${result.password}`)
    editingUser.value = { ...editingUser.value, must_change_password: true }
    resetPasswordConfirmVisible.value = false
  } catch (error) {
    // API 拦截器已处理错误
  } finally {
    resetPasswordLoading.value = false
  }
}

/** 角色选项 */
const roleOptions = computed(() => {
  if (userStore.role === 'super_admin') {
    return [
      { value: 'admin', label: '管理员' },
      { value: 'editor', label: '编辑' },
      { value: 'user', label: '普通用户' }
    ]
  }

  if (userStore.role === 'admin') {
    return [
      { value: 'editor', label: '编辑' },
      { value: 'user', label: '普通用户' }
    ]
  }

  return [{ value: 'user', label: '普通用户' }]
})

/**
 * 密码验证：至少8位，必须包含大写字母和数字
 */
const validatePassword = (password) => {
  if (password.length < 8) {
    return '密码至少需要8位'
  }
  if (!/[A-Z]/.test(password)) {
    return '密码必须包含至少一个大写字母'
  }
  if (!/[0-9]/.test(password)) {
    return '密码必须包含至少一个数字'
  }
  return ''
}

/**
 * 表单验证
 */
const validateCreateForm = () => {
  let isValid = true
  
  // 重置错误
  createErrors.username = ''
  createErrors.email = ''
  createErrors.password = ''
  createErrors.role = ''
  
  if (!createForm.username.trim()) {
    createErrors.username = '请输入用户名'
    isValid = false
  } else if (createForm.username.length < 3) {
    createErrors.username = '用户名至少需要3个字符'
    isValid = false
  }
  
  if (!createForm.email.trim()) {
    createErrors.email = '请输入邮箱'
    isValid = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(createForm.email)) {
    createErrors.email = '请输入有效的邮箱地址'
    isValid = false
  }
  
  const passwordError = validatePassword(createForm.password)
  if (passwordError) {
    createErrors.password = passwordError
    isValid = false
  }
  
  if (!createForm.role) {
    createErrors.role = '请选择角色'
    isValid = false
  }
  
  return isValid
}

/**
 * 重置创建表单
 */
const resetCreateForm = () => {
  createForm.username = ''
  createForm.email = ''
  createForm.password = ''
  createForm.role = 'user'
  createErrors.username = ''
  createErrors.email = ''
  createErrors.password = ''
  createErrors.role = ''
}

const queryParams = reactive({
  page: 1,
  page_size: 10,
  role: route.query.role || '',
  keyword: ''
})

/**
 * 监听路由中的 role 参数变化
 */
watch(() => route.query.role, (newRole) => {
  queryParams.role = newRole || ''
  handleSearch()
})

/**
 * 加载数据
 */
const loadData = async () => {
  loading.value = true
  try {
    const data = await getUsers(queryParams)
    users.value = data.items
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
 * 分页处理
 */
const changePage = (newPage) => {
  queryParams.page = newPage
  loadData()
}

/**
 * 获取角色显示名称
 */
const getRoleName = (role) => {
  const roles = {
    'super_admin': '超级管理员',
    'admin': '管理员',
    'editor': '编辑',
    'user': '普通用户'
  }
  return roles[role] || role
}

/**
 * 获取角色徽章样式
 */
const getRoleBadgeClass = (role) => {
  switch (role) {
    case 'super_admin':
      return 'bg-purple-50 text-purple-600 border-purple-100'
    case 'admin':
      return 'bg-blue-50 text-blue-600 border-blue-100'
    case 'editor':
      return 'bg-amber-50 text-amber-600 border-amber-100'
    default:
      return 'bg-slate-50 text-slate-500 border-slate-100'
  }
}

/**
 * 操作处理
 */
const openCreateModal = () => {
  resetCreateForm()
  createModalVisible.value = true
}

/**
 * 提交创建用户
 */
const handleSubmitCreate = async () => {
  if (!validateCreateForm()) return
  
  createLoading.value = true
  try {
    await createUser({
      username: createForm.username,
      email: createForm.email,
      password: createForm.password,
      role: createForm.role
    })
    toast.success('用户创建成功')
    createModalVisible.value = false
    loadData()
  } catch (error) {
    // API 拦截器已处理错误 toast
  } finally {
    createLoading.value = false
  }
}

/**
 * 打开编辑弹窗
 */
const openEditModal = (user) => {
  editingUser.value = user
  activeTab.value = 'basic'
  editForm.username = user.username
  editForm.email = user.email
  editForm.is_active = user.is_active ?? true
  editForm.role = user.role || 'user'
  originalEditRole.value = editForm.role
  editErrors.username = ''
  editErrors.email = ''
  editModalVisible.value = true
  
  if (user.role !== 'user') {
    loadUserPermissions(user.id)
  }
}

/**
 * 编辑表单验证
 */
const validateEditForm = () => {
  let isValid = true
  
  // 重置错误
  editErrors.username = ''
  editErrors.email = ''
  
  if (!editForm.username.trim()) {
    editErrors.username = '请输入用户名'
    isValid = false
  } else if (editForm.username.length < 2) {
    editErrors.username = '用户名至少需要2个字符'
    isValid = false
  }
  
  if (!editForm.email.trim()) {
    editErrors.email = '请输入邮箱'
    isValid = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(editForm.email)) {
    editErrors.email = '请输入有效的邮箱地址'
    isValid = false
  }
  
  return isValid
}

/**
 * 提交编辑用户
 */
const handleSubmitEdit = async () => {
  if (!validateEditForm()) return
  
  editLoading.value = true
  try {
    await updateUser(editingUser.value.id, {
      username: editForm.username,
      email: editForm.email,
      is_active: editForm.is_active
    })
    if (editForm.role !== originalEditRole.value) {
      await updateUserRole(editingUser.value.id, editForm.role)
    }
    toast.success('用户信息更新成功')
    editModalVisible.value = false
    loadData()
  } catch (error) {
    // API 拦截器已处理错误 toast
  } finally {
    editLoading.value = false
  }
}
const handleDelete = async (user) => {
  if (confirm(`确定要删除用户 ${user.username} 吗？`)) {
    try {
      await deleteUser(user.id)
      toast.success('删除成功')
      loadData()
    } catch (error) {
      // API 拦截器已处理错误 toast
    }
  }
}

onMounted(() => {
  loadData()
  loadTextbooks()
})
</script>
