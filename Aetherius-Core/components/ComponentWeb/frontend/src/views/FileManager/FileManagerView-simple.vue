<template>
  <div class="file-manager-view">
    <div style="padding: 20px; background: lightblue; margin: 10px; text-align: center;">
      <h1>简化版文件管理器</h1>
      <p>这是一个简化版本，用于测试Vue组件是否能正常渲染</p>
      <p>当前时间: {{ currentTime }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const currentTime = ref('')

onMounted(() => {
  currentTime.value = new Date().toLocaleString()
  console.log('简化版文件管理器已加载')
})
</script>

<style scoped>
.file-manager-view {
  height: 100%;
  background: #f5f5f5;
}
</style>