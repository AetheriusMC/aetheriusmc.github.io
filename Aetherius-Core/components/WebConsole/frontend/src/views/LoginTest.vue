<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center">
    <div class="bg-white p-8 rounded-lg shadow-md w-96">
      <h2 class="text-2xl font-bold mb-6 text-center">登录测试</h2>
      
      <form @submit.prevent="handleLogin">
        <div class="mb-4">
          <label class="block text-sm font-medium mb-2">用户名</label>
          <input 
            v-model="form.username"
            type="text" 
            class="w-full px-3 py-2 border border-gray-300 rounded-md"
            placeholder="请输入用户名"
          >
        </div>
        
        <div class="mb-6">
          <label class="block text-sm font-medium mb-2">密码</label>
          <input 
            v-model="form.password"
            type="password" 
            class="w-full px-3 py-2 border border-gray-300 rounded-md"
            placeholder="请输入密码"
          >
        </div>
        
        <button 
          type="submit"
          class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700"
          :disabled="!form.username || !form.password"
        >
          登录
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

console.log('LoginTest.vue 加载成功')

const form = ref({
  username: '',
  password: ''
})

const handleLogin = async () => {
  console.log('开始登录...', form.value)
  
  try {
    // 直接调用登录API
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: form.value.username,
        password: form.value.password
      })
    })
    
    console.log('登录响应状态:', response.status)
    const data = await response.json()
    console.log('登录响应数据:', data)
    
    if (response.ok && data.access_token) {
      alert('登录成功! Token: ' + data.access_token.substring(0, 20) + '...')
      console.log('登录成功，用户信息:', data.user)
    } else {
      alert('登录失败: ' + (data.message || '未知错误'))
    }
  } catch (error) {
    console.error('登录错误:', error)
    alert('登录失败: ' + error.message)
  }
}
</script>