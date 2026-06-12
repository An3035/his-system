<template>
  <div class="patient-index">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside width="220px" class="sidebar">
        <div class="logo">
          <span>🏥 患者服务中心</span>
        </div>

        <div class="nav-menu">
          <router-link to="/patient/dashboard" class="nav-item">
            🏠 首页概览
          </router-link>
          <router-link to="/patient/registrations" class="nav-item">
            📋 我的挂号
          </router-link>
          <router-link to="/patient/prescriptions" class="nav-item">
            📝 我的处方
          </router-link>
          <router-link to="/patient/bills" class="nav-item">
            💰 我的账单
          </router-link>
          <router-link to="/patient/aichat" class="nav-item">
            🤖 AI 健康助手
          </router-link>
        </div>

        <div class="logout" @click="handleLogout">
          🚪 退出登录
        </div>
      </el-aside>

      <el-container>
        <el-header class="header">
          <div class="header-title">{{ title }}</div>
          <div class="user-info">
            欢迎，{{ username }}
          </div>
        </el-header>
        <el-main class="main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showSuccess } from '../utils/message'

const router = useRouter()
const route = useRoute()

const username = ref(localStorage.getItem('real_name') || '患者')
const role = ref(localStorage.getItem('role') || 'patient')

const titleMap: Record<string, string> = {
  dashboard: '首页概览',
  registrations: '我的挂号',
  prescriptions: '我的处方',
  bills: '我的账单',
  aichat: 'AI 健康助手',
}

const title = computed(() => {
  const path = route.path.split('/').pop() || ''
  return titleMap[path] || '患者服务中心'
})

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('real_name')
  localStorage.removeItem('role')
  localStorage.removeItem('patient_id')
  showSuccess('已安全退出')
  router.push('/login')
}
</script>

<style scoped>
.patient-index {
  height: 100vh;
  overflow: hidden;
}

.patient-index > .el-container {
  height: 100%;
}

/* ==========================================================================
   侧边栏 — 温暖蓝绿色调（患者端）
   ========================================================================== */
.sidebar {
  width: 232px !important;
  min-width: 232px !important;
  background: linear-gradient(
    180deg,
    #0d3b3b 0%,
    #0f4a4a 20%,
    #115555 40%,
    #136060 60%,
    #115555 80%,
    #0d3b3b 100%
  ) !important;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow: 2px 0 20px rgba(0, 0, 0, 0.15);
}

.logo {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  text-align: center;
  flex-shrink: 0;
}

.logo span {
  color: #ffffff;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.nav-menu {
  flex: 1;
  min-height: 0;
  padding: 12px 0;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-menu::-webkit-scrollbar {
  width: 4px;
}
.nav-menu::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  margin: 2px 8px;
  color: rgba(255, 255, 255, 0.65) !important;
  text-decoration: none;
  font-size: 13px;
  font-weight: 400;
  letter-spacing: 0.03em;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.nav-item:hover {
  color: #ffffff !important;
  background: rgba(255, 255, 255, 0.06);
  transform: translateX(3px);
}

.nav-item.router-link-active {
  background: linear-gradient(
    135deg,
    rgba(52, 211, 153, 0.85) 0%,
    rgba(16, 185, 129, 0.7) 50%,
    rgba(52, 211, 153, 0.85) 100%
  ) !important;
  color: #ffffff !important;
  font-weight: 600;
}

.nav-item.router-link-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: #ffffff;
  border-radius: 0 3px 3px 0;
}

.logout {
  padding: 12px 20px;
  margin: 4px 8px 12px;
  color: rgba(255, 255, 255, 0.5) !important;
  font-size: 13px;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.3s ease;
  text-align: center;
  flex-shrink: 0;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.logout:hover {
  background: rgba(255, 77, 79, 0.2) !important;
  color: #ff7875 !important;
}

/* ==========================================================================
   顶部栏
   ========================================================================== */
.header {
  height: 56px !important;
  background: #ffffff !important;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  border-bottom: 2px solid #10b981;
}

.header-title {
  font-size: 16px;
  font-weight: 700;
  color: #1f2329;
}

.user-info {
  font-size: 13px;
  color: #4e5969;
  padding: 6px 14px;
  border-radius: 20px;
  background: #f0fdf4;
  border: 1px solid #a7f3d0;
  color: #059669;
}

/* ==========================================================================
   主内容区
   ========================================================================== */
.main {
  min-height: 0 !important;
  flex: 1;
  background: #f8fafb;
  padding: 20px;
  overflow-y: auto !important;
  overflow-x: hidden;
}

.main::-webkit-scrollbar {
  width: 6px;
}
.main::-webkit-scrollbar-thumb {
  background: #c9cdd4;
  border-radius: 3px;
}

/* 响应式 */
@media screen and (max-width: 1366px) {
  .sidebar {
    width: 200px !important;
    min-width: 200px !important;
  }
  .nav-item {
    padding: 10px 16px;
    font-size: 12px;
  }
}
</style>
