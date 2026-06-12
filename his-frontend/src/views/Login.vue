<template>
  <div class="login-root">
    <!-- 左侧品牌区 -->
    <div class="brand-panel">
      <div class="brand-orb orb1"></div>
      <div class="brand-orb orb2"></div>
      <div class="brand-orb orb3"></div>

      <div class="brand-content">
        <div class="brand-icon">🏥</div>
        <h1 class="brand-title">医院信息系统</h1>
        <p class="brand-subtitle">Hospital Information System</p>
        <div class="brand-divider"></div>
        <ul class="feature-list">
          <li><span class="feat-dot"></span>门诊挂号 · 处方管理</li>
          <li><span class="feat-dot"></span>药房药库 · 库存监控</li>
          <li><span class="feat-dot"></span>住院管理 · 护士工作站</li>
          <li><span class="feat-dot"></span>AI 智能辅助诊断</li>
        </ul>
      </div>

      <div class="brand-footer">Powered by 南昌师范学院</div>
    </div>

    <!-- 右侧表单区 -->
    <div class="form-panel">
      <div class="form-card">
        <div class="card-accent"></div>

        <div class="form-header">
          <div class="form-logo">HIS</div>

          <!-- ========== 🆕 双入口 Tab 切换 ========== -->
          <div class="entry-tabs">
            <button
              class="entry-tab"
              :class="{ active: activeTab === 'staff' }"
              @click="switchTab('staff')"
            >
              🩺 医护登录
            </button>
            <button
              class="entry-tab"
              :class="{ active: activeTab === 'patient' }"
              @click="switchTab('patient')"
            >
              👤 患者入口
            </button>
          </div>

          <p class="form-desc">
            {{ activeTab === 'staff' ? '请登录您的账号以继续使用' : '登录或注册您的患者账号' }}
          </p>
        </div>

        <!-- 错误提示 -->
        <transition name="shake">
          <div v-if="errorMsg" class="error-alert">
            <span class="error-icon">⚠</span>
            {{ errorMsg }}
          </div>
        </transition>

        <!-- ========== 医护登录表单 ========== -->
        <div class="form-body" v-if="activeTab === 'staff'">
          <div class="field-group" :class="{ focused: focusedField === 'username' }">
            <label class="field-label">用户名</label>
            <div class="field-wrap">
              <span class="field-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                </svg>
              </span>
              <input
                v-model="staffUsername"
                type="text"
                class="field-input"
                placeholder="请输入用户名"
                autocomplete="username"
                @focus="focusedField = 'username'"
                @blur="focusedField = ''"
                @keyup.enter="focusPwd"
                ref="usernameRef"
              />
            </div>
          </div>

          <div class="field-group" :class="{ focused: focusedField === 'password' }">
            <label class="field-label">密码</label>
            <div class="field-wrap">
              <span class="field-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
              </span>
              <input
                v-model="staffPassword"
                :type="showPwd ? 'text' : 'password'"
                class="field-input"
                placeholder="请输入密码"
                autocomplete="current-password"
                @focus="focusedField = 'password'"
                @blur="focusedField = ''"
                @keyup.enter="staffLogin"
                ref="pwdRef"
              />
              <button class="pwd-toggle" type="button" @click="showPwd = !showPwd" tabindex="-1">
                <svg v-if="!showPwd" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                </svg>
                <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- 快速填充提示 -->
          <div class="hint-accounts">
            <span class="hint-label">快速登录：</span>
            <button v-for="acc in quickAccounts" :key="acc.u" class="hint-btn"
              type="button" @click="fillAccount(acc)">
              {{ acc.label }}
            </button>
          </div>

          <button
            class="login-btn"
            :class="{ loading: isLoading }"
            :disabled="isLoading"
            @click="staffLogin"
          >
            <span v-if="!isLoading" class="btn-text">
              登 录
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
              </svg>
            </span>
            <span v-else class="btn-spinner"></span>
          </button>
        </div>

        <!-- ========== 患者登录/注册表单 ========== -->
        <div class="form-body" v-if="activeTab === 'patient'">
          <!-- 登录模式 -->
          <template v-if="!patientIsRegister">
            <div class="field-group" :class="{ focused: focusedField === 'phone' }">
              <label class="field-label">手机号</label>
              <div class="field-wrap">
                <span class="field-icon">📱</span>
                <input
                  v-model="patientPhone"
                  type="tel"
                  class="field-input"
                  placeholder="请输入注册手机号"
                  @focus="focusedField = 'phone'"
                  @blur="focusedField = ''"
                  @keyup.enter="patientLogin"
                />
              </div>
            </div>

            <div class="field-group" :class="{ focused: focusedField === 'pwd2' }">
              <label class="field-label">密码</label>
              <div class="field-wrap">
                <span class="field-icon">🔒</span>
                <input
                  v-model="patientPwd"
                  :type="showPwd2 ? 'text' : 'password'"
                  class="field-input"
                  placeholder="请输入密码"
                  @focus="focusedField = 'pwd2'"
                  @blur="focusedField = ''"
                  @keyup.enter="patientLogin"
                />
                <button class="pwd-toggle" type="button" @click="showPwd2 = !showPwd2" tabindex="-1">
                  {{ showPwd2 ? '🙈' : '👁' }}
                </button>
              </div>
            </div>

            <button
              class="login-btn"
              :class="{ loading: isPatientLoading }"
              :disabled="isPatientLoading"
              @click="patientLogin"
            >
              <span v-if="!isPatientLoading" class="btn-text">登 录</span>
              <span v-else class="btn-spinner"></span>
            </button>

            <div class="form-switch">
              没有账号？
              <button class="switch-link" type="button" @click="patientIsRegister = true; errorMsg = ''">
                立即注册
              </button>
            </div>
          </template>

          <!-- 注册模式 -->
          <template v-else>
            <div class="field-group">
              <label class="field-label">姓名</label>
              <div class="field-wrap">
                <span class="field-icon">👤</span>
                <input v-model="patientRegName" type="text" class="field-input" placeholder="请输入真实姓名" />
              </div>
            </div>

            <div class="field-group">
              <label class="field-label">性别</label>
              <div class="field-wrap" style="border:none;background:transparent;display:flex;gap:16px;padding:4px 0;">
                <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:14px;">
                  <input type="radio" v-model="patientRegGender" value="男" /> 男
                </label>
                <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:14px;">
                  <input type="radio" v-model="patientRegGender" value="女" /> 女
                </label>
              </div>
            </div>

            <div class="field-group">
              <label class="field-label">手机号</label>
              <div class="field-wrap">
                <span class="field-icon">📱</span>
                <input v-model="patientPhone" type="tel" class="field-input" placeholder="用于登录" />
              </div>
            </div>

            <div class="field-group">
              <label class="field-label">身份证号 <span style="color:#909399;font-weight:400;">(选填)</span></label>
              <div class="field-wrap">
                <span class="field-icon">🪪</span>
                <input v-model="patientRegIdCard" type="text" class="field-input" placeholder="18位身份证号码" />
              </div>
            </div>

            <div class="field-group">
              <label class="field-label">设置密码</label>
              <div class="field-wrap">
                <span class="field-icon">🔒</span>
                <input
                  v-model="patientPwd"
                  :type="showPwd2 ? 'text' : 'password'"
                  class="field-input"
                  placeholder="6位以上密码"
                />
                <button class="pwd-toggle" type="button" @click="showPwd2 = !showPwd2" tabindex="-1">
                  {{ showPwd2 ? '🙈' : '👁' }}
                </button>
              </div>
            </div>

            <button
              class="login-btn"
              :class="{ loading: isPatientLoading }"
              :disabled="isPatientLoading"
              @click="patientRegister"
            >
              <span v-if="!isPatientLoading" class="btn-text">注册并登录</span>
              <span v-else class="btn-spinner"></span>
            </button>

            <div class="form-switch">
              已有账号？
              <button class="switch-link" type="button" @click="patientIsRegister = false; errorMsg = ''">
                返回登录
              </button>
            </div>
          </template>
        </div>

        <div class="form-footer">
          <p v-if="activeTab === 'staff'">默认管理员账号 <code>admin</code> / <code>Admin@123</code></p>
          <p v-else>注册即表示同意《用户服务协议》和《隐私政策》</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

