<template>
  <!-- 路由视图：带过渡动画的页面切换
       key 使用顶层路由路径，确保仅 login↔index 切换时触发过渡，
       index 子路由（dashboard/patient 等）由 Index.vue 内部的 router-view 渲染，不触发此处过渡 -->
  <router-view v-slot="{ Component, route }">
    <transition :name="route.meta.transition || 'fade-slide'" mode="out-in">
      <component :is="Component" :key="route.matched[0]?.path || route.path" />
    </transition>
  </router-view>
  <!-- 全局语音输入：按住空格键说话（所有页面生效） -->
  <VoiceInput />
</template>

<script setup>
import VoiceInput from './components/VoiceInput.vue'
</script>

<style>
/* ── 全局基础重置 ── */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
</style>