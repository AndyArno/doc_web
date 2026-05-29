<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 bg-white p-10 rounded-2xl shadow-xl">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          修改密码
        </h2>
        <p class="mt-3 text-center text-sm text-gray-500">
          请输入您的用户名/邮箱和原密码来验证身份
        </p>
      </div>
      
      <form class="mt-8 space-y-6" @submit.prevent="handleSubmit">
        <div class="space-y-4">
          <FormInput
            v-model="form.account"
            label="用户名/邮箱"
            placeholder="请输入用户名或邮箱"
            :disabled="loading"
            :error="errors.account"
          />
          
          <FormInput
            v-model="form.old_password"
            label="原密码"
            type="password"
            placeholder="请输入原密码"
            :disabled="loading"
            :error="errors.old_password"
          />
          
          <FormInput
            v-model="form.new_password"
            label="新密码"
            type="password"
            placeholder="请输入新密码（至少8位，包含大写字母和数字）"
            :disabled="loading"
            :error="errors.new_password"
          />
          
          <FormInput
            v-model="form.confirm_password"
            label="确认密码"
            type="password"
            placeholder="请再次输入新密码"
            :disabled="loading"
            :error="errors.confirm_password"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full flex justify-center py-3 px-4 border border-transparent text-sm font-semibold rounded-xl text-white bg-brand-600 hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-brand"
        >
          <span v-if="loading" class="flex items-center">
            <Loader2 class="animate-spin h-5 w-5 mr-2" />
            正在提交...
          </span>
          <span v-else>提交修改</span>
        </button>
      </form>
      
      <div class="text-center">
        <router-link to="/login" class="text-sm text-brand-600 hover:text-brand-500">
          ← 返回登录
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Loader2 } from 'lucide-vue-next'
import FormInput from '@/components/FormInput.vue'
import { forgotPassword } from '@/api/auth'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const toast = useToast()

const loading = ref(false)
const form = reactive({
  account: '',
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const errors = reactive({
  account: '',
  old_password: '',
  new_password: '',
  confirm_password: ''
})

/**
 * 验证表单
 * @returns {boolean} 是否验证通过
 */
function validate(): boolean {
  let isValid = true
  errors.account = ''
  errors.old_password = ''
  errors.new_password = ''
  errors.confirm_password = ''

  if (!form.account.trim()) {
    errors.account = '请输入用户名或邮箱'
    isValid = false
  }

  if (!form.old_password) {
    errors.old_password = '请输入原密码'
    isValid = false
  }

  if (!form.new_password) {
    errors.new_password = '请输入新密码'
    isValid = false
  } else if (form.new_password.length < 8) {
    errors.new_password = '密码至少8位'
    isValid = false
  } else if (!/[A-Z]/.test(form.new_password)) {
    errors.new_password = '密码必须包含大写字母'
    isValid = false
  } else if (!/[0-9]/.test(form.new_password)) {
    errors.new_password = '密码必须包含数字'
    isValid = false
  }

  if (!form.confirm_password) {
    errors.confirm_password = '请确认新密码'
    isValid = false
  } else if (form.new_password !== form.confirm_password) {
    errors.confirm_password = '两次输入的密码不一致'
    isValid = false
  }

  return isValid
}

/**
 * 处理提交
 */
async function handleSubmit() {
  if (!validate()) return

  loading.value = true
  try {
    await forgotPassword({
      account: form.account,
      old_password: form.old_password,
      new_password: form.new_password
    })
    toast.success('密码修改成功，请重新登录')
    router.push('/login')
  } catch (error) {
    // 错误处理已在 Axios 拦截器中统一处理
  } finally {
    loading.value = false
  }
}
</script>
