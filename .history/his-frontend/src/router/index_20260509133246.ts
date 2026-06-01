import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Index from '../views/Index.vue'
import Dashboard from '../views/Dashboard.vue'
import Patient from '../views/Patient.vue'
import Registration from '../views/Registration.vue'
import Drug from '../views/Drug.vue'
import Pharmacy from '../views/Pharmacy.vue'
import Warehouse from '../views/Warehouse.vue'
import Prescription from '../views/Prescription.vue'
import AiChat from '../views/AiChat.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  {
    path: '/index',
    component: Index,
    redirect: '/index/dashboard',
    children: [
      { path: 'dashboard',    component: Dashboard },
      { path: 'patient',      component: Patient },
      { path: 'registration', component: Registration },
      { path: 'drug',         component: Drug },
      { path: 'pharmacy',     component: Pharmacy },
      { path: 'warehouse',    component: Warehouse },
      { path: 'prescription', component: Prescription },
      { path: 'ai',           component: AiChat },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router