// ── Tab 切换 ──
const activeTab = ref('staff')

// ── 医护登录 ──
const staffUsername = ref('')
const staffPassword = ref('')
const isLoading = ref(false)
const showPwd = ref(false)
const focusedField = ref('')
const usernameRef = ref(null)
const pwdRef = ref(null)

const quickAccounts = [
  { label: '管理员', u: 'admin',        p: 'Admin@123' },
  { label: '医生',   u: 'doctor1',     p: 'Doctor@123' },
  { label: '药师',   u: 'pharmacist1', p: 'Pharma@123' },
]

// ── 患者登录/注册 ──
const patientIsRegister = ref(false)
const patientPhone = ref('')
const patientPwd = ref('')
const patientRegName = ref('')
const patientRegGender = ref('男')
const patientRegIdCard = ref('')
const showPwd2 = ref(false)
const isPatientLoading = ref(false)

// ── 通用 ──
const errorMsg = ref('')

// ── Tab 切换 ──
const switchTab = (tab: string) => {
  activeTab.value = tab
  errorMsg.value = ''
}

// ── 医护登录 ──
const fillAccount = (acc: { u: string; p: string }) => {
  staffUsername.value = acc.u
  staffPassword.value = acc.p
  errorMsg.value = ''
}

const focusPwd = () => pwdRef.value?.focus()

