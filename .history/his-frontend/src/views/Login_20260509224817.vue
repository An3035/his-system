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
        <!-- 顶部装饰线 -->
        <div class="card-accent"></div>

        <div class="form-header">
          <div class="form-logo">HIS</div>
          <h2 class="form-title">欢迎回来</h2>
          <p class="form-desc">请登录您的账号以继续使用</p>
        </div>

        <!-- 错误提示 -->
        <transition name="shake">
          <div v-if="errorMsg" class="error-alert">
            <span class="error-icon">⚠</span>
            {{ errorMsg }}
          </div>
        </transition>

        <div class="form-body">
          <!-- 用户名 -->
          <div class="field-group" :class="{ focused: focusedField === 'username' }">
            <label class="field-label">用户名</label>
            <div class="field-wrap">
              <span class="field-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                </svg>
              </span>
              <input
                v-model="username"
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

          <!-- 密码 -->
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
                v-model="password"
                :type="showPwd ? 'text' : 'password'"
                class="field-input"
                placeholder="请输入密码"
                autocomplete="current-password"
                @focus="focusedField = 'password'"
                @blur="focusedField = ''"
                @keyup.enter="login"
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

          <!-- 登录按钮 -->
          <button
            class="login-btn"
            :class="{ loading: isLoading }"
            :disabled="isLoading"
            @click="login"
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

        <div class="form-footer">
          <p>默认管理员账号 <code>admin</code> / <code>Admin@123</code></p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router    = useRouter()
const username  = ref('')
const password  = ref('')
const isLoading = ref(false)
const errorMsg  = ref('')
const showPwd   = ref(false)
const focusedField = ref('')
const usernameRef = ref(null)
const pwdRef      = ref(null)

const quickAccounts = [
  { label: '管理员', u: 'admin',       p: 'Admin@123' },
  { label: '医生',   u: 'doctor1',    p: 'Doctor@123' },
  { label: '药师',   u: 'pharmacist1',p: 'Pharma@123' },
]

const fillAccount = (acc) => {
  username.value = acc.u
  password.value = acc.p
  errorMsg.value = ''
}

const focusPwd = () => pwdRef.value?.focus()

