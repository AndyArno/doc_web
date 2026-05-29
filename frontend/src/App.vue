<script setup>
/**
 * App 根组件
 * 
 * 使用 Vue Router 的 router-view 进行页面路由切换。
 * 包含 ErrorBoundary 捕获子组件错误。
 * Toast 消息提示由 useToast composable 提供全局服务。
 */
import ErrorBoundary from '@/components/ErrorBoundary.vue'
</script>

<template>
  <ErrorBoundary>
    <div class="min-h-screen bg-white text-gray-900 font-sans antialiased">
      <router-view />
    </div>
  </ErrorBoundary>
</template>

<style>
/* 全局样式可以放在这里或 style.css */
</style>
