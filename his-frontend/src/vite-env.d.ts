/// <reference types="vite/client" />

// 声明 .vue 文件的类型，让TS认识Vue组件
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}