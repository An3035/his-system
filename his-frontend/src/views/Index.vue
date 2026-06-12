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
/* ═══════════════════════════════════════════════════════════════════════════
   HIS 主布局 — 侧边导航 + 顶部栏 + 内容区
   医疗行业商务风 · 动态视觉增强版 v3.0

   🎬 新增动效 (2026-06-10):
   - 侧边栏：呼吸渐变背景 + Logo流光扫过 + 浮动光球 + 菜单脉冲光晕
   - 顶部栏：标题指示点脉冲 + 底部流动光线
   - 内容区：医疗十字水印网格
   🔧 保留 v2.1 滚动修复
   ═══════════════════════════════════════════════════════════════════════════ */

/* ==========================================================================
   〇、关键帧动画定义
   ========================================================================== */

/* 🎬 侧边栏背景呼吸 — 深蓝→靛蓝→青蓝→深蓝 12秒缓慢循环 */
@keyframes sidebarBreathe {
  0%   { background-position: 0% 0%; }
  25%  { background-position: 0% 50%; }
  50%  { background-position: 0% 100%; }
  75%  { background-position: 0% 50%; }
  100% { background-position: 0% 0%; }
}

/* 🎬 Logo 文字流光扫过 — 一道光泽从左到右 */
@keyframes logoShimmer {
  0%   { background-position: -200% center; }
  100% { background-position: 200% center; }
}

/* 🎬 浮动光球漂移 (大球) */
@keyframes orbFloat1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25%  { transform: translate(30px, -25px) scale(1.08); }
  50%  { transform: translate(-10px, -40px) scale(0.95); }
  75%  { transform: translate(-25px, -10px) scale(1.04); }
}

/* 🎬 浮动光球漂移 (小球) */
@keyframes orbFloat2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33%  { transform: translate(-20px, -30px) scale(1.1); }
  66%  { transform: translate(15px, -15px) scale(0.92); }
}

/* 🎬 浮动光球漂移 (微球) */
@keyframes orbFloat3 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50%  { transform: translate(25px, -20px) scale(1.15); }
}

/* 🎬 选中菜单项呼吸光晕 */
@keyframes activeGlow {
  0%, 100% { box-shadow: 0 2px 12px rgba(22, 119, 255, 0.4), 0 0 20px rgba(64, 150, 255, 0.15); }
  50%      { box-shadow: 0 2px 20px rgba(22, 119, 255, 0.6), 0 0 35px rgba(64, 150, 255, 0.3); }
}

/* 🎬 标题指示点脉冲 */
@keyframes dotPulse {
  0%, 100% { box-shadow: 0 0 6px rgba(22, 119, 255, 0.4); transform: scale(1); }
  50%      { box-shadow: 0 0 14px rgba(22, 119, 255, 0.7); transform: scale(1.6); }
}

/* 🎬 Header 底部光线流动 */
@keyframes headerLineFlow {
  0%   { background-position: -200% center; }
  100% { background-position: 200% center; }
}

/* 🎬 医疗十字粒子浮动 */
@keyframes crossFloat1 {
  0%, 100% { transform: translateY(0) rotate(0deg); opacity: 0.06; }
  50%      { transform: translateY(-60px) rotate(15deg); opacity: 0.14; }
}
@keyframes crossFloat2 {
  0%, 100% { transform: translateY(0) rotate(0deg); opacity: 0.04; }
  50%      { transform: translateY(-40px) rotate(-10deg); opacity: 0.1; }
}

/* ==========================================================================
   一、根容器
   ========================================================================== */
.index-container {
  height: 100vh;
  overflow: hidden;
  position: relative;
}

.index-container > .el-container {
  height: 100%;
}

.index-container > .el-container > .el-container {
  min-height: 0;
}

/* ==========================================================================
   二、左侧侧边导航栏 — 动态增强
   ========================================================================== */
.sidebar {
  width: 232px !important;
  min-width: 232px !important;
  /* 🎬 多色渐变背景 + 呼吸动画: 深蓝→靛蓝→藏青→深蓝 */
  background: linear-gradient(
    180deg,
    #0a1929 0%,
    #0d1f3c 20%,
    #0f2447 40%,
    #112b52 60%,
    #0f2447 80%,
    #0a1929 100%
  ) !important;
  background-size: 100% 300% !important;
  animation: sidebarBreathe 14s ease-in-out infinite;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow: 2px 0 20px rgba(0, 0, 0, 0.15);
  position: relative;
  z-index: 10;
}

/* 🎬 侧边栏浮动光球1 — 左上角大蓝光 */
.sidebar::before {
  content: '';
  position: absolute;
  top: -80px;
  left: -60px;
  width: 220px;
  height: 220px;
  background: radial-gradient(circle, rgba(22, 119, 255, 0.18), rgba(64, 150, 255, 0.06), transparent 70%);
  border-radius: 50%;
  pointer-events: none;
  animation: orbFloat1 11s ease-in-out infinite;
  z-index: 0;
}

