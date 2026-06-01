<template>
  <div id="app">
    <LoginPage />
  </div>
</template>

<script setup>
// 路径必须和你的文件位置一致！
import LoginPage from './views/Login.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
html, body, #app {
  height: 100%;
}
</style>