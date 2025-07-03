<template>
  <div class="console-view">
    <!-- 控制台工具栏 -->
    <div class="console-toolbar">
      <div class="toolbar-left">
        <h3 class="toolbar-title">
          <el-icon><Monitor /></el-icon>
          实时控制台
        </h3>
        <el-tag 
          :type="connectionTagType"
          size="small"
          effect="dark"
          @click="handleConnectionClick"
        >
          <el-icon :class="{ 'rotating': isReconnecting }">
            <component :is="connectionIcon" />
          </el-icon>
          {{ connectionText }}
        </el-tag>
        
        <!-- 服务器状态显示 -->
        <div class="server-status-display">
          <el-tag 
            :type="dashboardStore.isServerRunning ? 'success' : 'danger'" 
            size="small"
            effect="dark"
          >
            <el-icon><Monitor /></el-icon>
            {{ dashboardStore.isServerRunning ? '服务器运行中' : '服务器已停止' }}
          </el-tag>
          
          <el-tag v-if="dashboardStore.isServerRunning" type="info" size="small" effect="plain">
            运行时间: {{ dashboardStore.formattedUptime }}
          </el-tag>
          
          <el-tag type="info" size="small" effect="plain">
            玩家: {{ dashboardStore.playerCount }}/{{ dashboardStore.maxPlayers }}
          </el-tag>
          
          <el-tag 
            :type="dashboardStore.tps >= 19 ? 'success' : dashboardStore.tps >= 15 ? 'warning' : 'danger'" 
            size="small" 
            effect="plain"
          >
            TPS: {{ dashboardStore.tps.toFixed(1) }}
          </el-tag>
        </div>
      </div>
      
      <div class="toolbar-right">
        <!-- 搜索 -->
        <el-input
          v-model="searchQuery"
          placeholder="搜索日志..."
          :prefix-icon="Search"
          size="small"
          style="width: 200px"
          clearable
        />
        
        <!-- 级别过滤 -->
        <el-select
          v-model="selectedLevels"
          placeholder="级别"
          size="small"
          multiple
          collapse-tags
          style="width: 120px"
        >
          <el-option
            v-for="level in logLevels"
            :key="level.value"
            :label="level.label"
            :value="level.value"
          />
        </el-select>
        
        <!-- 操作按钮 -->
        <el-button-group size="small">
          <el-button @click="clearConsole" :icon="Delete">清空</el-button>
          <el-button 
            @click="toggleAutoScroll" 
            :type="autoScroll ? 'primary' : 'default'"
            :icon="Bottom"
          >
            自动滚动
          </el-button>
          <el-button @click="exportLogs" :icon="Download">导出</el-button>
        </el-button-group>
        
        <!-- 主题切换 -->
        <el-dropdown @command="changeTheme">
          <el-button size="small" :icon="Sunny" />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="dark">深色主题</el-dropdown-item>
              <el-dropdown-item command="light">浅色主题</el-dropdown-item>
              <el-dropdown-item command="matrix">绿色终端</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 控制台主体 -->
    <div class="console-main">
      <!-- 日志输出区域 -->
      <div 
        ref="consoleOutput" 
        :class="['console-output', `theme-${theme}`]"
        @scroll="handleScroll"
      >
        <div v-if="filteredMessages.length === 0" class="empty-state">
          <el-icon :size="48"><Monitor /></el-icon>
          <p>{{ connectionStatus.connected ? '等待日志输出...' : '等待连接...' }}</p>
        </div>
        
        <div
          v-for="(message, index) in visibleMessages"
          :key="getMessageKey(message, index)"
          :class="['log-line', `level-${message.data.level.toLowerCase()}`]"
        >
          <span class="log-time">{{ formatTime(message.timestamp) }}</span>
          <span class="log-level">[{{ message.data.level }}]</span>
          <span class="log-source">[{{ message.data.source }}]</span>
          <span class="log-content">{{ message.data.message }}</span>
        </div>
      </div>

      <!-- 命令输入区域 -->
      <div class="command-input-area">
        <!-- 命令提示 -->
        <div v-if="commandHelp" class="command-help">
          <el-icon><InfoFilled /></el-icon>
          <span>{{ commandHelp.desc }} - {{ commandHelp.syntax }}</span>
        </div>
        
        <!-- 输入框 -->
        <div class="command-input">
          <el-autocomplete
            v-model="currentCommand"
            :fetch-suggestions="fetchSuggestions"
            placeholder="输入命令... 支持前缀: / (MC) ! (系统) @ (脚本) $ (组件) # (插件)"
            @select="handleSuggestionSelect"
            @input="handleCommandInput"
            @keydown="handleKeyDown"
            :disabled="!connectionStatus.connected"
            size="default"
            clearable
          >
            <template #prefix>
              <el-icon><ChatDotRound /></el-icon>
            </template>
            
            <template #default="{ item }">
              <div class="suggestion-item">
                <div class="suggestion-command">{{ item.value }}</div>
                <div class="suggestion-desc">{{ item.desc }}</div>
              </div>
            </template>
            
            <template #append>
              <el-button 
                type="primary"
                @click="sendCommand"
                :disabled="!currentCommand.trim() || !connectionStatus.connected"
                :icon="Promotion"
              >
                发送
              </el-button>
            </template>
          </el-autocomplete>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { 
  Monitor, Search, Delete, Bottom, Download, Sunny, 
  InfoFilled, ChatDotRound, Promotion, Connection, Close, Loading
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useWebSocketStore } from '@/stores/websocket'
import { useConsoleStore } from '@/stores/console'
import { useDashboardStore } from '@/stores/dashboard'
import type { ConsoleMessage } from '@/types'

