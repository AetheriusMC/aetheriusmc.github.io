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

    <!-- 主应用界面 (仪表板、控制台、监控等) -->
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

      <div style="max-width: 1200px; margin: 0 auto; padding: 30px 20px;">
        <div style="text-align: center; margin-bottom: 40px;">
          <h2 style="font-size: 28px; margin-bottom: 10px; color: #333;">欢迎使用 Aetherius WebConsole</h2>
          <p style="color: #666; font-size: 16px;">企业级Minecraft服务器管理平台</p>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 40px;">
          <div style="background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h3 style="font-size: 18px; margin-bottom: 10px; color: #333;">服务器状态</h3>
            <p style="font-size: 24px; font-weight: bold; color: #28a745; margin: 0;">在线</p>
          </div>
          
          <div style="background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h3 style="font-size: 18px; margin-bottom: 10px; color: #333;">在线玩家</h3>
            <p style="font-size: 24px; font-weight: bold; color: #007bff; margin: 0;">0 / 20</p>
          </div>
          
          <div style="background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h3 style="font-size: 18px; margin-bottom: 10px; color: #333;">CPU 使用率</h3>
            <p style="font-size: 24px; font-weight: bold; color: #6f42c1; margin: 0;">15%</p>
          </div>
        </div>

        <div style="text-align: center;">
          <h3 style="font-size: 20px; margin-bottom: 20px; color: #333;">快速操作</h3>
          <div style="display: flex; justify-content: center; gap: 15px; flex-wrap: wrap;">
            <button style="padding: 12px 24px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
              查看控制台
            </button>
            <button style="padding: 12px 24px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
              管理插件
            </button>
            <button style="padding: 12px 24px; background: #ffc107; color: #212529; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
              查看日志
            </button>
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
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px;">
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
              <div v-else style="padding: 0;">
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
                >
                  {{ plugin.enabled ? '禁用' : '启用' }}
                </button>
              </div>
            </div>
          </div>

          <!-- 文件管理页面 -->
          <div v-else-if="currentPage === 'files'">
            <h2 style="font-size: 24px; margin-bottom: 20px; color: #333;">文件管理</h2>
            <div style="background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 20px;">
              <div style="margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #eee;">
                <div style="font-size: 14px; color: #666;">当前路径: /server/</div>
              </div>
              <div v-for="file in files" :key="file.name" style="padding: 10px 0; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center;">
                  <span style="margin-right: 10px;">{{ file.type === 'folder' ? '📁' : '📄' }}</span>
                  <span>{{ file.name }}</span>
                </div>
                <div style="font-size: 12px; color: #666;">{{ file.size }}</div>
              </div>
            </div>
          </div>

          <!-- 设置页面 -->
          <div v-else-if="currentPage === 'settings'">
            <h2 style="font-size: 24px; margin-bottom: 20px; color: #333;">系统设置</h2>
            <div style="background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 30px;">
              <div style="margin-bottom: 30px;">
                <h3 style="margin-bottom: 15px; color: #333;">服务器配置</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
                  <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: 500;">服务器名称</label>
                    <input type="text" value="我的Minecraft服务器" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                  </div>
                  <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: 500;">最大玩家数</label>
                    <input type="number" value="20" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                  </div>
                  <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: 500;">游戏模式</label>
                    <select style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                      <option>生存模式</option>
                      <option>创造模式</option>
                      <option>冒险模式</option>
                    </select>
                  </div>
                  <div>
                    <label style="display: block; margin-bottom: 5px; font-weight: 500;">难度</label>
                    <select style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                      <option>和平</option>
                      <option>简单</option>
                      <option>普通</option>
                      <option>困难</option>
                    </select>
                  </div>
                </div>
                <button style="margin-top: 20px; padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                  保存设置
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

console.log('App-Final.vue 加载成功')

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
  { id: 'files', name: '文件管理', icon: '📁' },
  { id: 'settings', name: '系统设置', icon: '⚙️' }
])

// 模拟数据
const systemStats = ref({
  cpu: 24,
  memory: 68,
  disk: 45,
  network: '2.3 MB/s'
})

const consoleLogs = ref([
  { time: '14:32:01', message: '[INFO] 服务器启动完成' },
  { time: '14:32:15', message: '[INFO] 已加载 15 个插件' },
  { time: '14:33:42', message: '[INFO] Steve 加入了游戏' },
  { time: '14:35:18', message: '[INFO] Alex 加入了游戏' },
  { time: '14:36:05', message: '[CHAT] <Steve> 大家好！' }
])

const onlinePlayers = ref([
  { name: 'Steve', joinTime: '14:33:42' },
  { name: 'Alex', joinTime: '14:35:18' }
])

const plugins = ref([
  { name: 'EssentialsX', version: '2.19.4', description: '提供基础服务器命令和功能', enabled: true },
  { name: 'WorldEdit', version: '7.2.12', description: '强大的世界编辑工具', enabled: true },
  { name: 'LuckPerms', version: '5.4.30', description: '权限管理插件', enabled: true },
  { name: 'Vault', version: '1.7.3', description: '经济系统API插件', enabled: false },
  { name: 'PlaceholderAPI', version: '2.11.2', description: '变量占位符API', enabled: true }
])

const files = ref([
  { name: 'plugins', type: 'folder', size: '15 items' },
  { name: 'world', type: 'folder', size: '2.1 GB' },
  { name: 'logs', type: 'folder', size: '48 items' },
  { name: 'server.properties', type: 'file', size: '1.2 KB' },
  { name: 'ops.json', type: 'file', size: '156 B' },
  { name: 'whitelist.json', type: 'file', size: '89 B' }
])

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
      // 可以保存token到localStorage
      localStorage.setItem('access_token', data.access_token)
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

const sendCommand = () => {
  if (!consoleCommand.value.trim()) return
  
  console.log('发送命令:', consoleCommand.value)
  
  // 添加到控制台日志
  const now = new Date()
  const timeStr = now.toTimeString().slice(0, 8)
  consoleLogs.value.push({
    time: timeStr,
    message: `[CONSOLE] ${consoleCommand.value}`
  })
  
  // 模拟命令响应
  setTimeout(() => {
    consoleLogs.value.push({
      time: timeStr,
      message: `[INFO] 命令已执行: ${consoleCommand.value}`
    })
  }, 500)
  
  consoleCommand.value = ''
}

const getMenuItemStyle = (itemId: string) => {
  const isActive = currentPage.value === itemId
  return {
    backgroundColor: isActive ? '#007bff' : 'transparent',
    color: isActive ? 'white' : '#333',
    fontWeight: isActive ? '500' : 'normal'
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

onMounted(() => {
  checkConnection()
  
  // 检查是否已经登录
  const token = localStorage.getItem('access_token')
  if (token) {
    console.log('发现已保存的token，直接进入仪表板')
    currentPage.value = 'dashboard'
  }
  
  // 定期更新系统统计数据
  setInterval(() => {
    systemStats.value.cpu = Math.floor(Math.random() * 100)
    systemStats.value.memory = Math.floor(Math.random() * 100)
    systemStats.value.disk = Math.floor(Math.random() * 100)
    systemStats.value.network = (Math.random() * 10).toFixed(1) + ' MB/s'
  }, 3000)
})
</script>