// 逐步测试各个依赖的导入
console.log('开始调试main.ts...')

try {
  console.log('1. 测试Vue导入...')
  const { createApp } = await import('vue')
  console.log('✅ Vue导入成功')

  console.log('2. 测试Pinia导入...')
  const { createPinia } = await import('pinia')
  console.log('✅ Pinia导入成功')

  console.log('3. 测试路由导入...')
  const router = await import('./router')
  console.log('✅ Router导入成功')

  console.log('4. 测试App组件导入...')
  const App = await import('./App-simple.vue')
  console.log('✅ App组件导入成功')

  console.log('5. 测试Toast导入...')
  const Toast = await import('vue-toastification')
  console.log('✅ Toast导入成功')

  console.log('6. 测试CSS导入...')
  await import('vue-toastification/dist/index.css')
  await import('./style.css')
  console.log('✅ CSS导入成功')

  console.log('7. 创建Vue应用...')
  const app = createApp(App.default)
  console.log('✅ Vue应用创建成功')

  console.log('8. 配置Pinia...')
  app.use(createPinia())
  console.log('✅ Pinia配置成功')

  console.log('9. 配置路由...')
  app.use(router.default)
  console.log('✅ 路由配置成功')

  console.log('10. 配置Toast...')
  app.use(Toast.default, {
    position: 'top-right',
    timeout: 5000
  })
  console.log('✅ Toast配置成功')

  console.log('11. 挂载应用...')
  app.mount('#app')
  console.log('✅ 应用挂载成功')

} catch (error) {
  console.error('❌ 依赖导入失败:', error)
  
  // 显示错误信息
  const appEl = document.getElementById('app')
  if (appEl) {
    appEl.innerHTML = `
      <div style="padding: 20px; color: red; font-family: Arial;">
        <h1>应用加载失败</h1>
        <p>错误: ${error}</p>
        <p>请查看控制台获取详细信息</p>
      </div>
    `
  }
}