<template>
  <div class="dashboard-view">
    <!-- 实时性能指标卡片 -->
    <el-row :gutter="16" class="metrics-row">
      <el-col :span="6">
        <el-card class="metric-card server-status">
          <div class="metric-content">
            <div class="metric-icon">
              <el-icon :size="24"><Monitor /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-title">服务器状态</div>
              <div :class="['metric-value', { 'online': serverStatus.is_running }]">
                {{ serverStatus.is_running ? '运行中' : '已停止' }}
              </div>
              <div class="metric-subtitle">
                {{ serverStatus.is_running ? `运行时间: ${formatUptime(serverStatus.uptime)}` : '点击启动服务器' }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="metric-card tps-card">
          <div class="metric-content">
            <div class="metric-icon">
              <el-icon :size="24"><Cpu /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-title">TPS</div>
              <div :class="['metric-value', getTpsClass(performance.tps)]">
                {{ performance.tps?.toFixed(1) || '--' }}
              </div>
              <div class="metric-subtitle">
                平均: {{ performance.tps_avg?.toFixed(1) || '--' }} | 最低: {{ performance.tps_min?.toFixed(1) || '--' }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="metric-card memory-card">
          <div class="metric-content">
            <div class="metric-icon">
              <el-icon :size="24"><PieChart /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-title">内存使用</div>
              <div :class="['metric-value', getMemoryClass(performance.memory_usage)]">
                {{ (performance.memory_usage || 0).toFixed(1) }}%
              </div>
              <div class="metric-subtitle">
                {{ formatMemory(performance.memory_used) }} / {{ formatMemory(performance.memory_total) }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="metric-card players-card">
          <div class="metric-content">
            <div class="metric-icon">
              <el-icon :size="24"><User /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-title">在线玩家</div>
              <div class="metric-value">
                {{ onlinePlayers.length }} / {{ serverStatus.max_players || 20 }}
              </div>
              <div class="metric-subtitle">
                {{ onlinePlayers.length > 0 ? `活跃玩家: ${onlinePlayers.length}` : '暂无玩家在线' }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 详细性能图表 -->
    <el-row :gutter="16" class="charts-row">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="chart-header">
              <el-icon><TrendCharts /></el-icon>
              <span>TPS 趋势图</span>
              <el-tag :type="getTpsTagType(performance.tps)" size="small">
                {{ getTpsDescription(performance.tps) }}
              </el-tag>
            </div>
          </template>
          <div ref="tpsChart" class="chart-container"></div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="chart-header">
              <el-icon><Monitor /></el-icon>
              <span>内存使用趋势</span>
              <el-tag :type="getMemoryTagType(performance.memory_usage)" size="small">
                {{ getMemoryDescription(performance.memory_usage) }}
              </el-tag>
            </div>
          </template>
          <div ref="memoryChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 服务器控制面板和玩家列表 -->
    <el-row :gutter="16" class="control-row">
      <el-col :span="16">
        <el-card class="control-card">
          <template #header>
            <div class="chart-header">
              <el-icon><Operation /></el-icon>
              <span>服务器控制</span>
              <div class="control-status">
                <el-tag :type="serverStatus.is_running ? 'success' : 'danger'" size="small">
                  {{ serverStatus.is_running ? '运行中' : '已停止' }}
                </el-tag>
              </div>
            </div>
          </template>
          
          <div class="control-panel">
            <!-- 服务器控制按钮 -->
            <div class="control-buttons">
              <el-button 
                type="success" 
                size="large"
                :disabled="serverStatus.is_running || controlLoading"
                :loading="controlLoading && pendingAction === 'start'"
                @click="handleServerControl('start')"
              >
                <el-icon><VideoPlay /></el-icon>
                启动服务器
              </el-button>
              
              <el-button 
                type="warning" 
                size="large"
                :disabled="!serverStatus.is_running || controlLoading"
                :loading="controlLoading && pendingAction === 'restart'"
                @click="handleServerControl('restart')"
              >
                <el-icon><Refresh /></el-icon>
                重启服务器
              </el-button>
              
              <el-button 
                type="danger" 
                size="large"
                :disabled="!serverStatus.is_running || controlLoading"
                :loading="controlLoading && pendingAction === 'stop'"
                @click="handleServerControl('stop')"
              >
                <el-icon><VideoPause /></el-icon>
                停止服务器
              </el-button>
            </div>

            <!-- 快速命令 -->
            <div class="quick-commands">
              <div class="command-group">
                <label>快速命令:</label>
                <el-button-group size="small">
                  <el-button @click="executeQuickCommand('save-all')">保存世界</el-button>
                  <el-button @click="executeQuickCommand('list')">玩家列表</el-button>
                  <el-button @click="executeQuickCommand('time set day')">设为白天</el-button>
                  <el-button @click="executeQuickCommand('weather clear')">清除天气</el-button>
                </el-button-group>
              </div>
            </div>

            <!-- 服务器信息 -->
            <div class="server-info">
              <el-descriptions :column="3" size="small" border>
                <el-descriptions-item label="服务器版本">
                  {{ serverStatus.version || 'Unknown' }}
                </el-descriptions-item>
                <el-descriptions-item label="世界名称">
                  {{ serverStatus.world_name || 'world' }}
                </el-descriptions-item>
                <el-descriptions-item label="游戏模式">
                  {{ serverStatus.gamemode || 'survival' }}
                </el-descriptions-item>
                <el-descriptions-item label="难度">
                  {{ serverStatus.difficulty || 'normal' }}
                </el-descriptions-item>
                <el-descriptions-item label="最大玩家数">
                  {{ serverStatus.max_players || 20 }}
                </el-descriptions-item>
                <el-descriptions-item label="端口">
                  {{ serverStatus.port || 25565 }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="players-card">
          <template #header>
            <div class="chart-header">
              <el-icon><User /></el-icon>
              <span>在线玩家 ({{ onlinePlayers.length }})</span>
              <el-button size="small" @click="refreshPlayers">刷新</el-button>
            </div>
          </template>
          
          <div class="players-list">
            <div v-if="onlinePlayers.length === 0" class="empty-players">
              <el-icon :size="48"><User /></el-icon>
              <p>暂无玩家在线</p>
            </div>
            
            <div v-else class="player-list">
              <div 
                v-for="player in onlinePlayers" 
                :key="player.name"
                class="player-item"
                @click="showPlayerDetails(player)"
              >
                <div class="player-avatar">
                  <img 
                    :src="getPlayerAvatar(player.name)" 
                    :alt="player.name"
                    @error="handleAvatarError"
                  />
                </div>
                <div class="player-info">
                  <div class="player-name">{{ player.name }}</div>
                  <div class="player-stats">
                    在线时长: {{ formatDuration(player.play_time) }}
                  </div>
                </div>
                <div class="player-actions">
                  <el-dropdown @command="(cmd) => handlePlayerAction(cmd, player)">
                    <el-button size="small" text>
                      <el-icon><More /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="kick">踢出</el-dropdown-item>
                        <el-dropdown-item command="ban">封禁</el-dropdown-item>
                        <el-dropdown-item command="op">给予OP</el-dropdown-item>
                        <el-dropdown-item command="tp">传送到我</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统资源监控 -->
    <el-row :gutter="16" class="system-row">
      <el-col :span="24">
        <el-card class="system-card">
          <template #header>
            <div class="chart-header">
              <el-icon><Setting /></el-icon>
              <span>系统资源监控</span>
              <el-tag type="info" size="small">实时更新</el-tag>
            </div>
          </template>
          
          <el-row :gutter="16">
            <el-col :span="8">
              <div class="system-metric">
                <div class="system-metric-header">
                  <el-icon><Cpu /></el-icon>
                  <span>CPU 使用率</span>
                </div>
                <div class="system-metric-value">
                  {{ (performance.cpu_usage || 0).toFixed(1) }}%
                </div>
                <el-progress 
                  :percentage="performance.cpu_usage || 0" 
                  :color="getProgressColor(performance.cpu_usage)"
                  :show-text="false"
                />
              </div>
            </el-col>
            
            <el-col :span="8">
              <div class="system-metric">
                <div class="system-metric-header">
                  <el-icon><PieChart /></el-icon>
                  <span>内存使用率</span>
                </div>
                <div class="system-metric-value">
                  {{ (performance.memory_usage || 0).toFixed(1) }}%
                </div>
                <el-progress 
                  :percentage="performance.memory_usage || 0" 
                  :color="getProgressColor(performance.memory_usage)"
                  :show-text="false"
                />
              </div>
            </el-col>
            
            <el-col :span="8">
              <div class="system-metric">
                <div class="system-metric-header">
                  <el-icon><Monitor /></el-icon>
                  <span>磁盘使用率</span>
                </div>
                <div class="system-metric-value">
                  {{ (performance.disk_usage || 0).toFixed(1) }}%
                </div>
                <el-progress 
                  :percentage="performance.disk_usage || 0" 
                  :color="getProgressColor(performance.disk_usage)"
                  :show-text="false"
                />
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { 
  Monitor, User, Cpu, PieChart, TrendCharts, Operation, 
  VideoPlay, VideoPause, Refresh, More, Setting
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useWebSocketStore } from '@/stores/websocket'
import { useDashboardStore } from '@/stores/dashboard'
import * as echarts from 'echarts'

const wsStore = useWebSocketStore()
const dashboardStore = useDashboardStore()

// 响应式数据
const controlLoading = ref(false)
const pendingAction = ref('')
const tpsChart = ref<HTMLElement>()
const memoryChart = ref<HTMLElement>()
let tpsChartInstance: echarts.ECharts | null = null
let memoryChartInstance: echarts.ECharts | null = null

// 图表数据
const tpsHistory = ref<number[]>([])
const memoryHistory = ref<number[]>([])
const timeLabels = ref<string[]>([])

// 计算属性
const serverStatus = computed(() => dashboardStore.serverStatus)
const performance = computed(() => dashboardStore.performance)
const onlinePlayers = computed(() => dashboardStore.onlinePlayers)

// TPS 状态判断
function getTpsClass(tps: number | undefined): string {
  if (!tps) return 'unknown'
  if (tps >= 19.5) return 'excellent'
  if (tps >= 18) return 'good'
  if (tps >= 15) return 'fair'
  return 'poor'
}

function getTpsTagType(tps: number | undefined): string {
  if (!tps) return 'info'
  if (tps >= 19.5) return 'success'
  if (tps >= 18) return 'success'
  if (tps >= 15) return 'warning'
  return 'danger'
}

function getTpsDescription(tps: number | undefined): string {
  if (!tps) return '未知'
  if (tps >= 19.5) return '优秀'
  if (tps >= 18) return '良好'
  if (tps >= 15) return '一般'
  return '较差'
}

// 内存状态判断
function getMemoryClass(usage: number | undefined): string {
  if (!usage) return 'unknown'
  if (usage < 60) return 'good'
  if (usage < 80) return 'warning'
  return 'danger'
}

function getMemoryTagType(usage: number | undefined): string {
  if (!usage) return 'info'
  if (usage < 60) return 'success'
  if (usage < 80) return 'warning'
  return 'danger'
}

function getMemoryDescription(usage: number | undefined): string {
  if (!usage) return '未知'
  if (usage < 60) return '正常'
  if (usage < 80) return '较高'
  return '过高'
}

function getProgressColor(value: number | undefined): string {
  if (!value) return '#909399'
  if (value < 60) return '#67c23a'
  if (value < 80) return '#e6a23c'
  return '#f56c6c'
}

// 格式化函数
function formatUptime(seconds: number | undefined): string {
  if (!seconds) return '--'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}时${minutes}分`
  }
  return `${minutes}分钟`
}

function formatMemory(bytes: number | undefined): string {
  if (!bytes) return '--'
  const gb = bytes / (1024 * 1024 * 1024)
  return `${gb.toFixed(1)}GB`
}

function formatDuration(seconds: number | undefined): string {
  if (!seconds) return '--'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${hours}h${minutes}m`
}

// 服务器控制
async function handleServerControl(action: string) {
  controlLoading.value = true
  pendingAction.value = action
  
  try {
    const actionNames = {
      start: '启动',
      stop: '停止',
      restart: '重启'
    }
    
    await ElMessageBox.confirm(
      `确定要${actionNames[action]}服务器吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const success = await dashboardStore.controlServer(action)
    if (success) {
      ElMessage.success(`服务器${actionNames[action]}命令已发送`)
    } else {
      ElMessage.error(`服务器${actionNames[action]}失败`)
    }
  } catch {
    // 用户取消操作
  } finally {
    controlLoading.value = false
    pendingAction.value = ''
  }
}

// 快速命令
function executeQuickCommand(command: string) {
  if (!serverStatus.value.is_running) {
    ElMessage.warning('服务器未运行')
    return
  }
  
  wsStore.sendConsoleCommand(command)
  ElMessage.success(`命令已发送: ${command}`)
}

// 玩家操作
function refreshPlayers() {
  dashboardStore.fetchOnlinePlayers()
}

function getPlayerAvatar(playerName: string): string {
  return `https://mc-heads.net/avatar/${playerName}/32`
}

function handleAvatarError(event: Event) {
  const img = event.target as HTMLImageElement
  img.src = '/default-avatar.png' // 默认头像
}

function showPlayerDetails(player: any) {
  ElMessage.info(`玩家详情: ${player.name}`)
}

function handlePlayerAction(action: string, player: any) {
  const commands = {
    kick: `kick ${player.name}`,
    ban: `ban ${player.name}`,
    op: `op ${player.name}`,
    tp: `tp ${player.name} @p`
  }
  
  if (commands[action]) {
    executeQuickCommand(commands[action])
  }
}

// 图表初始化
function initCharts() {
  nextTick(() => {
    if (tpsChart.value) {
      tpsChartInstance = echarts.init(tpsChart.value)
      updateTpsChart()
    }
    
    if (memoryChart.value) {
      memoryChartInstance = echarts.init(memoryChart.value)
      updateMemoryChart()
    }
  })
}

function updateTpsChart() {
  if (!tpsChartInstance) return
  
  const option = {
    title: {
      text: 'TPS 实时监控',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br/>TPS: {c}'
    },
    xAxis: {
      type: 'category',
      data: timeLabels.value,
      axisLabel: { fontSize: 12 }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 20,
      axisLabel: { fontSize: 12 }
    },
    series: [{
      data: tpsHistory.value,
      type: 'line',
      smooth: true,
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
          ]
        }
      },
      lineStyle: { color: '#409EFF' },
      itemStyle: { color: '#409EFF' }
    }]
  }
  
  tpsChartInstance.setOption(option)
}

function updateMemoryChart() {
  if (!memoryChartInstance) return
  
  const option = {
    title: {
      text: '内存使用监控',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br/>内存使用率: {c}%'
    },
    xAxis: {
      type: 'category',
      data: timeLabels.value,
      axisLabel: { fontSize: 12 }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { 
        fontSize: 12,
        formatter: '{value}%'
      }
    },
    series: [{
      data: memoryHistory.value,
      type: 'line',
      smooth: true,
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
            { offset: 1, color: 'rgba(103, 194, 58, 0.1)' }
          ]
        }
      },
      lineStyle: { color: '#67c23a' },
      itemStyle: { color: '#67c23a' }
    }]
  }
  
  memoryChartInstance.setOption(option)
}

