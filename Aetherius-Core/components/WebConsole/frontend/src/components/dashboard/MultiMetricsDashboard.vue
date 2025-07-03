<template>
  <div class="multi-metrics-dashboard">
    <!-- Dashboard Header -->
    <div class="dashboard-header">
      <div class="header-content">
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
          高级性能监控仪表板
        </h2>
        <p class="text-gray-600 dark:text-gray-400 mt-1">
          实时多维度服务器性能监控和分析
        </p>
      </div>
      
      <div class="header-controls">
        <!-- Auto Refresh Toggle -->
        <label class="flex items-center space-x-2">
          <input
            v-model="autoRefresh"
            type="checkbox"
            class="form-checkbox h-4 w-4 text-blue-600"
          />
          <span class="text-sm text-gray-700 dark:text-gray-300">自动刷新</span>
        </label>
        
        <!-- Refresh Interval -->
        <select 
          v-model="refreshInterval" 
          :disabled="!autoRefresh"
          class="form-select text-sm"
        >
          <option :value="15000">15秒</option>
          <option :value="30000">30秒</option>
          <option :value="60000">1分钟</option>
          <option :value="300000">5分钟</option>
        </select>
        
        <!-- Manual Refresh -->
        <button 
          @click="refreshAllData"
          :disabled="loading"
          class="btn btn-primary"
        >
          <ArrowPathIcon 
            class="w-4 h-4" 
            :class="{ 'animate-spin': loading }"
          />
          刷新
        </button>
      </div>
    </div>
    
    <!-- Quick Stats Cards -->
    <div class="quick-stats">
      <div class="stats-grid">
        <div 
          v-for="stat in quickStats" 
          :key="stat.key"
          class="stat-card"
          :class="stat.alertLevel"
        >
          <div class="stat-icon">
            <component :is="stat.icon" class="w-6 h-6" />
          </div>
          <div class="stat-content">
            <div class="stat-label">{{ stat.label }}</div>
            <div class="stat-value">{{ stat.value }}</div>
            <div v-if="stat.change" class="stat-change" :class="stat.changeType">
              <component :is="stat.changeIcon" class="w-4 h-4" />
              {{ stat.change }}
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Charts Grid -->
    <div class="charts-container">
      <!-- System Performance Row -->
      <div class="chart-row">
        <div class="chart-section">
          <AdvancedMetricsChart
            title="CPU使用率"
            description="系统CPU使用情况和负载"
            :metrics="['cpu_percent']"
            :height="280"
            :auto-refresh="autoRefresh"
            :refresh-interval="refreshInterval"
            chart-type="area"
            show-stats
            @data-update="onDataUpdate('cpu', $event)"
            @error="onChartError"
          />
        </div>
        
        <div class="chart-section">
          <AdvancedMetricsChart
            title="内存使用"
            description="系统内存使用情况"
            :metrics="['memory_percent']"
            :height="280"
            :auto-refresh="autoRefresh"
            :refresh-interval="refreshInterval"
            chart-type="area"
            show-stats
            @data-update="onDataUpdate('memory', $event)"
            @error="onChartError"
          />
        </div>
      </div>
      
      <!-- Server Performance Row -->
      <div class="chart-row">
        <div class="chart-section">
          <AdvancedMetricsChart
            title="TPS监控"
            description="服务器tick性能"
            :metrics="['tps', 'mspt']"
            :height="280"
            :auto-refresh="autoRefresh"
            :refresh-interval="refreshInterval"
            chart-type="line"
            show-stats
            @data-update="onDataUpdate('tps', $event)"
            @error="onChartError"
          />
        </div>
        
        <div class="chart-section">
          <AdvancedMetricsChart
            title="JVM内存"
            description="Java虚拟机内存使用"
            :metrics="['heap_memory']"
            :height="280"
            :auto-refresh="autoRefresh"
            :refresh-interval="refreshInterval"
            chart-type="area"
            show-stats
            @data-update="onDataUpdate('jvm', $event)"
            @error="onChartError"
          />
        </div>
      </div>
      
      <!-- Network and Storage Row -->
      <div class="chart-row">
        <div class="chart-section">
          <AdvancedMetricsChart
            title="网络流量"
            description="网络I/O统计"
            :metrics="['network_bytes_sent', 'network_bytes_recv']"
            :height="280"
            :auto-refresh="autoRefresh"
            :refresh-interval="refreshInterval"
            chart-type="line"
            @data-update="onDataUpdate('network', $event)"
            @error="onChartError"
          />
        </div>
        
        <div class="chart-section">
          <AdvancedMetricsChart
            title="磁盘使用"
            description="磁盘空间和I/O"
            :metrics="['disk_percent']"
            :height="280"
            :auto-refresh="autoRefresh"
            :refresh-interval="refreshInterval"
            chart-type="bar"
            show-stats
            @data-update="onDataUpdate('disk', $event)"
            @error="onChartError"
          />
        </div>
      </div>
      
      <!-- Performance Comparison Chart -->
      <div class="chart-full-width">
        <AdvancedMetricsChart
          title="性能对比分析"
          description="多维度性能指标对比（标准化显示）"
          :metrics="['cpu_percent', 'memory_percent', 'tps']"
          :height="320"
          :auto-refresh="autoRefresh"
          :refresh-interval="refreshInterval"
          chart-type="line"
          show-legend
          time-range="6h"
          @data-update="onDataUpdate('comparison', $event)"
          @error="onChartError"
        />
      </div>
    </div>
    
    <!-- Performance Alerts -->
    <div v-if="alerts.length > 0" class="alerts-section">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        性能警报
      </h3>
      <div class="alerts-list">
        <div 
          v-for="alert in alerts" 
          :key="alert.id"
          class="alert-item"
          :class="alert.severity"
        >
          <div class="alert-icon">
            <ExclamationTriangleIcon v-if="alert.severity === 'warning'" class="w-5 h-5" />
            <ExclamationCircleIcon v-else-if="alert.severity === 'error'" class="w-5 h-5" />
            <InformationCircleIcon v-else class="w-5 h-5" />
          </div>
          <div class="alert-content">
            <div class="alert-title">{{ alert.title }}</div>
            <div class="alert-message">{{ alert.message }}</div>
            <div class="alert-time">{{ formatTime(alert.timestamp) }}</div>
          </div>
          <button 
            @click="dismissAlert(alert.id)"
            class="alert-dismiss"
          >
            <XMarkIcon class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
    
    <!-- Performance Recommendations -->
    <div class="recommendations-section">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        性能建议
      </h3>
      <div class="recommendations-list">
        <div 
          v-for="(recommendation, index) in recommendations"
          :key="index"
          class="recommendation-item"
        >
          <LightBulbIcon class="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
          <span class="text-sm text-gray-700 dark:text-gray-300">{{ recommendation }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import {
  ArrowPathIcon,
  CpuChipIcon,
  CircleStackIcon,
  ClockIcon,
  ServerIcon,
  ExclamationTriangleIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
  XMarkIcon,
  LightBulbIcon,
  ArrowUpIcon,
  ArrowDownIcon
} from '@heroicons/vue/24/outline'
import AdvancedMetricsChart from '../charts/AdvancedMetricsChart.vue'
import { apiClient } from '@/services/api'

interface Alert {
  id: string
  title: string
  message: string
  severity: 'info' | 'warning' | 'error'
  timestamp: string
}

interface QuickStat {
  key: string
  label: string
  value: string
  icon: any
  alertLevel?: string
  change?: string
  changeType?: 'positive' | 'negative'
  changeIcon?: any
}

// Reactive state
const loading = ref(false)
const autoRefresh = ref(true)
const refreshInterval = ref(30000)
const chartData = ref<Record<string, any>>({})
const alerts = ref<Alert[]>([])
const recommendations = ref<string[]>([])

let refreshTimer: NodeJS.Timeout | null = null

// Quick stats computed from chart data
const quickStats = computed<QuickStat[]>(() => {
  const stats: QuickStat[] = [
    {
      key: 'cpu',
      label: 'CPU使用率',
      value: formatValue(chartData.value.cpu?.latest?.cpu_percent, '%'),
      icon: CpuChipIcon,
      alertLevel: getAlertLevel(chartData.value.cpu?.latest?.cpu_percent, 80, 90),
      change: '较昨日 +2.3%',
      changeType: 'negative',
      changeIcon: ArrowUpIcon
    },
    {
      key: 'memory',
      label: '内存使用',
      value: formatValue(chartData.value.memory?.latest?.memory_percent, '%'),
      icon: CircleStackIcon,
      alertLevel: getAlertLevel(chartData.value.memory?.latest?.memory_percent, 75, 85),
      change: '较昨日 -1.1%',
      changeType: 'positive',
      changeIcon: ArrowDownIcon
    },
    {
      key: 'tps',
      label: '当前TPS',
      value: formatValue(chartData.value.tps?.latest?.tps, ''),
      icon: ClockIcon,
      alertLevel: getAlertLevel(20 - (chartData.value.tps?.latest?.tps || 20), 1, 5),
      change: '较昨日 +0.2',
      changeType: 'positive',
      changeIcon: ArrowUpIcon
    },
    {
      key: 'uptime',
      label: '运行时间',
      value: '2天 14小时',
      icon: ServerIcon,
      alertLevel: 'normal'
    }
  ]
  
  return stats
})

// Helper functions
const formatValue = (value: number | undefined, unit: string): string => {
  if (value === undefined || isNaN(value)) return 'N/A'
  
  if (unit === '%') {
    return `${value.toFixed(1)}%`
  } else if (unit === 'MB') {
    return `${value.toFixed(1)} MB`
  } else {
    return value.toFixed(2)
  }
}

const getAlertLevel = (value: number | undefined, warningThreshold: number, errorThreshold: number): string => {
  if (value === undefined || isNaN(value)) return 'normal'
  
  if (value >= errorThreshold) return 'error'
  if (value >= warningThreshold) return 'warning'
  return 'normal'
}

const formatTime = (timestamp: string): string => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

// Event handlers
const onDataUpdate = (chartType: string, data: any) => {
  chartData.value[chartType] = {
    data,
    latest: extractLatestValues(data),
    timestamp: new Date().toISOString()
  }
  
  // Check for performance alerts
  checkPerformanceAlerts()
}

const onChartError = (error: string) => {
  console.error('Chart error:', error)
  // Add error alert
  addAlert('图表错误', error, 'error')
}

const extractLatestValues = (data: any): Record<string, number> => {
  const latest: Record<string, number> = {}
  
  if (data?.datasets) {
    data.datasets.forEach((dataset: any) => {
      const values = dataset.data as number[]
      if (values.length > 0) {
        const metricName = dataset.label.toLowerCase().replace(/[^a-z]/g, '_')
        latest[metricName] = values[values.length - 1]
      }
    })
  }
  
  return latest
}

const checkPerformanceAlerts = () => {
  const cpu = chartData.value.cpu?.latest?.cpu_percent
  const memory = chartData.value.memory?.latest?.memory_percent
  const tps = chartData.value.tps?.latest?.tps
  
  // CPU alert
  if (cpu && cpu > 90) {
    addAlert(
      'CPU使用率过高',
      `当前CPU使用率为 ${cpu.toFixed(1)}%，建议检查系统负载`,
      'error'
    )
  } else if (cpu && cpu > 80) {
    addAlert(
      'CPU使用率偏高',
      `当前CPU使用率为 ${cpu.toFixed(1)}%，请注意监控`,
      'warning'
    )
  }
  
  // Memory alert
  if (memory && memory > 85) {
    addAlert(
      '内存使用率过高',
      `当前内存使用率为 ${memory.toFixed(1)}%，可能需要释放内存`,
      'error'
    )
  }
  
  // TPS alert
  if (tps && tps < 15) {
    addAlert(
      'TPS过低',
      `当前TPS为 ${tps.toFixed(1)}，服务器性能可能受到影响`,
      'warning'
    )
  }
}

const addAlert = (title: string, message: string, severity: 'info' | 'warning' | 'error') => {
  const alert: Alert = {
    id: Date.now().toString(),
    title,
    message,
    severity,
    timestamp: new Date().toISOString()
  }
  
  // Check if similar alert already exists
  const exists = alerts.value.some(a => a.title === title && a.severity === severity)
  if (!exists) {
    alerts.value.unshift(alert)
    
    // Keep only last 10 alerts
    if (alerts.value.length > 10) {
      alerts.value = alerts.value.slice(0, 10)
    }
  }
}

const dismissAlert = (alertId: string) => {
  const index = alerts.value.findIndex(a => a.id === alertId)
  if (index !== -1) {
    alerts.value.splice(index, 1)
  }
}

const refreshAllData = () => {
  loading.value = true
  // Charts will refresh themselves through their auto-refresh mechanism
  setTimeout(() => {
    loading.value = false
  }, 1000)
}

const loadRecommendations = async () => {
  try {
    const response = await apiClient.post('/enhanced-monitoring/performance/analyze')
    recommendations.value = response.data.analysis?.recommendations || []
  } catch (error) {
    console.error('Failed to load recommendations:', error)
  }
}

const setupAutoRefresh = () => {
  if (autoRefresh.value && refreshInterval.value > 0) {
    refreshTimer = setInterval(() => {
      loadRecommendations()
    }, refreshInterval.value)
  }
}

const clearAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// Watch for auto refresh changes
watch([autoRefresh, refreshInterval], () => {
  clearAutoRefresh()
  setupAutoRefresh()
})

// Lifecycle
onMounted(() => {
  loadRecommendations()
  setupAutoRefresh()
})

onUnmounted(() => {
  clearAutoRefresh()
})
</script>

<style scoped>
.multi-metrics-dashboard {
  @apply space-y-6;
}

.dashboard-header {
  @apply flex items-start justify-between mb-6;
}

.header-content h2 {
  @apply mb-1;
}

.header-controls {
  @apply flex items-center space-x-4;
}

.form-checkbox {
  @apply rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500;
}

.form-select {
  @apply bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500;
}

.quick-stats {
  @apply mb-6;
}

.stats-grid {
  @apply grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4;
}

.stat-card {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm border p-4 flex items-center space-x-3;
}

.stat-card.warning {
  @apply border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/20;
}

.stat-card.error {
  @apply border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20;
}

.stat-icon {
  @apply flex-shrink-0 p-2 rounded-lg bg-gray-100 dark:bg-gray-700;
}

.stat-content {
  @apply flex-1 min-w-0;
}

.stat-label {
  @apply text-sm text-gray-500 dark:text-gray-400;
}

.stat-value {
  @apply text-lg font-semibold text-gray-900 dark:text-white;
}

.stat-change {
  @apply flex items-center space-x-1 text-xs;
}

.stat-change.positive {
  @apply text-green-600 dark:text-green-400;
}

.stat-change.negative {
  @apply text-red-600 dark:text-red-400;
}

.charts-container {
  @apply space-y-6;
}

.chart-row {
  @apply grid grid-cols-1 lg:grid-cols-2 gap-6;
}

.chart-section {
  @apply flex-1;
}

.chart-full-width {
  @apply w-full;
}

.alerts-section {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6;
}

.alerts-list {
  @apply space-y-3;
}

.alert-item {
  @apply flex items-start space-x-3 p-3 rounded-lg border;
}

.alert-item.info {
  @apply border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20;
}

.alert-item.warning {
  @apply border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/20;
}

.alert-item.error {
  @apply border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20;
}

.alert-icon {
  @apply flex-shrink-0;
}

.alert-content {
  @apply flex-1 min-w-0;
}

.alert-title {
  @apply font-medium text-gray-900 dark:text-white text-sm;
}

.alert-message {
  @apply text-gray-600 dark:text-gray-400 text-sm mt-1;
}

.alert-time {
  @apply text-gray-500 dark:text-gray-500 text-xs mt-1;
}

.alert-dismiss {
  @apply flex-shrink-0 p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded;
}

.recommendations-section {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6;
}

.recommendations-list {
  @apply space-y-3;
}

.recommendation-item {
  @apply flex items-start space-x-3;
}
</style>