const wsStore = useWebSocketStore()
const consoleStore = useConsoleStore()
const dashboardStore = useDashboardStore()

// 响应式数据
const searchQuery = ref('')
const selectedLevels = ref(['INFO', 'WARN', 'ERROR', 'COMMAND'])
const currentCommand = ref('')
const commandHistory = ref<string[]>([])
const historyIndex = ref(-1)
const autoScroll = ref(true)
const theme = ref('dark')
const consoleOutput = ref<HTMLElement>()

// 日志级别定义
const logLevels = [
  { label: 'INFO', value: 'INFO' },
  { label: 'WARN', value: 'WARN' },
  { label: 'ERROR', value: 'ERROR' },
  { label: 'DEBUG', value: 'DEBUG' },
  { label: 'COMMAND', value: 'COMMAND' }
]

// 命令定义
const commands = ref([
  // Minecraft 命令
  { value: '/list', desc: '显示在线玩家', syntax: '/list', category: 'minecraft' },
  { value: '/say', desc: '向所有玩家发送消息', syntax: '/say <message>', category: 'minecraft' },
  { value: '/tp', desc: '传送玩家', syntax: '/tp <player> [target]', category: 'minecraft' },
  { value: '/gamemode', desc: '更改游戏模式', syntax: '/gamemode <mode> [player]', category: 'minecraft' },
  { value: '/time set', desc: '设置时间', syntax: '/time set <day|night|time>', category: 'minecraft' },
  { value: '/weather', desc: '设置天气', syntax: '/weather <clear|rain|thunder>', category: 'minecraft' },
  { value: '/ban', desc: '封禁玩家', syntax: '/ban <player> [reason]', category: 'minecraft' },
  { value: '/kick', desc: '踢出玩家', syntax: '/kick <player> [reason]', category: 'minecraft' },
  { value: '/op', desc: '给予OP权限', syntax: '/op <player>', category: 'minecraft' },
  { value: '/deop', desc: '移除OP权限', syntax: '/deop <player>', category: 'minecraft' },
  
  // Aetherius 系统命令
  { value: '!status', desc: '显示服务器状态', syntax: '!status', category: 'system' },
  { value: '!reload', desc: '重载配置', syntax: '!reload', category: 'system' },
  { value: '!backup', desc: '创建备份', syntax: '!backup [name]', category: 'system' },
  { value: '!performance', desc: '显示性能信息', syntax: '!performance', category: 'system' },
  
  // 组件命令
  { value: '$list', desc: '列出所有组件', syntax: '$list', category: 'component' },
  { value: '$enable', desc: '启用组件', syntax: '$enable <name>', category: 'component' },
  { value: '$disable', desc: '禁用组件', syntax: '$disable <name>', category: 'component' },
  { value: '$status', desc: '组件状态', syntax: '$status [name]', category: 'component' },
  { value: '$reload', desc: '重载组件', syntax: '$reload <name>', category: 'component' },
  
  // 插件命令
  { value: '#list', desc: '列出插件', syntax: '#list', category: 'plugin' },
  { value: '#enable', desc: '启用插件', syntax: '#enable <name>', category: 'plugin' },
  { value: '#disable', desc: '禁用插件', syntax: '#disable <name>', category: 'plugin' },
  
  // 脚本命令
  { value: '@reload', desc: '重载脚本', syntax: '@reload', category: 'script' },
  { value: '@run', desc: '执行脚本', syntax: '@run <script>', category: 'script' }
])

// 计算属性
const connectionStatus = computed(() => wsStore.consoleStatus)
const isReconnecting = computed(() => connectionStatus.value.reconnecting)

