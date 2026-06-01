<template>
  <div class="layout">
    <!-- 侧边栏 -->
    <div class="sidebar">
      <div class="sidebar-logo">
        <span class="logo-icon">🏥</span>
        <span class="logo-text">HIS医院信息系统</span>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/index/dashboard"   class="nav-item">📊 首页概览</router-link>
        <router-link to="/index/patient"      class="nav-item">👤 患者管理</router-link>
        <router-link to="/index/registration" class="nav-item">📋 门诊挂号</router-link>
        <router-link to="/index/drug"         class="nav-item">💊 药品管理</router-link>
        <router-link to="/index/pharmacy"     class="nav-item">🏪 药房管理</router-link>
        <router-link to="/index/warehouse"    class="nav-item">🏭 药库管理</router-link>
        <router-link to="/index/prescription" class="nav-item">📄 处方管理</router-link>
        <router-link to="/index/admissions"   class="nav-item">🏥 住院管理</router-link>
        <router-link to="/index/nurse"        class="nav-item">👩‍⚕️ 护理管理</router-link>
        <router-link to="/index/ai"           class="nav-item">🤖 AI 助手</router-link>
        <div class="nav-divider"></div>
        <a class="nav-item nav-logout" @click="logout">🚪 退出登录</a>
      </nav>
    </div>

    <!-- 主内容区 -->
    <div class="main-area">
      <div class="topbar">
        <span class="page-title">{{ currentTitle }}</span>
        <span class="user-info">当前用户：{{ userName }}</span>
      </div>
      <div class="content-wrap">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import Nurse from './Nurse.vue'

const router = useRouter()
const route  = useRoute()

const userName = computed(() => localStorage.getItem('real_name') || localStorage.getItem('username') || '管理员')

const titleMap = {
  dashboard:    '首页概览',
  patient:      '患者管理',
  registration: '门诊挂号',
  drug:         '药品管理',
  pharmacy:     '药房管理',
  warehouse:    '药库管理',
  prescription: '处方管理',
  ai:           'AI 助手',
  admissions:   '住院管理',
  Nurse:        '护士管理'
}
const currentTitle = computed(() => {
  const seg = route.path.split('/').pop()
  return titleMap[seg] || 'HIS 医院信息系统'
})

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('real_name')
  router.push('/login')
}
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  background: #f0f2f5;
}

/* ── 侧边栏 ── */
.sidebar {
  width: 220px;
  min-width: 220px;
  background: #1e2a3a;
  display: flex;
  flex-direction: column;
}
.sidebar-logo {
  padding: 24px 20px 20px;
  border-bottom: 1px solid #2d3f52;
  display: flex;
  align-items: center;
  gap: 10px;
}
.logo-icon { font-size: 24px; }
.logo-text {
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.3;
}
.sidebar-nav {
  flex: 1;
  padding: 12px 0;
  display: flex;
  flex-direction: column;
}
.nav-item {
  display: block;
  padding: 12px 24px;
  color: #8fa3b8;
  text-decoration: none;
  font-size: 14px;
  transition: all .2s;
  cursor: pointer;
}
.nav-item:hover { background: #2d3f52; color: #fff; }
.nav-item.router-link-active { background: #1677ff; color: #fff; }
.nav-divider { height: 1px; background: #2d3f52; margin: 12px 0; }
.nav-logout { color: #f87171; }
.nav-logout:hover { background: #3f1f1f; color: #fca5a5; }

/* ── 主区域 ── */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.topbar {
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e8ecf0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
}
.page-title { font-size: 16px; font-weight: 600; color: #1a2332; }
.user-info   { font-size: 14px; color: #667085; }
.content-wrap { flex: 1; overflow-y: auto; padding: 20px; }
</style>