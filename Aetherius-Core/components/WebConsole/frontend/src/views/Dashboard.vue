<template>
  <div class="space-y-6">
    <!-- Quick Stats -->
    <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
      <div class="card p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <UsersIcon class="h-8 w-8 text-blue-600 dark:text-blue-400" />
          </div>
          <div class="ml-5 w-0 flex-1">
            <dl>
              <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">在线玩家</dt>
              <dd class="text-lg font-medium text-gray-900 dark:text-white">
                {{ serverStore.playerCount }}/{{ serverStore.maxPlayers }}
              </dd>
            </dl>
          </div>
        </div>
      </div>

      <div class="card p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <CpuChipIcon class="h-8 w-8 text-green-600 dark:text-green-400" />
          </div>
          <div class="ml-5 w-0 flex-1">
            <dl>
              <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">CPU使用率</dt>
              <dd class="text-lg font-medium text-gray-900 dark:text-white">
                {{ serverStore.cpuUsage?.toFixed(1) }}%
              </dd>
            </dl>
          </div>
        </div>
      </div>

      <div class="card p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <CircleStackIcon class="h-8 w-8 text-purple-600 dark:text-purple-400" />
          </div>
          <div class="ml-5 w-0 flex-1">
            <dl>
              <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">内存使用</dt>
              <dd class="text-lg font-medium text-gray-900 dark:text-white">
                {{ formatBytes(serverStore.memoryUsage?.used || 0) }}
              </dd>
            </dl>
          </div>
        </div>
      </div>

      <div class="card p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div class="w-8 h-8 rounded-full flex items-center justify-center" :class="serverStatusColor">
              <div class="w-4 h-4 rounded-full bg-white"></div>
            </div>
          </div>
          <div class="ml-5 w-0 flex-1">
            <dl>
              <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">服务器状态</dt>
              <dd class="text-lg font-medium text-gray-900 dark:text-white">
                {{ serverStatusText }}
              </dd>
            </dl>
          </div>
        </div>
      </div>
    </div>

    <!-- Server Controls -->
    <div class="card p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">服务器控制</h3>
        <div class="flex space-x-3">
          <button
            @click="serverStore.startServer()"
            :disabled="serverStore.loading || serverStore.isOnline"
            class="btn btn-primary"
          >
            <PlayIcon class="w-4 h-4 mr-2" />
            启动
          </button>
          <button
            @click="serverStore.stopServer()"
            :disabled="serverStore.loading || !serverStore.isOnline"
            class="btn btn-secondary"
          >
            <StopIcon class="w-4 h-4 mr-2" />
            停止
          </button>
          <button
            @click="serverStore.restartServer()"
            :disabled="serverStore.loading || !serverStore.isOnline"
            class="btn btn-secondary"
          >
            <ArrowPathIcon class="w-4 h-4 mr-2" />
            重启
          </button>
        </div>
      </div>
      
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Server Info -->
        <div>
          <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-3">服务器信息</h4>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-500 dark:text-gray-400">版本:</span>
              <span class="text-gray-900 dark:text-white">{{ serverStore.status?.version }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500 dark:text-gray-400">运行时间:</span>
              <span class="text-gray-900 dark:text-white">{{ formatUptime(serverStore.status?.uptime) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500 dark:text-gray-400">MOTD:</span>
              <span class="text-gray-900 dark:text-white">{{ serverStore.status?.motd }}</span>
            </div>
          </div>
        </div>

        <!-- Resource Usage -->
        <div>
          <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-3">资源使用</h4>
          <div class="space-y-3">
            <!-- Memory -->
            <div>
              <div class="flex justify-between text-sm mb-1">
                <span class="text-gray-500 dark:text-gray-400">内存</span>
                <span class="text-gray-900 dark:text-white">
                  {{ formatBytes(serverStore.memoryUsage?.used || 0) }} / {{ formatBytes(serverStore.memoryUsage?.max || 0) }}
                </span>
              </div>
              <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  class="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  :style="{ width: `${serverStore.memoryUsage?.percentage || 0}%` }"
                ></div>
              </div>
            </div>

            <!-- Disk -->
            <div>
              <div class="flex justify-between text-sm mb-1">
                <span class="text-gray-500 dark:text-gray-400">磁盘</span>
                <span class="text-gray-900 dark:text-white">
                  {{ formatBytes(serverStore.diskUsage?.used || 0) }} / {{ formatBytes(serverStore.diskUsage?.total || 0) }}
                </span>
              </div>
              <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  class="bg-green-600 h-2 rounded-full transition-all duration-300"
                  :style="{ width: `${serverStore.diskUsage?.percentage || 0}%` }"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Enhanced Performance Monitoring -->
    <div class="card p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">性能监控</h3>
        <div class="flex space-x-2">
          <button
            @click="showBasicChart = !showBasicChart"
            class="btn btn-sm btn-secondary"
            :class="{ 'btn-primary': showBasicChart }"
          >
            基础图表
          </button>
          <button
            @click="showAdvancedDashboard = !showAdvancedDashboard"
            class="btn btn-sm btn-secondary"
            :class="{ 'btn-primary': showAdvancedDashboard }"
          >
            高级监控
          </button>
        </div>
      </div>
      
      <!-- Basic Chart View -->
      <div v-if="showBasicChart" class="h-64">
        <Line
          v-if="chartData"
          :data="chartData"
          :options="chartOptions"
          class="w-full h-full"
        />
        <div v-else class="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
          加载中...
        </div>
      </div>
      
      <!-- Advanced Dashboard View -->
      <div v-if="showAdvancedDashboard" class="mt-4">
        <MultiMetricsDashboard />
      </div>
    </div>

    <!-- Recent Activities -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Online Players -->
      <div class="card p-6">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">在线玩家</h3>
        <div v-if="serverStore.onlinePlayers.length === 0" class="text-center py-8">
          <UsersIcon class="w-12 h-12 mx-auto text-gray-400 dark:text-gray-600" />
          <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">暂无在线玩家</p>
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="player in serverStore.onlinePlayers.slice(0, 5)"
            :key="player.uuid"
            class="flex items-center space-x-3"
          >
            <img
              :src="`https://crafthead.net/avatar/${player.uuid}/32`"
              :alt="player.username"
              class="w-8 h-8 rounded-lg"
            />
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-900 dark:text-white">{{ player.username }}</p>
              <p class="text-xs text-gray-500 dark:text-gray-400">{{ player.location?.world }}</p>
            </div>
          </div>
          <div v-if="serverStore.onlinePlayers.length > 5" class="text-center">
            <router-link
              to="/players"
              class="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
            >
              查看全部 {{ serverStore.onlinePlayers.length }} 个玩家
            </router-link>
          </div>
        </div>
      </div>

      <!-- System Info -->
      <div class="card p-6">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">系统信息</h3>
        <div class="space-y-3 text-sm">
          <div class="flex justify-between">
            <span class="text-gray-500 dark:text-gray-400">Java版本:</span>
            <span class="text-gray-900 dark:text-white">OpenJDK 17.0.2</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500 dark:text-gray-400">操作系统:</span>
            <span class="text-gray-900 dark:text-white">Linux Ubuntu 22.04</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500 dark:text-gray-400">可用内存:</span>
            <span class="text-gray-900 dark:text-white">8.00 GB</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500 dark:text-gray-400">CPU核心:</span>
            <span class="text-gray-900 dark:text-white">4 cores</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  UsersIcon,
  CpuChipIcon,
  CircleStackIcon,
  PlayIcon,
  StopIcon,
  ArrowPathIcon
} from '@heroicons/vue/24/outline'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { useServerStore } from '@/stores/server'
import { useThemeStore } from '@/stores/theme'
import MultiMetricsDashboard from '@/components/dashboard/MultiMetricsDashboard.vue'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const serverStore = useServerStore()
const themeStore = useThemeStore()

const chartData = ref(null)
const showBasicChart = ref(true)
const showAdvancedDashboard = ref(false)

const serverStatusColor = computed(() => {
  switch (serverStore.status?.status) {
    case 'online':
      return 'bg-green-500'
    case 'offline':
      return 'bg-red-500'
    case 'starting':
    case 'stopping':
      return 'bg-yellow-500'
    default:
      return 'bg-gray-500'
  }
})

const serverStatusText = computed(() => {
  const status = serverStore.status?.status
  switch (status) {
    case 'online':
      return '在线'
    case 'offline':
      return '离线'
    case 'starting':
      return '启动中'
    case 'stopping':
      return '关闭中'
    default:
      return '未知'
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
      labels: {
        color: themeStore.isDark ? '#e5e7eb' : '#374151',
        usePointStyle: true,
        pointStyle: 'circle'
      }
    },
    tooltip: {
      mode: 'index' as const,
      intersect: false,
      backgroundColor: themeStore.isDark ? '#374151' : '#ffffff',
      titleColor: themeStore.isDark ? '#f9fafb' : '#111827',
      bodyColor: themeStore.isDark ? '#e5e7eb' : '#374151',
      borderColor: themeStore.isDark ? '#6b7280' : '#d1d5db',
      borderWidth: 1
    }
  },
  scales: {
    x: {
      grid: {
        color: themeStore.isDark ? '#374151' : '#f3f4f6'
      },
      ticks: {
        color: themeStore.isDark ? '#9ca3af' : '#6b7280'
      }
    },
    y: {
      beginAtZero: true,
      max: 100,
      grid: {
        color: themeStore.isDark ? '#374151' : '#f3f4f6'
      },
      ticks: {
        color: themeStore.isDark ? '#9ca3af' : '#6b7280',
        callback: function(value: any) {
          return value + '%'
        }
      }
    }
  },
  interaction: {
    mode: 'nearest' as const,
    axis: 'x' as const,
    intersect: false
  },
  elements: {
    point: {
      radius: 3,
      hoverRadius: 6
    },
    line: {
      tension: 0.3
    }
  }
}))

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatUptime = (seconds: number | undefined): string => {
  if (!seconds) return '0秒'
  
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (days > 0) {
    return `${days}天 ${hours}小时`
  } else if (hours > 0) {
    return `${hours}小时 ${minutes}分钟`
  } else {
    return `${minutes}分钟`
  }
}

const updateChartData = () => {
  const metrics = serverStore.metrics
  if (metrics.length === 0) return

  const labels = metrics.map(m => {
    const date = new Date(m.timestamp)
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  })

  chartData.value = {
    labels,
    datasets: [
      {
        label: 'CPU使用率',
        data: metrics.map(m => m.cpu_usage),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true
      },
      {
        label: '内存使用率',
        data: metrics.map(m => m.memory_usage),
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: true
      }
    ]
  }
}

let updateInterval: NodeJS.Timeout

onMounted(async () => {
  // Load initial data
  await Promise.all([
    serverStore.fetchServerStatus(),
    serverStore.fetchOnlinePlayers(),
    serverStore.fetchMetrics('1h')
  ])

  updateChartData()

  // Set up periodic updates
  updateInterval = setInterval(async () => {
    await Promise.all([
      serverStore.fetchServerStatus(),
      serverStore.fetchOnlinePlayers(),
      serverStore.fetchMetrics('1h')
    ])
    updateChartData()
  }, 30000) // Update every 30 seconds
})

onUnmounted(() => {
  if (updateInterval) {
    clearInterval(updateInterval)
  }
})
</script>