import { createApp } from 'vue'
import App from './App.vue'
// 引入 ElementPlus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

const app = createApp(App)
app.use(ElementPlus) // 注册 ElementPlus
app.mount('#app')