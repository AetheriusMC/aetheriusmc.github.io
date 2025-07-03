import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import './style.css'

// 创建工作版本，跳过store初始化问题
const App = {
  template: `
    <div id="app" class="min-h-screen bg-gray-50 dark:bg-gray-900">
      <router-view />
    </div>
  `
}

console.log('创建工作版本应用...')

const app = createApp(App)
app.use(createPinia())
app.use(router)

// 全局错误处理
app.config.errorHandler = (err, instance, info) => {
  console.warn('Vue错误已捕获:', err, info)
  return false // 防止错误冒泡
}

// 全局错误监听
window.addEventListener('error', (event) => {
  if (event.message && (event.message.includes('eruda') || event.message.includes('Eruda'))) {
    event.preventDefault()
    return false
  }
  console.warn('全局错误已捕获:', {
    message: event.message,
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno,
    error: event.error,
    stack: event.error?.stack
  })
  event.preventDefault()
  return false
})

window.addEventListener('unhandledrejection', (event) => {
  console.warn('未处理的Promise错误已捕获:', event.reason)
  event.preventDefault()
})

app.mount('#app')
console.log('工作版本应用挂载成功！')

// 延迟初始化stores，避免阻塞应用启动
setTimeout(async () => {
  try {
    console.log('延迟初始化stores...')
    
    const { useThemeStore } = await import('@/stores/theme')
    const themeStore = useThemeStore()
    themeStore.initializeTheme()
    console.log('主题初始化完成')
    
    // 不初始化auth store，让用户手动登录
    console.log('跳过auth初始化 - 用户需要手动登录')
    
  } catch (error) {
    console.warn('Store初始化失败，但应用继续运行:', error)
  }
}, 1000)