const connectionTagType = computed(() => {
  if (connectionStatus.value.connected) return 'success'
  if (isReconnecting.value) return 'warning'
  return 'danger'
})

const connectionIcon = computed(() => {
  if (connectionStatus.value.connected) return Connection
  if (isReconnecting.value) return Loading
  return Close
})

const connectionText = computed(() => {
  if (connectionStatus.value.connected) return '已连接'
  if (isReconnecting.value) return '连接中'
  return '未连接'
})

const displayMessages = computed(() => {
  const messages = wsStore.consoleMessages
  // 限制显示的消息数量以提高性能
  return messages.slice(-1000)
})

const filteredMessages = computed(() => {
  let messages = displayMessages.value
  
  // 级别过滤
  if (selectedLevels.value.length > 0 && selectedLevels.value.length < logLevels.length) {
    messages = messages.filter(msg => selectedLevels.value.includes(msg.data.level))
  }
  
  // 搜索过滤
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    messages = messages.filter(msg => 
      msg.data.message.toLowerCase().includes(query) ||
      msg.data.source.toLowerCase().includes(query)
    )
  }
  
  return messages
})

const visibleMessages = computed(() => {
  // 虚拟滚动 - 只显示可见区域的消息
  return filteredMessages.value.slice(-200) // 简化版虚拟滚动
})

const commandHelp = computed(() => {
  if (!currentCommand.value.trim()) return null
  const cmd = currentCommand.value.trim().toLowerCase()
  return commands.value.find(c => 
    c.value.toLowerCase().startsWith(cmd) || 
    cmd.startsWith(c.value.toLowerCase())
  )
})

// 方法
function formatTime(timestamp: string): string {
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function getMessageKey(message: ConsoleMessage, index: number): string {
  return `${message.timestamp}-${index}`
}

function handleConnectionClick() {
  if (!connectionStatus.value.connected && !isReconnecting.value) {
    wsStore.reconnectConsole()
  }
}

function clearConsole() {
  wsStore.clearConsoleMessages()
  ElMessage.success('控制台已清空')
}

function toggleAutoScroll() {
  autoScroll.value = !autoScroll.value
  if (autoScroll.value) {
    scrollToBottom()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (consoleOutput.value) {
      consoleOutput.value.scrollTop = consoleOutput.value.scrollHeight
    }
  })
}

function handleScroll() {
  if (!consoleOutput.value) return
  const { scrollTop, scrollHeight, clientHeight } = consoleOutput.value
  const isAtBottom = Math.abs(scrollHeight - clientHeight - scrollTop) < 10
  
  if (!isAtBottom && autoScroll.value) {
    autoScroll.value = false
  }
}

function sendCommand() {
  const command = currentCommand.value.trim()
  if (!command || !connectionStatus.value.connected) return

  // 添加到历史记录
  if (commandHistory.value[commandHistory.value.length - 1] !== command) {
    commandHistory.value.push(command)
    if (commandHistory.value.length > 50) {
      commandHistory.value.shift()
    }
  }
  
  historyIndex.value = -1

  // 发送命令
  if (wsStore.sendConsoleCommand(command)) {
    currentCommand.value = ''
    
    // 添加命令到输出
    wsStore.addConsoleMessage({
      type: 'console_log',
      timestamp: new Date().toISOString(),
      data: {
        level: 'COMMAND',
        source: 'Client',
        message: `> ${command}`
      }
    })
  } else {
    ElMessage.error('命令发送失败')
  }
}

function handleKeyDown(event: KeyboardEvent) {
  switch (event.key) {
    case 'Enter':
      if (!event.shiftKey) {
        event.preventDefault()
        sendCommand()
      }
      break
      
    case 'ArrowUp':
      event.preventDefault()
      navigateHistory(1)
      break
      
    case 'ArrowDown':
      event.preventDefault()
      navigateHistory(-1)
      break
  }
}

function navigateHistory(direction: number) {
  if (commandHistory.value.length === 0) return

  const newIndex = historyIndex.value + direction
  
  if (newIndex >= 0 && newIndex < commandHistory.value.length) {
    historyIndex.value = newIndex
    const commandIndex = commandHistory.value.length - 1 - historyIndex.value
    currentCommand.value = commandHistory.value[commandIndex]
  } else if (newIndex < 0) {
    historyIndex.value = -1
    currentCommand.value = ''
  }
}

