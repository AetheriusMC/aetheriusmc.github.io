<template>
  <div class="performance-baseline">
    <!-- Header -->
    <div class="baseline-header">
      <div class="header-content">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">
          性能基线监控
        </h2>
        <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
          监控关键指标偏离正常基线的情况
        </p>
      </div>
      
      <div class="header-actions">
        <button 
          @click="refreshData"
          :disabled="loading"
          class="btn btn-secondary"
        >
          <ArrowPathIcon 
            class="w-4 h-4 mr-2" 
            :class="{ 'animate-spin': loading }"
          />
          刷新数据
        </button>
        <button 
          @click="showConfigModal = true"
          class="btn btn-primary"
        >
          <CogIcon class="w-4 h-4 mr-2" />
          配置基线
        </button>
      </div>
    </div>
    
    <!-- Baseline Overview -->
    <div class="baseline-overview">
      <div class="overview-stats">
        <div class="stat-card">
          <div class="stat-icon normal">
            <CheckCircleIcon class="w-6 h-6" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ normalCount }}</div>
            <div class="stat-label">正常指标</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon warning">
            <ExclamationTriangleIcon class="w-6 h-6" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ warningCount }}</div>
            <div class="stat-label">偏离基线</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon error">
            <ExclamationCircleIcon class="w-6 h-6" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ errorCount }}</div>
            <div class="stat-label">严重偏离</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon disabled">
            <EyeSlashIcon class="w-6 h-6" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ disabledCount }}</div>
            <div class="stat-label">已禁用</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Baseline Metrics Grid -->
    <div class="metrics-grid">
      <div
        v-for="metric in baselineMetrics"
        :key="metric.metric_name"
        class="metric-card"
        :class="getMetricStatusClass(metric)"
      >
        <!-- Metric Header -->
        <div class="metric-header">
          <div class="metric-info">
            <h3 class="metric-title">{{ getMetricDisplayName(metric.metric_name) }}</h3>
            <div class="metric-status">
              <div class="status-indicator" :class="getMetricStatus(metric)">
                <div class="status-dot"></div>
                <span class="status-text">{{ getMetricStatusText(metric) }}</span>
              </div>
            </div>
          </div>
          
          <div class="metric-controls">
            <button 
              @click="toggleMetric(metric)"
              class="control-btn"
              :title="metric.enabled ? '禁用监控' : '启用监控'"
            >
              <EyeIcon v-if="metric.enabled" class="w-4 h-4" />
              <EyeSlashIcon v-else class="w-4 h-4" />
            </button>
            <button 
              @click="configureMetric(metric)"
              class="control-btn"
              title="配置基线"
            >
              <CogIcon class="w-4 h-4" />
            </button>
          </div>
        </div>
        
        <!-- Current vs Baseline -->
        <div class="metric-comparison">
          <div class="current-value">
            <label class="value-label">当前值</label>
            <div class="value-display">
              <span class="value">{{ formatMetricValue(metric.current_value, metric.metric_name) }}</span>
              <div v-if="metric.deviation" class="deviation" :class="getDeviationClass(metric.deviation)">
                <component :is="getDeviationIcon(metric.deviation)" class="w-3 h-3" />
                {{ Math.abs(metric.deviation).toFixed(1) }}%
              </div>
            </div>
          </div>
          
          <div class="baseline-value">
            <label class="value-label">基线值</label>
            <div class="value-display">
              <span class="value">{{ formatMetricValue(metric.baseline_value, metric.metric_name) }}</span>
              <span class="tolerance">±{{ metric.tolerance_percent }}%</span>
            </div>
          </div>
        </div>
        
        <!-- Baseline Chart -->
        <div class="metric-chart">
          <canvas 
            :ref="el => chartRefs[metric.metric_name] = el"
            class="baseline-chart-canvas"
            :data-metric="metric.metric_name"
          ></canvas>
        </div>
        
        <!-- Metric Details -->
        <div class="metric-details">
          <div class="detail-item">
            <span class="detail-label">测量窗口:</span>
            <span class="detail-value">{{ metric.measurement_window }}秒</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">上次更新:</span>
            <span class="detail-value">{{ formatRelativeTime(metric.last_updated) }}</span>
          </div>
          <div v-if="metric.anomaly_detected" class="detail-item anomaly">
            <span class="detail-label">异常检测:</span>
            <span class="detail-value">{{ metric.anomaly_description }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Anomaly History -->
    <div class="anomaly-history">
      <div class="section-header">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">
          异常历史
        </h3>
        <select v-model="historyFilter" class="form-select text-sm">
          <option value="24h">最近24小时</option>
          <option value="7d">最近7天</option>
          <option value="30d">最近30天</option>
        </select>
      </div>
      
      <div class="history-timeline">
        <div
          v-for="anomaly in anomalyHistory"
          :key="anomaly.id"
          class="timeline-item"
          :class="anomaly.severity"
        >
          <div class="timeline-marker"></div>
          <div class="timeline-content">
            <div class="anomaly-title">{{ anomaly.metric_name }} - {{ anomaly.title }}</div>
            <div class="anomaly-description">{{ anomaly.description }}</div>
            <div class="anomaly-meta">
              <span class="anomaly-time">{{ formatTime(anomaly.timestamp) }}</span>
              <span class="anomaly-duration">持续 {{ anomaly.duration }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Baseline Configuration Modal -->
    <BaselineConfigModal
      v-if="showConfigModal"
      :metric="configMetric"
      @save="saveBaselineConfig"
      @close="closeConfigModal"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import {
  ArrowPathIcon,
  CogIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ExclamationCircleIcon,
  EyeIcon,
  EyeSlashIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  MinusIcon
} from '@heroicons/vue/24/outline'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  type Chart
} from 'chart.js'
import BaselineConfigModal from './BaselineConfigModal.vue'
import { apiClient } from '@/services/api'
import { useThemeStore } from '@/stores/theme'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

interface BaselineMetric {
  metric_name: string
  baseline_value: number
  tolerance_percent: number
  measurement_window: number
  enabled: boolean
  current_value?: number
  deviation?: number
  last_updated?: string
  anomaly_detected?: boolean
  anomaly_description?: string
}

interface Anomaly {
  id: string
  metric_name: string
  title: string
  description: string
  severity: 'warning' | 'error'
  timestamp: string
  duration: string
}

const themeStore = useThemeStore()

// State
const baselineMetrics = ref<BaselineMetric[]>([])
const anomalyHistory = ref<Anomaly[]>([])
const loading = ref(false)
const historyFilter = ref('24h')
const showConfigModal = ref(false)
const configMetric = ref<BaselineMetric | null>(null)

// Chart management
const chartRefs = ref<Record<string, HTMLCanvasElement>>({})
const chartInstances = ref<Record<string, Chart>>({})

// Computed stats
const normalCount = computed(() => 
  baselineMetrics.value.filter(m => m.enabled && getMetricStatus(m) === 'normal').length
)

const warningCount = computed(() => 
  baselineMetrics.value.filter(m => m.enabled && getMetricStatus(m) === 'warning').length
)

const errorCount = computed(() => 
  baselineMetrics.value.filter(m => m.enabled && getMetricStatus(m) === 'error').length
)

const disabledCount = computed(() => 
  baselineMetrics.value.filter(m => !m.enabled).length
)

// Methods
const loadBaselines = async () => {
  try {
    const response = await apiClient.get('/enhanced-monitoring/performance/baseline')
    baselineMetrics.value = response.data.map((metric: any) => ({
      ...metric,
      current_value: Math.random() * 100, // Mock current value
      deviation: (Math.random() - 0.5) * 40, // Mock deviation
      last_updated: new Date().toISOString(),
      anomaly_detected: Math.random() > 0.8,
      anomaly_description: Math.random() > 0.8 ? '检测到异常模式' : undefined
    }))
  } catch (error) {
    console.error('Failed to load baselines:', error)
  }
}

const loadAnomalyHistory = async () => {
  try {
    // TODO: Implement API call
    // Mock data for now
    anomalyHistory.value = [
      {
        id: '1',
        metric_name: 'CPU使用率',
        title: '高CPU使用率',
        description: 'CPU使用率持续超过基线值15%以上',
        severity: 'warning',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        duration: '45分钟'
      },
      {
        id: '2',
        metric_name: 'TPS',
        title: 'TPS显著下降',
        description: 'TPS低于基线值20%以上，可能影响游戏体验',
        severity: 'error',
        timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
        duration: '12分钟'
      }
    ]
  } catch (error) {
    console.error('Failed to load anomaly history:', error)
  }
}

const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadBaselines(),
      loadAnomalyHistory()
    ])
    await nextTick()
    initializeCharts()
  } finally {
    loading.value = false
  }
}

