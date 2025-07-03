import { createApp, h } from 'vue'

console.log('Vue导入成功')

// 使用render函数而不是template
const app = createApp({
  render() {
    return h('div', {
      style: {
        padding: '20px',
        fontFamily: 'Arial, sans-serif',
        backgroundColor: '#f0f0f0',
        border: '2px solid green'
      }
    }, [
      h('h1', 'Vue Render函数测试'),
      h('p', '如果你能看到这个，说明Vue render函数工作正常'),
      h('p', `当前时间: ${new Date().toLocaleString()}`)
    ])
  }
})

console.log('开始挂载Vue应用...')
app.mount('#app')
console.log('Vue应用挂载完成')