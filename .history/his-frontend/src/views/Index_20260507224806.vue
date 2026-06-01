<template>
  <el-container style="height: 100vh">
    <!-- 侧边栏 -->
    <el-aside width="200px" style="background-color: #2f4050">
      <div class="logo">🏥 HIS医院系统</div>
      <el-menu
        background-color="#2f4050"
        text-color="#fff"
        active-text-color="#409eff"
      >
        <el-menu-item index="1">
          <i class="el-icon-user"></i>
          <span>患者管理</span>
        </el-menu-item>
        <el-menu-item index="2">
          <i class="el-icon-notebook-2"></i>
          <span>门诊挂号</span>
        </el-menu-item>
        <el-menu-item index="3">
          <i class="el-icon-shopping-cart-2"></i>
          <span>药房管理</span>
        </el-menu-item>
        <el-menu-item index="4">
          <i class="el-icon-setting"></i>
          <span>系统设置</span>
        </el-menu-item>
        <el-menu-item index="5" @click="logout">
          <i class="el-icon-switch-button"></i>
          <span>退出登录</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 右侧主体 -->
    <el-container>
      <!-- 顶部导航 -->
      <el-header style="background: #fff; border-bottom: 1px solid #eee">
        <div style="float: right">
          <span>欢迎：管理员</span>
        </div>
      </el-header>
      <!-- 内容区 -->
      <el-main style="background: #f3f3f4">
        <div class="home-welcome">
          <h1>欢迎使用医院信息管理系统(HIS)</h1>
          <p>登录成功！当前Token已生效</p>
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
const router = useRouter()

// 退出登录
const logout = () => {
  localStorage.removeItem('token')
  ElMessage.success('退出成功')
  router.push('/login')
}
</script>

<style scoped>
.logo {
  color: white;
  text-align: center;
  font-size: 18px;
  font-weight: bold;
  line-height: 60px;
  height: 60px;
  border-bottom: 1px solid #3d5060;
}
.el-header {
  padding: 0 20px;
  line-height: 60px;
}
.home-welcome {
  text-align: center;
  margin-top: 100px;
}
</style>