<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <div class="p-8">
      <h1 class="text-2xl font-bold text-gray-900">Aetherius WebConsole</h1>
      <p class="text-gray-600 mt-2">应用加载成功 - 简化版本</p>
    </div>
    <router-view />
  </div>
</template>

<script setup lang="ts">
// 最简化的App组件，不导入任何stores
console.log('App组件setup函数执行')
</script>

<style>
html {
  font-family: 'Inter', sans-serif;
}

#app {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>