const saveUserInfo = (data: any) => {
  localStorage.setItem('username', data.username)
  localStorage.setItem('real_name', data.real_name || data.username)
  localStorage.setItem('role', data.role || '')
  if (data.patient_id) {
    localStorage.setItem('patient_id', String(data.patient_id))
  }
}

const staffLogin = async () => {
  errorMsg.value = ''
  if (!staffUsername.value.trim() || !staffPassword.value) {
    errorMsg.value = '请输入用户名和密码'
    return
  }
  isLoading.value = true
  try {
    const formData = new URLSearchParams()
    formData.append('username', staffUsername.value.trim())
    formData.append('password', staffPassword.value)

    const res = await axios.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    localStorage.setItem('token', res.data.access_token)

    // 获取用户信息以确定角色
    const me = await axios.get('/api/auth/me', {
      headers: { Authorization: `Bearer ${res.data.access_token}` }
    })
    saveUserInfo(me.data)

    // 按角色跳转
    if (me.data.role === 'patient') {
      router.push('/patient')
    } else {
      router.push('/index')
    }
  } catch (err: any) {
    const detail = err.response?.data?.detail
    errorMsg.value = detail === '用户名或密码错误'
      ? '用户名或密码错误，请重试'
      : (detail || '登录失败，请检查网络连接')
  } finally {
    isLoading.value = false
  }
}

// ── 患者登录 ──
const patientLogin = async () => {
  errorMsg.value = ''
  if (!patientPhone.value.trim() || !patientPwd.value) {
    errorMsg.value = '请输入手机号和密码'
    return
  }
  isPatientLoading.value = true
  try {
    const formData = new URLSearchParams()
    formData.append('username', patientPhone.value.trim())
    formData.append('password', patientPwd.value)

    const res = await axios.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    localStorage.setItem('token', res.data.access_token)

    const me = await axios.get('/api/auth/me', {
      headers: { Authorization: `Bearer ${res.data.access_token}` }
    })
    saveUserInfo(me.data)
    router.push('/patient')
  } catch (err: any) {
    const detail = err.response?.data?.detail
    const status = err.response?.status
    if (status === 401) {
      errorMsg.value = '手机号或密码错误'
    } else {
      errorMsg.value = detail || '登录失败，请检查网络连接'
    }
  } finally {
    isPatientLoading.value = false
  }
}

// ── 患者注册 ──
const patientRegister = async () => {
  errorMsg.value = ''
  if (!patientRegName.value.trim()) {
    errorMsg.value = '请输入姓名'
    return
  }
  if (!patientPhone.value.trim()) {
    errorMsg.value = '请输入手机号'
    return
  }
  if (!patientPwd.value || patientPwd.value.length < 6) {
    errorMsg.value = '请设置至少6位密码'
    return
  }
  isPatientLoading.value = true
  try {
    const res = await axios.post('/api/auth/patient-register', {
      name: patientRegName.value.trim(),
      gender: patientRegGender.value,
      phone: patientPhone.value.trim(),
      id_card: patientRegIdCard.value || undefined,
      password: patientPwd.value,
    })
    localStorage.setItem('token', res.data.access_token)
    saveUserInfo(res.data.user)
    router.push('/patient')
  } catch (err: any) {
    const detail = err.response?.data?.detail
    const status = err.response?.status
    if (status === 409) {
      errorMsg.value = '该手机号已注册，请直接登录'
    } else {
      errorMsg.value = detail || '注册失败，请稍后重试'
    }
  } finally {
    isPatientLoading.value = false
  }
}

