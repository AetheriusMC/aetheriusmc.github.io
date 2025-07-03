import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ServerStatus, SystemMetrics, Plugin, WorldInfo, Player } from '@/types'
import { apiClient } from '@/services/api'
import { useToast } from 'vue-toastification'

const toast = useToast()

export const useServerStore = defineStore('server', () => {
  const status = ref<ServerStatus | null>(null)
  const metrics = ref<SystemMetrics[]>([])
  const plugins = ref<Plugin[]>([])
  const worlds = ref<WorldInfo[]>([])
  const onlinePlayers = ref<Player[]>([])
  const loading = ref(false)
  const connecting = ref(false)

  const isOnline = computed(() => status.value?.status === 'online')
  const playerCount = computed(() => status.value?.players_online || 0)
  const maxPlayers = computed(() => status.value?.max_players || 0)
  const memoryUsage = computed(() => status.value?.memory_usage)
  const cpuUsage = computed(() => status.value?.cpu_usage || 0)
  const diskUsage = computed(() => status.value?.disk_usage)

  const fetchServerStatus = async (): Promise<void> => {
    try {
      const response = await apiClient.get('/server/status')
      if (response.data.success) {
        status.value = response.data.data
      }
    } catch (error) {
      console.error('Failed to fetch server status:', error)
    }
  }

  const startServer = async (): Promise<boolean> => {
    try {
      loading.value = true
      const response = await apiClient.post('/server/start')
      
      if (response.data.success) {
        toast.success('服务器启动中...')
        await fetchServerStatus()
        return true
      } else {
        toast.error(response.data.message || '服务器启动失败')
        return false
      }
    } catch (error: any) {
      console.error('Server start error:', error)
      toast.error(error.response?.data?.message || '服务器启动失败')
      return false
    } finally {
      loading.value = false
    }
  }

  const stopServer = async (): Promise<boolean> => {
    try {
      loading.value = true
      const response = await apiClient.post('/server/stop')
      
      if (response.data.success) {
        toast.success('服务器关闭中...')
        await fetchServerStatus()
        return true
      } else {
        toast.error(response.data.message || '服务器关闭失败')
        return false
      }
    } catch (error: any) {
      console.error('Server stop error:', error)
      toast.error(error.response?.data?.message || '服务器关闭失败')
      return false
    } finally {
      loading.value = false
    }
  }

  const restartServer = async (): Promise<boolean> => {
    try {
      loading.value = true
      const response = await apiClient.post('/server/restart')
      
      if (response.data.success) {
        toast.success('服务器重启中...')
        await fetchServerStatus()
        return true
      } else {
        toast.error(response.data.message || '服务器重启失败')
        return false
      }
    } catch (error: any) {
      console.error('Server restart error:', error)
      toast.error(error.response?.data?.message || '服务器重启失败')
      return false
    } finally {
      loading.value = false
    }
  }

  const killServer = async (): Promise<boolean> => {
    try {
      loading.value = true
      const response = await apiClient.post('/server/kill')
      
      if (response.data.success) {
        toast.success('服务器强制关闭')
        await fetchServerStatus()
        return true
      } else {
        toast.error(response.data.message || '服务器强制关闭失败')
        return false
      }
    } catch (error: any) {
      console.error('Server kill error:', error)
      toast.error(error.response?.data?.message || '服务器强制关闭失败')
      return false
    } finally {
      loading.value = false
    }
  }

  const fetchMetrics = async (timeRange: string = '1h'): Promise<void> => {
    try {
      const response = await apiClient.get(`/monitoring/metrics`, {
        params: { time_range: timeRange }
      })
      if (response.data.success) {
        metrics.value = response.data.data
      }
    } catch (error) {
      console.error('Failed to fetch metrics:', error)
    }
  }

  const fetchPlugins = async (): Promise<void> => {
    try {
      const response = await apiClient.get('/server/plugins')
      if (response.data.success) {
        plugins.value = response.data.data
      }
    } catch (error) {
      console.error('Failed to fetch plugins:', error)
    }
  }

  const enablePlugin = async (pluginName: string): Promise<boolean> => {
    try {
      const response = await apiClient.post(`/server/plugins/${pluginName}/enable`)
      
      if (response.data.success) {
        toast.success(`插件 ${pluginName} 已启用`)
        await fetchPlugins()
        return true
      } else {
        toast.error(response.data.message || `插件 ${pluginName} 启用失败`)
        return false
      }
    } catch (error: any) {
      console.error('Plugin enable error:', error)
      toast.error(error.response?.data?.message || `插件 ${pluginName} 启用失败`)
      return false
    }
  }

  const disablePlugin = async (pluginName: string): Promise<boolean> => {
    try {
      const response = await apiClient.post(`/server/plugins/${pluginName}/disable`)
      
      if (response.data.success) {
        toast.success(`插件 ${pluginName} 已禁用`)
        await fetchPlugins()
        return true
      } else {
        toast.error(response.data.message || `插件 ${pluginName} 禁用失败`)
        return false
      }
    } catch (error: any) {
      console.error('Plugin disable error:', error)
      toast.error(error.response?.data?.message || `插件 ${pluginName} 禁用失败`)
      return false
    }
  }

  const reloadPlugin = async (pluginName: string): Promise<boolean> => {
    try {
      const response = await apiClient.post(`/server/plugins/${pluginName}/reload`)
      
      if (response.data.success) {
        toast.success(`插件 ${pluginName} 已重载`)
        await fetchPlugins()
        return true
      } else {
        toast.error(response.data.message || `插件 ${pluginName} 重载失败`)
        return false
      }
    } catch (error: any) {
      console.error('Plugin reload error:', error)
      toast.error(error.response?.data?.message || `插件 ${pluginName} 重载失败`)
      return false
    }
  }

  const fetchWorlds = async (): Promise<void> => {
    try {
      const response = await apiClient.get('/server/worlds')
      if (response.data.success) {
        worlds.value = response.data.data
      }
    } catch (error) {
      console.error('Failed to fetch worlds:', error)
    }
  }

  const fetchOnlinePlayers = async (): Promise<void> => {
    try {
      const response = await apiClient.get('/players/online')
      if (response.data.success) {
        onlinePlayers.value = response.data.data
      }
    } catch (error) {
      console.error('Failed to fetch online players:', error)
    }
  }

  const sendCommand = async (command: string): Promise<boolean> => {
    try {
      const response = await apiClient.post('/console/command', { command })
      
      if (response.data.success) {
        return true
      } else {
        toast.error(response.data.message || '命令执行失败')
        return false
      }
    } catch (error: any) {
      console.error('Command execution error:', error)
      toast.error(error.response?.data?.message || '命令执行失败')
      return false
    }
  }

  const getPerformanceData = async (): Promise<any> => {
    try {
      const response = await apiClient.get('/server/performance')
      if (response.data.success) {
        return response.data.data
      }
    } catch (error) {
      console.error('Failed to fetch performance data:', error)
    }
    return null
  }

  return {
    status: computed(() => status.value),
    metrics: computed(() => metrics.value),
    plugins: computed(() => plugins.value),
    worlds: computed(() => worlds.value),
    onlinePlayers: computed(() => onlinePlayers.value),
    loading: computed(() => loading.value),
    connecting: computed(() => connecting.value),
    isOnline,
    playerCount,
    maxPlayers,
    memoryUsage,
    cpuUsage,
    diskUsage,
    fetchServerStatus,
    startServer,
    stopServer,
    restartServer,
    killServer,
    fetchMetrics,
    fetchPlugins,
    enablePlugin,
    disablePlugin,
    reloadPlugin,
    fetchWorlds,
    fetchOnlinePlayers,
    sendCommand,
    getPerformanceData
  }
})