const initializeCharts = () => {
  baselineMetrics.value.forEach(metric => {
    const canvas = chartRefs.value[metric.metric_name]
    if (canvas) {
      createMetricChart(metric, canvas)
    }
  })
}

const createMetricChart = (metric: BaselineMetric, canvas: HTMLCanvasElement) => {
  // Destroy existing chart if any
  if (chartInstances.value[metric.metric_name]) {
    chartInstances.value[metric.metric_name].destroy()
  }

  // Generate mock historical data
  const now = new Date()
  const labels = []
  const data = []
  const baselineData = []
  
  for (let i = 23; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 60 * 60 * 1000)
    labels.push(time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }))
    
    // Mock data with some variance around baseline
    const variance = (Math.random() - 0.5) * metric.tolerance_percent * 2
    const value = metric.baseline_value * (1 + variance / 100)
    data.push(value)
    baselineData.push(metric.baseline_value)
  }

  const isDark = themeStore.isDark
  
  const chart = new ChartJS(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: '实际值',
          data,
          borderColor: getMetricColor(metric),
          backgroundColor: getMetricColor(metric) + '20',
          fill: false,
          tension: 0.3
        },
        {
          label: '基线值',
          data: baselineData,
          borderColor: isDark ? '#6b7280' : '#9ca3af',
          borderDash: [5, 5],
          fill: false,
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: isDark ? '#374151' : '#ffffff',
          titleColor: isDark ? '#f9fafb' : '#111827',
          bodyColor: isDark ? '#e5e7eb' : '#374151',
          borderColor: isDark ? '#6b7280' : '#d1d5db',
          borderWidth: 1
        }
      },
      scales: {
        x: {
          display: false
        },
        y: {
          display: false,
          beginAtZero: true
        }
      },
      elements: {
        point: {
          radius: 2,
          hoverRadius: 4
        },
        line: {
          borderWidth: 2
        }
      }
    }
  })

  chartInstances.value[metric.metric_name] = chart
}

