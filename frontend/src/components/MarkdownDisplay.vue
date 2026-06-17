<script setup>
/**
 * @file MarkdownDisplay.vue
 * @description Markdown渲染组件，支持语法高亮、表格、图片懒加载
 * @property {string} content - Markdown源码
 * @emits {TOCItem[]} toc-update - 当目录标题更新时触发
 */
import { ref, watch, onMounted } from 'vue';
import markdownIt from 'markdown-it';
import hljs from 'highlight.js';
import DOMPurify from 'dompurify';
import 'highlight.js/styles/github-dark.min.css';
import { getMediaUrl } from '@/utils/url';
import katex from 'katex'
import texmath from 'markdown-it-texmath'

const props = defineProps({
  content: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['toc-update']);

const renderedHtml = ref('');

// 初始化 markdown-it
const md = markdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs rounded-xl my-4 overflow-hidden"><code class="p-4 block font-mono text-[15px] leading-normal">${
          hljs.highlight(str, { language: lang, ignoreIllegals: true }).value
        }</code></pre>`;
      } catch (e) { /* ignore highlight errors, fall through to plain text */ }
    }
    return `<pre class="hljs rounded-xl my-4 overflow-hidden"><code class="p-4 block font-mono text-[15px] leading-normal">${md.utils.escapeHtml(str)}</code></pre>`;
  }
});

md.use(texmath, { engine: katex, delimiters: 'dollars' })
md.linkify.set({ fuzzyLink: false })

/**
 * 为标题添加 ID 并提取目录项
 * @param {string} content - Markdown内容
 * @returns {{html: string, toc: TOCItem[]}}
 */
const renderWithToc = (content) => {
  const toc = [];
  const tokens = md.parse(content, {});
  
  tokens.forEach((token, index) => {
    if (token.type === 'heading_open') {
      const level = parseInt(token.tag.slice(1));
      if (level >= 1 && level <= 3) {
        const nextToken = tokens[index + 1];
        if (nextToken && nextToken.type === 'inline') {
          const text = nextToken.content;
          const id = `heading-${text.toLowerCase().replace(/\s+/g, '-').replace(/[^\w\u4e00-\u9fa5-]/g, '')}-${toc.length}`;
          
          // 为标题 token 添加 id 属性
          token.attrs = token.attrs || [];
          token.attrs.push(['id', id]);
          
          toc.push({
            id,
            text,
            level
          });
        }
      }
    }
  });

  return {
    html: md.render(content), // 注意：md.render 内部也会调用 md.parse，为了简单我们直接渲染
    // 但上面的 token.attrs 修改在 md.render 时并不生效，因为 md.render 会重新 parse。
    // 所以我们需要拦截标题渲染。
    toc
  };
};

// 重新定义标题渲染规则以包含 ID 和源行号
md.renderer.rules.heading_open = (tokens, idx, options, env, self) => {
  const token = tokens[idx];
  const level = parseInt(token.tag.slice(1));
  const line = token.map ? token.map[0] : 0;
  if (level >= 1 && level <= 3) {
    const nextToken = tokens[idx + 1];
    if (nextToken && nextToken.type === 'inline') {
      const text = nextToken.content;
      const id = `heading-${text.toLowerCase().replace(/\s+/g, '-').replace(/[^\w\u4e00-\u9fa5-]/g, '')}`;
      return `<${token.tag} id="${id}" data-source-line="${line}" class="markdown-heading">`;
    }
  }
  return `<${token.tag} data-source-line="${line}">`;
};

// 段落 - 添加源行号（跳过列表项内隐藏的段落标签）
md.renderer.rules.paragraph_open = (tokens, idx, options, env, self) => {
  const token = tokens[idx];
  if (token.hidden) return '';
  const line = token.map ? token.map[0] : 0;
  return `<p data-source-line="${line}">`;
};

// 无序列表 - 添加源行号
md.renderer.rules.bullet_list_open = (tokens, idx, options, env, self) => {
  const token = tokens[idx];
  const line = token.map ? token.map[0] : 0;
  return `<ul data-source-line="${line}">`;
};

// 有序列表 - 添加源行号
md.renderer.rules.ordered_list_open = (tokens, idx, options, env, self) => {
  const token = tokens[idx];
  const line = token.map ? token.map[0] : 0;
  return `<ol data-source-line="${line}">`;
};

// 代码块 (fence) - 添加源行号并保持语法高亮
md.renderer.rules.fence = (tokens, idx, options, env, self) => {
  const token = tokens[idx];
  const line = token.map ? token.map[0] : 0;
  const info = token.info ? md.utils.escapeHtml(token.info) : '';
  const code = token.content;

  let highlighted = '';
  if (info && hljs.getLanguage(info)) {
    try {
      highlighted = hljs.highlight(code, { language: info, ignoreIllegals: true }).value;
    } catch (e) {
      highlighted = md.utils.escapeHtml(code);
    }
  } else {
    highlighted = md.utils.escapeHtml(code);
  }

  return `<pre class="hljs rounded-xl my-4 overflow-hidden" data-source-line="${line}"><code class="p-4 block font-mono text-[15px] leading-normal">${highlighted}</code></pre>`;
};

// 引用 - 添加源行号
md.renderer.rules.blockquote_open = (tokens, idx, options, env, self) => {
  const token = tokens[idx];
  const line = token.map ? token.map[0] : 0;
  return `<blockquote data-source-line="${line}">`;
};

// 表格 - 添加源行号
md.renderer.rules.table_open = (tokens, idx, options, env, self) => {
  const token = tokens[idx];
  const line = token.map ? token.map[0] : 0;
  return `<table data-source-line="${line}">`;
};

// 处理图片渲染，添加圆角和居中样式
md.renderer.rules.image = (tokens, idx, options, env, self) => {
  const token = tokens[idx];
  const srcIdx = token.attrIndex('src');
  const src = getMediaUrl(token.attrs[srcIdx][1]);
  const alt = token.content;
  return `<figure class="flex flex-col items-center my-8">
    <img src="${src}" alt="${alt}" class="rounded-xl shadow-sm max-w-full h-auto border border-gray-100" />
    ${alt ? `<figcaption class="mt-2 text-sm text-gray-500 italic">${alt}</figcaption>` : ''}
  </figure>`;
};

const updateContent = () => {
  if (!props.content) {
    renderedHtml.value = '';
    emit('toc-update', []);
    return;
  }

  // 提取 TOC
  const toc = [];
  const tokens = md.parse(props.content, {});
  tokens.forEach((token, index) => {
    if (token.type === 'heading_open') {
      const level = parseInt(token.tag.slice(1));
      if (level >= 1 && level <= 3) {
        const nextToken = tokens[index + 1];
        if (nextToken && nextToken.type === 'inline') {
          const text = nextToken.content;
          const id = `heading-${text.toLowerCase().replace(/\s+/g, '-').replace(/[^\w\u4e00-\u9fa5-]/g, '')}`;
          toc.push({ id, text, level });
        }
      }
    }
  });

  renderedHtml.value = DOMPurify.sanitize(md.render(props.content), {
    ADD_TAGS: ['math', 'semantics', 'annotation', 'mrow', 'mi', 'mn', 'mo',
               'msup', 'msub', 'mfrac', 'mtext', 'mspace', 'mstyle',
               'mtable', 'mtr', 'mtd', 'munder', 'mover', 'mphantom',
               'menclose', 'msqrt', 'mroot'],
    ADD_ATTR: ['aria-hidden', 'stretchy', 'linethickness', 'columnspacing', 'rowspacing']
  });
  emit('toc-update', toc);
};

watch(() => props.content, updateContent, { immediate: true });

onMounted(updateContent);
</script>

<template>
  <div class="markdown-body prose max-w-none" v-html="renderedHtml"></div>
</template>

<style scoped>
@reference "../style.css";

.markdown-body :deep(h1) {
  @apply text-3xl font-bold mb-6 pb-4 border-b border-gray-200 mt-8 text-gray-900;
}
.markdown-body :deep(h2) {
  @apply text-2xl font-bold mb-4 mt-10 text-gray-900;
}
.markdown-body :deep(h3) {
  @apply text-xl font-bold mb-3 mt-8 text-gray-900;
}
.markdown-body :deep(p) {
  @apply text-base leading-[1.75] mb-4 text-gray-700;
}
.markdown-body :deep(ul) {
  @apply list-disc list-outside mb-4 pl-6 space-y-2;
}
.markdown-body :deep(ol) {
  @apply list-decimal list-outside mb-4 pl-6 space-y-2;
}
.markdown-body :deep(li) {
  @apply text-gray-700;
}
.markdown-body :deep(blockquote) {
  @apply border-l-4 border-brand-500 bg-brand-50 px-6 py-4 rounded-r-lg mb-6 italic text-gray-800;
}
.markdown-body :deep(table) {
  @apply w-full border-separate border-spacing-0 mb-6 border-2 border-black rounded-lg overflow-hidden;
}
.markdown-body :deep(thead) {
  @apply bg-gray-50;
}
.markdown-body :deep(th) {
  @apply px-4 py-3 border border-gray-200 text-left font-semibold text-gray-900 text-sm;
}
.markdown-body :deep(td) {
  @apply px-4 py-3 border border-gray-200 text-gray-700 text-sm;
}
.markdown-body :deep(tr:nth-child(even)) {
  @apply bg-gray-50/50;
}
.markdown-body :deep(a) {
  @apply text-brand-600 hover:text-brand-500 underline underline-offset-4 decoration-brand-200 transition-colors;
}
.markdown-body :deep(code:not(.hljs code)) {
  @apply bg-gray-100 px-1.5 py-0.5 rounded-md font-mono text-[0.9em] text-gray-800 border border-gray-200 mx-0.5;
}
</style>
