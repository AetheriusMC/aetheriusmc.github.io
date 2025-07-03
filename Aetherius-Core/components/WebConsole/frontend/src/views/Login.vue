<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <div class="flex justify-center">
        <div class="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center">
          <ServerIcon class="w-8 h-8 text-white" />
        </div>
      </div>
      <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-white">
        Aetherius WebConsole
      </h2>
      <p class="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
        登录到您的服务器管理控制台
      </p>
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
                class="appearance-none block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="请输入用户名"
                :disabled="loading"
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
                name="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                required
                class="appearance-none block w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="请输入密码"
                :disabled="loading"
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 pr-3 flex items-center"
                @click="showPassword = !showPassword"
              >
                <EyeIcon v-if="showPassword" class="h-5 w-5 text-gray-400" />
                <EyeSlashIcon v-else class="h-5 w-5 text-gray-400" />
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
                class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label for="remember-me" class="ml-2 block text-sm text-gray-900 dark:text-gray-300">
                记住我
              </label>
            </div>

            <div class="text-sm">
              <a href="#" class="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300">
                忘记密码？
              </a>
            </div>
          </div>

          <div>
            <button
              type="submit"
              class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
              :disabled="loading || !form.username || !form.password"
            >
              <span class="absolute left-0 inset-y-0 flex items-center pl-3">
                <ArrowRightCircleIcon
                  v-if="!loading"
                  class="h-5 w-5 text-blue-500 group-hover:text-blue-400"
                />
                <div v-else class="animate-spin h-5 w-5 border-2 border-blue-300 border-t-transparent rounded-full"></div>
              </span>
              {{ loading ? '登录中...' : '登录' }}
            </button>
          </div>
        </form>

        <!-- System info -->
        <div class="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
          <div class="text-center text-xs text-gray-500 dark:text-gray-400">
            <p>Aetherius WebConsole v2.0.0</p>
            <p class="mt-1">企业级Minecraft服务器管理平台</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Connection status -->
    <div class="fixed bottom-4 right-4">
      <div
        v-if="connectionStatus !== 'connected'"
        class="flex items-center space-x-2 px-3 py-2 bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 rounded-md shadow-sm"
      >
        <ExclamationTriangleIcon class="w-4 h-4" />
        <span class="text-sm">{{ getConnectionStatusText() }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import {
  ServerIcon,
  EyeIcon,
  EyeSlashIcon,
  ArrowRightCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/vue/24/outline'
import { useToast } from 'vue-toastification'
import { apiClient } from '@/services/api'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const themeStore = useThemeStore()
const toast = useToast()

const form = ref({
  username: '',
  password: '',
  rememberMe: false
})

const showPassword = ref(false)
const loading = ref(false)
const connectionStatus = ref<'connected' | 'connecting' | 'disconnected'>('connecting')

const handleLogin = async () => {
  console.log('Login button clicked!')
  console.log('Form data:', form.value)
  
  if (loading.value) return
  
  loading.value = true
  
  try {
    console.log('Calling authStore.login...')
    const success = await authStore.login(form.value.username, form.value.password)
    console.log('Login result:', success)
    
    if (success) {
      // Redirect to intended page or dashboard
      const redirect = route.query.redirect as string || '/'
      console.log('Redirecting to:', redirect)
      router.push(redirect)
    }
  } catch (error) {
    console.error('Login error:', error)
  } finally {
    loading.value = false
  }
}

const checkConnection = async () => {
  try {
    connectionStatus.value = 'connecting'
    // 直接调用health端点，绕过apiClient的baseURL
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
      return '正在连接服务器...'
    case 'disconnected':
      return '无法连接到服务器'
    default:
      return ''
  }
}

let connectionInterval: NodeJS.Timeout

onMounted(async () => {
  // Initialize theme
  themeStore.initializeTheme()
  
  // Check if already authenticated
  if (authStore.isAuthenticated) {
    router.push('/')
    return
  }
  
  // Check connection status
  await checkConnection()
  
  // Set up periodic connection checks
  connectionInterval = setInterval(checkConnection, 10000)
})

onUnmounted(() => {
  if (connectionInterval) {
    clearInterval(connectionInterval)
  }
})
</script>