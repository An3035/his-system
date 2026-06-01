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
          <el-button type="primary" block @click="handleLogin">登录系统</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const loginForm = ref({
  username: 'admin',
  password: 'Admin@123'
})

const handleLogin = async () => {
  try {
    // 1. 用正确的后端登录接口路径（利用vite代理，避免跨域）
    // 2. 用表单格式发送数据，符合FastAPI OAuth2的要求
    const params = new URLSearchParams()
    params.append('username', loginForm.value.username)
    params.append('password', loginForm.value.password)

    const res = await axios.post('/api/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
    
    localStorage.setItem('token', res.data.access_token)
    ElMessage.success('🎉 登录成功！Token 已保存')
    console.log('登录返回数据:', res.data)
  } catch (err) {
    ElMessage.error('❌ 登录失败！请检查控制台错误信息')
    // 打开浏览器控制台（F12），看Network里的请求状态码
    console.error('错误详情:', err)
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