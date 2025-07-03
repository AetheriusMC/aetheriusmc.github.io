// 最基础的测试 - 不导入任何Vue或其他库
console.log('Script loaded successfully')

document.addEventListener('DOMContentLoaded', () => {
  const app = document.getElementById('app')
  if (app) {
    app.innerHTML = `
      <div style="padding: 20px; font-family: Arial, sans-serif;">
        <h1>基础测试页面</h1>
        <p>如果你能看到这个页面，说明JavaScript基础功能正常</p>
        <p>时间: ${new Date().toLocaleString()}</p>
      </div>
    `
  } else {
    console.error('找不到#app元素')
  }
})