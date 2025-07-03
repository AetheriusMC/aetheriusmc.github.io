export interface User {
  id: string
  username: string
  email: string
  role: UserRole
  avatar?: string
  created_at: string
  last_login?: string
  is_active: boolean
}

export enum UserRole {
  ADMIN = 'admin',
  MODERATOR = 'moderator',
  USER = 'user'
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface ServerStatus {
  status: 'online' | 'offline' | 'starting' | 'stopping'
  players_online: number
  max_players: number
  version: string
  motd: string
  uptime: number
  memory_usage: MemoryUsage
  cpu_usage: number
  disk_usage: DiskUsage
}

export interface MemoryUsage {
  used: number
  allocated: number
  max: number
  percentage: number
}

export interface DiskUsage {
  used: number
  total: number
  percentage: number
}

export interface Player {
  uuid: string
  username: string
  display_name?: string
  online: boolean
  ip_address?: string
  location?: PlayerLocation
  gamemode?: string
  health: number
  food_level: number
  experience: number
  level: number
  first_join: string
  last_seen: string
  playtime: number
  banned: boolean
  ban_reason?: string
  banned_until?: string
}

export interface PlayerLocation {
  world: string
  x: number
  y: number
  z: number
  yaw: number
  pitch: number
}

export interface ConsoleMessage {
  id: string
  timestamp: string
  level: 'info' | 'warning' | 'error' | 'debug'
  message: string
  source?: string
}

export interface FileSystemItem {
  name: string
  path: string
  type: 'file' | 'directory'
  size?: number
  modified: string
  permissions?: string
  is_readable: boolean
  is_writable: boolean
}

export interface BackupInfo {
  id: string
  name: string
  path: string
  size: number
  created_at: string
  type: 'full' | 'incremental' | 'world' | 'plugins'
  status: 'completed' | 'in_progress' | 'failed'
  description?: string
}

export interface SystemMetrics {
  timestamp: string
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  network_rx: number
  network_tx: number
  active_connections: number
  tps: number
  mspt: number
}

export interface NotificationData {
  id: string
  title: string
  message: string
  type: 'system' | 'security' | 'player' | 'server' | 'maintenance' | 'alert' | 'info' | 'warning' | 'error'
  priority: 'low' | 'medium' | 'high' | 'critical'
  timestamp: string
  read: boolean
  sender?: string
  actions?: NotificationAction[]
}

export interface NotificationAction {
  label: string
  action: string
  style?: 'primary' | 'secondary' | 'danger'
}

export interface WebSocketMessage {
  type: string
  data: any
  timestamp?: string
  id?: string
}

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
  code?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
  has_next: boolean
  has_prev: boolean
}

export interface ChartDataPoint {
  x: string | number
  y: number
  label?: string
}

export interface ChartConfig {
  type: 'line' | 'bar' | 'doughnut' | 'pie'
  data: {
    labels: string[]
    datasets: ChartDataset[]
  }
  options?: any
}

export interface ChartDataset {
  label: string
  data: number[]
  backgroundColor?: string | string[]
  borderColor?: string
  borderWidth?: number
  fill?: boolean
  tension?: number
}

export interface Plugin {
  name: string
  version: string
  description?: string
  author?: string
  enabled: boolean
  dependencies?: string[]
  soft_dependencies?: string[]
  load_before?: string[]
  api_version?: string
  website?: string
}

export interface WorldInfo {
  name: string
  environment: 'normal' | 'nether' | 'end'
  seed: number
  spawn_location: PlayerLocation
  time: number
  weather: 'clear' | 'rain' | 'storm'
  difficulty: 'peaceful' | 'easy' | 'normal' | 'hard'
  players: number
  entities: number
  chunks_loaded: number
  size: number
}

export interface ServerConfig {
  [key: string]: any
}

export interface CommandHistory {
  id: string
  command: string
  timestamp: string
  user: string
  success: boolean
  output?: string
}