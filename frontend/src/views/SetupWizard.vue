<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 bg-white p-10 rounded-2xl shadow-xl">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          系统初始化设置
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          首次部署，请配置管理员账户和基本设置
        </p>
      </div>

      <form class="mt-8 space-y-6" @submit.prevent="handleSubmit">
        <div class="space-y-4">
          <!-- Admin Username -->
          <FormInput
            v-model="form.admin_username"
            label="管理员用户名"
            placeholder="3-50位字母、数字或下划线"
            :disabled="loading"
            :error="errors.admin_username"
            data-testid="admin-username"
          />

          <!-- Admin Email -->
          <FormInput
            v-model="form.admin_email"
            label="管理员邮箱"
            placeholder="请输入邮箱地址"
            type="email"
            :disabled="loading"
            :error="errors.admin_email"
            data-testid="admin-email"
          />

          <!-- Admin Password -->
          <div>
            <FormInput
              v-model="form.admin_password"
              label="管理员密码"
              type="password"
              placeholder="至少8位，包含大写字母和数字"
              :disabled="loading"
              :error="errors.admin_password"
              data-testid="admin-password"
            />
            <!-- Password strength hints -->
            <div class="mt-1 space-y-1">
              <p :class="form.admin_password.length >= 8 ? 'text-green-600' : 'text-gray-400'" class="text-xs flex items-center gap-1">
                <Check v-if="form.admin_password.length >= 8" class="h-3 w-3" />
                <X v-else class="h-3 w-3" />
                至少8位字符
              </p>
              <p :class="/[A-Z]/.test(form.admin_password) ? 'text-green-600' : 'text-gray-400'" class="text-xs flex items-center gap-1">
                <Check v-if="/[A-Z]/.test(form.admin_password)" class="h-3 w-3" />
                <X v-else class="h-3 w-3" />
                包含大写字母
              </p>
              <p :class="/[0-9]/.test(form.admin_password) ? 'text-green-600' : 'text-gray-400'" class="text-xs flex items-center gap-1">
                <Check v-if="/[0-9]/.test(form.admin_password)" class="h-3 w-3" />
                <X v-else class="h-3 w-3" />
                包含数字
              </p>
            </div>
          </div>

          <!-- CORS Origins -->
          <FormInput
            v-model="form.cors_origins"
            label="CORS 域名"
            placeholder="https://example.com,https://www.example.com"
            :disabled="loading"
            :error="errors.cors_origins"
            data-testid="cors-origins"
          />
        </div>

        <!-- Error Alert -->
        <div v-if="submitError" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {{ submitError }}
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-semibold rounded-xl text-white bg-brand-600 hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-brand"
          data-testid="submit-btn"
        >
          <span v-if="loading" class="absolute left-4 flex items-center">
            <Loader2 class="animate-spin h-5 w-5 text-brand-100" />
          </span>
          {{ loading ? '正在初始化...' : '完成初始化' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
/**
 * SetupWizard - 系统初始化页面
 *
 * @description 首次部署时的初始化设置页面，提交管理员账户和 CORS 配置到后端，
 * 成功后跳转到登录页。使用原始 axios 而非 apiClient（因为初始化时无认证 token）。
 */
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useToast } from '@/composables/useToast'
import FormInput from '@/components/FormInput.vue'
import { Loader2, Check, X } from 'lucide-vue-next'

const router = useRouter()
const toast = useToast()

const loading = ref(false)
const submitError = ref('')

const form = reactive({
  admin_username: '',
  admin_email: '',
  admin_password: '',
  cors_origins: ''
})

const errors = reactive({
  admin_username: '',
  admin_email: '',
  admin_password: '',
  cors_origins: ''
})

/**
 * 验证表单
 * @returns {boolean} 是否验证通过
 */
function validate() {
  let isValid = true
  errors.admin_username = ''
  errors.admin_email = ''
  errors.admin_password = ''
  errors.cors_origins = ''

  if (!form.admin_username.trim()) {
    errors.admin_username = '请输入管理员用户名'
    isValid = false
  } else if (!/^[a-zA-Z0-9_]+$/.test(form.admin_username)) {
    errors.admin_username = '用户名只能包含字母、数字和下划线'
    isValid = false
  } else if (form.admin_username.length < 3) {
    errors.admin_username = '用户名至少3位'
    isValid = false
  }

  if (!form.admin_email.trim()) {
    errors.admin_email = '请输入邮箱地址'
    isValid = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.admin_email)) {
    errors.admin_email = '请输入有效的邮箱地址'
    isValid = false
  }

  if (!form.admin_password) {
    errors.admin_password = '请输入密码'
    isValid = false
  } else if (form.admin_password.length < 8) {
    errors.admin_password = '密码至少8位'
    isValid = false
  } else if (!/[A-Z]/.test(form.admin_password)) {
    errors.admin_password = '密码需包含大写字母'
    isValid = false
  } else if (!/[0-9]/.test(form.admin_password)) {
    errors.admin_password = '密码需包含数字'
    isValid = false
  }

  if (!form.cors_origins.trim()) {
    errors.cors_origins = '请输入至少一个 CORS 域名'
    isValid = false
  }

  return isValid
}

/**
 * 处理初始化提交
 */
async function handleSubmit() {
  submitError.value = ''
  if (!validate()) return

  loading.value = true
  try {
    // Use direct axios — no auth interceptor needed during initial setup
    const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
    const response = await axios.post(`${apiBase}/setup/initialize`, {
      admin_username: form.admin_username,
      admin_email: form.admin_email,
      admin_password: form.admin_password,
      cors_origins: form.cors_origins
    })

    if (response.data.code === 200) {
      toast.success('系统初始化成功！请使用管理员账户登录')
      router.push('/login')
    } else {
      submitError.value = response.data.message || '初始化失败'
    }
  } catch (error) {
    if (error.response?.data?.message) {
      submitError.value = error.response.data.message
    } else {
      submitError.value = '网络连接失败，请检查后端服务是否启动'
    }
  } finally {
    loading.value = false
  }
}
</script>