import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'

// 禁用Eruda错误
window.addEventListener('error', (event) => {
  if (event.message.includes('eruda') || event.message.includes('Eruda') || event.message.includes('Script error')) {
    event.preventDefault()
    event.stopPropagation()
    return false
  }
})

// 创建最小化的App组件
const MinimalApp = {
  template: `
    <div class="min-h-screen bg-gray-50">
      <div class="p-8">
        <h1 class="text-2xl font-bold text-gray-900">Aetherius WebConsole</h1>
        <p class="text-gray-600 mt-2">最小化版本运行成功</p>
        <div class="mt-4">
          <router-link to="/login" class="text-blue-600 hover:text-blue-800 mr-4">登录</router-link>
          <router-link to="/" class="text-blue-600 hover:text-blue-800">首页</router-link>
        </div>
      </div>
      <router-view />
    </div>
  `
}

console.log('创建最小化应用...')

const app = createApp(MinimalApp)
app.use(createPinia())
app.use(router)

app.mount('#app')

console.log('应用挂载成功！')