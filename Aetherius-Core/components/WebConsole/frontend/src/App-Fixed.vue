<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <!-- 登录页面 -->
    <div v-if="currentPage === 'login'" style="padding: 20px;">
      <div style="max-width: 400px; margin: 0 auto; margin-top: 100px; padding: 30px; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <h1 style="font-size: 28px; margin-bottom: 30px; text-align: center; color: #333;">Aetherius WebConsole</h1>
        
        <form @submit.prevent="handleLogin">
          <div style="margin-bottom: 20px;">
            <label style="display: block; margin-bottom: 5px; font-weight: 500;">用户名</label>
            <input 
              v-model="form.username"
              type="text" 
              style="width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
              placeholder="请输入用户名"
              required
            >
          </div>
          
          <div style="margin-bottom: 25px;">
            <label style="display: block; margin-bottom: 5px; font-weight: 500;">密码</label>
            <input 
              v-model="form.password"
              type="password" 
              style="width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
              placeholder="请输入密码"
              required
            >
          </div>
          
          <button 
            type="submit"
            style="width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: 500;"
            :disabled="loading || !form.username || !form.password"
          >
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </form>
        
        <div style="margin-top: 15px; text-align: center; font-size: 12px; color: #666;">
          连接状态: <span :style="connectionStatusStyle">{{ connectionStatusText }}</span>
        </div>
      </div>
    </div>

    <!-- 主应用界面 -->
    <div v-else>
      <!-- 顶部导航栏 -->
      <div style="background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <div style="max-width: 1200px; margin: 0 auto; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center;">
          <h1 style="font-size: 24px; margin: 0; color: #333;">Aetherius WebConsole</h1>
          <button 
            @click="handleLogout"
            style="padding: 8px 16px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;"
          >
            退出登录
          </button>
        </div>
      </div>

      <div style="display: flex; min-height: calc(100vh - 70px);">
        <!-- 侧边导航菜单 -->
        <div style="width: 250px; background: #f8f9fa; border-right: 1px solid #dee2e6; padding: 20px 0;">
          <nav>
            <div 
              v-for="item in menuItems" 
              :key="item.id"
              @click="currentPage = item.id"
              :style="getMenuItemStyle(item.id)"
              style="padding: 12px 20px; cursor: pointer; display: flex; align-items: center; margin-bottom: 2px; transition: all 0.2s;"
            >
              <span style="margin-right: 10px;">{{ item.icon }}</span>
              <span>{{ item.name }}</span>
            </div>
          </nav>
        </div>

        <!-- 主内容区域 -->
        <div style="flex: 1; padding: 30px;">
          <!-- 仪表板页面 -->
          <div v-if="currentPage === 'dashboard'">
            <div style="text-align: center; margin-bottom: 40px;">
              <h2 style="font-size: 28px; margin-bottom: 10px; color: #333;">欢迎使用 Aetherius WebConsole</h2>
              <p style="color: #666; font-size: 16px;">企业级Minecraft服务器管理平台</p>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 40px;">
              <div style="background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h3 style="font-size: 18px; margin-bottom: 10px; color: #333;">服务器状态</h3>
                <p :style="getServerStatusStyle()" style="font-size: 24px; font-weight: bold; margin: 0;">{{ getServerStatusText() }}</p>
              </div>
              
              <div style="background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h3 style="font-size: 18px; margin-bottom: 10px; color: #333;">在线玩家</h3>
                <p style="font-size: 24px; font-weight: bold; color: #007bff; margin: 0;">{{ systemStats.players_online }} / {{ systemStats.max_players }}</p>
              </div>
              
              <div style="background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h3 style="font-size: 18px; margin-bottom: 10px; color: #333;">TPS</h3>
                <p :style="getTpsStyle()" style="font-size: 24px; font-weight: bold; margin: 0;">{{ systemStats.tps.toFixed(1) }}</p>
              </div>
              
              <div style="background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h3 style="font-size: 18px; margin-bottom: 10px; color: #333;">CPU 使用率</h3>
                <p style="font-size: 24px; font-weight: bold; color: #6f42c1; margin: 0;">{{ systemStats.cpu }}%</p>
              </div>
            </div>

            <div style="text-align: center;">
              <h3 style="font-size: 20px; margin-bottom: 20px; color: #333;">快速操作</h3>
              <div style="display: flex; justify-content: center; gap: 15px; flex-wrap: wrap;">
                <button @click="currentPage = 'console'" style="padding: 12px 24px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
                  查看控制台
                </button>
                <button @click="currentPage = 'plugins'" style="padding: 12px 24px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
                  管理插件
                </button>
                <button @click="currentPage = 'monitoring'" style="padding: 12px 24px; background: #ffc107; color: #212529; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
                  查看监控
                </button>
              </div>
            </div>
          </div>

          <!-- 控制台页面 -->
          <div v-else-if="currentPage === 'console'">
            <h2 style="font-size: 24px; margin-bottom: 20px; color: #333;">服务器控制台</h2>
            <div style="background: #1a1a1a; color: #00ff00; padding: 20px; border-radius: 8px; font-family: 'Courier New', monospace; height: 400px; overflow-y: auto;">
              <div v-for="(log, index) in consoleLogs" :key="index" style="margin-bottom: 5px;">
                [{{ log.time }}] {{ log.message }}
              </div>
            </div>
            <div style="margin-top: 15px; display: flex; gap: 10px;">
              <input 
                v-model="consoleCommand"
                @keyup.enter="sendCommand"
                type="text" 
                placeholder="输入服务器命令..."
                style="flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px;"
              >
              <button 
                @click="sendCommand"
                style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;"
              >
                发送
              </button>
            </div>
          </div>

          <!-- 监控页面 -->
          <div v-else-if="currentPage === 'monitoring'">
            <h2 style="font-size: 24px; margin-bottom: 20px; color: #333;">系统监控</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
              <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center;">
                <h3 style="margin-bottom: 15px; color: #333;">CPU 使用率</h3>
                <div style="font-size: 36px; font-weight: bold; color: #007bff;">{{ systemStats.cpu }}%</div>
              </div>
              <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center;">
                <h3 style="margin-bottom: 15px; color: #333;">内存使用</h3>
                <div style="font-size: 36px; font-weight: bold; color: #28a745;">{{ systemStats.memory }}%</div>
              </div>
              <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center;">
                <h3 style="margin-bottom: 15px; color: #333;">磁盘使用</h3>
                <div style="font-size: 36px; font-weight: bold; color: #ffc107;">{{ systemStats.disk }}%</div>
              </div>
              <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center;">
                <h3 style="margin-bottom: 15px; color: #333;">网络流量</h3>
                <div style="font-size: 20px; font-weight: bold; color: #6f42c1;">{{ systemStats.network }}</div>
              </div>
            </div>
          </div>

          <!-- 玩家管理页面 -->
          <div v-else-if="currentPage === 'players'">
            <h2 style="font-size: 24px; margin-bottom: 20px; color: #333;">玩家管理</h2>
            <div style="background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden;">
              <div style="padding: 20px; border-bottom: 1px solid #eee;">
                <h3 style="margin: 0; color: #333;">在线玩家 ({{ onlinePlayers.length }})</h3>
              </div>
              <div v-if="onlinePlayers.length === 0" style="padding: 40px; text-align: center; color: #666;">
                当前没有在线玩家
              </div>
              <div v-else>
                <div v-for="player in onlinePlayers" :key="player.name" style="padding: 15px 20px; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center;">
                  <div>
                    <div style="font-weight: 500; margin-bottom: 5px;">{{ player.name }}</div>
                    <div style="font-size: 12px; color: #666;">{{ player.joinTime }}</div>
                  </div>
                  <div style="display: flex; gap: 10px;">
                    <button style="padding: 5px 10px; background: #ffc107; color: #212529; border: none; border-radius: 3px; cursor: pointer; font-size: 12px;">
                      踢出
                    </button>
                    <button style="padding: 5px 10px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 12px;">
                      封禁
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 插件管理页面 -->
          <div v-else-if="currentPage === 'plugins'">
            <h2 style="font-size: 24px; margin-bottom: 20px; color: #333;">插件管理</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px;">
              <div v-for="plugin in plugins" :key="plugin.name" style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
                  <div>
                    <h3 style="margin: 0 0 5px 0; color: #333;">{{ plugin.name }}</h3>
                    <div style="font-size: 12px; color: #666;">版本 {{ plugin.version }}</div>
                  </div>
                  <span :style="plugin.enabled ? 'color: #28a745; font-weight: bold;' : 'color: #dc3545; font-weight: bold;'">
                    {{ plugin.enabled ? '已启用' : '已禁用' }}
                  </span>
                </div>
                <p style="color: #666; font-size: 14px; margin-bottom: 15px;">{{ plugin.description }}</p>
                <button 
                  :style="plugin.enabled ? 'background: #dc3545;' : 'background: #28a745;'"
                  style="color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; width: 100%;"
                  @click="togglePlugin(plugin)"
                >
                  {{ plugin.enabled ? '禁用' : '启用' }}
                </button>
              </div>
            </div>
          </div>

          <!-- 组件管理页面 -->
          <div v-else-if="currentPage === 'components'">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
              <h2 style="font-size: 24px; margin: 0; color: #333;">Aetherius 组件管理</h2>
              <button 
                @click="loadComponents"
                style="padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;"
              >
                🔄 刷新
              </button>
            </div>
            
            <div style="margin-bottom: 30px; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
              <h3 style="margin: 0 0 15px 0; color: #333;">组件概览</h3>
              <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                <div style="text-align: center;">
                  <div style="font-size: 28px; font-weight: bold; color: #007bff; margin-bottom: 5px;">{{ components.length }}</div>
                  <div style="color: #666;">总组件数</div>
                </div>
                <div style="text-align: center;">
                  <div style="font-size: 28px; font-weight: bold; color: #28a745; margin-bottom: 5px;">{{ components.filter(c => c.enabled).length }}</div>
                  <div style="color: #666;">已启用</div>
                </div>
                <div style="text-align: center;">
                  <div style="font-size: 28px; font-weight: bold; color: #dc3545; margin-bottom: 5px;">{{ components.filter(c => !c.enabled).length }}</div>
                  <div style="color: #666;">已禁用</div>
                </div>
                <div style="text-align: center;">
                  <div style="font-size: 28px; font-weight: bold; color: #ffc107; margin-bottom: 5px;">{{ components.filter(c => c.status === 'running').length }}</div>
                  <div style="color: #666;">运行中</div>
                </div>
              </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 20px;">
              <div v-for="component in components" :key="component.name" style="background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 4px solid;" :style="{ borderLeftColor: getComponentBorderColor(component) }">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
                  <div style="flex: 1;">
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                      <h3 style="margin: 0; color: #333; margin-right: 10px;">{{ component.name }}</h3>
                      <span style="padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;" :style="getComponentStatusStyle(component.status)">
                        {{ getComponentStatusText(component.status) }}
                      </span>
                    </div>
                    <div style="font-size: 12px; color: #666; margin-bottom: 5px;">版本 {{ component.version || 'Unknown' }}</div>
                    <div style="font-size: 12px; color: #666;">类型: {{ component.type || 'Component' }}</div>
                  </div>
                  <div style="display: flex; align-items: center;">
                    <span :style="component.enabled ? 'color: #28a745; font-weight: bold;' : 'color: #dc3545; font-weight: bold;'" style="font-size: 12px; margin-right: 10px;">
                      {{ component.enabled ? '已启用' : '已禁用' }}
                    </span>
                  </div>
                </div>
                
                <p style="color: #666; font-size: 14px; margin-bottom: 15px; line-height: 1.4;">
                  {{ component.description || '暂无描述' }}
                </p>
                
                <div style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 4px; font-size: 12px;">
                  <div style="margin-bottom: 5px;"><strong>路径:</strong> {{ component.path }}</div>
                  <div v-if="component.config_file" style="margin-bottom: 5px;"><strong>配置:</strong> {{ component.config_file }}</div>
                  <div v-if="component.dependencies && component.dependencies.length > 0">
                    <strong>依赖:</strong> {{ component.dependencies.join(', ') }}
                  </div>
                </div>
                
                <div style="display: flex; gap: 10px;">
                  <button 
                    :style="component.enabled ? 'background: #dc3545;' : 'background: #28a745;'"
                    style="flex: 1; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-size: 14px;"
                    @click="toggleComponent(component)"
                    :disabled="component.loading"
                  >
                    {{ component.loading ? '处理中...' : (component.enabled ? '禁用' : '启用') }}
                  </button>
                  
                  <button 
                    v-if="component.enabled && component.status === 'running'"
                    style="background: #fd7e14; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-size: 14px;"
                    @click="restartComponent(component)"
                    :disabled="component.loading"
                  >
                    🔄 重启
                  </button>
                  
                  <button 
                    style="background: #6c757d; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-size: 14px;"
                    @click="viewComponentLogs(component)"
                  >
                    📋 日志
                  </button>
                </div>
              </div>
            </div>

            <!-- 无组件提示 -->
            <div v-if="components.length === 0" style="text-align: center; padding: 60px; color: #666;">
              <div style="font-size: 48px; margin-bottom: 20px;">🧩</div>
              <h3 style="margin-bottom: 15px;">暂无组件</h3>
              <p>系统中暂未发现任何组件，或组件加载失败</p>
              <button 
                @click="loadComponents"
                style="margin-top: 15px; padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;"
              >
                重新扫描组件
              </button>
            </div>
          </div>

          <!-- 其他页面显示开发中 -->
          <div v-else>
            <h2 style="font-size: 24px; margin-bottom: 20px; color: #333;">{{ getCurrentPageName() }}</h2>
            <div style="text-align: center; padding: 60px; color: #666;">
              <h3 style="margin-bottom: 15px;">功能开发中...</h3>
              <p>该功能正在开发中，敬请期待！</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

