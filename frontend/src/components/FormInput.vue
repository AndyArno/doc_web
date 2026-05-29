<template>
  <div class="flex flex-col gap-1.5 w-full">
    <label v-if="label" class="text-sm font-medium text-gray-700">
      {{ label }}
    </label>
    <div class="relative">
      <input
        :value="modelValue"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        :type="type"
        :placeholder="placeholder"
        :disabled="disabled"
        :class="[
          'w-full rounded-lg border px-3.5 py-2.5 text-sm transition-all focus:outline-none disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-400',
          error 
            ? 'border-red-500 bg-red-50 focus:ring-2 focus:ring-red-500/50' 
            : 'border-gray-200 bg-white focus:border-brand-500 focus:ring-2 focus:ring-brand-500/50'
        ]"
      />
    </div>
    <span v-if="error" class="text-xs text-red-500">
      {{ error }}
    </span>
  </div>
</template>

<script setup lang="ts">
/**
 * FormInput 表单输入框组件
 * 
 * @description 支持 label、v-model、错误提示、禁用状态等功能的通用输入框
 * 
 * @property {string} modelValue - 绑定值，支持 v-model
 * @property {string} [label] - 输入框标签
 * @property {string} [placeholder] - 占位文字
 * @property {string} [type='text'] - 输入框类型 (text, password, email, etc.)
 * @property {boolean} [disabled=false] - 是否禁用
 * @property {string} [error] - 错误信息，非空时显示错误样式
 * 
 * @example
 * <FormInput v-model="username" label="用户名" placeholder="请输入用户名" :error="errors.username" />
 */

interface Props {
  modelValue: string | number;
  label?: string;
  placeholder?: string;
  type?: string;
  disabled?: boolean;
  error?: string;
}

withDefaults(defineProps<Props>(), {
  modelValue: '',
  type: 'text',
  disabled: false
});

defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();
</script>
