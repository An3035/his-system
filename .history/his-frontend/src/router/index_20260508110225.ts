import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Index from '../views/Index.vue'
import Patient from '../views/Patient.vue'
import Registration from '../views/Registration.vue'
import Pharmacy from '../views/Pharmacy.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { 
    path: '/index', 
    component: Index,
    redirect: '/index/patient', // 重定向到子路由
    children: [
      // 子路由必须用「相对路径」（不带 /），才能被 Index.vue 的 <router-view> 渲染
      { path: 'patient', component: Patient },
      { path: 'registration', component: Registration },
      { path: 'pharmacy', component: Pharmacy }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：未登录拦截
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router