console.log('App-Fixed.vue 加载成功')

const currentPage = ref('login')
const loading = ref(false)
const connectionStatus = ref<'connected' | 'connecting' | 'disconnected'>('connecting')
const consoleCommand = ref('')

const form = ref({
  username: '',
  password: ''
})

// 菜单项定义
const menuItems = ref([
  { id: 'dashboard', name: '仪表板', icon: '📊' },
  { id: 'console', name: '控制台', icon: '💻' },
  { id: 'monitoring', name: '系统监控', icon: '📈' },
  { id: 'players', name: '玩家管理', icon: '👥' },
  { id: 'plugins', name: '插件管理', icon: '🔧' },
  { id: 'components', name: '组件管理', icon: '🧩' },
  { id: 'files', name: '文件管理', icon: '📁' },
  { id: 'settings', name: '系统设置', icon: '⚙️' }
])

// 真实数据
const systemStats = ref({
  cpu: 0,
  memory: 0,
  disk: 0,
  network: '0 MB/s',
  tps: 20.0,
  players_online: 0,
  max_players: 20
})

const consoleLogs = ref([])
const onlinePlayers = ref([])
const plugins = ref([])
const components = ref([])
const serverStatus = ref('unknown')

const connectionStatusText = computed(() => {
  switch (connectionStatus.value) {
    case 'connecting': return '连接中...'
    case 'connected': return '已连接'
    case 'disconnected': return '连接失败'
    default: return '未知状态'
  }
})

