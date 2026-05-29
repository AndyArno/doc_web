import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

/**
 * Vitest 测试配置
 * - jsdom 环境：模拟浏览器 API
 * - 路径别名：@ 映射到 src/
 */
export default defineConfig({
  plugins: [vue()],
  test: {
    // 使用 jsdom 模拟浏览器环境
    environment: 'jsdom',
    // 全局测试 API（describe, it, expect 等）
    globals: true,
    // 测试文件匹配模式
    include: ['src/**/*.{test,spec}.{js,ts}'],
    // 排除目录
    exclude: ['node_modules', 'dist'],
  },
  resolve: {
    alias: {
      // 路径别名 @ -> src/
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
