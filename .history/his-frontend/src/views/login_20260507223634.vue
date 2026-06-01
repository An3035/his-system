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
// 确保用相对路径导入，和你的 api 文件夹位置一致
import { loginApiAuthLoginPost } from '../api'

const loginForm = ref({
  username: 'admin',
  password: 'Admin@123'
})

// 真实登录逻辑：调用后端接口，获取 Token 并保存
const handleLogin = async () => {
  try {
    // 调用自动生成的登录接口
    const res = await loginApiAuthLoginPost(loginForm.value)
    // 把 Token 保存到本地存储，后续接口会自动携带
    localStorage.setItem('token', res.access_token)
    ElMessage.success('🎉 登录成功！Token 已保存')
    console.log('登录返回数据（含 Token）：', res)
    // 这里可以加跳转逻辑，比如跳转到首页
    // window.location.href = '/dashboard'
  } catch (err) {
    ElMessage.error('❌ 登录失败！请检查：用户名/密码、后端服务是否运行')
    console.error('登录错误详情：', err)
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