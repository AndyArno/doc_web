<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 bg-white p-10 rounded-2xl shadow-xl">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          修改密码
        </h2>
        <div class="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div class="flex items-start gap-3">
            <AlertTriangle class="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <p class="text-sm text-amber-800">
              为了账号安全，请修改初始密码
            </p>
          </div>
        </div>
      </div>
      
      <form class="mt-8 space-y-6" @submit.prevent="handleChangePassword">
        <div class="space-y-4">
          <FormInput
            v-model="form.old_password"
            label="旧密码"
            type="password"
            placeholder="请输入旧密码"
            :disabled="loading"
            :error="errors.old_password"
          />
          
          <FormInput
            v-model="form.new_password"
            label="新密码"
            type="password"
            placeholder="请输入新密码"
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

        <div class="space-y-3">
          <button
            type="submit"
            :disabled="loading"
            class="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-semibold rounded-xl text-white bg-brand-600 hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-brand"
          >
            <span v-if="loading" class="absolute left-4 flex items-center">
              <Loader2 class="animate-spin h-5 w-5 text-brand-100" />
            </span>
            {{ loading ? '正在修改...' : '修改密码' }}
          </button>
          
          <button
            type="button"
            :disabled="loading"
            @click="handleLogout"
            class="w-full flex justify-center py-3 px-4 border border-gray-300 text-sm font-semibold rounded-xl text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <LogOut class="h-5 w-5 mr-2" />
            登出
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 修改密码页面
 * 
 * @description 处理用户修改密码逻辑，用于管理员重置密码后的首次登录
 */
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { changePassword, logout as logoutApi } from '@/api/auth'
import { useUserStore } from '@/stores/user'
import { useToast } from '@/composables/useToast'
import FormInput from '@/components/FormInput.vue'
import { Loader2, AlertTriangle, LogOut } from 'lucide-vue-next'

const router = useRouter()
const userStore = useUserStore()
const toast = useToast()

const loading = ref(false)
const form = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const errors = reactive({
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
  errors.old_password = ''
  errors.new_password = ''
  errors.confirm_password = ''

  if (!form.old_password) {
    errors.old_password = '请输入旧密码'
    isValid = false
  }

  if (!form.new_password) {
    errors.new_password = '请输入新密码'
    isValid = false
  } else if (form.new_password.length < 6) {
    errors.new_password = '密码长度至少为 6 位'
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
 * 处理修改密码提交
 */
async function handleChangePassword() {
  if (!validate()) return

  loading.value = true
  try {
    await changePassword({
      old_password: form.old_password,
      new_password: form.new_password
    })
    
    toast.success('密码修改成功')
    
    // 更新用户状态
    if (userStore.userInfo) {
      userStore.setUserInfo({
        ...userStore.userInfo,
        must_change_password: false,
        role: userStore.userInfo.role
      })
    }
    
    // 跳转到首页
    router.push('/')
  } catch (error) {
    // 错误处理已在 Axios 拦截器中统一处理
    // 清空旧密码
    form.old_password = ''
  } finally {
    loading.value = false
  }
}

/**
 * 处理登出
 */
async function handleLogout() {
  try {
    await logoutApi()
  } catch (error) {
    // 忽略登出错误，继续清除本地状态
  } finally {
    userStore.logout()
    toast.success('已登出')
    router.push('/login')
  }
}
</script>
