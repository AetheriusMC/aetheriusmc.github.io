// 测试Vue导入
import { createApp } from 'vue'

console.log('Vue导入成功')

try {
  const app = createApp({
    template: `
      <div style="padding: 20px; font-family: Arial, sans-serif;">
        <h1>Vue测试成功</h1>
        <p>Vue应用已成功创建和挂载</p>
        <p>当前时间: {{ currentTime }}</p>
        <button @click="updateTime">更新时间</button>
      </div>
    `,
    data() {
      return {
        currentTime: new Date().toLocaleString()
      }
    },
    methods: {
      updateTime() {
        this.currentTime = new Date().toLocaleString()
      }
    }
  })
  
  app.mount('#app')
  console.log('Vue应用挂载成功')
  
} catch (error) {
  console.error('Vue应用创建或挂载失败:', error)
  
  // 降级到普通HTML
  const appEl = document.getElementById('app')
  if (appEl) {
    appEl.innerHTML = `
      <div style="padding: 20px; font-family: Arial, sans-serif; border: 2px solid red;">
        <h1>Vue应用创建失败</h1>
        <p>错误: ${error}</p>
        <p>使用降级HTML显示</p>
      </div>
    `
  }
}