import axios from 'axios'
import type { AxiosInstance, AxiosResponse } from 'axios'
import type { 
  ServerStatus, 
  Player, 
  CommandResponse, 
  DashboardOverview,
  ApiError 
} from '@/types'

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add request ID for tracking
    config.headers['X-Request-ID'] = Date.now().toString()
    console.log('API Request:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log('API Response:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.response?.data)
    
    // Handle common error cases
    if (error.response?.status === 503) {
      console.warn('Aetherius Core is not available')
    }
    
    return Promise.reject(error)
  }
)

// API functions
export class ApiClient {
  // Health check
  static async healthCheck(): Promise<any> {
    const response = await apiClient.get('/health')
    return response.data
  }

  // Dashboard APIs
  static async getDashboardOverview(): Promise<DashboardOverview> {
    const response = await apiClient.get('/dashboard/overview')
    return response.data
  }

  static async getServerStatus(): Promise<ServerStatus> {
    const response = await apiClient.get('/server/status')
    return response.data
  }

  static async getOnlinePlayers(): Promise<Player[]> {
    const response = await apiClient.get('/players')
    return response.data
  }

  static async getServerMetrics(hours: number = 1): Promise<any> {
    const response = await apiClient.get(`/server/metrics?hours=${hours}`)
    return response.data
  }

  static async getCurrentPerformance(): Promise<any> {
    const response = await apiClient.get('/server/performance')
    return response.data
  }

  static async getServerSummary(): Promise<any> {
    const response = await apiClient.get('/server/summary')
    return response.data
  }

  // Server control APIs
  static async startServer(): Promise<any> {
    const response = await apiClient.post('/server/start')
    return response.data
  }

  static async stopServer(): Promise<any> {
    const response = await apiClient.post('/server/stop')
    return response.data
  }

  static async restartServer(): Promise<any> {
    const response = await apiClient.post('/server/restart')
    return response.data
  }

  // Console APIs
  static async getConsoleStatus(): Promise<any> {
    const response = await apiClient.get('/console/status')
    return response.data
  }

  static async executeCommand(command: string): Promise<CommandResponse> {
    const response = await apiClient.post('/console/command', { command })
    return response.data
  }

  static async getConsoleHistory(limit: number = 100): Promise<any> {
    const response = await apiClient.get(`/console/history?limit=${limit}`)
    return response.data
  }

  // Player management APIs
  static async kickPlayer(uuid: string, reason?: string): Promise<any> {
    const response = await apiClient.post(`/players/${uuid}/action`, {
      action: 'kick',
      reason: reason || 'Kicked by admin'
    })
    return response.data
  }

  static async banPlayer(uuid: string, reason?: string): Promise<any> {
    const response = await apiClient.post(`/players/${uuid}/action`, {
      action: 'ban',
      reason: reason || 'Banned by admin'
    })
    return response.data
  }

  static async opPlayer(uuid: string): Promise<any> {
    const response = await apiClient.post(`/players/${uuid}/action`, {
      action: 'op'
    })
    return response.data
  }

  static async deopPlayer(uuid: string): Promise<any> {
    const response = await apiClient.post(`/players/${uuid}/action`, {
      action: 'deop'
    })
    return response.data
  }

  // Enhanced Player Management APIs
  static async searchPlayers(params: {
    page?: number
    per_page?: number
    query?: string
    online_only?: boolean
    game_mode?: string
    min_level?: number | null
    max_level?: number | null
    sort_by?: string
    sort_order?: string
  }): Promise<any> {
    const searchParams = new URLSearchParams()
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value))
      }
    })
    
    const response = await apiClient.get(`/players?${searchParams.toString()}`)
    return response.data
  }

  static async getPlayerDetails(playerIdentifier: string): Promise<any> {
    const response = await apiClient.get(`/players/${playerIdentifier}`)
    return response.data
  }

  static async executePlayerAction(playerIdentifier: string, actionData: {
    action: string
    reason?: string
    duration?: number
  }): Promise<any> {
    const response = await apiClient.post(`/players/${playerIdentifier}/action`, actionData)
    return response.data
  }

  static async executeBatchPlayerAction(actionData: {
    player_uuids: string[]
    action: string
    reason?: string
    duration?: number
  }): Promise<any> {
    const response = await apiClient.post('/players/batch-action', actionData)
    return response.data
  }

  static async getPlayerOperationsHistory(params: {
    page?: number
    per_page?: number
    player_identifier?: string
    action?: string
    operator?: string
  } = {}): Promise<any> {
    const searchParams = new URLSearchParams()
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value))
      }
    })
    
    const response = await apiClient.get(`/players/operations/history?${searchParams.toString()}`)
    return response.data
  }

  // File Management APIs
  static async listFiles(params: {
    path?: string
    show_hidden?: boolean
    recursive?: boolean
  } = {}): Promise<any> {
    const searchParams = new URLSearchParams()
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value))
      }
    })
    
    const response = await apiClient.get(`/files/list?${searchParams.toString()}`)
    return response.data
  }

  static async getFileContent(path: string, encoding: string = 'utf-8'): Promise<any> {
    const response = await apiClient.get(`/files/content?path=${encodeURIComponent(path)}&encoding=${encoding}`)
    return response.data
  }

  static async saveFileContent(path: string, content: string, encoding: string = 'utf-8', backup: boolean = true): Promise<any> {
    const response = await apiClient.post('/files/save', {
      path,
      content,
      encoding,
      backup
    })
    return response.data
  }

  static async uploadFile(file: File, destinationPath: string, overwrite: boolean = false): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('destination_path', destinationPath)
    formData.append('overwrite', String(overwrite))

    const response = await apiClient.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  }

  static async downloadFile(path: string): Promise<Blob> {
    const response = await apiClient.get(`/files/download?path=${encodeURIComponent(path)}`, {
      responseType: 'blob'
    })
    return response.data
  }

  static async fileOperation(operation: string, sourcePath: string, destinationPath?: string): Promise<any> {
    const response = await apiClient.post('/files/operation', {
      operation,
      source_path: sourcePath,
      destination_path: destinationPath
    })
    return response.data
  }

  static async searchFiles(params: {
    path?: string
    query: string
    file_types?: string[]
    max_results?: number
  }): Promise<any> {
    const response = await apiClient.post('/files/search', params)
    return response.data
  }

  static async getFileInfo(path: string): Promise<any> {
    const response = await apiClient.get(`/files/info?path=${encodeURIComponent(path)}`)
    return response.data
  }
}

// Error handling utility
export function handleApiError(error: any): ApiError {
  if (error.response?.data) {
    return error.response.data as ApiError
  }
  
  return {
    error: 'Network Error',
    details: { message: error.message },
    status_code: error.response?.status || 0,
    timestamp: new Date().toISOString()
  }
}

// Utility function for API calls with error handling
export async function apiCall<T>(
  apiFunction: () => Promise<T>,
  errorMessage: string = 'API call failed'
): Promise<{ data: T | null; error: ApiError | null }> {
  try {
    const data = await apiFunction()
    return { data, error: null }
  } catch (error) {
    console.error(errorMessage, error)
    return { data: null, error: handleApiError(error) }
  }
}

export default apiClient