<script setup>
/**
 * ConfirmDialog - 确认对话框组件
 *
 * @description 一个高度集成的确认对话框，用于执行危险操作或重要操作前的二次确认。
 *
 * @example
 * <ConfirmDialog 
 *   v-model:visible="showConfirm" 
 *   title="删除提示" 
 *   message="您确定要删除这个章节吗？此操作不可撤销。"
 *   type="danger"
 *   @confirm="handleConfirm"
 * />
 */
import { AlertTriangle, AlertCircle } from 'lucide-vue-next';
import Modal from './Modal.vue';

const props = defineProps({
  /** 是否显示 */
  visible: {
    type: Boolean,
    default: false
  },
  /** 弹窗标题 */
  title: {
    type: String,
    default: '确认'
  },
  /** 提示消息内容 */
  message: {
    type: String,
    default: ''
  },
  /** 确认按钮文字 */
  confirmText: {
    type: String,
    default: '确认'
  },
  /** 取消按钮文字 */
  cancelText: {
    type: String,
    default: '取消'
  },
  /** 对话框类型 */
  type: {
    type: String,
    default: 'warning',
    validator: (value) => ['warning', 'danger'].includes(value)
  },
  /** 弹窗宽度 */
  width: {
    type: String,
    default: '420px'
  }
});

const emit = defineEmits(['confirm', 'cancel', 'update:visible']);

/**
 * 处理确认操作
 */
const handleConfirm = () => {
  emit('confirm');
  emit('update:visible', false);
};

/**
 * 处理取消操作
 */
const handleCancel = () => {
  emit('cancel');
  emit('update:visible', false);
};
</script>

<template>
  <Modal 
    :visible="visible" 
    :title="title" 
    :width="width" 
    @close="handleCancel"
  >
    <div class="flex items-start gap-4">
      <!-- 图标区域 -->
      <div 
        class="flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center"
        :class="type === 'danger' ? 'bg-red-50' : 'bg-yellow-50'"
      >
        <AlertCircle 
          v-if="type === 'danger'" 
          class="h-6 w-6 text-red-500" 
        />
        <AlertTriangle 
          v-else 
          class="h-6 w-6 text-yellow-500" 
        />
      </div>

      <!-- 文字区域 -->
      <div class="flex-1">
        <p class="text-sm text-gray-700 leading-relaxed mt-1">
          {{ message }}
        </p>
      </div>
    </div>

    <!-- 自定义底部按钮 -->
    <template #footer>
      <button
        type="button"
        class="px-5 py-2.5 rounded-xl border border-gray-200 bg-white text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-100"
        @click="handleCancel"
      >
        {{ cancelText }}
      </button>
      
      <button
        type="button"
        class="px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all shadow-brand focus:outline-none focus:ring-2 focus:ring-offset-2"
        :class="[
          type === 'danger' 
            ? 'bg-red-500 hover:bg-red-600 focus:ring-red-500 shadow-red-500/20' 
            : 'bg-brand-500 hover:bg-brand-600 focus:ring-brand-500 shadow-brand/20'
        ]"
        @click="handleConfirm"
      >
        {{ confirmText }}
      </button>
    </template>
  </Modal>
</template>
