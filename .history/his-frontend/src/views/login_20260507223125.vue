<template>
  <div class="login-page">
    <div class="box">
      <h1>医院信息系统 HIS</h1>
      <div class="form">
        <div>用户名：admin</div>
        <div>密码：Admin@123</div>
        <button class="btn">登录</button>
      </div>
    </div>
  </div>
</template>

<script setup>
// 空脚本，无任何代码！绝对不报错
</script>

<style>
.login-page {
  width: 100vw;
  height: 100vh;
  background: #f0f2f5;
  display: flex;
  justify-content: center;
  align-items: center;
}
.box {
  background: white;
  padding: 40px;
  border-radius: 10px;
  box-shadow: 0 0 10px #ccc;
  text-align: center;
}
.btn {
  background: #409eff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  margin-top: 20px;
  cursor: pointer;
}
</style>