const connectionStatusStyle = computed(() => {
  switch (connectionStatus.value) {
    case 'connecting': return 'color: #ffc107;'
    case 'connected': return 'color: #28a745;'
    case 'disconnected': return 'color: #dc3545;'
    default: return 'color: #6c757d;'
  }
})

const handleLogin = async () => {
  console.log('开始登录:', form.value)
  
  if (loading.value) return
  loading.value = true
  
  try {
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
    
    const data = await response.json()
    console.log('登录响应:', response.status, data)
    
    if (response.ok && data.access_token) {
      console.log('登录成功，切换到仪表板')
      currentPage.value = 'dashboard'
      localStorage.setItem('access_token', data.access_token)
      
      // 初始化数据
      setTimeout(initializeData, 500)
    } else {
      alert('登录失败: ' + (data.message || '未知错误'))
    }
  } catch (error) {
    console.error('登录错误:', error)
    alert('登录失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const handleLogout = () => {
  console.log('退出登录')
  currentPage.value = 'login'
  form.value.username = ''
  form.value.password = ''
  localStorage.removeItem('access_token')
}


const getMenuItemStyle = (itemId: string) => {
  const isActive = currentPage.value === itemId
  return {
    backgroundColor: isActive ? '#007bff' : 'transparent',
    color: isActive ? 'white' : '#333',
    fontWeight: isActive ? '500' : 'normal'
  }
}

const getCurrentPageName = () => {
  const item = menuItems.value.find(m => m.id === currentPage.value)
  return item ? item.name : '未知页面'
}

const getServerStatusText = () => {
  switch (serverStatus.value) {
    case 'online': return '在线'
    case 'offline': return '离线'
    case 'starting': return '启动中'
    case 'stopping': return '停止中'
    default: return '未知'
  }
}

const getServerStatusStyle = () => {
  switch (serverStatus.value) {
    case 'online': return 'color: #28a745;'
    case 'offline': return 'color: #dc3545;'
    case 'starting': return 'color: #ffc107;'
    case 'stopping': return 'color: #fd7e14;'
    default: return 'color: #6c757d;'
  }
}

const getTpsStyle = () => {
  const tps = systemStats.value.tps
  if (tps >= 19) return 'color: #28a745;'
  if (tps >= 15) return 'color: #ffc107;'
  return 'color: #dc3545;'
}

// API调用函数
const apiCall = async (endpoint: string, options: any = {}) => {
  const token = localStorage.getItem('access_token')
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options.headers
  }
  
  const response = await fetch(`/api/v1${endpoint}`, {
    ...options,
    headers
  })
  
  if (!response.ok) {
    throw new Error(`API call failed: ${response.status}`)
  }
  
  return response.json()
}

const loadSystemStats = async () => {
  try {
    console.log('加载系统监控数据...')
    const data = await apiCall('/enhanced-monitoring/system-metrics')
    
    systemStats.value = {
      cpu: Math.round(data.cpu_usage || 0),
      memory: Math.round(data.memory_usage || 0),
      disk: Math.round(data.disk_usage || 0),
      network: `${(data.network_rx / 1024 / 1024).toFixed(1)} MB/s`,
      tps: data.tps || 20.0,
      players_online: data.players_online || 0,
      max_players: data.max_players || 20
    }
    console.log('系统监控数据加载成功:', systemStats.value)
  } catch (error) {
    console.error('加载系统监控失败:', error)
  }
}

const loadServerStatus = async () => {
  try {
    console.log('加载服务器状态...')
    const data = await apiCall('/server/status')
    serverStatus.value = data.status || 'unknown'
    systemStats.value.players_online = data.players_online || 0
    systemStats.value.max_players = data.max_players || 20
    console.log('服务器状态:', serverStatus.value)
  } catch (error) {
    console.error('加载服务器状态失败:', error)
    serverStatus.value = 'offline'
  }
}

const loadOnlinePlayers = async () => {
  try {
    console.log('加载在线玩家...')
    const data = await apiCall('/players/online')
    onlinePlayers.value = data.players || []
    console.log('在线玩家:', onlinePlayers.value)
  } catch (error) {
    console.error('加载在线玩家失败:', error)
    onlinePlayers.value = []
  }
}

const loadPlugins = async () => {
  try {
    console.log('加载插件列表...')
    const data = await apiCall('/plugins')
    plugins.value = data.plugins || []
    console.log('插件列表:', plugins.value)
  } catch (error) {
    console.error('加载插件列表失败:', error)
    plugins.value = []
  }
}

const loadComponents = async () => {
  try {
    console.log('加载组件列表...')
    const data = await apiCall('/components')
    components.value = (data.components || []).map(comp => ({
      ...comp,
      loading: false
    }))
    console.log('组件列表:', components.value)
  } catch (error) {
    console.error('加载组件列表失败:', error)
    components.value = []
  }
}

const togglePlugin = async (plugin: any) => {
  try {
    const action = plugin.enabled ? 'disable' : 'enable'
    console.log(`${action} plugin:`, plugin.name)
    
    await apiCall(`/plugins/${plugin.name}/${action}`, { method: 'POST' })
    
    // 重新加载插件列表
    await loadPlugins()
  } catch (error) {
    console.error('切换插件状态失败:', error)
    alert(`操作失败: ${error.message}`)
  }
}

const toggleComponent = async (component: any) => {
  try {
    component.loading = true
    const action = component.enabled ? 'disable' : 'enable'
    console.log(`${action} component:`, component.name)
    
    await apiCall(`/components/${component.name}/${action}`, { method: 'POST' })
    
    // 重新加载组件列表
    await loadComponents()
  } catch (error) {
    console.error('切换组件状态失败:', error)
    alert(`操作失败: ${error.message}`)
  } finally {
    component.loading = false
  }
}

const restartComponent = async (component: any) => {
  try {
    component.loading = true
    console.log('重启组件:', component.name)
    
    await apiCall(`/components/${component.name}/restart`, { method: 'POST' })
    
    // 等待一下再重新加载
    setTimeout(loadComponents, 2000)
  } catch (error) {
    console.error('重启组件失败:', error)
    alert(`重启失败: ${error.message}`)
  } finally {
    component.loading = false
  }
}

const viewComponentLogs = async (component: any) => {
  try {
    console.log('查看组件日志:', component.name)
    const data = await apiCall(`/components/${component.name}/logs?limit=100`)
    
    // 创建一个模态窗口显示日志
    const logs = data.logs || []
    const logText = logs.map(log => `[${log.timestamp}] ${log.level}: ${log.message}`).join('\n')
    
    // 简单的日志显示对话框
    const logWindow = window.open('', '_blank', 'width=800,height=600,scrollbars=yes')
    if (logWindow) {
      logWindow.document.write(`
        <html>
          <head><title>${component.name} 组件日志</title></head>
          <body style="font-family: monospace; padding: 20px; background: #1a1a1a; color: #00ff00;">
            <h2 style="color: white;">${component.name} 组件日志</h2>
            <pre style="white-space: pre-wrap; word-wrap: break-word;">${logText || '暂无日志'}</pre>
          </body>
        </html>
      `)
      logWindow.document.close()
    }
  } catch (error) {
    console.error('获取组件日志失败:', error)
    alert(`获取日志失败: ${error.message}`)
  }
}

const loadConsoleLogs = async () => {
  try {
    console.log('加载控制台日志...')
    const data = await apiCall('/console/logs?limit=50')
    consoleLogs.value = (data.logs || []).map(log => ({
      time: new Date(log.timestamp).toLocaleTimeString(),
      message: log.message
    }))
    console.log('控制台日志加载成功，条数:', consoleLogs.value.length)
  } catch (error) {
    console.error('加载控制台日志失败:', error)
    consoleLogs.value = []
  }
}

const sendCommand = async () => {
  if (!consoleCommand.value.trim()) return
  
  try {
    console.log('发送命令:', consoleCommand.value)
    
    const now = new Date()
    const timeStr = now.toLocaleTimeString()
    
    // 添加到本地日志显示
    consoleLogs.value.push({
      time: timeStr,
      message: `[CONSOLE] ${consoleCommand.value}`
    })
    
    // 发送到服务器
    await apiCall('/console/command', {
      method: 'POST',
      body: JSON.stringify({ command: consoleCommand.value })
    })
    
    consoleCommand.value = ''
    
    // 等待一下然后重新加载日志
    setTimeout(loadConsoleLogs, 1000)
  } catch (error) {
    console.error('发送命令失败:', error)
    consoleLogs.value.push({
      time: new Date().toLocaleTimeString(),
      message: `[ERROR] 命令发送失败: ${error.message}`
    })
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

// 组件状态相关函数
const getComponentBorderColor = (component: any) => {
  if (component.enabled && component.status === 'running') return '#28a745'
  if (component.enabled && component.status === 'stopped') return '#ffc107'
  return '#dc3545'
}

const getComponentStatusStyle = (status: string) => {
  switch (status) {
    case 'running':
      return 'background: #28a745; color: white;'
    case 'stopped':
      return 'background: #dc3545; color: white;'
    case 'starting':
      return 'background: #ffc107; color: #212529;'
    case 'stopping':
      return 'background: #fd7e14; color: white;'
    default:
      return 'background: #6c757d; color: white;'
  }
}

const getComponentStatusText = (status: string) => {
  switch (status) {
    case 'running': return '运行中'
    case 'stopped': return '已停止'
    case 'starting': return '启动中'
    case 'stopping': return '停止中'
    default: return '未知'
  }
}

// 初始化所有数据
const initializeData = async () => {
  console.log('初始化数据...')
  await Promise.all([
    loadSystemStats(),
    loadServerStatus(),
    loadOnlinePlayers(),
    loadPlugins(),
    loadComponents(),
    loadConsoleLogs()
  ])
  console.log('数据初始化完成')
}

onMounted(async () => {
  checkConnection()
  
  const token = localStorage.getItem('access_token')
  if (token) {
    console.log('发现已保存的token，直接进入仪表板')
    currentPage.value = 'dashboard'
    
    // 初始化所有数据
    await initializeData()
    
    // 设置定期更新数据 (每10秒)
    setInterval(async () => {
      try {
        await Promise.all([
          loadSystemStats(),
          loadServerStatus(),
          loadOnlinePlayers()
        ])
      } catch (error) {
        console.error('定期更新数据失败:', error)
      }
    }, 10000)
    
    // 设置控制台日志自动刷新 (每5秒)
    setInterval(() => {
      if (currentPage.value === 'console') {
        loadConsoleLogs()
      }
    }, 5000)
  }
})
</script>