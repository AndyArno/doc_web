<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="text-center">
      <div class="mb-6">
        <FileQuestion class="w-24 h-24 mx-auto text-gray-300" />
      </div>
      <h1 class="text-6xl font-bold text-gray-800 mb-4">404</h1>
      <p class="text-xl text-gray-600 mb-8">页面不存在</p>
      <router-link
        to="/"
        class="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        <Home class="w-5 h-5" />
        <span>返回首页</span>
      </router-link>
    </div>
  </div>
</template>

<script setup>
/**
 * NotFound.vue - 404 页面
 *
 * @description 当用户访问不存在的路由时显示的 404 错误页面。
 * 提供返回首页的快捷入口。
 */
import { FileQuestion, Home } from 'lucide-vue-next';
</script>
