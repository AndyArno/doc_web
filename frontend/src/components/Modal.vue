<script setup>
/**
 * Modal - 通用弹窗组件
 *
 * @description 一个高度可定制的弹窗组件，支持 Teleport 到 body，
 * 具有平滑的缩放和淡入动画。
 *
 * @example
 * <Modal v-model:visible="show" title="提示">
 *   <div>内容</div>
 *   <template #footer>
 *     <button @click="show = false">取消</button>
 *   </template>
 * </Modal>
 */
import { onMounted, onUnmounted, watch } from 'vue';
import { X } from 'lucide-vue-next';

const props = defineProps({
  /** 是否显示 */
  visible: {
    type: Boolean,
    default: false
  },
  /** 弹窗标题 */
  title: {
    type: String,
    default: ''
  },
  /** 弹窗宽度 */
  width: {
    type: String,
    default: '500px'
  },
  /** 是否显示关闭按钮 */
  closable: {
    type: Boolean,
    default: true
  },
  /** 点击遮罩层是否关闭 */
  maskClosable: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(['close', 'update:visible']);

/**
 * 关闭弹窗
 */
const handleClose = () => {
  emit('update:visible', false);
  emit('close');
};

/**
 * 处理遮罩层点击
 */
const handleMaskClick = () => {
  if (props.maskClosable && props.closable) {
    handleClose();
  }
};

/**
 * 处理 Esc 键点击
 */
const handleEsc = (e) => {
  if (props.visible && props.closable && e.key === 'Escape') {
    handleClose();
  }
};

onMounted(() => {
  window.addEventListener('keydown', handleEsc);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleEsc);
});

// 禁止背景滚动
watch(() => props.visible, (val) => {
  if (val) {
    document.body.style.overflow = 'hidden';
  } else {
    document.body.style.overflow = '';
  }
});
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="visible" class="fixed inset-0 z-50 overflow-y-auto" role="dialog" aria-modal="true">
        <!-- 遮罩层 -->
        <div 
          class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm transition-opacity" 
          @click="handleMaskClick"
        ></div>

        <!-- 弹窗容器 -->
        <div class="flex min-h-full items-center justify-center p-4 text-center sm:p-0">
          <Transition name="zoom" appear>
            <div 
              v-if="visible"
              class="relative transform overflow-hidden rounded-2xl bg-white text-left shadow-xl transition-all sm:my-8 w-full"
              :style="{ maxWidth: width }"
            >
              <!-- 头部 -->
              <div v-if="title || closable" class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                <h3 class="text-lg font-semibold text-gray-900 leading-6">
                  {{ title }}
                </h3>
                <button
                  v-if="closable"
                  type="button"
                  class="rounded-lg p-1 text-gray-400 hover:text-gray-500 hover:bg-gray-100 transition-colors focus:outline-none"
                  @click="handleClose"
                >
                  <span class="sr-only">Close</span>
                  <X class="h-5 w-5" />
                </button>
              </div>

              <!-- 内容区 -->
              <div class="px-6 py-4">
                <slot></slot>
              </div>

              <!-- 底部区 -->
              <div v-if="$slots.footer" class="px-6 py-4 border-t border-gray-100 bg-gray-50/50 flex justify-end gap-3">
                <slot name="footer"></slot>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* 淡入淡出动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 缩放动画 */
.zoom-enter-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.zoom-leave-active {
  transition: all 0.2s ease-in;
}

.zoom-enter-from {
  opacity: 0;
  transform: scale(0.95);
}

.zoom-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
