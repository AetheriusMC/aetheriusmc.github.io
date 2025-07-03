<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <div class="flex justify-center">
        <div class="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center">
          <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12l4-4M5 12l4 4"/>
          </svg>
        </div>
      </div>
      <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-white">
        Aetherius WebConsole
      </h2>
      <p class="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
        企业级Minecraft服务器管理平台
      </p>

      <!-- Connection Status -->
      <div class="mt-4 flex justify-center">
        <span :class="getConnectionStatusClass()" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
          <span :class="getConnectionIndicatorClass()" class="w-2 h-2 rounded-full mr-1.5"></span>
          {{ getConnectionStatusText() }}
        </span>
      </div>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
      <div class="bg-white dark:bg-gray-800 py-8 px-4 shadow sm:rounded-lg sm:px-10">
        <form class="space-y-6" @submit.prevent="handleLogin">
          <div>
            <label for="username" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
              用户名
            </label>
            <div class="mt-1">
              <input
                id="username"
                v-model="form.username"
                name="username"
                type="text"
                autocomplete="username"
                required
                class="appearance-none block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                placeholder="请输入用户名"
              />
            </div>
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
              密码
            </label>
            <div class="mt-1 relative">
              <input
                id="password"
                v-model="form.password"
                :name="showPassword ? 'text' : 'password'"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                required
                class="appearance-none block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm pr-10"
                placeholder="请输入密码"
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 pr-3 flex items-center"
                @click="showPassword = !showPassword"
              >
                <svg v-if="!showPassword" class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                </svg>
                <svg v-else class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21"/>
                </svg>
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <input
                id="remember-me"
                v-model="form.rememberMe"
                name="remember-me"
                type="checkbox"
                class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700"
              />
              <label for="remember-me" class="ml-2 block text-sm text-gray-900 dark:text-gray-300">
                记住登录状态
              </label>
            </div>
          </div>

          <div>
            <button
              type="submit"
              class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
              :disabled="loading || !form.username || !form.password"
            >
              <span class="absolute left-0 inset-y-0 flex items-center pl-3">
                <svg v-if="!loading" class="h-5 w-5 text-blue-500 group-hover:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"/>
                </svg>
                <div v-else class="animate-spin h-5 w-5 border-2 border-blue-300 border-t-transparent rounded-full"></div>
              </span>
              {{ loading ? '登录中...' : '登录' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'

console.log('LoginFixed.vue 加载成功')

const router = useRouter()
const route = useRoute()

const form = ref({
  username: '',
  password: '',
  rememberMe: false
})

const showPassword = ref(false)
const loading = ref(false)
const connectionStatus = ref<'connected' | 'connecting' | 'disconnected'>('connecting')

const handleLogin = async () => {
  console.log('登录开始:', form.value)
  
  if (loading.value) return
  
  loading.value = true
  
  try {
    // 调用登录API
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
    
    console.log('登录响应:', response.status)
    const data = await response.json()
    
    if (response.ok && data.access_token) {
      console.log('登录成功，跳转到dashboard')
      // 登录成功，跳转到dashboard
      router.push('/dashboard')
    } else {
      console.error('登录失败:', data.message)
      alert('登录失败: ' + (data.message || '未知错误'))
    }
  } catch (error) {
    console.error('登录错误:', error)
    alert('登录失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const checkConnection = async () => {
  try {
    connectionStatus.value = 'connecting'
    await fetch('/health')
    connectionStatus.value = 'connected'
  } catch (error) {
    connectionStatus.value = 'disconnected'
    console.error('Connection check failed:', error)
  }
}

const getConnectionStatusText = () => {
  switch (connectionStatus.value) {
    case 'connecting':
      return '连接中...'
    case 'connected':
      return '已连接'
    case 'disconnected':
      return '连接失败'
    default:
      return '未知状态'
  }
}

const getConnectionStatusClass = () => {
  switch (connectionStatus.value) {
    case 'connecting':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
    case 'connected':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
    case 'disconnected':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300'
  }
}

const getConnectionIndicatorClass = () => {
  switch (connectionStatus.value) {
    case 'connecting':
      return 'bg-yellow-400 animate-pulse'
    case 'connected':
      return 'bg-green-400'
    case 'disconnected':
      return 'bg-red-400'
    default:
      return 'bg-gray-400'
  }
}

// 启动时检查连接
checkConnection()
</script>