/* 🎬 侧边栏浮动光球2 — 中部青蓝光球 */
.sidebar::after {
  content: '';
  position: absolute;
  top: 45%;
  right: -70px;
  width: 180px;
  height: 180px;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.12), rgba(129, 140, 248, 0.05), transparent 70%);
  border-radius: 50%;
  pointer-events: none;
  animation: orbFloat2 13s ease-in-out infinite;
  z-index: 0;
}

/* 🎬 浮动光球3 — 底部医院十字水印 (包装在logo下) */
.logo::before {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  /* 🎬 底部logo分隔线流动渐变 */
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(22, 119, 255, 0.2) 15%,
    rgba(64, 150, 255, 0.5) 50%,
    rgba(22, 119, 255, 0.2) 85%,
    transparent 100%
  );
  background-size: 200% 100%;
  animation: headerLineFlow 4s linear infinite;
}

/* ── Logo 区域 ── */
.logo {
  padding: 22px 20px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
  overflow: hidden;
}

.logo span {
  color: #ffffff;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.06em;
  white-space: nowrap;
  /* 🎬 Logo文字渐变底色 + 流光扫过 */
  background: linear-gradient(
    135deg,
    #ffffff 0%,
    #d0e0ff 30%,
    #ffffff 50%,
    #b0d0ff 70%,
    #ffffff 100%
  );
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: logoShimmer 4s ease-in-out infinite;
  position: relative;
  z-index: 1;
}

/* 🎬 Logo区域背景微光晕 */
.logo::after {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 180px;
  height: 100%;
  background: radial-gradient(ellipse at center, rgba(22, 119, 255, 0.12), transparent 70%);
  pointer-events: none;
  z-index: 0;
}

/* ── 导航菜单容器 ── */
.nav-menu {
  flex: 1;
  min-height: 0;
  padding: 8px 0;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
  z-index: 1;
}

.nav-menu::-webkit-scrollbar {
  width: 4px;
}
.nav-menu::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}
.nav-menu::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* ── 导航菜单项 ── */
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 20px;
  margin: 2px 8px;
  color: rgba(255, 255, 255, 0.65) !important;
  text-decoration: none;
  font-size: 13px;
  font-weight: 400;
  letter-spacing: 0.03em;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  white-space: nowrap;
  flex-shrink: 0;
  z-index: 1;
}

/* 🎬 菜单项hover: 背景从左到右滑入效果 */
.nav-item::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(22, 119, 255, 0.2) 0%, rgba(64, 150, 255, 0.05) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
  border-radius: 8px;
  z-index: -1;
}
.nav-item:hover::after {
  opacity: 1;
}

.nav-item:hover {
  color: #ffffff !important;
  transform: translateX(3px);
}

/* 🎬 选中菜单项 — 呼吸光晕 + 流光表面 */
.nav-item.router-link-active {
  background: linear-gradient(
    135deg,
    rgba(22, 119, 255, 0.9) 0%,
    rgba(64, 150, 255, 0.75) 50%,
    rgba(22, 119, 255, 0.9) 100%
  ) !important;
  background-size: 200% 100% !important;
  color: #ffffff !important;
  font-weight: 600;
  animation: activeGlow 3s ease-in-out infinite, headerLineFlow 6s linear infinite;
  transform: translateX(0);
}

/* 选中项左侧高亮指示条 */
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
  box-shadow: 0 0 8px rgba(255, 255, 255, 0.6);
}

/* ── 退出登录按钮 ── */
.logout {
  padding: 12px 20px;
  margin: 4px 8px 12px;
  color: rgba(255, 255, 255, 0.5) !important;
  font-size: 13px;
  font-weight: 400;
  letter-spacing: 0.03em;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: center;
  flex-shrink: 0;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  position: relative;
  z-index: 1;
}
.logout:hover {
  background: rgba(255, 77, 79, 0.18) !important;
  color: #ff7875 !important;
  font-weight: 500;
  box-shadow: 0 0 16px rgba(255, 77, 79, 0.15);
}

/* 🎬 第四光球 — 在退出按钮区域附近 */
.logout::before {
  content: '';
  position: absolute;
  bottom: -30px;
  right: 20px;
  width: 100px;
  height: 100px;
  background: radial-gradient(circle, rgba(129, 140, 248, 0.08), transparent 70%);
  border-radius: 50%;
  pointer-events: none;
  animation: orbFloat3 9s ease-in-out infinite;
}

/* ==========================================================================
   三、顶部导航栏 / 头部栏 — 动态增强
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
  position: relative;
  z-index: 9;
  transition: box-shadow 0.3s ease;
}

/* 🎬 Header底部流动渐变光线 */
.header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--his-primary, #1677ff) 20%,
    #4096ff 50%,
    var(--his-primary, #1677ff) 80%,
    transparent 100%
  );
  background-size: 200% 100%;
  animation: headerLineFlow 5s linear infinite;
  pointer-events: none;
}

