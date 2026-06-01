import { createApp } from 'vue'
import App from './App.vue'
// 确保 ElementPlus 被正确引入和注册
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

const app = createApp(App)
app.use(ElementPlus) // 必须加这行！
app.mount('#app')