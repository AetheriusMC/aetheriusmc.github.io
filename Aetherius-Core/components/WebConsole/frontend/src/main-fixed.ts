import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import './style.css'

// 创建一个修复版的App组件，逐步添加store功能
const App = {
  template: `
    <div id="app" class="min-h-screen bg-gray-50 dark:bg-gray-900">
      <router-view />
    </div>
  `,
  async setup() {
    console.log('App setup开始...')
    
    try {
      // 延迟导入并初始化stores
      console.log('导入theme store...')
      const { useThemeStore } = await import('@/stores/theme')
      const themeStore = useThemeStore()
      
      console.log('初始化主题...')
      themeStore.initializeTheme()
      
      console.log('导入auth store...')
      const { useAuthStore } = await import('@/stores/auth')
      const authStore = useAuthStore()
      
      console.log('检查认证状态...')
      // 延迟执行认证检查
      setTimeout(async () => {
        try {
          await authStore.checkAuth()
          console.log('认证检查完成')
        } catch (error) {
          console.warn('认证检查失败，但应用继续运行:', error)
        }
      }, 100)
      
      console.log('App setup完成')
      
    } catch (error) {
      console.error('Store初始化失败:', error)
      // 不抛出错误，让应用继续运行
    }
    
    return {}
  }
}

console.log('创建修复版应用...')

const app = createApp(App)
app.use(createPinia())
app.use(router)

// 全局错误处理
app.config.errorHandler = (err, instance, info) => {
  console.error('Vue应用错误:', err, info)
  // 不让错误阻止应用运行
}

app.mount('#app')
console.log('修复版应用挂载成功！')