/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}

declare module 'markdown-it-texmath' {
  import type MarkdownIt from 'markdown-it'
  const texmath: (md: MarkdownIt, options: { engine: unknown; delimiters: string }) => void
  export default texmath
}
