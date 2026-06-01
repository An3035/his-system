<template>
  <div class="index-container">
    <el-container>
      <el-aside width="220px" class="sidebar">
        <div class="logo">
          <span>HIS医院信息系统</span>
        </div>

        <div class="nav-menu">
          <router-link to="/index/dashboard" class="nav-item" v-if="['admin', 'director'].includes(role)">
            📊 首页概览
          </router-link>
          <router-link to="/index/patient" class="nav-item" v-if="['admin', 'doctor', 'nurse', 'cashier'].includes(role)">
            👤 患者管理
          </router-link>
          <router-link to="/index/registration" class="nav-item" v-if="['admin', 'doctor', 'cashier'].includes(role)">
            📋 门诊挂号
          </router-link>
          <router-link to="/index/prescription" class="nav-item" v-if="['admin', 'doctor'].includes(role)">
            📝 处方管理
          </router-link>
          <router-link to="/index/drug" class="nav-item" v-if="['admin', 'pharmacist'].includes(role)">
            💊 药品管理
          </router-link>
          <router-link to="/index/pharmacy" class="nav-item" v-if="['admin', 'pharmacist'].includes(role)">
            🏪 药房管理
          </router-link>
          <router-link to="/index/warehouse" class="nav-item" v-if="['admin', 'pharmacist'].includes(role)">
            🏭 药库管理
          </router-link>
          <router-link to="/index/admission" class="nav-item" v-if="['admin', 'nurse', 'cashier'].includes(role)">
            🏥 住院管理
          </router-link>
          <router-link to="/index/nurse" class="nav-item" v-if="['admin', 'nurse'].includes(role)">
            👩‍⚕️ 护士工作站
          </router-link>
          <router-link to="/index/pharmacyorder" class="nav-item" v-if="['admin', 'pharmacist'].includes(role)">
            💊 医嘱发药
          </router-link>
          <router-link to="/index/charge" class="nav-item" v-if="['admin', 'cashier'].includes(role)">
            💰 收费管理
          </router-link>
          <router-link to="/index/director" class="nav-item" v-if="['admin', 'director'].includes(role)">
            📈 院长查询
          </router-link>
          <router-link to="/index/aichat" class="nav-item" v-if="['admin', 'doctor', 'nurse', 'pharmacist', 'cashier'].includes(role)">
            🤖 AI助手
          </router-link>
          <router-link to="/index/kb-manage" class="nav-item" v-if="['admin'].includes(role)">
            📚 知识库
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
            当前用户：{{ username }}
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

const username = ref(localStorage.getItem('username') || '系统管理员')
const role = ref(localStorage.getItem('role') || 'admin')

const titleMap: Record<string, string> = {
  dashboard: '首页概览',
  patient: '患者管理',
  registration: '门诊挂号',
  prescription: '处方管理',
  drug: '药品管理',
  pharmacy: '药房管理',
  warehouse: '药库管理',
  admission: '住院管理',
  nurse: '护士工作站',
  pharmacyorder: '医嘱发药',
  charge: '收费管理',
  director: '院长查询',
  aichat: 'AI助手',
  'kb-manage': '知识库管理'
}

const title = computed(() => {
  const path = route.path.split('/').pop() || ''
  return titleMap[path] || 'HIS医院信息系统'
})

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('role')
  showSuccess('退出登录成功')
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