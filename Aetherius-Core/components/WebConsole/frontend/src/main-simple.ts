import { createApp } from 'vue'

// 创建一个最简单的Vue应用
const app = createApp({
  template: `
    <div style="padding: 20px; font-family: Arial, sans-serif;">
      <h1>Aetherius WebConsole</h1>
      <p>测试页面 - Vue应用已成功加载</p>
      <button @click="showAlert">点击测试</button>
    </div>
  `,
  methods: {
    showAlert() {
      alert('Vue应用工作正常！')
    }
  }
})

app.mount('#app')