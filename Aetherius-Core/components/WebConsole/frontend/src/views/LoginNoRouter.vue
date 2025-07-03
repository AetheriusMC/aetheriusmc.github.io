<template>
  <div style="padding: 20px;">
    <h1 style="font-size: 24px; margin-bottom: 20px;">登录</h1>
    
    <form @submit.prevent="handleLogin" style="max-width: 400px;">
      <div style="margin-bottom: 15px;">
        <label style="display: block; margin-bottom: 5px;">用户名</label>
        <input 
          v-model="form.username"
          type="text" 
          style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"
          placeholder="请输入用户名"
        >
      </div>
      
      <div style="margin-bottom: 20px;">
        <label style="display: block; margin-bottom: 5px;">密码</label>
        <input 
          v-model="form.password"
          type="password" 
          style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"
          placeholder="请输入密码"
        >
      </div>
      
      <button 
        type="submit"
        style="width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;"
        :disabled="!form.username || !form.password"
      >
        登录
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

console.log('LoginNoRouter.vue 加载成功')

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
    } else {
      alert('登录失败: ' + (data.message || '未知错误'))
    }
  } catch (error) {
    console.error('登录错误:', error)
    alert('登录失败: ' + error.message)
  }
}
</script>