<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold mb-6">登录</h1>
    
    <form @submit.prevent="handleLogin" class="max-w-md">
      <div class="mb-4">
        <label class="block text-sm font-medium mb-2">用户名</label>
        <input 
          v-model="form.username"
          type="text" 
          class="w-full px-3 py-2 border border-gray-300 rounded"
          placeholder="请输入用户名"
        >
      </div>
      
      <div class="mb-6">
        <label class="block text-sm font-medium mb-2">密码</label>
        <input 
          v-model="form.password"
          type="password" 
          class="w-full px-3 py-2 border border-gray-300 rounded"
          placeholder="请输入密码"
        >
      </div>
      
      <button 
        type="submit"
        class="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
        :disabled="!form.username || !form.password"
      >
        登录
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

console.log('LoginBasic.vue 加载成功')

const form = ref({
  username: '',
  password: ''
})

const handleLogin = async () => {
  console.log('开始登录:', form.value)
  
  try {
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
    
    const data = await response.json()
    
    if (response.ok && data.access_token) {
      console.log('登录成功')
      alert('登录成功!')
      // 手动跳转
      window.location.href = '/dashboard'
    } else {
      alert('登录失败: ' + (data.message || '未知错误'))
    }
  } catch (error) {
    console.error('登录错误:', error)
    alert('登录失败: ' + error.message)
  }
}
</script>