const getMetricColor = (metric: BaselineMetric): string => {
  const status = getMetricStatus(metric)
  const colors = {
    normal: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    disabled: '#6b7280'
  }
  return colors[status]
}

const getMetricStatus = (metric: BaselineMetric): 'normal' | 'warning' | 'error' | 'disabled' => {
  if (!metric.enabled) return 'disabled'
  if (!metric.deviation) return 'normal'
  
  const absDeviation = Math.abs(metric.deviation)
  if (absDeviation > metric.tolerance_percent * 1.5) return 'error'
  if (absDeviation > metric.tolerance_percent) return 'warning'
  return 'normal'
}

const getMetricStatusClass = (metric: BaselineMetric): string => {
  return getMetricStatus(metric)
}

const getMetricStatusText = (metric: BaselineMetric): string => {
  const status = getMetricStatus(metric)
  const texts = {
    normal: '正常',
    warning: '偏离基线',
    error: '严重偏离',
    disabled: '已禁用'
  }
  return texts[status]
}

const getDeviationClass = (deviation: number): string => {
  if (deviation > 0) return 'positive'
  if (deviation < 0) return 'negative'
  return 'neutral'
}

const getDeviationIcon = (deviation: number) => {
  if (deviation > 0) return ArrowUpIcon
  if (deviation < 0) return ArrowDownIcon
  return MinusIcon
}

const toggleMetric = async (metric: BaselineMetric) => {
  try {
    metric.enabled = !metric.enabled
    // TODO: Implement API call
    console.log('Toggle metric:', metric.metric_name, metric.enabled)
  } catch (error) {
    console.error('Failed to toggle metric:', error)
    // Revert on error
    metric.enabled = !metric.enabled
  }
}

const configureMetric = (metric: BaselineMetric) => {
  configMetric.value = metric
  showConfigModal.value = true
}

const saveBaselineConfig = async (config: any) => {
  try {
    if (configMetric.value) {
      Object.assign(configMetric.value, config)
      // TODO: Implement API call
      console.log('Save baseline config:', config)
    }
    closeConfigModal()
  } catch (error) {
    console.error('Failed to save baseline config:', error)
  }
}

const closeConfigModal = () => {
  showConfigModal.value = false
  configMetric.value = null
}

const getMetricDisplayName = (metric: string): string => {
  const names: Record<string, string> = {
    'cpu_percent': 'CPU使用率',
    'memory_percent': '内存使用率',
    'tps': 'TPS',
    'mspt': 'MSPT'
  }
  return names[metric] || metric
}

const formatMetricValue = (value: number | undefined, metric: string): string => {
  if (value === undefined) return 'N/A'
  
  const units: Record<string, string> = {
    'cpu_percent': '%',
    'memory_percent': '%',
    'tps': '',
    'mspt': 'ms'
  }
  
  const unit = units[metric] || ''
  return `${value.toFixed(1)}${unit}`
}

const formatRelativeTime = (timestamp: string | undefined): string => {
  if (!timestamp) return '未知'
  
  const now = new Date()
  const time = new Date(timestamp)
  const diff = now.getTime() - time.getTime()
  
  const minutes = Math.floor(diff / (1000 * 60))
  if (minutes < 60) return `${minutes}分钟前`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  
  const days = Math.floor(hours / 24)
  return `${days}天前`
}

const formatTime = (timestamp: string): string => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

// Lifecycle
onMounted(() => {
  refreshData()
})

