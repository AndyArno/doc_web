<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 bg-white p-10 rounded-2xl shadow-xl">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          创建您的账号
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          已经有账号了？
          <router-link to="/login" class="font-medium text-brand-600 hover:text-brand-500">
            立即登录
          </router-link>
        </p>
      </div>
      
      <form class="mt-8 space-y-6" @submit.prevent="handleRegister">
        <div class="space-y-4">
          <FormInput
            v-model="form.username"
            label="用户名"
            placeholder="3-50个字符，仅字母数字下划线"
            :disabled="loading"
            :error="errors.username"
          />
          
          <FormInput
            v-model="form.email"
            label="邮箱"
            placeholder="请输入您的邮箱"
            :disabled="loading"
            :error="errors.email"
          />
          
          <FormInput
            v-model="form.password"
            label="密码"
            type="password"
            placeholder="至少 6 个字符"
            :disabled="loading"
            :error="errors.password"
          />
        </div>

        <div>
          <button
            type="submit"
            :disabled="loading"
            class="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-semibold rounded-xl text-white bg-brand-600 hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-brand"
          >
            <span v-if="loading" class="absolute left-4 flex items-center">
              <Loader2 class="animate-spin h-5 w-5 text-brand-100" />
            </span>
            {{ loading ? '正在注册...' : '立即注册' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
/**
 * 注册页面
 * 
 * @description 处理用户注册逻辑，包含表单验证、API 调用和路由跳转
 */
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '@/api/auth'
import { useToast } from '@/composables/useToast'
import FormInput from '@/components/FormInput.vue'
import { Loader2 } from 'lucide-vue-next'

const router = useRouter()
const toast = useToast()

const loading = ref(false)
const form = reactive({
  username: '',
  email: '',
  password: ''
})

const errors = reactive({
  username: '',
  email: '',
  password: ''
})

/**
 * 验证注册表单
 * @returns {boolean} 是否验证通过
 */
function validate() {
  let isValid = true
  // 重置错误信息
  errors.username = ''
  errors.email = ''
  errors.password = ''

  // 用户名验证：3-50字符，仅字母数字下划线
  const usernameRegex = /^[a-zA-Z0-9_]{3,50}$/
  if (!form.username.trim()) {
    errors.username = '请输入用户名'
    isValid = false
  } else if (!usernameRegex.test(form.username)) {
    errors.username = '用户名必须为3-50个字符，且仅包含字母、数字或下划线'
    isValid = false
  }

  // 邮箱验证
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!form.email.trim()) {
    errors.email = '请输入邮箱'
    isValid = false
  } else if (!emailRegex.test(form.email)) {
    errors.email = '请输入正确的邮箱格式'
    isValid = false
  }

  // 密码验证
  if (!form.password) {
    errors.password = '请输入密码'
    isValid = false
  } else if (form.password.length < 6) {
    errors.password = '密码长度至少为 6 个字符'
    isValid = false
  }

  return isValid
}

/**
 * 处理注册提交
 */
async function handleRegister() {
  if (!validate()) return

  loading.value = true
  try {
    await register(form)
    toast.success('注册成功，请登录')
    router.push('/login')
  } catch (error) {
    // 错误处理已在 Axios 拦截器中统一处理
  } finally {
    loading.value = false
  }
}
</script>
