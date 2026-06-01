<template>
  <div class="login-container">
    <el-form ref="loginFormRef" :model="loginForm" label-width="80px">
      <el-form-item label="用户名">
        <el-input v-model="loginForm.username"></el-input>
      </el-form-item>
      <el-form-item label="密码">
        <el-input v-model="loginForm.password" show-password></el-input>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="login">登录</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { loginApiAuthLoginPost } from '@/api'
import { ElMessage } from 'element-plus'

const loginForm = ref({
  username: 'admin',
  password: 'Admin@123'
})

const login = async () => {
  const res = await loginApiAuthLoginPost(loginForm.value)
  localStorage.setItem('token', res.access_token)
  ElMessage.success('登录成功')
  // 后面可以跳转到首页
}
</script>