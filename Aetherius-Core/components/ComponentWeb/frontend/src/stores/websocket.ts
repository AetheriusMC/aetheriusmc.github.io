import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { AutoReconnectWebSocket, createWebSocketUrl } from '@/utils/websocket'
import type { WSMessage, WSConnectionStatus, ConsoleMessage } from '@/types'

export const useWebSocketStore = defineStore('websocket', () => {
  // State
  const consoleWs = ref<AutoReconnectWebSocket | null>(null)
  const statusWs = ref<AutoReconnectWebSocket | null>(null)
  const dashboardWs = ref<AutoReconnectWebSocket | null>(null)
  
  const consoleStatus = ref<WSConnectionStatus>({
    connected: false,
    reconnecting: false
  })
  
  const statusConnectionStatus = ref<WSConnectionStatus>({
    connected: false,
    reconnecting: false
  })
  
  const dashboardStatus = ref<WSConnectionStatus>({
    connected: false,
    reconnecting: false
  })
  
  const consoleMessages = ref<ConsoleMessage[]>([])
  const maxConsoleMessages = 1000
  
  // Message handlers
  const messageHandlers = ref<Array<(message: WSMessage) => void>>([])
  
  // Dashboard connection flag
  const isDashboardMode = ref(false)

  // Computed
  const isConsoleConnected = computed(() => consoleStatus.value.connected)
  const isStatusConnected = computed(() => statusConnectionStatus.value.connected)
  const isDashboardConnected = computed(() => dashboardStatus.value.connected)
  const isAnyConnected = computed(() => isConsoleConnected.value || isStatusConnected.value || isDashboardConnected.value)

  // Actions
  function initConsoleWebSocket() {
    if (consoleWs.value) {
      return
    }

    const wsUrl = createWebSocketUrl('/console/ws')
    consoleWs.value = new AutoReconnectWebSocket(wsUrl)

    // Handle connection status changes
    consoleWs.value.onConnectionChange((status) => {
      consoleStatus.value = status
      console.log('Console WebSocket status:', status)
    })

    // Handle incoming messages
    consoleWs.value.onMessage((message: WSMessage) => {
      handleConsoleMessage(message)
    })

    // Connect
    consoleWs.value.connect().catch((error) => {
      console.error('Failed to connect console WebSocket:', error)
    })
  }

  function initStatusWebSocket() {
    if (statusWs.value) {
      return
    }

    const wsUrl = createWebSocketUrl('/dashboard/ws')
    statusWs.value = new AutoReconnectWebSocket(wsUrl)

    // Handle connection status changes
    statusWs.value.onConnectionChange((status) => {
      statusConnectionStatus.value = status
      console.log('Status WebSocket status:', status)
    })

    // Handle incoming messages
    statusWs.value.onMessage((message: WSMessage) => {
      handleStatusMessage(message)
    })

    // Connect
    statusWs.value.connect().catch((error) => {
      console.error('Failed to connect status WebSocket:', error)
    })
  }

  function handleConsoleMessage(message: WSMessage) {
    console.log('Console message received:', message)

    switch (message.type) {
      case 'console_log':
        addConsoleMessage({
          type: message.type,
          timestamp: message.timestamp,
          data: message.data
        })
        break

      case 'console_command_result':
        // Handle command execution results
        const { command, success, output } = message.data
        addConsoleMessage({
          type: 'console_log',
          timestamp: message.timestamp,
          data: {
            level: success ? 'INFO' : 'ERROR',
            source: 'Server',
            message: output || (success ? '命令执行成功' : '命令执行失败')
          }
        })
        console.log(`命令执行结果: ${command} -> ${success ? '成功' : '失败'}: ${output}`)
        break

      case 'server_log':
        // Handle real-time server log streaming
        addConsoleMessage({
          type: 'console_log',
          timestamp: message.timestamp,
          data: {
            level: message.data.level || 'INFO',
            source: 'Server',
            message: message.data.message
          }
        })
        break

      case 'connection_established':
        console.log('Console connection established:', message.data)
        break

      case 'pong':
        // Handle ping/pong
        break

      default:
        console.warn('Unknown console message type:', message.type)
    }
  }

  function handleStatusMessage(message: WSMessage) {
    console.log('Status message received:', message)

    switch (message.type) {
      case 'status_update':
        // Handle server status updates
        break

      case 'player_event':
        // Handle player events
        break

      default:
        console.warn('Unknown status message type:', message.type)
    }
  }

  function addConsoleMessage(message: ConsoleMessage) {
    consoleMessages.value.push(message)

    // Limit the number of stored messages
    if (consoleMessages.value.length > maxConsoleMessages) {
      consoleMessages.value.splice(0, consoleMessages.value.length - maxConsoleMessages)
    }
  }

  function sendConsoleCommand(command: string) {
    if (!consoleWs.value || !isConsoleConnected.value) {
      console.warn('Console WebSocket is not connected')
      return false
    }

    try {
      consoleWs.value.sendCommand(command)
      return true
    } catch (error) {
      console.error('Failed to send console command:', error)
      return false
    }
  }

  function clearConsoleMessages() {
    consoleMessages.value = []
  }

  function connectAll() {
    initConsoleWebSocket()
    initStatusWebSocket()
  }

  function disconnectAll() {
    if (consoleWs.value) {
      consoleWs.value.disconnect()
      consoleWs.value = null
    }

    if (statusWs.value) {
      statusWs.value.disconnect()
      statusWs.value = null
    }

    // Reset status
    consoleStatus.value = { connected: false, reconnecting: false }
    statusConnectionStatus.value = { connected: false, reconnecting: false }
  }

  function reconnectConsole() {
    if (consoleWs.value) {
      consoleWs.value.disconnect()
      consoleWs.value = null
    }
    initConsoleWebSocket()
  }

  function reconnectStatus() {
    if (statusWs.value) {
      statusWs.value.disconnect()
      statusWs.value = null
    }
    initStatusWebSocket()
  }

  function initDashboardWebSocket() {
    if (dashboardWs.value) {
      return
    }

    try {
      const wsUrl = createWebSocketUrl('/dashboard/ws')
      dashboardWs.value = new AutoReconnectWebSocket(wsUrl)

      // Handle connection status changes
      dashboardWs.value.onConnectionChange((status) => {
        dashboardStatus.value = status
        console.log('Dashboard WebSocket status:', status)
      })

      // Handle incoming messages
      dashboardWs.value.onMessage((message: WSMessage) => {
        handleDashboardMessage(message)
      })

      // Connect
      dashboardWs.value.connect().catch((error) => {
        console.error('Failed to connect dashboard WebSocket:', error)
      })
    } catch (error) {
      console.error('Error initializing dashboard WebSocket:', error)
    }
  }

  function handleDashboardMessage(message: WSMessage) {
    console.log('Dashboard message received:', message)

    // Call all registered message handlers
    messageHandlers.value.forEach(handler => {
      try {
        handler(message)
      } catch (error) {
        console.error('Error in message handler:', error)
      }
    })

    switch (message.type) {
      case 'dashboard_summary':
      case 'performance_update':
      case 'server_control_result':
        // These are handled by components via message handlers
        break

      case 'connection_established':
        console.log('Dashboard connection established:', message.data)
        break

      default:
        console.warn('Unknown dashboard message type:', message.type)
    }
  }

  function connectDashboard() {
    isDashboardMode.value = true
    initDashboardWebSocket()
  }

  function disconnectDashboard() {
    if (dashboardWs.value) {
      dashboardWs.value.disconnect()
      dashboardWs.value = null
    }
    dashboardStatus.value = { connected: false, reconnecting: false }
    isDashboardMode.value = false
  }

  function onMessage(handler: (message: WSMessage) => void) {
    messageHandlers.value.push(handler)
  }

  function offMessage(handler: (message: WSMessage) => void) {
    const index = messageHandlers.value.indexOf(handler)
    if (index > -1) {
      messageHandlers.value.splice(index, 1)
    }
  }

  function disconnect() {
    disconnectAll()
    disconnectDashboard()
  }

  // Auto-connect on store creation (console only by default)
  if (!isDashboardMode.value) {
    connectAll()
  }

  return {
    // State
    consoleStatus,
    statusConnectionStatus,
    dashboardStatus,
    consoleMessages,
    isDashboardMode,

    // Computed
    isConsoleConnected,
    isStatusConnected,
    isDashboardConnected,
    isAnyConnected,

    // Actions
    initConsoleWebSocket,
    initStatusWebSocket,
    initDashboardWebSocket,
    sendConsoleCommand,
    clearConsoleMessages,
    connectAll,
    disconnectAll,
    connectDashboard,
    disconnectDashboard,
    reconnectConsole,
    reconnectStatus,
    addConsoleMessage,
    onMessage,
    offMessage,
    disconnect
  }
})