onUnmounted(() => {
  // Destroy all chart instances
  Object.values(chartInstances.value).forEach(chart => {
    chart.destroy()
  })
})
</script>

<style scoped>
.performance-baseline {
  @apply space-y-6;
}

.baseline-header {
  @apply flex items-start justify-between;
}

.header-actions {
  @apply flex space-x-3;
}

.baseline-overview {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6;
}

.overview-stats {
  @apply grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4;
}

.stat-card {
  @apply flex items-center space-x-3 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg;
}

.stat-icon {
  @apply flex-shrink-0 p-2 rounded-lg;
}

.stat-icon.normal {
  @apply bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-400;
}

.stat-icon.warning {
  @apply bg-yellow-100 dark:bg-yellow-900 text-yellow-600 dark:text-yellow-400;
}

.stat-icon.error {
  @apply bg-red-100 dark:bg-red-900 text-red-600 dark:text-red-400;
}

.stat-icon.disabled {
  @apply bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400;
}

.stat-content {
  @apply flex-1;
}

.stat-value {
  @apply text-2xl font-bold text-gray-900 dark:text-white;
}

.stat-label {
  @apply text-sm text-gray-500 dark:text-gray-400;
}

.metrics-grid {
  @apply grid grid-cols-1 lg:grid-cols-2 gap-6;
}

.metric-card {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm border p-6 space-y-4;
}

.metric-card.normal {
  @apply border-green-200 dark:border-green-800;
}

.metric-card.warning {
  @apply border-yellow-200 dark:border-yellow-800;
}

.metric-card.error {
  @apply border-red-200 dark:border-red-800;
}

.metric-card.disabled {
  @apply border-gray-200 dark:border-gray-700 opacity-60;
}

.metric-header {
  @apply flex items-start justify-between;
}

.metric-info {
  @apply flex-1;
}

.metric-title {
  @apply text-lg font-medium text-gray-900 dark:text-white;
}

.metric-status {
  @apply mt-1;
}

.status-indicator {
  @apply flex items-center space-x-2;
}

.status-indicator.normal .status-dot {
  @apply w-2 h-2 bg-green-500 rounded-full;
}

.status-indicator.warning .status-dot {
  @apply w-2 h-2 bg-yellow-500 rounded-full;
}

.status-indicator.error .status-dot {
  @apply w-2 h-2 bg-red-500 rounded-full;
}

.status-indicator.disabled .status-dot {
  @apply w-2 h-2 bg-gray-400 rounded-full;
}

.status-text {
  @apply text-sm text-gray-600 dark:text-gray-400;
}

.metric-controls {
  @apply flex space-x-1;
}

.control-btn {
  @apply p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded;
}

.metric-comparison {
  @apply grid grid-cols-2 gap-4;
}

.current-value, .baseline-value {
  @apply text-center;
}

.value-label {
  @apply block text-xs text-gray-500 dark:text-gray-400 mb-1;
}

.value-display {
  @apply space-y-1;
}

.value {
  @apply block text-lg font-semibold text-gray-900 dark:text-white;
}

.deviation {
  @apply inline-flex items-center space-x-1 text-xs;
}

.deviation.positive {
  @apply text-red-600 dark:text-red-400;
}

.deviation.negative {
  @apply text-green-600 dark:text-green-400;
}

.deviation.neutral {
  @apply text-gray-600 dark:text-gray-400;
}

.tolerance {
  @apply text-xs text-gray-500 dark:text-gray-400;
}

.metric-chart {
  @apply h-24 relative;
}

.baseline-chart-canvas {
  @apply w-full h-full;
}

.metric-details {
  @apply space-y-2 text-sm;
}

.detail-item {
  @apply flex justify-between;
}

.detail-item.anomaly {
  @apply text-red-600 dark:text-red-400;
}

.detail-label {
  @apply text-gray-500 dark:text-gray-400;
}

.detail-value {
  @apply font-medium text-gray-900 dark:text-white;
}

.anomaly-history {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6;
}

.section-header {
  @apply flex items-center justify-between mb-4;
}

.form-select {
  @apply bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500;
}

.history-timeline {
  @apply space-y-4;
}

.timeline-item {
  @apply relative pl-8;
}

.timeline-item.warning .timeline-marker {
  @apply bg-yellow-400;
}

.timeline-item.error .timeline-marker {
  @apply bg-red-400;
}

.timeline-marker {
  @apply absolute left-0 top-2 w-3 h-3 rounded-full;
}

.timeline-content {
  @apply space-y-1;
}

.anomaly-title {
  @apply font-medium text-gray-900 dark:text-white;
}

.anomaly-description {
  @apply text-sm text-gray-600 dark:text-gray-400;
}

.anomaly-meta {
  @apply flex space-x-4 text-xs text-gray-500 dark:text-gray-400;
}
</style>