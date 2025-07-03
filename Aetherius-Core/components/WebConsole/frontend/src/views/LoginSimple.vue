<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center">
    <div class="max-w-md w-full">
      <div class="bg-white p-8 rounded-lg shadow">
        <h1 class="text-2xl font-bold text-center mb-6">Aetherius WebConsole</h1>
        
        <form @submit.prevent="handleLogin">
          <div class="mb-4">
            <label class="block text-sm font-medium mb-2">用户名</label>
            <input 
              v-model="username" 
              type="text" 
              class="w-full px-3 py-2 border rounded-md"
              required
            />
          </div>
          
          <div class="mb-6">
            <label class="block text-sm font-medium mb-2">密码</label>
            <input 
              v-model="password" 
              type="password" 
              class="w-full px-3 py-2 border rounded-md"
              required
            />
          </div>
          
          <button 
            type="submit" 
            class="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700"
            :disabled="loading"
          >
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </form>
        
        <p class="text-center text-sm text-gray-500 mt-4">
          测试登录页面
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)

const handleLogin = async () => {
  loading.value = true
  console.log('Login attempt:', username.value)
  
  // Simulate login delay
  setTimeout(() => {
    loading.value = false
    alert('登录功能正在开发中')
    // router.push('/')
  }, 1000)
}
</script>