onMounted(() => usernameRef.value?.focus())
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ═══════════════════════════════════════════════════════════════════════════
   HIS 登录页 — 双入口门户版 v5.0
   设计理念：医疗科技感 + 数据流动感 + 沉稳商务风
   新增：医护/患者双入口 Tab 切换 + 患者自助注册
   ═══════════════════════════════════════════════════════════════════════════ */

/* ==========================================================================
   〇、关键帧动画库 (12 个独立动画)
   ========================================================================== */

@keyframes brandBreathe {
  0%   { background-position: 0% 0%; }
  25%  { background-position: 60% 40%; }
  50%  { background-position: 100% 80%; }
  75%  { background-position: 30% 100%; }
  100% { background-position: 0% 0%; }
}

@keyframes orbA {
  0%,100%{ transform:translate(0,0) scale(1); opacity:.15; }
  25%   { transform:translate(35px,-30px) scale(1.12); opacity:.19; }
  50%   { transform:translate(-10px,-55px) scale(.9); opacity:.11; }
  75%   { transform:translate(-28px,-18px) scale(1.06); opacity:.16; }
}
@keyframes orbB {
  0%,100%{ transform:translate(0,0) scale(1); opacity:.12; }
  33%   { transform:translate(-25px,-42px) scale(1.15); opacity:.17; }
  66%   { transform:translate(18px,-15px) scale(.88); opacity:.09; }
}
@keyframes orbC {
  0%,100%{ transform:translate(0,0) scale(1); opacity:.1; }
  50%   { transform:translate(20px,-28px) scale(1.2); opacity:.15; }
}
@keyframes orbD {
  0%,100%{ transform:translate(0,0) scale(1); opacity:.06; }
  50%   { transform:translate(-18px,-22px) scale(1.25); opacity:.12; }
}
@keyframes orbE {
  0%,100%{ transform:translate(0,0) scale(1); opacity:.08; }
  30%   { transform:translate(-22px,-35px) scale(1.1); opacity:.14; }
  70%   { transform:translate(15px,-8px) scale(.92); opacity:.07; }
}
@keyframes orbF {
  0%,100%{ transform:translate(0,0) scale(1); opacity:.05; }
  50%   { transform:translate(10px,-40px) scale(1.3); opacity:.1; }
}

@keyframes crossRise1 {
  0%   { transform:translateY(0) rotate(0deg); opacity:0; }
  15%  { opacity:.12; }
  85%  { opacity:.04; }
  100% { transform:translateY(-500px) rotate(30deg); opacity:0; }
}
@keyframes crossRise2 {
  0%   { transform:translateY(0) rotate(0deg); opacity:0; }
  10%  { opacity:.1; }
  90%  { opacity:.03; }
  100% { transform:translateY(-420px) rotate(-25deg); opacity:0; }
}
@keyframes crossRise3 {
  0%   { transform:translateY(0) rotate(0deg); opacity:0; }
  20%  { opacity:.08; }
  80%  { opacity:.05; }
  100% { transform:translateY(-380px) rotate(15deg); opacity:0; }
}

@keyframes iconPulse {
  0%,100%{ transform:scale(1); filter:drop-shadow(0 4px 16px rgba(56,189,248,.45)); }
  50%   { transform:scale(1.08); filter:drop-shadow(0 4px 28px rgba(56,189,248,.7)); }
}
@keyframes ringExpand {
  0%   { transform:translate(-50%,-50%) scale(.8); opacity:.5; }
  100% { transform:translate(-50%,-50%) scale(1.6); opacity:0; }
}

@keyframes ecgSweep {
  0%   { background-position: -200% center; }
  100% { background-position: 200% center; }
}