function fetchSuggestions(queryString: string, callback: (suggestions: any[]) => void) {
  const query = queryString.toLowerCase()
  if (!query) {
    callback([])
    return
  }

  const suggestions = commands.value
    .filter(cmd => 
      cmd.value.toLowerCase().includes(query) || 
      cmd.desc.toLowerCase().includes(query)
    )
    .sort((a, b) => {
      // 优先匹配开头的命令
      const aStartsWith = a.value.toLowerCase().startsWith(query)
      const bStartsWith = b.value.toLowerCase().startsWith(query)
      if (aStartsWith && !bStartsWith) return -1
      if (!aStartsWith && bStartsWith) return 1
      return 0
    })
    .slice(0, 10)

  callback(suggestions)
}

function handleSuggestionSelect(suggestion: any) {
  currentCommand.value = suggestion.value + ' '
}

function handleCommandInput(value: string) {
  // 实时更新命令帮助
}

function changeTheme(themeName: string) {
  theme.value = themeName
  localStorage.setItem('console-theme', themeName)
}

function exportLogs() {
  const logs = filteredMessages.value.map(msg => {
    const time = formatTime(msg.timestamp)
    return `${time} [${msg.data.level}] [${msg.data.source}] ${msg.data.message}`
  }).join('\n')
  
  const blob = new Blob([logs], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `console-logs-${new Date().toISOString().split('T')[0]}.txt`
  a.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('日志已导出')
}

// 监听消息变化，自动滚动
watch(
  () => wsStore.consoleMessages.length,
  () => {
    if (autoScroll.value) {
      scrollToBottom()
    }
  }
)

// 监听连接状态变化
watch(
  () => connectionStatus.value.connected,
  (connected, wasConnected) => {
    if (connected && !wasConnected) {
      ElMessage.success('WebSocket已连接')
    } else if (!connected && wasConnected) {
      ElMessage.warning('WebSocket连接已断开')
    }
  }
)

onMounted(() => {
  // 加载主题
  const savedTheme = localStorage.getItem('console-theme')
  if (savedTheme) {
    theme.value = savedTheme
  }
  
  // 初始化stores
  wsStore.initConsoleWebSocket()
  dashboardStore.initialize()
  
  // 初始化控制台Store (获取真实服务器状态)
  consoleStore.initialize()
  
  // 滚动到底部
  scrollToBottom()
})

onUnmounted(() => {
  // 清理资源
  consoleStore.cleanup()
  dashboardStore.cleanup()
})
</script>

<style scoped>
.console-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color);
  position: relative;
}

