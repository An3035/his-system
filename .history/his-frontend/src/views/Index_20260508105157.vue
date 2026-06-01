<template>
  <el-container style="height: 100vh">
    <!-- 侧边栏 -->
    <el-aside width="200px" style="background-color: #2f4050">
      <div class="logo">🏥 HIS医院信息系统</div>
      <el-menu
        background-color="#2f4050"
        text-color="#fff"
        active-text-color="#409eff"
        router  <!-- 开启路由跳转 -->
        default-active="/patient"
      >
        <el-menu-item index="/patient">
          <i class="el-icon-user"></i>
          <span>患者管理</span>
        </el-menu-item>
        <el-menu-item index="/registration">
          <i class="el-icon-notebook-2"></i>
          <span>门诊挂号</span>
        </el-menu-item>
        <el-menu-item index="/pharmacy">
          <i class="el-icon-shopping-cart-2"></i>
          <span>药房管理</span>
        </el-menu-item>
        <el-menu-item index="logout" @click="logout">
          <i class="el-icon-switch-button"></i>
          <span>退出登录</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 右侧主体 -->
    <el-container>
      <el-header style="background: #fff; border-bottom: 1px solid #eee">
        <div style="float: right">
          <span>当前用户：管理员</span>
        </div>
      </el-header>
      <!-- 内容区：显示子页面（患者/挂号/药房） -->
      <el-main style="background: #f3f3f4; padding: 20px">
        <router-view />
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
  ElMessage.success('退出登录成功！')
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
</style>