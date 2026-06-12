import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Index from '../views/Index.vue'
import PatientIndex from '../views/PatientIndex.vue'
import Dashboard from '../views/Dashboard.vue'
import Patient from '../views/Patient.vue'
import Registration from '../views/Registration.vue'
import Drug from '../views/Drug.vue'
import Pharmacy from '../views/Pharmacy.vue'
import Warehouse from '../views/Warehouse.vue'
import Prescription from '../views/Prescription.vue'
import AiChat from '../views/AiChat.vue'
import Admission from '../views/Admission.vue'
import Nurse from '../views/Nurse.vue'
import Pharmacyorder from '../views/Pharmacyorder.vue'
import Charge from '../views/Charge.vue'
import Director from '../views/Director.vue'
import KbManage from '../views/KbManage.vue'
import PatientDashboard from '../views/PatientDashboard.vue'
import PatientRegistrations from '../views/PatientRegistrations.vue'
import PatientPrescriptions from '../views/PatientPrescriptions.vue'
import PatientBills from '../views/PatientBills.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  // ── 医护端路由 ──
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
      { path: 'aichat',       component: AiChat },
      { path: 'admission',    component: Admission },
      { path: 'nurse',        component: Nurse },
      { path: 'pharmacyorder', component: Pharmacyorder },
      { path: 'charge',       component: Charge },
      { path: 'director',     component: Director },
      { path: 'kb-manage',   component: KbManage },
    ]
  },
  // ── 患者端路由 ──
  {
    path: '/patient',
    component: PatientIndex,
    redirect: '/patient/dashboard',
    children: [
      { path: 'dashboard',     component: PatientDashboard },
      { path: 'registrations', component: PatientRegistrations },
      { path: 'prescriptions', component: PatientPrescriptions },
      { path: 'bills',         component: PatientBills },
      { path: 'aichat',        component: AiChat },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：未登录重定向到 /login；按角色隔离 /index 与 /patient
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
    return
  }

  // 按角色隔离路由
  const role = localStorage.getItem('role')
  if (token && role) {
    // 患者尝试访问医护端 → 重定向到患者端
    if (role === 'patient' && to.path.startsWith('/index')) {
      next('/patient')
      return
    }
    // 医护尝试访问患者端 → 重定向到医护端
    if (role !== 'patient' && to.path.startsWith('/patient')) {
      next('/index')
      return
    }
  }

  next()
})

export default router