.console-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5vh 2vw;
  background: var(--el-bg-color-page);
  border-bottom: 1px solid var(--el-border-color-light);
  flex-shrink: 0;
  height: 12vh; /* 工具栏占屏幕高度的12% */
  min-height: 70px;
  max-height: 100px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.server-status-display {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.toolbar-title {
  display: flex;
  align-items: center;
  gap: 0.5vw;
  margin: 0;
  font-size: clamp(14px, 1.5vw, 20px);
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.console-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.console-output {
  flex: 1;
  padding: 1.5vh 2vw;
  overflow-y: auto;
  font-family: 'JetBrains Mono', 'Consolas', 'Monaco', monospace;
  font-size: clamp(11px, 1.2vw, 14px);
  line-height: 1.4;
  background: #1e1e1e;
  color: #d4d4d4;
  height: calc(75vh - 12vh); /* 日志区域占75%，减去工具栏和命令输入区域 */
  max-height: calc(100vh - 200px);
}

.console-output.theme-light {
  background: #ffffff;
  color: #333333;
  border-top: 1px solid var(--el-border-color-light);
}

.console-output.theme-matrix {
  background: #0a0a0a;
  color: #00ff00;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
  text-align: center;
}

.empty-state p {
  margin: 12px 0 0 0;
  font-size: 14px;
}

.log-line {
  margin-bottom: 1px;
  word-wrap: break-word;
  display: flex;
  align-items: baseline;
}

.log-time {
  color: #808080;
  margin-right: 1vw;
  min-width: clamp(60px, 6vw, 90px);
  font-size: clamp(10px, 1vw, 13px);
}

.log-level {
  margin-right: 1vw;
  min-width: clamp(50px, 5vw, 80px);
  font-weight: 600;
  font-size: clamp(10px, 1vw, 13px);
}

.log-source {
  margin-right: 1vw;
  min-width: clamp(70px, 7vw, 100px);
  color: #9cdcfe;
  font-size: clamp(10px, 1vw, 13px);
}

.log-content {
  flex: 1;
  word-break: break-word;
}

/* 日志级别颜色 */
.level-info .log-level { color: #4fc3f7; }
.level-warn .log-level { color: #ffb74d; }
.level-error .log-level { color: #f48fb1; }
.level-debug .log-level { color: #81c784; }
.level-command .log-level { color: #ba68c8; }
.level-command .log-content { color: #ba68c8; font-weight: 600; }

/* 浅色主题颜色 */
.theme-light .level-info .log-level { color: #1976d2; }
.theme-light .level-warn .log-level { color: #f57c00; }
.theme-light .level-error .log-level { color: #d32f2f; }
.theme-light .level-debug .log-level { color: #388e3c; }
.theme-light .level-command .log-level { color: #7b1fa2; }
.theme-light .level-command .log-content { color: #7b1fa2; }
.theme-light .log-time { color: #666; }
.theme-light .log-source { color: #1565c0; }

/* 矩阵主题颜色 */
.theme-matrix .level-info .log-level { color: #00ff00; }
.theme-matrix .level-warn .log-level { color: #ffff00; }
.theme-matrix .level-error .log-level { color: #ff0000; }
.theme-matrix .level-debug .log-level { color: #00ffff; }
.theme-matrix .level-command .log-level { color: #ff00ff; }
.theme-matrix .level-command .log-content { color: #ff00ff; }

.command-input-area {
  padding: 1.5vh 2vw;
  background: var(--el-bg-color-page);
  border-top: 1px solid var(--el-border-color-light);
  flex-shrink: 0;
  height: 13vh; /* 命令输入区域占屏幕高度的13% */
  min-height: 80px;
  max-height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.command-help {
  display: flex;
  align-items: center;
  gap: 0.5vw;
  margin-bottom: 0.5vh;
  padding: 0.5vh 1vw;
  background: var(--el-color-info-light-9);
  border-radius: 4px;
  color: var(--el-color-info);
  font-size: clamp(10px, 1vw, 13px);
  line-height: 1.2;
}

.command-input {
  width: 100%;
}

.suggestion-item {
  padding: 4px 0;
}

.suggestion-command {
  font-weight: 600;
  color: var(--el-color-primary);
  font-family: 'JetBrains Mono', 'Consolas', monospace;
}

.suggestion-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 滚动条样式 */
.console-output::-webkit-scrollbar {
  width: 8px;
}

.console-output::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.console-output::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
}

.console-output::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .console-toolbar {
    flex-direction: column;
    gap: 1vh;
    padding: 2vh 4vw;
    height: 15vh; /* 移动端工具栏高度 */
    min-height: 90px;
  }
  
  .toolbar-right {
    width: 100%;
    justify-content: space-between;
  }
  
  .toolbar-right .el-input {
    width: 40vw !important;
    min-width: 120px;
  }
  
  .toolbar-right .el-select {
    width: 25vw !important;
    min-width: 80px;
  }
  
  .command-input-area {
    padding: 2vh 4vw;
    height: 15vh; /* 移动端命令输入区域高度 */
    min-height: 90px;
  }
  
  .console-output {
    height: calc(70vh - 15vh); /* 移动端日志区域占70%，减去工具栏 */
    padding: 2vh 4vw;
    font-size: clamp(10px, 3vw, 13px);
  }
}

/* 大屏幕优化 */
@media (min-width: 1920px) {
  .console-toolbar {
    height: 10vh; /* 大屏幕工具栏占比 */
    padding: 1vh 1.5vw;
  }
  
  .command-input-area {
    height: 15vh; /* 大屏幕命令输入区域占比 */
    padding: 1.5vh 1.5vw;
  }
  
  .console-output {
    height: calc(75vh - 10vh); /* 大屏幕日志区域占75%，减去工具栏 */
    padding: 1.5vh 1.5vw;
    font-size: clamp(12px, 0.8vw, 16px);
  }
}

/* 超小屏幕适配 */
@media (max-width: 480px) {
  .console-toolbar {
    height: 18vh; /* 超小屏幕工具栏高度 */
    padding: 2.5vh 5vw;
  }
  
  .command-input-area {
    height: 17vh; /* 超小屏幕命令输入区域高度 */
    padding: 2.5vh 5vw;
  }
  
  .console-output {
    height: calc(65vh - 18vh); /* 超小屏幕日志区域占65%，减去工具栏 */
    padding: 2.5vh 5vw;
    font-size: clamp(9px, 4vw, 12px);
  }
  
  .toolbar-right .el-input {
    width: 45vw !important;
  }
  
  .toolbar-right .el-select {
    width: 30vw !important;
  }
}

:deep(.el-autocomplete) {
  width: 100%;
}

:deep(.el-input-group__append .el-button) {
  background-color: var(--el-color-primary);
  border-color: var(--el-color-primary);
  color: white;
}
</style>