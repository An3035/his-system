<template>
  <div class="login-page">
    <div class="login-card">
      <h2>🏥 医院信息系统(HIS)登录</h2>
      <el-form :model="loginForm" class="login-form">
        <el-form-item label="用户名">
          <el-input v-model="loginForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" style="width: 100%" @click="handleLogin">登录系统</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
// ✅ 修复：使用封装好的 request 实例（已配置 baseURL: http://127.0.0.1:8000）
// 原来直接用裸 axios，没有 baseURL，请求会打到前端服务器（如 localhost:5173）而非后端
import request from '../utils/request'
import { useRouter } from 'vue-router'

const router = useRouter()
const loginForm = ref({
  username: 'admin',
  password: 'Admin@123'
})

const handleLogin = async () => {
  try {
    const params = new URLSearchParams()
    params.append('username', loginForm.value.username)
    params.append('password', loginForm.value.password)

    const res = await request.post('/api/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })

    localStorage.setItem('token', res.data.access_token)
    ElMessage.success('🎉 登录成功！')
    router.push('/index')
  } catch (err) {
    ElMessage.error('❌ 登录失败：' + (err.response?.data?.detail || err.message))
    console.error(err)
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
}
.login-card {
  width: 400px;
  padding: 32px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}
.login-card h2 {
  text-align: center;
  margin-bottom: 24px;
  color: #303133;
}
</style>