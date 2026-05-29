<script setup lang="ts">
/**
 * MediaPickerModal - 图形化媒体图片选择器
 *
 * @description 弹窗形式的图片选择器，加载全站图片列表，
 * 以网格形式展示缩略图，点击选中后触发 @select 事件并关闭弹窗。
 *
 * @example
 * <MediaPickerModal
 *   :visible="showPicker"
 *   @close="showPicker = false"
 *   @select="onImageSelected"
 * />
 */
import { ref, watch } from 'vue'
import Modal from '@/components/Modal.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { getMedia } from '@/api/media'
import type { Media } from '@/types/api'

interface Props {
  visible: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'select', media: Media): void
}>()

const images = ref<Media[]>([])
const loading = ref(false)

watch(() => props.visible, async (newVal) => {
  if (newVal) {
    loading.value = true
    try {
      const result = await getMedia({
        file_type: 'image',
        page: 1,
        page_size: 50
      })
      images.value = result.items
    } catch {
      // Axios interceptor handles error toast
    } finally {
      loading.value = false
    }
  }
})

function handleSelect(media: Media) {
  emit('select', media)
  emit('close')
}
</script>

<template>
  <Modal
    :visible="visible"
    title="选择图片"
    width="700px"
    @close="emit('close')"
  >
    <LoadingSpinner v-if="loading" text="加载图片..." class="py-12" />

    <div v-else-if="images.length === 0" class="text-center py-12">
      <p class="text-gray-400">暂无图片</p>
    </div>

    <div v-else class="grid grid-cols-3 gap-4 max-h-[60vh] overflow-y-auto p-1">
      <div
        v-for="img in images"
        :key="img.id"
        class="group cursor-pointer rounded-xl border border-gray-100 hover:border-brand-300 overflow-hidden bg-gray-50 transition-all hover:shadow-md"
        @click="handleSelect(img)"
      >
        <div class="aspect-square flex items-center justify-center overflow-hidden">
          <img
            :src="img.url"
            :alt="img.original_name"
            class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
            loading="lazy"
          />
        </div>
        <div class="p-2">
          <p class="text-xs text-gray-600 truncate" :title="img.original_name">
            {{ img.original_name }}
          </p>
        </div>
      </div>
    </div>
  </Modal>
</template>