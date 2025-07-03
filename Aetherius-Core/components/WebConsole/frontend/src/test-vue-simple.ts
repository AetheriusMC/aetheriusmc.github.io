import { createApp } from 'vue'

console.log('Vue导入成功')

// 测试最简单的Vue应用
console.log('开始创建Vue应用...')

const app = createApp({
  template: '<div>最简单的Vue应用</div>'
})

console.log('Vue应用创建成功，开始挂载...')

const appElement = document.getElementById('app')
console.log('app元素:', appElement)

if (appElement) {
  app.mount('#app')
  console.log('Vue应用挂载成功')
} else {
  console.error('找不到#app元素')
  document.body.innerHTML = '<div style="color: red;">找不到#app元素</div>'
}