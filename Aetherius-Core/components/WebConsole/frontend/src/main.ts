import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router/simple'
import App from './App-Fixed.vue'
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'
import './style.css'

console.log('启动应用...')

// 全局错误处理
window.addEventListener('error', (event) => {
  console.error('全局错误:', {
    message: event.message,
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno,
    error: event.error,
    stack: event.error?.stack
  })
  return false
})

window.addEventListener('unhandledrejection', (event) => {
  console.error('未处理的Promise错误:', event.reason)
  event.preventDefault()
})

try {
  const app = createApp(App)
  
  // 全局错误处理器
  app.config.errorHandler = (err, instance, info) => {
    console.error('Vue错误:', err, info)
    return false
  }

  // 先注册Pinia
  const pinia = createPinia()
  app.use(pinia)
  
  // 再注册路由
  app.use(router)
  app.use(Toast, {
    position: 'top-right',
    timeout: 5000,
    closeOnClick: true,
    pauseOnFocusLoss: true,
    pauseOnHover: true,
    draggable: true,
    draggablePercent: 0.6,
    showCloseButtonOnHover: false,
    hideProgressBar: false,
    closeButton: 'button',
    icon: true,
    rtl: false
  })

  app.mount('#app')
  console.log('应用挂载成功！')
} catch (error) {
  console.error('应用启动失败:', error)
}