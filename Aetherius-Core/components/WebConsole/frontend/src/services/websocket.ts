import { io, Socket } from 'socket.io-client'
import type { WebSocketMessage, ConsoleMessage, SystemMetrics, NotificationData } from '@/types'
import { useAuthStore } from '@/stores/auth'
import mitt, { Emitter } from 'mitt'

type WebSocketEvents = {
  connect: void
  disconnect: void
  reconnect: void
  error: Error
  console_message: ConsoleMessage
  system_metrics: SystemMetrics
  notification: NotificationData
  server_status: any
  player_join: any
  player_leave: any
}

export class WebSocketService {
  private sockets: Map<string, Socket> = new Map()
  private eventBus: Emitter<WebSocketEvents>
  private authStore: any

  constructor() {
    this.eventBus = mitt<WebSocketEvents>()
  }

  private getAuthToken(): string | null {
    if (!this.authStore) {
      this.authStore = useAuthStore()
    }
    return this.authStore.tokens?.access_token || null
  }

  connect(endpoint: string): Socket {
    if (this.sockets.has(endpoint)) {
      return this.sockets.get(endpoint)!
    }

    const token = this.getAuthToken()
    if (!token) {
      throw new Error('Authentication token required for WebSocket connection')
    }

    const socket = io(`/api/v1/ws/${endpoint}`, {
      auth: {
        token
      },
      transports: ['websocket'],
      upgrade: true,
      rememberUpgrade: true,
      timeout: 20000,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      maxReconnectionAttempts: 5,
      randomizationFactor: 0.5
    })

    this.setupSocketEvents(socket, endpoint)
    this.sockets.set(endpoint, socket)

    return socket
  }

  private setupSocketEvents(socket: Socket, endpoint: string): void {
    socket.on('connect', () => {
      console.log(`WebSocket connected: ${endpoint}`)
      this.eventBus.emit('connect')
    })

    socket.on('disconnect', (reason) => {
      console.log(`WebSocket disconnected: ${endpoint}, reason: ${reason}`)
      this.eventBus.emit('disconnect')
    })

    socket.on('reconnect', (attemptNumber) => {
      console.log(`WebSocket reconnected: ${endpoint}, attempt: ${attemptNumber}`)
      this.eventBus.emit('reconnect')
    })

    socket.on('connect_error', (error) => {
      console.error(`WebSocket connection error: ${endpoint}`, error)
      this.eventBus.emit('error', error)
    })

    // Handle specific message types
    socket.on('console_message', (data: ConsoleMessage) => {
      this.eventBus.emit('console_message', data)
    })

    socket.on('system_metrics', (data: SystemMetrics) => {
      this.eventBus.emit('system_metrics', data)
    })

    socket.on('notification', (data: NotificationData) => {
      this.eventBus.emit('notification', data)
    })

    socket.on('server_status', (data: any) => {
      this.eventBus.emit('server_status', data)
    })

    socket.on('player_join', (data: any) => {
      this.eventBus.emit('player_join', data)
    })

    socket.on('player_leave', (data: any) => {
      this.eventBus.emit('player_leave', data)
    })

    // Generic message handler
    socket.onAny((event: string, data: any) => {
      console.log(`WebSocket event: ${endpoint}/${event}`, data)
    })
  }

  disconnect(endpoint: string): void {
    const socket = this.sockets.get(endpoint)
    if (socket) {
      socket.disconnect()
      this.sockets.delete(endpoint)
      console.log(`WebSocket disconnected: ${endpoint}`)
    }
  }

  disconnectAll(): void {
    this.sockets.forEach((socket, endpoint) => {
      socket.disconnect()
      console.log(`WebSocket disconnected: ${endpoint}`)
    })
    this.sockets.clear()
  }

  send(endpoint: string, event: string, data: any): void {
    const socket = this.sockets.get(endpoint)
    if (socket && socket.connected) {
      socket.emit(event, data)
    } else {
      console.warn(`WebSocket not connected: ${endpoint}`)
    }
  }

  // Console WebSocket methods
  connectConsole(): Socket {
    return this.connect('console')
  }

  sendCommand(command: string): void {
    this.send('console', 'execute_command', { command })
  }

  subscribeToLogs(logTypes: string[] = []): void {
    this.send('console', 'subscribe_logs', { log_types: logTypes })
  }

  unsubscribeFromLogs(): void {
    this.send('console', 'unsubscribe_logs', {})
  }

  // Monitoring WebSocket methods
  connectMonitoring(): Socket {
    return this.connect('monitoring')
  }

  subscribeToMetrics(metrics: string[] = [], interval: number = 5): void {
    this.send('monitoring', 'subscribe_metrics', { 
      metrics, 
      interval 
    })
  }

  unsubscribeFromMetrics(): void {
    this.send('monitoring', 'unsubscribe_metrics', {})
  }

  // Notifications WebSocket methods
  connectNotifications(): Socket {
    return this.connect('notifications')
  }

  subscribeToNotifications(types: string[] = []): void {
    this.send('notifications', 'subscribe', { 
      notification_types: types 
    })
  }

  markNotificationsRead(notificationIds: string[]): void {
    this.send('notifications', 'mark_read', { 
      notification_ids: notificationIds 
    })
  }

  sendNotification(title: string, message: string, type: string = 'info', priority: string = 'medium'): void {
    this.send('notifications', 'send_notification', {
      title,
      message,
      notification_type: type,
      priority
    })
  }

  // Event subscription methods
  on<K extends keyof WebSocketEvents>(event: K, handler: (data: WebSocketEvents[K]) => void): void {
    this.eventBus.on(event, handler)
  }

  off<K extends keyof WebSocketEvents>(event: K, handler: (data: WebSocketEvents[K]) => void): void {
    this.eventBus.off(event, handler)
  }

  once<K extends keyof WebSocketEvents>(event: K, handler: (data: WebSocketEvents[K]) => void): void {
    const wrappedHandler = (data: WebSocketEvents[K]) => {
      handler(data)
      this.eventBus.off(event, wrappedHandler)
    }
    this.eventBus.on(event, wrappedHandler)
  }

  // Utility methods
  isConnected(endpoint: string): boolean {
    const socket = this.sockets.get(endpoint)
    return socket ? socket.connected : false
  }

  getConnectionState(endpoint: string): string {
    const socket = this.sockets.get(endpoint)
    if (!socket) return 'disconnected'
    return socket.connected ? 'connected' : 'disconnected'
  }

  getAllConnections(): Array<{ endpoint: string; connected: boolean }> {
    return Array.from(this.sockets.entries()).map(([endpoint, socket]) => ({
      endpoint,
      connected: socket.connected
    }))
  }
}

// Create and export singleton instance
export const websocketService = new WebSocketService()

// Export default for convenience
export default websocketService