<script setup>
/**
 * @file PageTOC.vue
 * @description 页内目录导航组件，支持点击跳转和平滑滚动
 * @property {TOCItem[]} headings - 标题列表
 */
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue';

const props = defineProps({
  headings: {
    type: Array,
    default: () => []
  }
});

const activeId = ref('');
let observer = null;

/**
 * 处理平滑滚动
 * @param {string} id - 目标标题ID
 */
const scrollToHeading = (id) => {
  const element = document.getElementById(id);
  if (element) {
    const yOffset = -80; // 顶部导航栏高度约为64px，增加偏移量
    const y = element.getBoundingClientRect().top + window.pageYOffset + yOffset;
    window.scrollTo({ top: y, behavior: 'smooth' });
    activeId.value = id;
  }
};

/**
 * 初始化 IntersectionObserver 以追踪当前阅读位置
 */
const initObserver = () => {
  if (observer) {
    observer.disconnect();
  }

  observer = new IntersectionObserver((entries) => {
    // 寻找进入视口顶部的标题
    const visibleEntries = entries.filter(entry => entry.isIntersecting);
    if (visibleEntries.length > 0) {
      // 优先选择最顶部的可见标题
      const topEntry = visibleEntries.reduce((prev, curr) => {
        return (prev.boundingClientRect.top < curr.boundingClientRect.top) ? prev : curr;
      });
      activeId.value = topEntry.target.id;
    }
  }, {
    rootMargin: '-80px 0px -80% 0px', // 关注视口顶部区域
    threshold: 0
  });

  nextTick(() => {
    props.headings.forEach(heading => {
      const element = document.getElementById(heading.id);
      if (element) {
        observer.observe(element);
      }
    });
  });
};

watch(() => props.headings, () => {
  initObserver();
}, { deep: true });

onMounted(() => {
  initObserver();
});

onUnmounted(() => {
  if (observer) {
    observer.disconnect();
  }
});
</script>

<template>
  <div class="page-toc bg-white p-6 sticky top-24 max-h-[calc(100vh-120px)] overflow-y-auto">
    <div class="flex items-center gap-2 mb-6 text-gray-900">
      <div class="w-1 h-5 bg-brand-500 rounded-full"></div>
      <h3 class="text-base font-bold tracking-wide">本页目录</h3>
    </div>

    <div v-if="headings.length === 0" class="text-sm text-gray-400 italic py-4">
      暂无目录
    </div>

    <nav v-else class="relative space-y-1">
      <!-- 垂直连接线 -->
      <div class="absolute left-1 top-2 bottom-2 w-px bg-gray-100"></div>
      
      <button
        v-for="heading in headings"
        :key="heading.id"
        @click="scrollToHeading(heading.id)"
        class="group relative flex items-center w-full py-1.5 transition-all duration-200 text-left"
        :class="[
          heading.level === 1 ? 'pl-4' : heading.level === 2 ? 'pl-8' : 'pl-12',
          activeId === heading.id ? 'text-brand-600 font-semibold' : 'text-gray-500 hover:text-gray-800'
        ]"
      >
        <!-- 活动点指示器 -->
        <div 
          v-if="activeId === heading.id"
          class="absolute left-0 w-2 h-2 bg-brand-500 rounded-full border-2 border-white shadow-sm z-10"
        ></div>
        
        <span class="text-sm leading-tight transition-colors">{{ heading.text }}</span>
      </button>
    </nav>
  </div>
</template>

<style scoped>
@reference "../style.css";

/* 隐藏滚动条但保留滚动功能 */
.page-toc {
  scrollbar-width: thin;
  scrollbar-color: #E5E7EB transparent;
}

.page-toc::-webkit-scrollbar {
  width: 4px;
}

.page-toc::-webkit-scrollbar-thumb {
  @apply bg-gray-200 rounded-full;
}

.page-toc::-webkit-scrollbar-track {
  @apply bg-transparent;
}
</style>
