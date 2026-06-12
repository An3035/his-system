import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
/* HIS 全局主题样式（医疗行业商务风 — 在 Element Plus 之后加载以覆盖默认样式） */
import './style.css'
// 引入路由
import router from './router'

const app = createApp(App)
app.use(ElementPlus)
app.use(router) // 注册路由
app.mount('#app')