// 更新图表数据
function updateChartData() {
  const now = new Date()
  const timeLabel = now.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
  
  // 添加新数据点
  tpsHistory.value.push(performance.value.tps || 0)
  memoryHistory.value.push(performance.value.memory_usage || 0)
  timeLabels.value.push(timeLabel)
  
  // 保持数据长度在合理范围内
  const maxDataPoints = 20
  if (tpsHistory.value.length > maxDataPoints) {
    tpsHistory.value.shift()
    memoryHistory.value.shift()
    timeLabels.value.shift()
  }
  
  // 更新图表
  updateTpsChart()
  updateMemoryChart()
}

onMounted(() => {
  // 初始化数据
  dashboardStore.fetchServerStatus()
  dashboardStore.fetchPerformance()
  dashboardStore.fetchOnlinePlayers()
  
  // 初始化WebSocket连接
  wsStore.initDashboardWebSocket()
  
  // 初始化图表
  initCharts()
  
  // 监听WebSocket消息
  const handleWebSocketMessage = (message: any) => {
    try {
      if (message.type === 'performance_update') {
        // 更新性能数据
        dashboardStore.performance = message.data
        updateChartData()
      } else if (message.type === 'dashboard_summary') {
        // 更新仪表盘摘要数据
        if (message.data.server_status) {
          dashboardStore.serverStatus = message.data.server_status
        }
        if (message.data.online_players) {
          dashboardStore.onlinePlayers = message.data.online_players
        }
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error)
    }
  }
  
  // 注册WebSocket消息处理器
  wsStore.onMessage(handleWebSocketMessage)
  
  // 设置定时更新作为后备方案
  const updateInterval = setInterval(() => {
    // 只在WebSocket未连接时使用定时更新
    if (!wsStore.isDashboardConnected) {
      dashboardStore.fetchPerformance()
      updateChartData()
    }
  }, 10000) // 每10秒更新一次作为后备
  
  // 清理定时器和WebSocket监听器
  onUnmounted(() => {
    clearInterval(updateInterval)
    wsStore.offMessage(handleWebSocketMessage)
    if (tpsChartInstance) {
      tpsChartInstance.dispose()
    }
    if (memoryChartInstance) {
      memoryChartInstance.dispose()
    }
  })
})
</script>