const login = async () => {
  errorMsg.value = ''
  if (!username.value.trim() || !password.value) {
    errorMsg.value = '请输入用户名和密码'
    return
  }
  isLoading.value = true
  try {
    // OAuth2PasswordRequestForm 要求 application/x-www-form-urlencoded
    const formData = new URLSearchParams()
    formData.append('username', username.value.trim())
    formData.append('password', password.value)

    const res = await axios.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    const token = res.data.access_token
    localStorage.setItem('token', token)

    // 获取当前用户信息
    try {
      const me = await axios.get('/api/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      })
      localStorage.setItem('username', me.data.username)
      localStorage.setItem('real_name', me.data.real_name || me.data.username)
    } catch { /* 非关键，忽略 */ }

    router.push('/index')
  } catch (err) {
    const detail = err.response?.data?.detail
    errorMsg.value = detail === '用户名或密码错误'
      ? '用户名或密码错误，请重试'
      : (detail || '登录失败，请检查网络连接')
  } finally {
    isLoading.value = false
  }
}

onMounted(() => usernameRef.value?.focus())
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── 根布局 ── */
.login-root {
  display: flex;
  min-height: 100vh;
  background: #f8fafc;
  font-family: 'DM Sans', 'PingFang SC', sans-serif;
}

/* ══════════════════════════════
   左侧品牌面板
══════════════════════════════ */
.brand-panel {
  flex: 0 0 440px;
  background: linear-gradient(145deg, #0f2744 0%, #1a3d6b 50%, #0d5c8f 100%);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 48px 44px;
}

/* 动态光球 */
.brand-orb {
  position: absolute;
  border-radius: 50%;
  opacity: 0.12;
  animation: float 8s ease-in-out infinite;
}
.orb1 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, #38bdf8, transparent);
  top: -80px; right: -60px;
  animation-delay: 0s;
}
.orb2 {
  width: 200px; height: 200px;
  background: radial-gradient(circle, #34d399, transparent);
  bottom: 100px; left: -60px;
  animation-delay: 3s;
}
.orb3 {
  width: 150px; height: 150px;
  background: radial-gradient(circle, #818cf8, transparent);
  bottom: -40px; right: 80px;
  animation-delay: 6s;
}
@keyframes float {
  0%, 100% { transform: translateY(0) scale(1); }
  50%       { transform: translateY(-20px) scale(1.05); }
}

.brand-content { position: relative; z-index: 1; }

.brand-icon {
  font-size: 52px;
  margin-bottom: 20px;
  display: block;
  filter: drop-shadow(0 4px 12px rgba(56,189,248,.4));
}

.brand-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 8px;
  letter-spacing: .02em;
}

.brand-subtitle {
  font-size: 13px;
  color: #7fb6d4;
  letter-spacing: .15em;
  text-transform: uppercase;
  margin: 0 0 32px;
}

.brand-divider {
  width: 40px; height: 3px;
  background: linear-gradient(90deg, #38bdf8, #818cf8);
  border-radius: 2px;
  margin-bottom: 28px;
}

.feature-list {
  list-style: none;
  padding: 0; margin: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.feature-list li {
  color: #9fcee8;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.feat-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #38bdf8;
  flex-shrink: 0;
  box-shadow: 0 0 6px #38bdf8;
}

.brand-footer {
  position: relative;
  z-index: 1;
  color: #4d7fa0;
  font-size: 12px;
  letter-spacing: .08em;
}

/* ══════════════════════════════
   右侧表单面板
══════════════════════════════ */
.form-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  background: #f8fafc;
}

.form-card {
  width: 100%;
  max-width: 420px;
  background: #ffffff;
  border-radius: 20px;
  box-shadow:
    0 0 0 1px rgba(0,0,0,.05),
    0 8px 32px rgba(15,39,68,.08),
    0 32px 64px rgba(15,39,68,.04);
  overflow: hidden;
  animation: slideUp .5s cubic-bezier(.22,1,.36,1) both;
}
@keyframes slideUp {
  from { opacity:0; transform: translateY(24px); }
  to   { opacity:1; transform: translateY(0); }
}

.card-accent {
  height: 4px;
  background: linear-gradient(90deg, #0f2744, #1a7fc4, #38bdf8);
}

.form-header {
  padding: 32px 36px 24px;
  text-align: center;
}

.form-logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px; height: 48px;
  background: linear-gradient(135deg, #0f2744, #1a7fc4);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: .1em;
  border-radius: 14px;
  margin-bottom: 16px;
  box-shadow: 0 4px 12px rgba(15,39,68,.25);
}

.form-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 24px;
  font-weight: 600;
  color: #0f2744;
  margin: 0 0 6px;
}

.form-desc {
  font-size: 14px;
  color: #8fa3b8;
  margin: 0;
}

/* ── 错误提示 ── */
.error-alert {
  margin: 0 36px 4px;
  padding: 10px 14px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 10px;
  color: #b91c1c;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.error-icon { font-size: 15px; }

.shake-enter-active { animation: shake .4s ease; }
@keyframes shake {
  0%,100% { transform: translateX(0); }
  20%,60% { transform: translateX(-6px); }
  40%,80% { transform: translateX(6px); }
}

/* ── 表单主体 ── */
.form-body { padding: 8px 36px 24px; }

.field-group {
  margin-bottom: 20px;
  transition: transform .15s;
}
.field-group.focused { transform: translateY(-1px); }

.field-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #4a6080;
  letter-spacing: .06em;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.field-wrap {
  display: flex;
  align-items: center;
  border: 1.5px solid #dde3ed;
  border-radius: 12px;
  background: #f8fafc;
  transition: border-color .2s, box-shadow .2s, background .2s;
  overflow: hidden;
}
.field-group.focused .field-wrap {
  border-color: #1a7fc4;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(26,127,196,.12);
}

.field-icon {
  padding: 0 12px 0 14px;
  color: #8fa3b8;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}
.field-group.focused .field-icon { color: #1a7fc4; }

.field-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  padding: 12px 12px 12px 0;
  font-size: 15px;
  color: #0f2744;
  font-family: inherit;
}
.field-input::placeholder { color: #b0bece; }

.pwd-toggle {
  padding: 0 14px;
  background: none;
  border: none;
  cursor: pointer;
  color: #8fa3b8;
  display: flex;
  align-items: center;
  transition: color .15s;
}
.pwd-toggle:hover { color: #1a7fc4; }

/* ── 快速填充 ── */
.hint-accounts {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}
.hint-label { font-size: 12px; color: #a0b4c8; }
.hint-btn {
  padding: 3px 10px;
  border: 1px solid #dde3ed;
  border-radius: 6px;
  background: #f0f5fa;
  font-size: 12px;
  color: #4a6080;
  cursor: pointer;
  transition: all .15s;
  font-family: inherit;
}
.hint-btn:hover {
  border-color: #1a7fc4;
  color: #1a7fc4;
  background: #eff7ff;
}

/* ── 登录按钮 ── */
.login-btn {
  width: 100%;
  height: 48px;
  background: linear-gradient(135deg, #0f2744 0%, #1a7fc4 100%);
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity .2s, transform .15s, box-shadow .2s;
  box-shadow: 0 4px 16px rgba(15,39,68,.28);
  font-family: inherit;
  letter-spacing: .04em;
}
.login-btn:hover:not(:disabled) {
  opacity: .92;
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(15,39,68,.32);
}
.login-btn:active:not(:disabled) { transform: translateY(0); }
.login-btn:disabled { opacity: .7; cursor: not-allowed; }

.btn-text {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-spinner {
  width: 20px; height: 20px;
  border: 2px solid rgba(255,255,255,.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── 底部说明 ── */
.form-footer {
  padding: 0 36px 28px;
  text-align: center;
}
.form-footer p {
  font-size: 12px;
  color: #a0b4c8;
  margin: 0;
}
.form-footer code {
  background: #eef3f8;
  color: #4a6080;
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 11px;
}

/* ── 响应式 ── */
@media (max-width: 768px) {
  .brand-panel { display: none; }
  .form-panel  { padding: 24px 16px; background: #0f2744; }
  .form-card   { max-width: 100%; }
}
</style>