import { createApp } from 'vue'
import { createPinia } from 'pinia'

console.log('开始测试stores...')

const app = createApp({
  template: `<div>Store测试页面</div>`
})

app.use(createPinia())

console.log('Pinia初始化完成')

// 测试theme store
try {
  console.log('测试theme store导入...')
  const themeModule = await import('@/stores/theme')
  console.log('Theme store模块:', themeModule)
  
  const { useThemeStore } = themeModule
  console.log('useThemeStore函数:', useThemeStore)
  
  console.log('调用useThemeStore()...')
  const themeStore = useThemeStore()
  console.log('Theme store实例:', themeStore)
  
  console.log('测试theme store方法...')
  if (themeStore && themeStore.initializeTheme) {
    console.log('initializeTheme方法存在')
    themeStore.initializeTheme()
    console.log('initializeTheme执行完成')
  } else {
    console.error('Theme store缺少initializeTheme方法')
  }
  
  console.log('✅ Theme store测试成功')
  
} catch (error) {
  console.error('❌ Theme store测试失败:', error)
}

// 测试auth store  
try {
  console.log('测试auth store导入...')
  const authModule = await import('@/stores/auth')
  console.log('Auth store模块:', authModule)
  
  const { useAuthStore } = authModule
  console.log('useAuthStore函数:', useAuthStore)
  
  const authStore = useAuthStore()
  console.log('Auth store实例:', authStore)
  
  console.log('✅ Auth store测试成功')
  
} catch (error) {
  console.error('❌ Auth store测试失败:', error)
}

app.mount('#app')
console.log('测试应用挂载完成')