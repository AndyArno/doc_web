<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 bg-white p-10 rounded-2xl shadow-xl">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          登录您的账号
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          还没有账号？
          <router-link to="/register" class="font-medium text-brand-600 hover:text-brand-500">
            立即注册
          </router-link>
        </p>
      </div>
      
      <form class="mt-8 space-y-6" @submit.prevent="handleLogin">
        <div class="space-y-4">
          <FormInput
            v-model="form.account"
            label="用户名或邮箱"
            placeholder="请输入用户名或邮箱"
            :disabled="loading"
            :error="errors.account"
          />
          
          <FormInput
            v-model="form.password"
            label="密码"
            type="password"
            placeholder="请输入密码"
            :disabled="loading"
            :error="errors.password"
          />
        </div>

        <!-- 修改密码入口 -->
        <div class="flex justify-end">
          <router-link 
            to="/forgot-password" 
            class="text-sm text-brand-600 hover:text-brand-500 font-medium"
          >
            修改密码
          </router-link>
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
            {{ loading ? '正在登录...' : '登录' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
/**
 * 登录页面
 * 
 * @description 处理用户登录逻辑，包含表单验证、API 调用、Token 存储和路由跳转
 */
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { login } from '@/api/auth'
import { useUserStore } from '@/stores/user'
import { useToast } from '@/composables/useToast'
import FormInput from '@/components/FormInput.vue'
import { Loader2 } from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const toast = useToast()

const loading = ref(false)
const form = reactive({
  account: '',
  password: ''
})

const errors = reactive({
  account: '',
  password: ''
})

/**
 * 验证表单
 * @returns {boolean} 是否验证通过
 */
function validate() {
  let isValid = true
  errors.account = ''
  errors.password = ''

  if (!form.account.trim()) {
    errors.account = '请输入用户名或邮箱'
    isValid = false
  }

  if (!form.password) {
    errors.password = '请输入密码'
    isValid = false
  }

  return isValid
}

/**
 * 处理登录提交
 */
async function handleLogin() {
  if (!validate()) return

  loading.value = true
  try {
    const result = await login(form)
    
    // 保存 Token
    userStore.setToken(result.access_token)
    
    // 获取并设置用户信息
    await userStore.getUserInfo()
    
    toast.success('登录成功')
    
    // 检查是否需要强制修改密码
    if (userStore.userInfo?.must_change_password) {
      router.push('/change-password')
      return
    }
    
    // 跳转到指定页面或首页
    const redirectPath = route.query.redirect || '/'
    router.push(redirectPath)
  } catch (error) {
    // 错误处理已在 Axios 拦截器中统一处理（显示 Toast）
    // 这里可以清空密码或做特定交互
    form.password = ''
  } finally {
    loading.value = false
  }
}
</script>
