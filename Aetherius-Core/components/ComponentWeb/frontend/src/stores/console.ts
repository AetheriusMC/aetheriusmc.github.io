import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ApiClient, apiCall } from '@/utils/api'

export const useConsoleStore = defineStore('console', () => {
  // State
  const consoleStatus = ref<any>({
    server_status: {
      is_running: false,
      uptime: 0,
      version: 'Unknown',
      player_count: 0,
      max_players: 20,
      tps: 0.0,
      cpu_usage: 0.0,
      memory_usage: { used: 0, max: 0, percentage: 0.0 }
    },
    console_connections: 0,
    core_connected: false
  })
  
  const consoleHistory = ref<any[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdated = ref<Date | null>(null)

  // Auto refresh settings
  const autoRefresh = ref(true)
  const refreshInterval = ref(10000) // 10 seconds
  let refreshTimer: number | null = null

  // Computed
  const isServerRunning = computed(() => consoleStatus.value.server_status?.is_running ?? false)
  const serverUptime = computed(() => consoleStatus.value.server_status?.uptime ?? 0)
  const playerCount = computed(() => consoleStatus.value.server_status?.player_count ?? 0)
  const maxPlayers = computed(() => consoleStatus.value.server_status?.max_players ?? 20)
  const serverTPS = computed(() => consoleStatus.value.server_status?.tps ?? 0)
  const cpuUsage = computed(() => consoleStatus.value.server_status?.cpu_usage ?? 0)
  const memoryUsage = computed(() => consoleStatus.value.server_status?.memory_usage ?? { used: 0, max: 0, percentage: 0.0 })
  const coreConnected = computed(() => consoleStatus.value.core_connected ?? false)
  const consoleConnections = computed(() => consoleStatus.value.console_connections ?? 0)

  // Format uptime as human readable string
  const formattedUptime = computed(() => {
    const uptime = serverUptime.value
    const hours = Math.floor(uptime / 3600)
    const minutes = Math.floor((uptime % 3600) / 60)
    const seconds = uptime % 60
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${seconds}s`
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`
    } else {
      return `${seconds}s`
    }
  })

  // Actions
  async function fetchConsoleStatus() {
    loading.value = true
    error.value = null

    const { data, error: apiError } = await apiCall(
      () => ApiClient.getConsoleStatus(),
      'Failed to fetch console status'
    )

    if (data) {
      consoleStatus.value = data
      lastUpdated.value = new Date()
    } else if (apiError) {
      error.value = apiError.error
    }

    loading.value = false
  }

  async function fetchConsoleHistory(limit: number = 100) {
    const { data, error: apiError } = await apiCall(
      () => ApiClient.getConsoleHistory(limit),
      'Failed to fetch console history'
    )

    if (data) {
      consoleHistory.value = data.history || []
    } else if (apiError) {
      error.value = apiError.error
    }
  }

  async function executeCommand(command: string) {
    loading.value = true
    error.value = null

    const { data, error: apiError } = await apiCall(
      () => ApiClient.executeCommand(command),
      'Failed to execute command'
    )

    if (data) {
      // Refresh status after command execution
      await fetchConsoleStatus()
      return true
    } else if (apiError) {
      error.value = apiError.error
      return false
    }

    loading.value = false
    return false
  }

  function startAutoRefresh() {
    if (refreshTimer) {
      clearInterval(refreshTimer)
    }

    if (autoRefresh.value) {
      refreshTimer = window.setInterval(() => {
        fetchConsoleStatus()
      }, refreshInterval.value)
    }
  }

  function stopAutoRefresh() {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }

  function setAutoRefresh(enabled: boolean) {
    autoRefresh.value = enabled
    if (enabled) {
      startAutoRefresh()
    } else {
      stopAutoRefresh()
    }
  }

  function setRefreshInterval(interval: number) {
    refreshInterval.value = interval
    if (autoRefresh.value) {
      startAutoRefresh()
    }
  }

  function clearError() {
    error.value = null
  }

  // Initialize
  function initialize() {
    fetchConsoleStatus()
    fetchConsoleHistory()
    startAutoRefresh()
  }

  // Cleanup
  function cleanup() {
    stopAutoRefresh()
  }

  return {
    // State
    consoleStatus,
    consoleHistory,
    loading,
    error,
    lastUpdated,
    autoRefresh,
    refreshInterval,

    // Computed
    isServerRunning,
    serverUptime,
    formattedUptime,
    playerCount,
    maxPlayers,
    serverTPS,
    cpuUsage,
    memoryUsage,
    coreConnected,
    consoleConnections,

    // Actions
    fetchConsoleStatus,
    fetchConsoleHistory,
    executeCommand,
    startAutoRefresh,
    stopAutoRefresh,
    setAutoRefresh,
    setRefreshInterval,
    clearError,
    initialize,
    cleanup
  }
})