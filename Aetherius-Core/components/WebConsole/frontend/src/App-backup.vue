<template>
  <div id="app" class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(async () => {
  try {
    // 延迟导入stores避免初始化问题
    const { useThemeStore } = await import('@/stores/theme')
    const { useAuthStore } = await import('@/stores/auth')
    
    const themeStore = useThemeStore()
    const authStore = useAuthStore()
    
    // Initialize theme
    themeStore.initializeTheme()
    
    // Check authentication status
    await authStore.checkAuth()
    
  } catch (error) {
    console.warn('Store initialization failed in App.vue:', error)
    // 不阻止应用继续运行
  }
})
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