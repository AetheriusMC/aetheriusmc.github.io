<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold mb-4">仪表板测试页面</h1>
    <p>如果你能看到这个页面，说明Dashboard组件正常工作</p>
    <button @click="testClick" class="bg-blue-500 text-white px-4 py-2 mt-4 rounded">
      测试按钮
    </button>
  </div>
</template>

<script setup lang="ts">
console.log('DashboardTest.vue 加载成功')

const testClick = () => {
  console.log('仪表板按钮点击成功!')
  alert('仪表板按钮点击成功!')
}
</script>