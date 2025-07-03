import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, AuthTokens } from '@/types'
import { apiClient } from '@/services/api'
import { useToast } from 'vue-toastification'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const tokens = ref<AuthTokens | null>(null)
  const loading = ref(false)
  
  // 在需要时才获取toast实例
  const getToast = () => {
    try {
      return useToast()
    } catch {
      // 如果toast不可用，返回mock对象
      return {
        success: (msg: string) => console.log('Success:', msg),
        error: (msg: string) => console.error('Error:', msg),
        info: (msg: string) => console.info('Info:', msg),
        warning: (msg: string) => console.warn('Warning:', msg)
      }
    }
  }
  
  const isAuthenticated = computed(() => !!tokens.value?.access_token)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isModerator = computed(() => user.value?.role === 'moderator' || isAdmin.value)

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      loading.value = true
      
      const response = await apiClient.post('/auth/login', {
        username,
        password
      })

      if (response.data.success) {
        tokens.value = response.data.data.tokens
        user.value = response.data.data.user
        
        // Store tokens in localStorage
        localStorage.setItem('auth_tokens', JSON.stringify(tokens.value))
        localStorage.setItem('user', JSON.stringify(user.value))
        
        // Set auth header for future requests
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${tokens.value.access_token}`
        
        getToast().success('登录成功')
        return true
      } else {
        getToast().error(response.data.message || '登录失败')
        return false
      }
    } catch (error: any) {
      console.error('Login error:', error)
      getToast().error(error.response?.data?.message || '登录失败')
      return false
    } finally {
      loading.value = false
    }
  }

  const logout = async (): Promise<void> => {
    try {
      if (tokens.value) {
        await apiClient.post('/auth/logout')
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // Clear local state
      user.value = null
      tokens.value = null
      
      // Clear localStorage
      localStorage.removeItem('auth_tokens')
      localStorage.removeItem('user')
      
      // Remove auth header
      delete apiClient.defaults.headers.common['Authorization']
      
      getToast().success('已退出登录')
    }
  }

  const refreshToken = async (): Promise<boolean> => {
    try {
      if (!tokens.value?.refresh_token) {
        return false
      }

      const response = await apiClient.post('/auth/refresh', {
        refresh_token: tokens.value.refresh_token
      })

      if (response.data.success) {
        tokens.value = response.data.data.tokens
        
        // Update localStorage
        localStorage.setItem('auth_tokens', JSON.stringify(tokens.value))
        
        // Update auth header
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${tokens.value.access_token}`
        
        return true
      }
    } catch (error) {
      console.error('Token refresh error:', error)
      await logout()
    }
    
    return false
  }

  const checkAuth = async (): Promise<void> => {
    try {
      // Try to load from localStorage
      const storedTokens = localStorage.getItem('auth_tokens')
      const storedUser = localStorage.getItem('user')
      
      if (storedTokens && storedUser) {
        tokens.value = JSON.parse(storedTokens)
        user.value = JSON.parse(storedUser)
        
        // Set auth header
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${tokens.value!.access_token}`
        
        // Verify token with server
        try {
          const response = await apiClient.get('/auth/me')
          if (response.data.success) {
            user.value = response.data.data
            localStorage.setItem('user', JSON.stringify(user.value))
          } else {
            throw new Error('Invalid token')
          }
        } catch (error) {
          // Try to refresh token
          const refreshed = await refreshToken()
          if (!refreshed) {
            await logout()
          }
        }
      }
    } catch (error) {
      console.error('Auth check error:', error)
      await logout()
    }
  }

  const updateProfile = async (data: Partial<User>): Promise<boolean> => {
    try {
      loading.value = true
      
      const response = await apiClient.put('/auth/profile', data)
      
      if (response.data.success) {
        user.value = { ...user.value!, ...response.data.data }
        localStorage.setItem('user', JSON.stringify(user.value))
        getToast().success('个人资料更新成功')
        return true
      } else {
        getToast().error(response.data.message || '更新失败')
        return false
      }
    } catch (error: any) {
      console.error('Profile update error:', error)
      getToast().error(error.response?.data?.message || '更新失败')
      return false
    } finally {
      loading.value = false
    }
  }

  const changePassword = async (currentPassword: string, newPassword: string): Promise<boolean> => {
    try {
      loading.value = true
      
      const response = await apiClient.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword
      })
      
      if (response.data.success) {
        getToast().success('密码修改成功')
        return true
      } else {
        getToast().error(response.data.message || '密码修改失败')
        return false
      }
    } catch (error: any) {
      console.error('Password change error:', error)
      getToast().error(error.response?.data?.message || '密码修改失败')
      return false
    } finally {
      loading.value = false
    }
  }

  // Setup token refresh interceptor
  const setupTokenRefresh = () => {
    apiClient.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401 && tokens.value) {
          const refreshed = await refreshToken()
          if (refreshed) {
            // Retry the original request
            const config = error.config
            config.headers['Authorization'] = `Bearer ${tokens.value!.access_token}`
            return apiClient.request(config)
          }
        }
        return Promise.reject(error)
      }
    )
  }

  // Initialize token refresh interceptor
  setupTokenRefresh()

  return {
    user: computed(() => user.value),
    tokens: computed(() => tokens.value),
    loading: computed(() => loading.value),
    isAuthenticated,
    isAdmin,
    isModerator,
    login,
    logout,
    refreshToken,
    checkAuth,
    updateProfile,
    changePassword
  }
})