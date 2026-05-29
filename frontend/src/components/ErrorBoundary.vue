/**
 * ErrorBoundary 错误边界组件
 * 
 * 捕获子组件树中的 JavaScript 错误，显示优雅的错误回退 UI。
 * 防止整个应用因局部错误而崩溃。
 */
<template>
  <slot v-if="!hasError" />
  <div v-else class="error-boundary">
    <AlertTriangle class="error-icon h-16 w-16 text-red-500" />
    <h2 class="mt-4 text-2xl font-bold text-gray-900">出错了</h2>
    <p class="mt-2 text-gray-600">{{ errorMessage }}</p>
    <button
      @click="retry"
      class="mt-6 px-6 py-2.5 bg-brand-500 text-white font-semibold rounded-xl hover:bg-brand-600 transition-colors"
    >
      重试
    </button>
  </div>
</template>

<script setup>
import { ref, onErrorCaptured } from 'vue'
import { AlertTriangle } from 'lucide-vue-next'

const hasError = ref(false)
const errorMessage = ref('')

onErrorCaptured((error) => {
  hasError.value = true
  errorMessage.value = error.message || '发生了未知错误'
  console.error('ErrorBoundary captured:', error)
  return false
})

function retry() {
  hasError.value = false
  errorMessage.value = ''
  location.reload()
}
</script>

<style scoped>
.error-boundary {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  padding: 48px;
  text-align: center;
}
</style>
