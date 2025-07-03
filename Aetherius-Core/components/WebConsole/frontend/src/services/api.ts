import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import type { ApiResponse } from '@/types'

class ApiClient {
  private instance: AxiosInstance

  constructor(baseURL: string = '/api/v1') {
    this.instance = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.instance.interceptors.request.use(
      (config) => {
        // Add timestamp to prevent caching
        if (config.method === 'get') {
          config.params = {
            ...config.params,
            _t: Date.now(),
          }
        }

        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor
    this.instance.interceptors.response.use(
      (response: AxiosResponse) => {
        return response
      },
      (error) => {
        // Handle network errors
        if (!error.response) {
          console.error('Network Error:', error.message)
          return Promise.reject({
            response: {
              data: {
                success: false,
                message: '网络连接错误',
                error: 'NETWORK_ERROR'
              }
            }
          })
        }

        // Handle HTTP errors
        const { status, data } = error.response
        
        switch (status) {
          case 401:
            console.error('Authentication Error:', data.message)
            break
          case 403:
            console.error('Authorization Error:', data.message)
            break
          case 404:
            console.error('Not Found Error:', data.message)
            break
          case 500:
            console.error('Server Error:', data.message)
            break
          default:
            console.error('API Error:', data.message)
        }

        return Promise.reject(error)
      }
    )
  }

  // HTTP Methods
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return this.instance.get(url, config)
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return this.instance.post(url, data, config)
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return this.instance.put(url, data, config)
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return this.instance.patch(url, data, config)
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return this.instance.delete(url, config)
  }

  // Upload file
  async upload<T = any>(url: string, formData: FormData, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return this.instance.post(url, formData, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...config?.headers,
      },
    })
  }

  // Download file
  async download(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<Blob>> {
    return this.instance.get(url, {
      ...config,
      responseType: 'blob',
    })
  }

  // Get axios instance for advanced usage
  get axios(): AxiosInstance {
    return this.instance
  }

  // Update default headers
  setDefaultHeaders(headers: Record<string, string>): void {
    Object.assign(this.instance.defaults.headers.common, headers)
  }

  // Remove default header
  removeDefaultHeader(headerName: string): void {
    delete this.instance.defaults.headers.common[headerName]
  }

  // Update base URL
  setBaseURL(baseURL: string): void {
    this.instance.defaults.baseURL = baseURL
  }

  // Update timeout
  setTimeout(timeout: number): void {
    this.instance.defaults.timeout = timeout
  }
}

// Create and export the API client instance
export const apiClient = new ApiClient()

// Export default instance for convenience
export default apiClient

// Utility functions
export const createFormData = (data: Record<string, any>): FormData => {
  const formData = new FormData()
  
  Object.entries(data).forEach(([key, value]) => {
    if (value instanceof File || value instanceof Blob) {
      formData.append(key, value)
    } else if (Array.isArray(value)) {
      value.forEach((item, index) => {
        formData.append(`${key}[${index}]`, item)
      })
    } else if (value !== null && value !== undefined) {
      formData.append(key, String(value))
    }
  })
  
  return formData
}

export const buildQueryString = (params: Record<string, any>): string => {
  const searchParams = new URLSearchParams()
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined) {
      if (Array.isArray(value)) {
        value.forEach(item => searchParams.append(key, String(item)))
      } else {
        searchParams.append(key, String(value))
      }
    }
  })
  
  return searchParams.toString()
}