@keyframes statusPulse {
  0%,100%{ box-shadow:0 0 4px #22c55e; background:#22c55e; }
  50%   { box-shadow:0 0 12px #22c55e,0 0 20px rgba(34,197,94,.5); background:#4ade80; }
}

@keyframes lineFlow {
  0%   { background-position: -200% center; }
  100% { background-position: 200% center; }
}

@keyframes borderRotate {
  0%   { background-position: 0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

@keyframes dotBounce {
  0%,15% { box-shadow:0 0 4px #38bdf8; transform:scale(1); }
  8%     { box-shadow:0 0 14px #38bdf8,0 0 22px rgba(56,189,248,.5); transform:scale(2); }
}

@keyframes btnShimmer {
  0%   { left:-100%; }
  100% { left:200%; }
}

@keyframes slideUp {
  from { opacity:0; transform:translateY(32px); }
  to   { opacity:1; transform:translateY(0); }
}
@keyframes fadeInScale {
  from { opacity:0; transform:scale(.94); }
  to   { opacity:1; transform:scale(1); }
}

@keyframes spin { to{transform:rotate(360deg);} }
@keyframes shake {
  0%,100%{transform:translateX(0);}
  20%,60%{transform:translateX(-6px);}
  40%,80%{transform:translateX(6px);}
}

/* ==========================================================================
   一、根布局
   ========================================================================== */
.login-root {
  display: flex;
  min-height: 100vh;
  background: #0a1628;
  font-family: 'DM Sans','PingFang SC',sans-serif;
  position: relative;
}

/* ==========================================================================
   二、左侧品牌面板
   ========================================================================== */
.brand-panel {
  flex: 0 0 480px;
  background: linear-gradient(
    170deg,
    #060f1f 0%,
    #0a1a30 15%,
    #0d2342 30%,
    #112d54 50%,
    #0d2342 65%,
    #091830 80%,
    #060f1f 100%
  );
  background-size: 200% 200%;
  animation: brandBreathe 16s ease-in-out infinite;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
}

.brand-orb {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
}

.brand-orb.orb1 {
  width:340px; height:340px;
  background:radial-gradient(circle, rgba(56,189,248,.18), rgba(22,119,255,.06), transparent 72%);
  top:-100px; right:-80px;
  animation:orbA 11s ease-in-out infinite;
}

.brand-orb.orb2 {
  width:240px; height:240px;
  background:radial-gradient(circle, rgba(52,211,153,.15), rgba(16,185,129,.05), transparent 72%);
  bottom:15%; left:-80px;
  animation:orbB 13s ease-in-out infinite;
}

.brand-orb.orb3 {
  width:180px; height:180px;
  background:radial-gradient(circle, rgba(129,140,248,.16), rgba(99,102,241,.05), transparent 72%);
  bottom:-60px; right:10%;
  animation:orbC 9s ease-in-out infinite;
}

.brand-orb.orb1::before {
  content:''; position:absolute; border-radius:50%;
  width:120px; height:120px;
  top:60%; left:50%;
  background:radial-gradient(circle, rgba(251,191,36,.12), transparent 70%);
  animation:orbD 7s ease-in-out infinite;
}

.brand-orb.orb2::before {
  content:''; position:absolute; border-radius:50%;
  width:100px; height:100px;
  top:30%; right:20%;
  background:radial-gradient(circle, rgba(34,211,238,.13), transparent 70%);
  animation:orbE 8s ease-in-out infinite;
}

.brand-orb.orb3::before {
  content:''; position:absolute; border-radius:50%;
  width:80px; height:80px;
  top:40%; left:30%;
  background:radial-gradient(circle, rgba(232,121,249,.1), transparent 70%);
  animation:orbF 10s ease-in-out infinite;
}

.brand-panel::before {
  content:'+';
  position:absolute;
  left:12%; bottom:-30px;
  font-size:28px; font-weight:100;
  color:rgba(56,189,248,.15);
  pointer-events:none; z-index:0;
  animation:crossRise1 14s linear infinite;
}

.brand-panel::after {
  content:'+';
  position:absolute;
  right:22%; bottom:-40px;
  font-size:20px; font-weight:100;
  color:rgba(129,140,248,.12);
  pointer-events:none; z-index:0;
  animation:crossRise2 11s linear infinite;
  animation-delay:3s;
}

.brand-orb.orb1::after {
  content:'+';
  position:absolute;
  left:50%; bottom:20%;
  font-size:22px; font-weight:100;
  color:rgba(52,211,153,.1);
  pointer-events:none;
  animation:crossRise3 12s linear infinite;
  animation-delay:6s;
}

.brand-content {
  position:relative;
  z-index:2;
  text-align:center;
  display:flex;
  flex-direction:column;
  align-items:center;
}

.brand-icon {
  font-size:56px;
  margin-bottom:24px;
  display:inline-block;
  position:relative;
  animation:iconPulse 3.5s ease-in-out infinite;
}

.brand-icon::before {
  content:'';
  position:absolute;
  top:50%; left:50%;
  width:70px; height:70px;
  border-radius:50%;
  border:2px solid rgba(56,189,248,.25);
  animation:ringExpand 3s ease-out infinite;
}

.brand-icon::after {
  content:'';
  position:absolute;
  top:50%; left:50%;
  width:70px; height:70px;
  border-radius:50%;
  border:2px solid rgba(129,140,248,.2);
  animation:ringExpand 3s ease-out infinite;
  animation-delay:1.5s;
}

.brand-title {
  font-family:'Noto Serif SC',serif;
  font-size:34px; font-weight:700;
  color:#fff;
  margin:0 0 8px;
  letter-spacing:.04em;
  text-shadow:0 2px 16px rgba(56,189,248,.15);
}

.brand-subtitle {
  font-size:13px;
  color:#7fb6d4;
  letter-spacing:.18em;
  text-transform:uppercase;
  margin:0 0 36px;
}

.brand-divider {
  width:200px; height:2px;
  background:
    repeating-linear-gradient(
      90deg,
      transparent 0px,
      rgba(56,189,248,.3) 2px,
      transparent 4px
    ),
    linear-gradient(90deg,
      transparent 0%,
      rgba(56,189,248,.6) 35%,
      rgba(129,140,248,.8) 45%,
      rgba(56,189,248,.6) 50%,
      rgba(52,211,153,.6) 55%,
      rgba(56,189,248,.3) 65%,
      transparent 100%
    );
  background-size:8px 100%, 300% 100%;
  background-position:center, 0% center;
  animation:ecgSweep 5s linear infinite;
  border-radius:1px;
  margin:0 0 32px;
  position:relative;
}

.brand-divider::after {
  content:'';
  position:absolute;
  right:0; top:50%;
  transform:translateY(-50%);
  width:4px; height:4px;
  border-radius:50%;
  background:#38bdf8;
  box-shadow:0 0 8px #38bdf8,0 0 16px rgba(56,189,248,.5);
}

.feature-list {
  list-style:none;
  padding:0; margin:0 0 32px;
  display:flex;
  flex-direction:column;
  gap:14px;
  align-items:center;
}
.feature-list li {
  color:#9fcee8;
  font-size:14px;
  display:flex;
  align-items:center;
  gap:10px;
  transition:all .3s ease;
}
.feature-list li:hover {
  color:#fff;
  transform:translateX(5px);
}

.feat-dot {
  width:6px; height:6px;
  border-radius:50%;
  background:#38bdf8;
  flex-shrink:0;
  animation:dotBounce 4s ease-in-out infinite;
}
.feature-list li:nth-child(2) .feat-dot { animation-delay:1s; }
.feature-list li:nth-child(3) .feat-dot { animation-delay:2s; }
.feature-list li:nth-child(4) .feat-dot { animation-delay:3s; }

.brand-content::after {
  content:'● 系统运行中';
  display:block;
  font-size:11px;
  color:rgba(255,255,255,.45);
  letter-spacing:.06em;
  white-space:nowrap;
}

.brand-content::before {
  content:'';
  display:block;
  width:8px; height:8px;
  border-radius:50%;
  background:#22c55e;
  margin:0 auto 6px;
  animation:statusPulse 2.5s ease-in-out infinite;
}

.brand-footer {
  position:relative;
  z-index:2;
  color:#4d7fa0;
  font-size:12px;
  letter-spacing:.08em;
  margin-top:auto;
  padding-top:20px;
}

/* ==========================================================================
   三、右侧表单面板
   ========================================================================== */
.form-panel {
  flex:1;
  display:flex;
  align-items:center;
  justify-content:center;
  padding:40px 32px;
  background:
    linear-gradient(rgba(22,119,255,.015) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22,119,255,.015) 1px, transparent 1px),
    linear-gradient(180deg, #0d1f36 0%, #0a1628 100%);
  background-size:36px 36px, 36px 36px, 100% 100%;
}

.form-card {
  width:100%;
  max-width:430px;
  background:rgba(255,255,255,.97);
  backdrop-filter:blur(12px);
  -webkit-backdrop-filter:blur(12px);
  border-radius:20px;
  box-shadow:
    0 0 0 1px rgba(255,255,255,.08),
    0 8px 32px rgba(0,0,0,.25),
    0 32px 64px rgba(0,0,0,.15);
  overflow:hidden;
  position:relative;
  animation:fadeInScale .55s cubic-bezier(.22,1,.36,1) both;
}

.form-card::before {
  content:'';
  position:absolute;
  inset:-2px;
  border-radius:22px;
  padding:2px;
  background:linear-gradient(
    230deg,
    #0f2744, #1a7fc4, #38bdf8, #818cf8, #34d399, #1a7fc4, #0f2744
  );
  background-size:400% 400%;
  mask:linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask:linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite:xor;
  mask-composite:exclude;
  animation:borderRotate 8s ease infinite;
  opacity:.5;
  pointer-events:none;
  z-index:0;
}

.card-accent {
  height:4px;
  background:linear-gradient(90deg,
    #0f2744,#1a7fc4,#38bdf8,#818cf8,#34d399,#1a7fc4,#0f2744
  );
  background-size:200% 100%;
  animation:lineFlow 4s linear infinite;
  position:relative;
  z-index:1;
}

/* ── 头部 ── */
.form-header {
  padding:24px 36px 20px;
  text-align:center;
  position:relative;
  z-index:1;
}

.form-logo {
  display:inline-flex;
  align-items:center;
  justify-content:center;
  width:50px; height:50px;
  background:linear-gradient(135deg, #0a1929, #1677ff);
  color:#fff;
  font-size:15px; font-weight:700;
  letter-spacing:.1em;
  border-radius:14px;
  margin-bottom:16px;
  box-shadow:0 4px 16px rgba(15,39,68,.3);
}

.form-logo:hover {
  transform:scale(1.06) translateY(-1px);
  box-shadow:0 6px 20px rgba(22,119,255,.35);
}

/* 🆕 双入口 Tab 切换 */
.entry-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 12px;
  padding: 4px;
  background: #f2f4f8;
  border-radius: 10px;
}

.entry-tab {
  flex: 1;
  padding: 8px 14px;
  border: none;
  border-radius: 8px;
  background: transparent;
  font-size: 13px;
  font-weight: 500;
  color: #6b7d95;
  cursor: pointer;
  transition: all 0.25s ease;
  font-family: inherit;
  letter-spacing: 0.03em;
}

.entry-tab:hover {
  color: #1f2329;
}

.entry-tab.active {
  background: #ffffff;
  color: #1677ff;
  font-weight: 600;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.form-desc {
  font-size: 13px;
  color: #8fa3b8;
  margin: 0;
}

/* 🆕 切换链接 */
.form-switch {
  text-align: center;
  margin-top: 16px;
  font-size: 13px;
  color: #8fa3b8;
}

.switch-link {
  background: none;
  border: none;
  color: #1677ff;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  font-family: inherit;
  padding: 0;
}

.switch-link:hover {
  text-decoration: underline;
}

/* ── 错误 ── */
.error-alert {
  margin:0 36px 4px;
  padding:10px 14px;
  background:#fef2f2;
  border:1px solid #fecaca;
  border-radius:10px;
  color:#b91c1c;
  font-size:13px;
  display:flex; align-items:center; gap:8px;
  position:relative; z-index:1;
}
.error-icon { font-size:15px; }
.shake-enter-active { animation:shake .4s ease; }

/* ── 表单体 ── */
.form-body {
  padding:8px 36px 24px;
  position:relative;
  z-index:1;
}

.field-group {
  margin-bottom:16px;
  transition:transform .2s ease;
}
.field-group.focused {
  transform:translateY(-2px);
}

.field-label {
  display:block;
  font-size:12px; font-weight:600;
  color:#4a6080;
  letter-spacing:.06em;
  text-transform:uppercase;
  margin-bottom:6px;
}

.field-wrap {
  display:flex; align-items:center;
  border:1.5px solid #dde3ed;
  border-radius:12px;
  background:#f8fafc;
  transition:all .3s ease;
  overflow:hidden;
}
.field-group.focused .field-wrap {
  border-color:#1677ff;
  background:#fff;
  box-shadow:0 0 0 4px rgba(22,119,255,.08), 0 0 0 1px rgba(22,119,255,.2), 0 4px 12px rgba(22,119,255,.1);
}

.field-icon {
  padding:0 10px 0 14px;
  color:#8fa3b8;
  display:flex; align-items:center;
  flex-shrink:0;
  transition:color .3s ease, transform .3s ease;
  font-size: 14px;
}
.field-group.focused .field-icon {
  color:#1677ff;
  transform:scale(1.15);
}

.field-input {
  flex:1; border:none; outline:none;
  background:transparent;
  padding:11px 12px 11px 0;
  font-size:14px; color:#0f2744;
  font-family:inherit;
}
.field-input::placeholder { color:#b0bece; }

.pwd-toggle {
  padding:0 14px;
  background:none; border:none;
  cursor:pointer;
  color:#8fa3b8;
  display:flex; align-items:center;
  transition:color .2s;
  font-size: 14px;
}
.pwd-toggle:hover { color:#1677ff; }

/* ── 快速填充 ── */
.hint-accounts {
  display:flex; align-items:center;
  gap:6px; margin-bottom:20px;
  flex-wrap:wrap;
}
.hint-label { font-size:12px; color:#a0b4c8; }
.hint-btn {
  padding:4px 12px;
  border:1px solid #dde3ed;
  border-radius:6px;
  background:#f0f5fa;
  font-size:12px; color:#4a6080;
  cursor:pointer;
  transition:all .25s ease;
  font-family:inherit;
}
.hint-btn:hover {
  border-color:#1677ff;
  color:#1677ff;
  background:#eff7ff;
  box-shadow:0 2px 8px rgba(22,119,255,.12);
  transform:translateY(-2px);
}

/* ── 登录按钮 ── */
.login-btn {
  width:100%; height:48px;
  background:linear-gradient(135deg, #0a1929 0%, #1677ff 50%, #0a1929 100%);
  background-size:200% 100%;
  color:#fff;
  border:none;
  border-radius:12px;
  font-size:16px; font-weight:600;
  cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  transition:all .35s ease, background-position 0s;
  box-shadow:0 4px 24px rgba(22,119,255,.35);
  font-family:inherit;
  letter-spacing:.06em;
  position:relative;
  overflow:hidden;
}

.login-btn::after {
  content:'';
  position:absolute; top:0; left:-100%;
  width:60%; height:100%;
  background:linear-gradient(90deg,
    transparent 0%,
    rgba(255,255,255,.06) 40%,
    rgba(255,255,255,.18) 50%,
    rgba(255,255,255,.06) 60%,
    transparent 100%
  );
  animation:btnShimmer 3.2s ease-in-out infinite;
  pointer-events:none;
}

.login-btn:hover:not(:disabled) {
  transform:translateY(-3px);
  box-shadow:0 8px 32px rgba(22,119,255,.45);
  background-position:100% 0;
}
.login-btn:active:not(:disabled) {
  transform:translateY(0);
  box-shadow:0 2px 8px rgba(22,119,255,.2);
}
.login-btn:disabled {
  opacity:.65; cursor:not-allowed;
}
.login-btn:disabled::after { display:none; }

.btn-text {
  display:flex; align-items:center; gap:10px;
  position:relative; z-index:1;
}

.btn-spinner {
  width:22px; height:22px;
  border:2px solid rgba(255,255,255,.25);
  border-top-color:#fff;
  border-radius:50%;
  animation:spin .7s linear infinite;
  position:relative; z-index:1;
}

/* ── 底部说明 ── */
.form-footer {
  padding:0 36px 24px;
  text-align:center;
  position:relative; z-index:1;
}
.form-footer p { font-size:12px; color:#a0b4c8; margin:0; }
.form-footer code {
  background:#eef3f8; color:#4a6080;
  padding:1px 5px; border-radius:4px;
  font-size:11px;
}

/* ==========================================================================
   四、响应式
   ========================================================================== */
@media (max-width: 860px) {
  .brand-panel { display:none; }
  .form-panel {
    padding:24px 16px;
    background:linear-gradient(160deg, #0a1929, #1a3d6b);
  }
  .form-card { max-width:100%; }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration:0.01ms !important;
    animation-iteration-count:1 !important;
  }
}
</style>