<style scoped>
.dashboard-view {
  padding: 20px;
  background: var(--el-bg-color);
  min-height: 100vh;
}

.metrics-row {
  margin-bottom: 20px;
}

.metric-card {
  height: 120px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.metric-content {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 20px;
}

.metric-icon {
  margin-right: 16px;
  color: var(--el-color-primary);
}

.metric-info {
  flex: 1;
}

.metric-title {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.metric-value {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--el-text-color-primary);
}

.metric-value.online {
  color: var(--el-color-success);
}

.metric-value.excellent {
  color: var(--el-color-success);
}

.metric-value.good {
  color: var(--el-color-success);
}

.metric-value.fair {
  color: var(--el-color-warning);
}

.metric-value.poor {
  color: var(--el-color-danger);
}

.metric-value.warning {
  color: var(--el-color-warning);
}

.metric-value.danger {
  color: var(--el-color-danger);
}

.metric-subtitle {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.charts-row {
  margin-bottom: 20px;
}

.chart-card {
  height: 300px;
}

.chart-header {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: space-between;
}

.chart-container {
  height: 240px;
  width: 100%;
}

.control-row {
  margin-bottom: 20px;
}

.control-card {
  height: 400px;
}

.control-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.control-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.control-status {
  margin-left: auto;
}

.quick-commands {
  padding: 16px;
  background: var(--el-fill-color-extra-light);
  border-radius: 6px;
}

.command-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.command-group label {
  font-weight: 500;
  color: var(--el-text-color-primary);
  min-width: 80px;
}

.server-info {
  flex: 1;
}

.players-card {
  height: 400px;
}

.players-list {
  height: 320px;
  overflow-y: auto;
}

.empty-players {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--el-text-color-secondary);
}

.empty-players p {
  margin: 12px 0 0 0;
}

.player-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.player-item {
  display: flex;
  align-items: center;
  padding: 12px;
  background: var(--el-fill-color-extra-light);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.player-item:hover {
  background: var(--el-fill-color-light);
}

.player-avatar {
  margin-right: 12px;
}

.player-avatar img {
  width: 32px;
  height: 32px;
  border-radius: 4px;
}

.player-info {
  flex: 1;
}

.player-name {
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 2px;
}

.player-stats {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.system-row {
  margin-bottom: 20px;
}

.system-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.system-card :deep(.el-card__header) {
  border-bottom-color: rgba(255, 255, 255, 0.2);
}

.system-card :deep(.el-card__body) {
  color: white;
}

.system-metric {
  text-align: center;
  padding: 20px;
}

.system-metric-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
  opacity: 0.9;
}

.system-metric-value {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 12px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .metrics-row .el-col {
    margin-bottom: 16px;
  }
}

@media (max-width: 768px) {
  .dashboard-view {
    padding: 12px;
  }
  
  .control-buttons {
    flex-direction: column;
  }
  
  .control-buttons .el-button {
    width: 100%;
  }
  
  .command-group {
    flex-direction: column;
    align-items: flex-start;
  }
}

:deep(.el-descriptions) {
  --el-descriptions-item-bordered-label-background: var(--el-fill-color-extra-light);
}
</style>