.header.scrolled {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

/* ── 页面标题 ── */
.header-title {
  font-size: 16px;
  font-weight: 700;
  color: #1f2329;
  letter-spacing: 0.04em;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 🎬 标题前装饰点 — 脉冲呼吸 */
.header-title::before {
  content: '';
  display: inline-block;
  width: 7px;
  height: 7px;
  background: #1677ff;
  border-radius: 50%;
  animation: dotPulse 2.5s ease-in-out infinite;
}

/* ── 用户信息 ── */
.user-info {
  font-size: 13px;
  color: #4e5969;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  background: #f7f8fa;
  border: 1px solid #e5e6eb;
  transition: all 0.3s ease;
}
.user-info:hover {
  background: #e6f4ff;
  border-color: #91caff;
  color: #1677ff;
  box-shadow: 0 0 12px rgba(22, 119, 255, 0.1);
}

/* ==========================================================================
   四、主内容区 — 🎬 动态浅色背景
   ========================================================================== */

/* 🎬 内容区背景呼吸动画 */
@keyframes mainBreathe {
  0%, 100% { background-position: 0% 0%, 0% 0%, 0 0; }
  50%      { background-position: 0% 100%, 100% 0%, 0 0; }
}

/* 🎬 内容区光斑缓慢漂移 */
@keyframes mainOrbDrift {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33%      { transform: translate(60px, -40px) scale(1.2); }
  66%      { transform: translate(-30px, 20px) scale(0.85); }
}

.main {
  min-height: 0 !important;
  flex: 1;
  /* 🎬 三层动态背景:
     层1: 极淡网格
     层2: 微暖渐变呼吸
     层3: 底色 */
  background:
    /* 细微十字网格 */
    linear-gradient(rgba(22, 119, 255, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.02) 1px, transparent 1px),
    /* 🎬 微暖渐变: 蓝灰→暖白→蓝灰 缓慢呼吸 */
    linear-gradient(
      170deg,
      #f8f9fc 0%,
      #f5f7fb 20%,
      #fafcff 40%,
      #f6f8fc 60%,
      #f8f9fc 80%,
      #f4f6fa 100%
    );
  background-size:
    36px 36px,
    36px 36px,
    200% 200%;
  padding: 20px;
  overflow-y: auto !important;
  overflow-x: hidden;
  position: relative;
  animation: mainBreathe 12s ease-in-out infinite;
}

/* 🎬 内容区左上角微光斑 */
.main::before {
  content: '';
  position: fixed;
  top: 120px;
  right: 40px;
  width: 280px;
  height: 280px;
  background: radial-gradient(circle, rgba(22, 119, 255, 0.03), rgba(64, 150, 255, 0.01), transparent 70%);
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
  animation: mainOrbDrift 18s ease-in-out infinite;
}

/* 🎬 内容区右下角微光斑 */
.main::after {
  content: '';
  position: fixed;
  bottom: 40px;
  left: 260px;
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.025), rgba(129, 140, 248, 0.01), transparent 70%);
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
  animation: mainOrbDrift 14s ease-in-out infinite;
  animation-delay: 5s;
}

.main::-webkit-scrollbar {
  width: 6px;
}
.main::-webkit-scrollbar-track {
  background: transparent;
}
.main::-webkit-scrollbar-thumb {
  background: #c9cdd4;
  border-radius: 3px;
}
.main::-webkit-scrollbar-thumb:hover {
  background: #a8adb8;
}

/* ==========================================================================
   五、响应式适配
   ========================================================================== */
@media screen and (max-width: 1366px) {
  .sidebar {
    width: 200px !important;
    min-width: 200px !important;
  }
  .nav-item {
    padding: 9px 16px;
    margin: 1px 6px;
    font-size: 12px;
    border-radius: 6px;
  }
  .logo { padding: 16px 14px 14px; }
  .logo span { font-size: 13px; }
  .header { padding: 0 16px; }
  .main { padding: 16px; background-size: 32px 32px; /* 小屏缩小网格 */ }
}

@media screen and (min-width: 1601px) {
  .sidebar {
    width: 248px !important;
    min-width: 248px !important;
  }
  .nav-item {
    padding: 13px 24px;
    font-size: 14px;
  }
  .main { padding: 24px; background-size: 48px 48px; /* 大屏放大网格 */ }
}

/* 🎬 prefers-reduced-motion: 尊重用户动效偏好 */
@media (prefers-reduced-motion: reduce) {
  .sidebar,
  .sidebar::before,
  .sidebar::after,
  .logo span,
  .nav-item.router-link-active,
  .header::after,
  .header-title::before,
  .logout::before {
    animation: none !important;
  }
}
</style>