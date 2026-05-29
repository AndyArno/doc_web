<template>
  <div class="flex flex-col gap-1.5 w-full">
    <label v-if="label" class="text-sm font-medium text-gray-700">
      {{ label }}
    </label>
    <div class="relative">
      <select
        :value="modelValue"
        @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
        :disabled="disabled"
        :class="[
          'w-full appearance-none rounded-lg border pl-3.5 pr-10 py-2.5 text-sm transition-all focus:outline-none disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-400',
          error 
            ? 'border-red-500 bg-red-50 focus:ring-2 focus:ring-red-500/50' 
            : 'border-gray-200 bg-white focus:border-brand-500 focus:ring-2 focus:ring-brand-500/50'
        ]"
      >
        <option v-if="placeholder" value="" disabled selected>
          {{ placeholder }}
        </option>
        <option
          v-for="option in options"
          :key="option.value"
          :value="option.value"
          :disabled="option.disabled"
        >
          {{ option.label }}
        </option>
      </select>
      <!-- 自定义选择箭头 -->
      <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400">
        <ChevronDown :size="16" />
      </div>
    </div>
    <span v-if="error" class="text-xs text-red-500">
      {{ error }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { ChevronDown } from 'lucide-vue-next';
/**
 * FormSelect 表单选择器组件
 * 
 * @description 支持 label、v-model、选项配置、禁用状态等功能的通用下拉选择器
 * 
 * @property {string} modelValue - 绑定值，支持 v-model
 * @property {string} [label] - 输入框标签
 * @property {Option[]} options - 选项列表
 * @property {string} [placeholder='请选择'] - 占位文字
 * @property {boolean} [disabled=false] - 是否禁用
 * @property {string} [error] - 错误信息，非空时显示错误样式
 * 
 * @example
 * <FormSelect v-model="role" label="用户角色" :options="roleOptions" />
 */

export interface Option {
  value: string;
  label: string;
  disabled?: boolean;
}

interface Props {
  modelValue: string;
  label?: string;
  options: Option[];
  placeholder?: string;
  disabled?: boolean;
  error?: string;
}

withDefaults(defineProps<Props>(), {
  modelValue: '',
  placeholder: '请选择',
  disabled: false
});

defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();
</script>
