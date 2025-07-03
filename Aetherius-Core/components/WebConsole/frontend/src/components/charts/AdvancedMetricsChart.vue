<template>
  <div class="advanced-metrics-chart">
    <!-- Chart Header -->
    <div class="chart-header">
      <div class="chart-title">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          {{ title }}
        </h3>
        <p v-if="description" class="text-sm text-gray-500 dark:text-gray-400">
          {{ description }}
        </p>
      </div>
      
      <div class="chart-controls">
        <!-- Time Range Selector -->
        <select 
          v-model="selectedTimeRange" 
          @change="onTimeRangeChange"
          class="form-select text-sm"
        >
          <option value="5m">5分钟</option>
          <option value="15m">15分钟</option>
          <option value="1h">1小时</option>
          <option value="6h">6小时</option>
          <option value="24h">24小时</option>
        </select>
        
        <!-- Chart Type Selector -->
        <select 
          v-model="selectedChartType" 
          @change="onChartTypeChange"
          class="form-select text-sm ml-2"
        >
          <option value="line">线图</option>
          <option value="area">面积图</option>
          <option value="bar">柱状图</option>
        </select>
        
        <!-- Refresh Button -->
        <button 
          @click="refreshData"
          :disabled="loading"
          class="btn btn-sm btn-secondary ml-2"
        >
          <ArrowPathIcon 
            class="w-4 h-4" 
            :class="{ 'animate-spin': loading }"
          />
        </button>
      </div>
    </div>
    
    <!-- Chart Container -->
    <div class="chart-container" :style="{ height: `${height}px` }">
      <div v-if="loading" class="chart-loading">
        <div class="animate-pulse">
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-4"></div>
          <div class="h-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
      
      <div v-else-if="error" class="chart-error">
        <ExclamationTriangleIcon class="w-8 h-8 text-red-500 mx-auto mb-2" />
        <p class="text-sm text-red-600 dark:text-red-400">{{ error }}</p>
        <button @click="refreshData" class="btn btn-sm btn-primary mt-2">
          重试
        </button>
      </div>
      
      <div v-else-if="!chartData || chartData.datasets.length === 0" class="chart-empty">
        <ChartBarIcon class="w-8 h-8 text-gray-400 mx-auto mb-2" />
        <p class="text-sm text-gray-500 dark:text-gray-400">暂无数据</p>
      </div>
      
      <canvas 
        v-else
        ref="chartCanvas"
        class="chart-canvas"
      ></canvas>
    </div>
    
    <!-- Chart Legend -->
    <div v-if="showLegend && chartData" class="chart-legend">
      <div class="legend-items">
        <div 
          v-for="(dataset, index) in chartData.datasets" 
          :key="index"
          class="legend-item"
        >
          <div 
            class="legend-color"
            :style="{ backgroundColor: dataset.borderColor }"
          ></div>
          <span class="legend-label">{{ dataset.label }}</span>
          <span v-if="latestValues[index]" class="legend-value">
            {{ formatValue(latestValues[index], dataset.unit) }}
          </span>
        </div>
      </div>
    </div>
    
    <!-- Statistics Panel -->
    <div v-if="showStats && statistics" class="chart-stats">
      <div class="stats-grid">
        <div class="stat-item">
          <span class="stat-label">平均值</span>
          <span class="stat-value">{{ formatValue(statistics.avg, statistics.unit) }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">最大值</span>
          <span class="stat-value">{{ formatValue(statistics.max, statistics.unit) }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">最小值</span>
          <span class="stat-value">{{ formatValue(statistics.min, statistics.unit) }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">当前值</span>
          <span class="stat-value">{{ formatValue(statistics.current, statistics.unit) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import {
  ArrowPathIcon,
  ExclamationTriangleIcon,
  ChartBarIcon
} from '@heroicons/vue/24/outline'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  type ChartConfiguration,
  type ChartData,
  type Chart
} from 'chart.js'
import { useThemeStore } from '@/stores/theme'
import { apiClient } from '@/services/api'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface Props {
  title: string
  description?: string
  metrics: string[]
  height?: number
  showLegend?: boolean
  showStats?: boolean
  autoRefresh?: boolean
  refreshInterval?: number
  chartType?: 'line' | 'area' | 'bar'
  timeRange?: string
}

const props = withDefaults(defineProps<Props>(), {
  height: 300,
  showLegend: true,
  showStats: false,
  autoRefresh: true,
  refreshInterval: 30000,
  chartType: 'line',
  timeRange: '1h'
})

const emit = defineEmits<{
  dataUpdate: [data: any]
  error: [error: string]
}>()

const themeStore = useThemeStore()

// Reactive state
const chartCanvas = ref<HTMLCanvasElement>()
const chartInstance = ref<Chart | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const chartData = ref<ChartData | null>(null)
const latestValues = ref<number[]>([])
const statistics = ref<any>(null)
const selectedTimeRange = ref(props.timeRange)
const selectedChartType = ref(props.chartType)

let refreshTimer: NodeJS.Timeout | null = null

// Color palette for multiple metrics
const colors = [
  '#3b82f6', // blue
  '#10b981', // emerald
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // violet
  '#06b6d4', // cyan
  '#84cc16', // lime
  '#f97316'  // orange
]

// Chart configuration
const chartConfig = computed<ChartConfiguration>(() => {
  const isDark = themeStore.isDark
  
  return {
    type: selectedChartType.value,
    data: chartData.value || { labels: [], datasets: [] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false, // We use custom legend
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: isDark ? '#374151' : '#ffffff',
          titleColor: isDark ? '#f9fafb' : '#111827',
          bodyColor: isDark ? '#e5e7eb' : '#374151',
          borderColor: isDark ? '#6b7280' : '#d1d5db',
          borderWidth: 1,
          callbacks: {
            label: (context) => {
              const dataset = context.dataset
              const value = context.parsed.y
              return `${dataset.label}: ${formatValue(value, dataset.unit)}`
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            color: isDark ? '#374151' : '#f3f4f6'
          },
          ticks: {
            color: isDark ? '#9ca3af' : '#6b7280',
            callback: function(value, index) {
              const label = this.getLabelForValue(value as number)
              return new Date(label).toLocaleTimeString('zh-CN', {
                hour: '2-digit',
                minute: '2-digit'
              })
            }
          }
        },
        y: {
          beginAtZero: true,
          grid: {
            color: isDark ? '#374151' : '#f3f4f6'
          },
          ticks: {
            color: isDark ? '#9ca3af' : '#6b7280',
            callback: function(value) {
              return formatValue(value as number, '')
            }
          }
        }
      },
      interaction: {
        mode: 'nearest',
        axis: 'x',
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
      },
      animation: {
        duration: 750,
        easing: 'easeInOutQuart'
      }
    }
  }
})

// Format value with unit
const formatValue = (value: number, unit?: string): string => {
  if (typeof value !== 'number' || isNaN(value)) return 'N/A'
  
  if (unit === '%' || unit === 'percent') {
    return `${value.toFixed(1)}%`
  } else if (unit === 'MB' || unit === 'memory') {
    return `${value.toFixed(1)} MB`
  } else if (unit === 'ms') {
    return `${value.toFixed(1)} ms`
  } else if (unit === 'bytes') {
    return formatBytes(value)
  } else {
    return value.toFixed(2)
  }
}

// Format bytes to human readable
const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Fetch metrics data
const fetchData = async () => {
  loading.value = true
  error.value = null
  
  try {
    const promises = props.metrics.map(metric => 
      apiClient.get('/enhanced-monitoring/metrics/history', {
        params: {
          metric,
          duration_hours: getHoursFromTimeRange(selectedTimeRange.value),
          interval_minutes: getIntervalFromTimeRange(selectedTimeRange.value)
        }
      })
    )
    
    const responses = await Promise.all(promises)
    
    // Process data
    const datasets = responses.map((response, index) => {
      const data = response.data.data || []
      const metric = props.metrics[index]
      const color = colors[index % colors.length]
      
      // Determine unit based on metric name
      let unit = ''
      if (metric.includes('percent') || metric.includes('cpu')) unit = '%'
      else if (metric.includes('memory') || metric.includes('mb')) unit = 'MB'
      else if (metric.includes('ms')) unit = 'ms'
      
      return {
        label: getMetricDisplayName(metric),
        data: data.map((point: any) => point.value),
        borderColor: color,
        backgroundColor: selectedChartType.value === 'area' 
          ? color + '20' 
          : color,
        fill: selectedChartType.value === 'area',
        unit
      }
    })
    
    // Extract labels from first response
    const labels = responses[0]?.data.data?.map((point: any) => point.timestamp) || []
    
    chartData.value = {
      labels,
      datasets
    }
    
    // Update latest values
    latestValues.value = datasets.map(dataset => {
      const data = dataset.data as number[]
      return data[data.length - 1] || 0
    })
    
    // Calculate statistics for first metric
    if (datasets.length > 0) {
      const firstDataset = datasets[0].data as number[]
      if (firstDataset.length > 0) {
        const values = firstDataset.filter(v => !isNaN(v))
        statistics.value = {
          avg: values.reduce((a, b) => a + b, 0) / values.length,
          max: Math.max(...values),
          min: Math.min(...values),
          current: values[values.length - 1],
          unit: datasets[0].unit
        }
      }
    }
    
    emit('dataUpdate', chartData.value)
    
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : '获取数据失败'
    error.value = errorMessage
    emit('error', errorMessage)
  } finally {
    loading.value = false
  }
}

// Get hours from time range
const getHoursFromTimeRange = (range: string): number => {
  const map: Record<string, number> = {
    '5m': 0.1,
    '15m': 0.25,
    '1h': 1,
    '6h': 6,
    '24h': 24
  }
  return map[range] || 1
}

// Get interval from time range
const getIntervalFromTimeRange = (range: string): number => {
  const map: Record<string, number> = {
    '5m': 1,
    '15m': 1,
    '1h': 5,
    '6h': 15,
    '24h': 60
  }
  return map[range] || 5
}

// Get metric display name
const getMetricDisplayName = (metric: string): string => {
  const names: Record<string, string> = {
    'cpu_percent': 'CPU使用率',
    'memory_mb': '内存使用',
    'memory_percent': '内存使用率',
    'tps': 'TPS',
    'mspt': 'MSPT',
    'disk_percent': '磁盘使用率',
    'network_bytes': '网络流量',
    'heap_memory': '堆内存',
    'gc_time': 'GC时间',
    'thread_count': '线程数'
  }
  return names[metric] || metric
}

// Initialize chart
const initChart = async () => {
  await nextTick()
  
  if (chartCanvas.value && chartData.value) {
    if (chartInstance.value) {
      chartInstance.value.destroy()
    }
    
    chartInstance.value = new ChartJS(chartCanvas.value, chartConfig.value)
  }
}

// Update chart
const updateChart = () => {
  if (chartInstance.value && chartData.value) {
    chartInstance.value.data = chartData.value
    chartInstance.value.options = chartConfig.value.options
    chartInstance.value.update('none')
  }
}

// Event handlers
const onTimeRangeChange = () => {
  fetchData()
}

const onChartTypeChange = () => {
  initChart()
}

const refreshData = () => {
  fetchData()
}

// Auto refresh setup
const setupAutoRefresh = () => {
  if (props.autoRefresh && props.refreshInterval > 0) {
    refreshTimer = setInterval(fetchData, props.refreshInterval)
  }
}

const clearAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// Watch for theme changes
watch(() => themeStore.isDark, () => {
  updateChart()
})

// Watch for chart data changes
watch(chartData, () => {
  updateChart()
})

// Watch for props changes
watch(() => props.metrics, () => {
  fetchData()
})

// Lifecycle
onMounted(() => {
  fetchData()
  setupAutoRefresh()
})

onUnmounted(() => {
  clearAutoRefresh()
  if (chartInstance.value) {
    chartInstance.value.destroy()
  }
})

// Watch for chart data to initialize chart
watch(chartData, async (newData) => {
  if (newData) {
    await initChart()
  }
}, { immediate: false })
</script>

<style scoped>
.advanced-metrics-chart {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4;
}

.chart-header {
  @apply flex items-start justify-between mb-4;
}

.chart-title h3 {
  @apply mb-1;
}

.chart-controls {
  @apply flex items-center space-x-2;
}

.form-select {
  @apply bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500;
}

.chart-container {
  @apply relative;
}

.chart-loading, .chart-error, .chart-empty {
  @apply flex flex-col items-center justify-center h-full text-center;
}

.chart-canvas {
  @apply w-full h-full;
}

.chart-legend {
  @apply mt-4 pt-4 border-t border-gray-200 dark:border-gray-700;
}

.legend-items {
  @apply flex flex-wrap gap-4;
}

.legend-item {
  @apply flex items-center space-x-2;
}

.legend-color {
  @apply w-3 h-3 rounded;
}

.legend-label {
  @apply text-sm text-gray-700 dark:text-gray-300;
}

.legend-value {
  @apply text-sm font-medium text-gray-900 dark:text-white;
}

.chart-stats {
  @apply mt-4 pt-4 border-t border-gray-200 dark:border-gray-700;
}

.stats-grid {
  @apply grid grid-cols-2 sm:grid-cols-4 gap-4;
}

.stat-item {
  @apply text-center;
}

.stat-label {
  @apply block text-xs text-gray-500 dark:text-gray-400;
}

.stat-value {
  @apply block text-sm font-medium text-gray-900 dark:text-white mt-1;
}
</style>