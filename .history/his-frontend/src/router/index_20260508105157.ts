import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Index from '../views/Index.vue'
// 导入新创建的3个页面
import Patient from '../views/Patient.vue'
import Registration from '../views/Registration.vue'
import Pharmacy from '../views/Pharmacy.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { 
    path: '/index', 
    component: Index,
    redirect: '/patient', // 默认显示患者管理
    children: [
      { path: '/patient', component: Patient },
      { path: '/registration', component: Registration },
      { path: '/pharmacy', component: Pharmacy }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：未登录不能访问首页
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router