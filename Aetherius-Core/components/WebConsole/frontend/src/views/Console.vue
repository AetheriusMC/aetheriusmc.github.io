<template>
  <div class="space-y-6">
    <!-- Console Header -->
    <div class="card p-6">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-white">服务器控制台</h2>
          <div class="flex items-center space-x-2">
            <div class="w-2 h-2 rounded-full" :class="connectionStatusColor"></div>
            <span class="text-sm text-gray-600 dark:text-gray-300">{{ connectionStatusText }}</span>
          </div>
        </div>
        
        <div class="flex items-center space-x-2">
          <button
            @click="toggleAutoScroll"
            class="btn btn-secondary text-sm"
            :class="{ 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300': autoScroll }"
          >
            <ArrowDownIcon class="w-4 h-4 mr-2" />
            {{ autoScroll ? '关闭自动滚动' : '开启自动滚动' }}
          </button>
          
          <button
            @click="clearConsole"
            class="btn btn-secondary text-sm"
          >
            <TrashIcon class="w-4 h-4 mr-2" />
            清空
          </button>
          
          <div class="relative">
            <button
              @click="showFilters = !showFilters"
              class="btn btn-secondary text-sm"
              :class="{ 'bg-gray-200 dark:bg-gray-600': showFilters }"
            >
              <FunnelIcon class="w-4 h-4 mr-2" />
              筛选
            </button>
            
            <!-- Filter dropdown -->
            <div
              v-if="showFilters"
              class="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg z-10 border border-gray-200 dark:border-gray-700"
            >
              <div class="p-3 space-y-2">
                <label class="flex items-center">
                  <input
                    v-model="filters.info"
                    type="checkbox"
                    class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">信息</span>
                </label>
                <label class="flex items-center">
                  <input
                    v-model="filters.warning"
                    type="checkbox"
                    class="rounded border-gray-300 text-yellow-600 focus:ring-yellow-500"
                  />
                  <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">警告</span>
                </label>
                <label class="flex items-center">
                  <input
                    v-model="filters.error"
                    type="checkbox"
                    class="rounded border-gray-300 text-red-600 focus:ring-red-500"
                  />
                  <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">错误</span>
                </label>
                <label class="flex items-center">
                  <input
                    v-model="filters.debug"
                    type="checkbox"
                    class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">调试</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Console Display -->
    <div class="card p-0 overflow-hidden">
      <div
        ref="consoleContainer"
        class="console-terminal h-96 overflow-y-auto custom-scrollbar"
        @scroll="handleScroll"
      >
        <div v-if="filteredMessages.length === 0" class="p-8 text-center">
          <TerminalIcon class="w-12 h-12 mx-auto text-gray-400 dark:text-gray-600" />
          <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
            {{ isConnected ? '暂无日志消息' : '正在连接控制台...' }}
          </p>
        </div>
        
        <div v-else class="space-y-1">
          <div
            v-for="message in filteredMessages"
            :key="message.id"
            class="console-line"
            :class="getMessageClass(message.level)"
          >
            <span class="text-gray-400 text-xs mr-2">
              {{ formatTime(message.timestamp) }}
            </span>
            <span v-if="message.source" class="text-blue-400 text-xs mr-2">
              [{{ message.source }}]
            </span>
            <span class="font-mono text-sm">{{ message.message }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Command Input -->
    <div class="card p-4">
      <form @submit.prevent="sendCommand" class="flex space-x-3">
        <div class="flex-1 relative">
          <input
            ref="commandInput"
            v-model="currentCommand"
            type="text"
            placeholder="输入服务器命令..."
            class="w-full px-4 py-2 bg-gray-900 text-green-400 font-mono text-sm border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            :disabled="!isConnected || loading"
            @keydown="handleKeyDown"
          />
          
          <!-- Command suggestions -->
          <div
            v-if="showSuggestions && suggestions.length > 0"
            class="absolute top-full left-0 right-0 mt-1 bg-gray-800 border border-gray-600 rounded-md shadow-lg z-20 max-h-48 overflow-y-auto"
          >
            <div
              v-for="(suggestion, index) in suggestions"
              :key="suggestion"
              class="px-4 py-2 text-sm text-green-400 font-mono cursor-pointer hover:bg-gray-700"
              :class="{ 'bg-gray-700': index === selectedSuggestion }"
              @click="selectSuggestion(suggestion)"
            >
              {{ suggestion }}
            </div>
          </div>
        </div>
        
        <button
          type="submit"
          class="btn btn-primary"
          :disabled="!isConnected || loading || !currentCommand.trim()"
        >
          <PaperAirplaneIcon class="w-4 h-4 mr-2" />
          发送
        </button>
      </form>
    </div>

    <!-- Command History -->
    <div class="card p-6">
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">命令历史</h3>
      
      <div v-if="commandHistory.length === 0" class="text-center py-8">
        <ClockIcon class="w-12 h-12 mx-auto text-gray-400 dark:text-gray-600" />
        <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">暂无命令历史</p>
      </div>
      
      <div v-else class="space-y-3">
        <div
          v-for="cmd in commandHistory.slice(-10)"
          :key="cmd.id"
          class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-md"
        >
          <div class="flex-1">
            <div class="flex items-center space-x-2">
              <code class="text-sm font-mono text-gray-900 dark:text-white">{{ cmd.command }}</code>
              <span
                class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                :class="cmd.success 
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'"
              >
                {{ cmd.success ? '成功' : '失败' }}
              </span>
            </div>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {{ formatTime(cmd.timestamp) }} - {{ cmd.user }}
            </p>
          </div>
          
          <button
            @click="repeatCommand(cmd.command)"
            class="ml-4 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            title="重复执行"
          >
            <ArrowPathIcon class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import {
  TerminalIcon,
  ArrowDownIcon,
  TrashIcon,
  FunnelIcon,
  PaperAirplaneIcon,
  ClockIcon,
  ArrowPathIcon
} from '@heroicons/vue/24/outline'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import type { ConsoleMessage, CommandHistory } from '@/types'
import { websocketService } from '@/services/websocket'
import { useServerStore } from '@/stores/server'
import { useAuthStore } from '@/stores/auth'
import { useToast } from 'vue-toastification'

const serverStore = useServerStore()
const authStore = useAuthStore()
const toast = useToast()

const consoleContainer = ref<HTMLElement>()
const commandInput = ref<HTMLInputElement>()

const messages = ref<ConsoleMessage[]>([])
const commandHistory = ref<CommandHistory[]>([])
const currentCommand = ref('')
const autoScroll = ref(true)
const loading = ref(false)
const isConnected = ref(false)
const showFilters = ref(false)
const showSuggestions = ref(false)
const selectedSuggestion = ref(0)

const filters = ref({
  info: true,
  warning: true,
  error: true,
  debug: true
})

const historyIndex = ref(-1)
const commandCache = ref<string[]>([])

const connectionStatusColor = computed(() => {
  return isConnected.value ? 'bg-green-500' : 'bg-red-500'
})

const connectionStatusText = computed(() => {
  return isConnected.value ? '已连接' : '已断开'
})

const filteredMessages = computed(() => {
  return messages.value.filter(msg => {
    switch (msg.level) {
      case 'info':
        return filters.value.info
      case 'warning':
        return filters.value.warning
      case 'error':
        return filters.value.error
      case 'debug':
        return filters.value.debug
      default:
        return true
    }
  })
})

const suggestions = computed(() => {
  if (!currentCommand.value.trim()) return []
  
  const commands = [
    'help', 'stop', 'reload', 'save-all', 'save-on', 'save-off',
    'whitelist add', 'whitelist remove', 'whitelist list',
    'op', 'deop', 'kick', 'ban', 'ban-ip', 'pardon', 'pardon-ip',
    'gamemode survival', 'gamemode creative', 'gamemode adventure', 'gamemode spectator',
    'difficulty peaceful', 'difficulty easy', 'difficulty normal', 'difficulty hard',
    'weather clear', 'weather rain', 'weather thunder',
    'time set day', 'time set night', 'time set noon', 'time set midnight',
    'tp', 'teleport', 'give', 'summon', 'kill', 'clear',
    'effect give', 'effect clear', 'enchant', 'experience add',
    'world', 'plugins', 'version', 'seed', 'list'
  ]
  
  const input = currentCommand.value.toLowerCase()
  return commands.filter(cmd => cmd.toLowerCase().startsWith(input)).slice(0, 10)
})

const getMessageClass = (level: string): string => {
  switch (level) {
    case 'info':
      return 'console-line info'
    case 'warning':
      return 'console-line warning'
    case 'error':
      return 'console-line error'
    case 'debug':
      return 'console-line debug'
    default:
      return 'console-line'
  }
}

const formatTime = (timestamp: string): string => {
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const scrollToBottom = async () => {
  if (autoScroll.value && consoleContainer.value) {
    await nextTick()
    consoleContainer.value.scrollTop = consoleContainer.value.scrollHeight
  }
}

const handleScroll = () => {
  if (!consoleContainer.value) return
  
  const { scrollTop, scrollHeight, clientHeight } = consoleContainer.value
  const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10
  
  if (!isAtBottom && autoScroll.value) {
    autoScroll.value = false
  }
}

const toggleAutoScroll = () => {
  autoScroll.value = !autoScroll.value
  if (autoScroll.value) {
    scrollToBottom()
  }
}

const clearConsole = () => {
  messages.value = []
  toast.success('控制台已清空')
}

const sendCommand = async () => {
  if (!currentCommand.value.trim() || !isConnected.value || loading.value) return
  
  const command = currentCommand.value.trim()
  loading.value = true
  
  try {
    // Send command via WebSocket
    websocketService.sendCommand(command)
    
    // Add to command history
    const historyItem: CommandHistory = {
      id: Date.now().toString(),
      command,
      timestamp: new Date().toISOString(),
      user: authStore.user?.username || 'Unknown',
      success: true
    }
    commandHistory.value.push(historyItem)
    
    // Add to command cache for auto-complete
    if (!commandCache.value.includes(command)) {
      commandCache.value.push(command)
    }
    
    // Clear input
    currentCommand.value = ''
    historyIndex.value = -1
    showSuggestions.value = false
    
  } catch (error) {
    console.error('Failed to send command:', error)
    toast.error('命令发送失败')
  } finally {
    loading.value = false
  }
}

const handleKeyDown = (event: KeyboardEvent) => {
  switch (event.key) {
    case 'ArrowUp':
      event.preventDefault()
      if (showSuggestions.value && suggestions.value.length > 0) {
        selectedSuggestion.value = Math.max(0, selectedSuggestion.value - 1)
      } else {
        navigateHistory(-1)
      }
      break
      
    case 'ArrowDown':
      event.preventDefault()
      if (showSuggestions.value && suggestions.value.length > 0) {
        selectedSuggestion.value = Math.min(suggestions.value.length - 1, selectedSuggestion.value + 1)
      } else {
        navigateHistory(1)
      }
      break
      
    case 'Tab':
      event.preventDefault()
      if (showSuggestions.value && suggestions.value.length > 0) {
        selectSuggestion(suggestions.value[selectedSuggestion.value])
      }
      break
      
    case 'Enter':
      if (showSuggestions.value && suggestions.value.length > 0) {
        event.preventDefault()
        selectSuggestion(suggestions.value[selectedSuggestion.value])
      }
      break
      
    case 'Escape':
      showSuggestions.value = false
      break
  }
}

const navigateHistory = (direction: number) => {
  const history = commandHistory.value.map(h => h.command)
  if (history.length === 0) return
  
  historyIndex.value = Math.max(-1, Math.min(history.length - 1, historyIndex.value + direction))
  
  if (historyIndex.value >= 0) {
    currentCommand.value = history[history.length - 1 - historyIndex.value]
  } else {
    currentCommand.value = ''
  }
}

const selectSuggestion = (suggestion: string) => {
  currentCommand.value = suggestion
  showSuggestions.value = false
  selectedSuggestion.value = 0
  commandInput.value?.focus()
}

const repeatCommand = (command: string) => {
  currentCommand.value = command
  commandInput.value?.focus()
}

const handleConsoleMessage = (message: ConsoleMessage) => {
  messages.value.push(message)
  
  // Keep only last 1000 messages
  if (messages.value.length > 1000) {
    messages.value = messages.value.slice(-1000)
  }
  
  scrollToBottom()
}

const handleWebSocketConnect = () => {
  isConnected.value = true
  toast.success('控制台连接成功')
}

const handleWebSocketDisconnect = () => {
  isConnected.value = false
  toast.warning('控制台连接断开')
}

const handleWebSocketError = (error: Error) => {
  isConnected.value = false
  toast.error(`控制台连接错误: ${error.message}`)
}

// Watch for command input changes to show suggestions
watch(currentCommand, (newValue) => {
  showSuggestions.value = newValue.trim().length > 0 && suggestions.value.length > 0
  selectedSuggestion.value = 0
})

onMounted(() => {
  // Connect to console WebSocket
  websocketService.connectConsole()
  
  // Subscribe to all log types
  websocketService.subscribeToLogs()
  
  // Set up WebSocket event listeners
  websocketService.on('connect', handleWebSocketConnect)
  websocketService.on('disconnect', handleWebSocketDisconnect)
  websocketService.on('error', handleWebSocketError)
  websocketService.on('console_message', handleConsoleMessage)
  
  // Focus command input
  nextTick(() => {
    commandInput.value?.focus()
  })
})

onUnmounted(() => {
  // Clean up WebSocket listeners
  websocketService.off('connect', handleWebSocketConnect)
  websocketService.off('disconnect', handleWebSocketDisconnect)
  websocketService.off('error', handleWebSocketError)
  websocketService.off('console_message', handleConsoleMessage)
  
  // Unsubscribe from logs
  websocketService.unsubscribeFromLogs()
})
</script>