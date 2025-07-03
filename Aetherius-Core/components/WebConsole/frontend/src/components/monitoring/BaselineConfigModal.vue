<template>
  <div class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-container" @click.stop>
      <!-- Modal Header -->
      <div class="modal-header">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">
          配置基线 - {{ getMetricDisplayName(metric?.metric_name) }}
        </h3>
        <button @click="$emit('close')" class="modal-close-btn">
          <XMarkIcon class="w-5 h-5" />
        </button>
      </div>
      
      <!-- Modal Body -->
      <div class="modal-body">
        <div v-if="metric" class="config-sections">
          <!-- Current Status -->
          <div class="status-section">
            <h4 class="section-title">当前状态</h4>
            <div class="status-grid">
              <div class="status-item">
                <label class="status-label">当前值</label>
                <div class="status-value">
                  {{ formatMetricValue(currentValue, metric.metric_name) }}
                </div>
              </div>
              <div class="status-item">
                <label class="status-label">基线值</label>
                <div class="status-value">
                  {{ formatMetricValue(metric.baseline_value, metric.metric_name) }}
                </div>
              </div>
              <div class="status-item">
                <label class="status-label">偏离程度</label>
                <div class="status-value" :class="getDeviationClass(deviation)">
                  {{ deviation !== null ? `${deviation > 0 ? '+' : ''}${deviation.toFixed(1)}%` : 'N/A' }}
                </div>
              </div>
              <div class="status-item">
                <label class="status-label">监控状态</label>
                <div class="status-value">
                  <span class="status-badge" :class="metric.enabled ? 'enabled' : 'disabled'">
                    {{ metric.enabled ? '已启用' : '已禁用' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Baseline Configuration -->
          <div class="config-section">
            <h4 class="section-title">基线配置</h4>
            <div class="config-grid">
              <div class="config-item">
                <label class="config-label">
                  基线值 *
                  <span class="unit-hint">({{ getMetricUnit(metric.metric_name) }})</span>
                </label>
                <input
                  v-model.number="formData.baseline_value"
                  type="number"
                  step="0.1"
                  class="form-input"
                  placeholder="输入基线值"
                  required
                />
                <div class="help-text">
                  期望的正常值，系统将以此为基准检测异常
                </div>
              </div>
              
              <div class="config-item">
                <label class="config-label">容差百分比 *</label>
                <div class="tolerance-input">
                  <input
                    v-model.number="formData.tolerance_percent"
                    type="range"
                    min="1"
                    max="50"
                    step="1"
                    class="form-range"
                  />
                  <span class="tolerance-value">{{ formData.tolerance_percent }}%</span>
                </div>
                <div class="tolerance-preview">
                  正常范围: {{ getToleranceRange() }}
                </div>
              </div>
              
              <div class="config-item">
                <label class="config-label">测量窗口 (秒) *</label>
                <select v-model.number="formData.measurement_window" class="form-select">
                  <option :value="60">1分钟</option>
                  <option :value="300">5分钟</option>
                  <option :value="600">10分钟</option>
                  <option :value="1800">30分钟</option>
                  <option :value="3600">1小时</option>
                </select>
                <div class="help-text">
                  计算平均值的时间窗口长度
                </div>
              </div>
              
              <div class="config-item">
                <label class="config-label">监控启用</label>
                <label class="toggle-switch">
                  <input
                    v-model="formData.enabled"
                    type="checkbox"
                    class="sr-only"
                  />
                  <span class="toggle-slider"></span>
                  <span class="toggle-label">
                    {{ formData.enabled ? '启用基线监控' : '禁用基线监控' }}
                  </span>
                </label>
              </div>
            </div>
          </div>
          
          <!-- Advanced Settings -->
          <div class="config-section">
            <div class="section-header">
              <h4 class="section-title">高级设置</h4>
              <button
                type="button"
                @click="showAdvanced = !showAdvanced"
                class="toggle-btn"
              >
                {{ showAdvanced ? '收起' : '展开' }}
                <ChevronDownIcon 
                  class="w-4 h-4 ml-1 transition-transform"
                  :class="{ 'rotate-180': showAdvanced }"
                />
              </button>
            </div>
            
            <div v-show="showAdvanced" class="advanced-settings">
              <div class="config-grid">
                <div class="config-item">
                  <label class="config-label">异常检测敏感度</label>
                  <select v-model="formData.sensitivity" class="form-select">
                    <option value="low">低 - 只检测明显异常</option>
                    <option value="medium">中 - 平衡检测</option>
                    <option value="high">高 - 检测细微变化</option>
                  </select>
                </div>
                
                <div class="config-item">
                  <label class="config-label">学习周期 (天)</label>
                  <input
                    v-model.number="formData.learning_period"
                    type="number"
                    min="1"
                    max="30"
                    class="form-input"
                  />
                  <div class="help-text">
                    自动调整基线的历史数据学习周期
                  </div>
                </div>
                
                <div class="config-item">
                  <label class="checkbox-item">
                    <input
                      v-model="formData.auto_adjust"
                      type="checkbox"
                      class="form-checkbox"
                    />
                    <span>自动调整基线</span>
                  </label>
                  <div class="help-text">
                    根据历史数据自动调整基线值
                  </div>
                </div>
                
                <div class="config-item">
                  <label class="checkbox-item">
                    <input
                      v-model="formData.seasonal_adjustment"
                      type="checkbox"
                      class="form-checkbox"
                    />
                    <span>季节性调整</span>
                  </label>
                  <div class="help-text">
                    考虑时间段的规律性变化
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Historical Analysis -->
          <div class="config-section">
            <h4 class="section-title">历史分析</h4>
            <div class="analysis-content">
              <div class="analysis-stats">
                <div class="stat-item">
                  <span class="stat-label">7天平均值</span>
                  <span class="stat-value">{{ formatMetricValue(historicalStats.avg_7d, metric.metric_name) }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">30天平均值</span>
                  <span class="stat-value">{{ formatMetricValue(historicalStats.avg_30d, metric.metric_name) }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">变异系数</span>
                  <span class="stat-value">{{ historicalStats.coefficient_variation.toFixed(2) }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">异常频率</span>
                  <span class="stat-value">{{ historicalStats.anomaly_frequency.toFixed(1) }}%</span>
                </div>
              </div>
              
              <div class="analysis-actions">
                <button 
                  @click="useHistoricalBaseline(7)"
                  class="btn btn-sm btn-secondary"
                >
                  使用7天平均值
                </button>
                <button 
                  @click="useHistoricalBaseline(30)"
                  class="btn btn-sm btn-secondary"
                >
                  使用30天平均值
                </button>
              </div>
            </div>
          </div>
          
          <!-- Baseline Preview -->
          <div class="config-section">
            <h4 class="section-title">基线预览</h4>
            <div class="preview-chart">
              <canvas ref="previewChartCanvas" class="chart-canvas"></canvas>
            </div>
            <div class="preview-legend">
              <div class="legend-item">
                <div class="legend-color current"></div>
                <span>当前基线</span>
              </div>
              <div class="legend-item">
                <div class="legend-color new"></div>
                <span>新基线</span>
              </div>
              <div class="legend-item">
                <div class="legend-color tolerance"></div>
                <span>容差范围</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Modal Footer -->
      <div class="modal-footer">
        <div class="footer-info">
          <InformationCircleIcon class="w-5 h-5 text-blue-500" />
          <span class="text-sm text-gray-600 dark:text-gray-400">
            基线配置将在保存后立即生效
          </span>
        </div>
        
        <div class="footer-actions">
          <button @click="resetToDefault" class="btn btn-secondary">
            重置默认值
          </button>
          <button @click="$emit('close')" class="btn btn-secondary">
            取消
          </button>
          <button @click="saveConfig" class="btn btn-primary">
            保存配置
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import {
  XMarkIcon,
  ChevronDownIcon,
  InformationCircleIcon
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
  Filler,
  type Chart
} from 'chart.js'
import { useThemeStore } from '@/stores/theme'

interface BaselineMetric {
  metric_name: string
  baseline_value: number
  tolerance_percent: number
  measurement_window: number
  enabled: boolean
  current_value?: number
  deviation?: number
}

interface Props {
  metric: BaselineMetric | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  save: [config: any]
  close: []
}>()

const themeStore = useThemeStore()

// Form state
const formData = ref({
  baseline_value: 0,
  tolerance_percent: 10,
  measurement_window: 300,
  enabled: true,
  sensitivity: 'medium',
  learning_period: 7,
  auto_adjust: false,
  seasonal_adjustment: false
})

const showAdvanced = ref(false)
const previewChartCanvas = ref<HTMLCanvasElement>()
const previewChart = ref<Chart | null>(null)

// Mock historical stats
const historicalStats = ref({
  avg_7d: 45.2,
  avg_30d: 42.8,
  coefficient_variation: 0.15,
  anomaly_frequency: 2.3
})

// Mock current value and deviation
const currentValue = ref(48.5)
const deviation = computed(() => {
  if (!props.metric) return null
  return ((currentValue.value - formData.value.baseline_value) / formData.value.baseline_value) * 100
})

// Methods
const getMetricDisplayName = (metric: string | undefined): string => {
  if (!metric) return ''
  const names: Record<string, string> = {
    'cpu_percent': 'CPU使用率',
    'memory_percent': '内存使用率',
    'tps': 'TPS',
    'mspt': 'MSPT'
  }
  return names[metric] || metric
}

const getMetricUnit = (metric: string): string => {
  const units: Record<string, string> = {
    'cpu_percent': '%',
    'memory_percent': '%',
    'tps': '',
    'mspt': 'ms'
  }
  return units[metric] || ''
}

const formatMetricValue = (value: number | undefined, metric: string): string => {
  if (value === undefined) return 'N/A'
  const unit = getMetricUnit(metric)
  return `${value.toFixed(1)}${unit}`
}

const getDeviationClass = (deviation: number | null): string => {
  if (deviation === null) return ''
  if (Math.abs(deviation) > formData.value.tolerance_percent) {
    return deviation > 0 ? 'positive-high' : 'negative-high'
  }
  return deviation > 0 ? 'positive' : 'negative'
}

const getToleranceRange = (): string => {
  const baseline = formData.value.baseline_value
  const tolerance = formData.value.tolerance_percent
  const unit = props.metric ? getMetricUnit(props.metric.metric_name) : ''
  
  const lower = baseline * (1 - tolerance / 100)
  const upper = baseline * (1 + tolerance / 100)
  
  return `${lower.toFixed(1)}${unit} - ${upper.toFixed(1)}${unit}`
}

const useHistoricalBaseline = (days: number) => {
  if (days === 7) {
    formData.value.baseline_value = historicalStats.value.avg_7d
  } else if (days === 30) {
    formData.value.baseline_value = historicalStats.value.avg_30d
  }
  updatePreviewChart()
}

const resetToDefault = () => {
  if (props.metric) {
    formData.value = {
      baseline_value: props.metric.baseline_value,
      tolerance_percent: props.metric.tolerance_percent,
      measurement_window: props.metric.measurement_window,
      enabled: props.metric.enabled,
      sensitivity: 'medium',
      learning_period: 7,
      auto_adjust: false,
      seasonal_adjustment: false
    }
  }
  updatePreviewChart()
}

const saveConfig = () => {
  emit('save', { ...formData.value })
}

const handleOverlayClick = () => {
  emit('close')
}

const initializePreviewChart = async () => {
  await nextTick()
  
  if (!previewChartCanvas.value || !props.metric) return
  
  // Generate mock historical data
  const labels = []
  const actualData = []
  const currentBaselineData = []
  const newBaselineData = []
  const upperToleranceData = []
  const lowerToleranceData = []
  
  const now = new Date()
  for (let i = 23; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 60 * 60 * 1000)
    labels.push(time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }))
    
    // Mock actual data with some variance
    const variance = (Math.random() - 0.5) * 20
    actualData.push(props.metric.baseline_value + variance)
    
    // Current baseline
    currentBaselineData.push(props.metric.baseline_value)
    
    // New baseline
    newBaselineData.push(formData.value.baseline_value)
    
    // Tolerance bands for new baseline
    const tolerance = formData.value.tolerance_percent / 100
    upperToleranceData.push(formData.value.baseline_value * (1 + tolerance))
    lowerToleranceData.push(formData.value.baseline_value * (1 - tolerance))
  }
  
  const isDark = themeStore.isDark
  
  previewChart.value = new ChartJS(previewChartCanvas.value, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: '实际值',
          data: actualData,
          borderColor: '#3b82f6',
          backgroundColor: 'transparent',
          fill: false,
          tension: 0.3
        },
        {
          label: '当前基线',
          data: currentBaselineData,
          borderColor: '#6b7280',
          borderDash: [5, 5],
          fill: false,
          pointRadius: 0
        },
        {
          label: '新基线',
          data: newBaselineData,
          borderColor: '#10b981',
          borderDash: [3, 3],
          fill: false,
          pointRadius: 0
        },
        {
          label: '容差上限',
          data: upperToleranceData,
          borderColor: '#f59e0b',
          backgroundColor: 'rgba(245, 158, 11, 0.1)',
          fill: '+1',
          pointRadius: 0,
          borderWidth: 1
        },
        {
          label: '容差下限',
          data: lowerToleranceData,
          borderColor: '#f59e0b',
          backgroundColor: 'rgba(245, 158, 11, 0.1)',
          fill: false,
          pointRadius: 0,
          borderWidth: 1
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
          grid: {
            color: isDark ? '#374151' : '#f3f4f6'
          },
          ticks: {
            color: isDark ? '#9ca3af' : '#6b7280'
          }
        },
        y: {
          grid: {
            color: isDark ? '#374151' : '#f3f4f6'
          },
          ticks: {
            color: isDark ? '#9ca3af' : '#6b7280'
          }
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
}

const updatePreviewChart = () => {
  if (!previewChart.value || !props.metric) return
  
  // Update new baseline and tolerance data
  const newBaselineData = Array(24).fill(formData.value.baseline_value)
  const tolerance = formData.value.tolerance_percent / 100
  const upperToleranceData = Array(24).fill(formData.value.baseline_value * (1 + tolerance))
  const lowerToleranceData = Array(24).fill(formData.value.baseline_value * (1 - tolerance))
  
  previewChart.value.data.datasets[2].data = newBaselineData
  previewChart.value.data.datasets[3].data = upperToleranceData
  previewChart.value.data.datasets[4].data = lowerToleranceData
  
  previewChart.value.update()
}

// Watch for form changes to update preview
watch(() => [formData.value.baseline_value, formData.value.tolerance_percent], () => {
  updatePreviewChart()
})

// Initialize form data when metric changes
watch(() => props.metric, (newMetric) => {
  if (newMetric) {
    formData.value = {
      baseline_value: newMetric.baseline_value,
      tolerance_percent: newMetric.tolerance_percent,
      measurement_window: newMetric.measurement_window,
      enabled: newMetric.enabled,
      sensitivity: 'medium',
      learning_period: 7,
      auto_adjust: false,
      seasonal_adjustment: false
    }
    
    // Generate mock historical stats based on metric
    historicalStats.value = {
      avg_7d: newMetric.baseline_value * (0.9 + Math.random() * 0.2),
      avg_30d: newMetric.baseline_value * (0.85 + Math.random() * 0.3),
      coefficient_variation: 0.1 + Math.random() * 0.2,
      anomaly_frequency: Math.random() * 5
    }
    
    initializePreviewChart()
  }
}, { immediate: true })

onMounted(() => {
  if (props.metric) {
    initializePreviewChart()
  }
})
</script>

<style scoped>
.modal-overlay {
  @apply fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50;
}

.modal-container {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col;
}

.modal-header {
  @apply flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700;
}

.modal-close-btn {
  @apply p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded;
}

.modal-body {
  @apply flex-1 overflow-y-auto p-6;
}

.modal-footer {
  @apply flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900;
}

.footer-info {
  @apply flex items-center space-x-2;
}

.footer-actions {
  @apply flex space-x-3;
}

.config-sections {
  @apply space-y-6;
}

.config-section, .status-section {
  @apply space-y-4;
}

.section-title {
  @apply text-lg font-medium text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-700 pb-2;
}

.section-header {
  @apply flex items-center justify-between;
}

.toggle-btn {
  @apply flex items-center text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300;
}

.status-grid, .config-grid {
  @apply grid grid-cols-1 md:grid-cols-2 gap-4;
}

.status-item {
  @apply space-y-1;
}

.status-label {
  @apply block text-sm text-gray-500 dark:text-gray-400;
}

.status-value {
  @apply text-lg font-semibold text-gray-900 dark:text-white;
}

.status-value.positive {
  @apply text-orange-600 dark:text-orange-400;
}

.status-value.positive-high {
  @apply text-red-600 dark:text-red-400;
}

.status-value.negative {
  @apply text-blue-600 dark:text-blue-400;
}

.status-value.negative-high {
  @apply text-green-600 dark:text-green-400;
}

.status-badge {
  @apply inline-flex items-center px-2 py-1 rounded-full text-xs font-medium;
}

.status-badge.enabled {
  @apply bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200;
}

.status-badge.disabled {
  @apply bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200;
}

.config-item {
  @apply space-y-2;
}

.config-label {
  @apply block text-sm font-medium text-gray-700 dark:text-gray-300;
}

.unit-hint {
  @apply text-gray-500 dark:text-gray-400 font-normal;
}

.form-input, .form-select {
  @apply w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500;
}

.form-range {
  @apply w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer;
}

.form-checkbox {
  @apply rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500;
}

.tolerance-input {
  @apply flex items-center space-x-3;
}

.tolerance-value {
  @apply text-sm font-medium text-gray-900 dark:text-white min-w-[3rem];
}

.tolerance-preview {
  @apply text-sm text-gray-600 dark:text-gray-400;
}

.help-text {
  @apply text-xs text-gray-500 dark:text-gray-400;
}

.toggle-switch {
  @apply relative inline-flex items-center cursor-pointer;
}

.toggle-slider {
  @apply w-11 h-6 bg-gray-200 dark:bg-gray-700 rounded-full relative transition-colors duration-200 mr-3;
}

.toggle-slider::before {
  @apply content-[''] absolute top-0.5 left-0.5 bg-white dark:bg-gray-300 w-5 h-5 rounded-full transition-transform duration-200;
}

.toggle-switch input:checked + .toggle-slider {
  @apply bg-blue-600;
}

.toggle-switch input:checked + .toggle-slider::before {
  @apply transform translate-x-5;
}

.toggle-label {
  @apply text-sm text-gray-700 dark:text-gray-300;
}

.advanced-settings {
  @apply mt-4 space-y-4;
}

.checkbox-item {
  @apply flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300;
}

.analysis-content {
  @apply space-y-4;
}

.analysis-stats {
  @apply grid grid-cols-2 md:grid-cols-4 gap-4;
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

.analysis-actions {
  @apply flex space-x-3;
}

.preview-chart {
  @apply h-64 bg-gray-50 dark:bg-gray-900 rounded-lg p-4;
}

.chart-canvas {
  @apply w-full h-full;
}

.preview-legend {
  @apply flex flex-wrap gap-4 mt-4;
}

.legend-item {
  @apply flex items-center space-x-2;
}

.legend-color {
  @apply w-3 h-3 rounded;
}

.legend-color.current {
  @apply bg-gray-400;
}

.legend-color.new {
  @apply bg-green-500;
}

.legend-color.tolerance {
  @apply bg-yellow-400;
}
</style>