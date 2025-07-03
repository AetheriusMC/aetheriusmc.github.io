<template>
  <div class="predictive-analysis">
    <div class="analysis-header">
      <h4 class="analysis-title">预测性分析</h4>
      <p class="analysis-description">基于历史数据预测未来性能趋势</p>
    </div>
    
    <div class="prediction-grid">
      <!-- Predictions Cards -->
      <div class="predictions-section">
        <h5 class="section-title">预测结果</h5>
        <div class="predictions-list">
          <div 
            v-for="prediction in predictions"
            :key="prediction.metric"
            class="prediction-card"
          >
            <div class="prediction-header">
              <span class="prediction-metric">{{ prediction.metric }}</span>
              <span class="prediction-confidence" :class="getConfidenceClass(prediction.confidence)">
                {{ prediction.confidence }}% 置信度
              </span>
            </div>
            <div class="prediction-content">
              <div class="prediction-value">
                <span class="current-label">当前:</span>
                <span class="current-value">{{ prediction.current }}</span>
              </div>
              <div class="prediction-arrow">
                <ArrowRightIcon class="w-4 h-4" />
              </div>
              <div class="prediction-value">
                <span class="predicted-label">预测:</span>
                <span class="predicted-value" :class="getPredictionClass(prediction.trend)">
                  {{ prediction.predicted }}
                </span>
              </div>
            </div>
            <div class="prediction-trend">
              <component :is="getTrendIcon(prediction.trend)" class="w-4 h-4" />
              <span>{{ getTrendDescription(prediction.trend, prediction.change) }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Forecast Chart -->
      <div class="forecast-section">
        <h5 class="section-title">趋势预测</h5>
        <canvas ref="forecastChart" class="forecast-canvas"></canvas>
      </div>
    </div>
    
    <!-- Risk Assessment -->
    <div class="risk-assessment">
      <h5 class="section-title">风险评估</h5>
      <div class="risk-grid">
        <div 
          v-for="risk in riskFactors"
          :key="risk.factor"
          class="risk-item"
          :class="risk.level"
        >
          <div class="risk-icon">
            <component :is="getRiskIcon(risk.level)" class="w-5 h-5" />
          </div>
          <div class="risk-content">
            <div class="risk-factor">{{ risk.factor }}</div>
            <div class="risk-description">{{ risk.description }}</div>
            <div class="risk-probability">风险概率: {{ risk.probability }}%</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Recommendations -->
    <div class="recommendations">
      <h5 class="section-title">预防性建议</h5>
      <div class="recommendations-list">
        <div 
          v-for="(recommendation, index) in recommendations"
          :key="index"
          class="recommendation-item"
        >
          <LightBulbIcon class="w-5 h-5 text-yellow-500" />
          <div class="recommendation-content">
            <div class="recommendation-text">{{ recommendation.text }}</div>
            <div class="recommendation-timeline">建议时间: {{ recommendation.timeline }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  ArrowRightIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  MinusIcon,
  ExclamationTriangleIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
  LightBulbIcon
} from '@heroicons/vue/24/outline'

interface Props {
  period: string
}

const props = defineProps<Props>()
const forecastChart = ref<HTMLCanvasElement>()

// Mock prediction data
const predictions = ref([
  {
    metric: 'CPU使用率',
    current: '45.2%',
    predicted: '52.8%',
    confidence: 87,
    trend: 'increasing',
    change: 7.6
  },
  {
    metric: '内存使用',
    current: '62.8%',
    predicted: '68.4%',
    confidence: 92,
    trend: 'increasing',
    change: 5.6
  },
  {
    metric: 'TPS',
    current: '19.2',
    predicted: '18.7',
    confidence: 78,
    trend: 'decreasing',
    change: -2.6
  }
])

const riskFactors = ref([
  {
    factor: '内存不足风险',
    description: '内存使用率持续增长，可能在7天内达到临界值',
    probability: 78,
    level: 'high'
  },
  {
    factor: 'CPU过载风险',
    description: 'CPU使用率波动较大，高峰期可能出现性能瓶颈',
    probability: 45,
    level: 'medium'
  },
  {
    factor: 'TPS下降风险',
    description: 'TPS呈现缓慢下降趋势，需要监控',
    probability: 32,
    level: 'low'
  }
])

const recommendations = ref([
  {
    text: '建议在未来3天内增加内存配置或优化内存使用',
    timeline: '3天内'
  },
  {
    text: '监控CPU密集型插件，考虑在高峰期禁用非必要插件',
    timeline: '1周内'
  },
  {
    text: '定期重启服务器以清理内存碎片',
    timeline: '每周'
  }
])

const getConfidenceClass = (confidence: number): string => {
  if (confidence >= 80) return 'high-confidence'
  if (confidence >= 60) return 'medium-confidence'
  return 'low-confidence'
}

const getPredictionClass = (trend: string): string => {
  const classes = {
    'increasing': 'text-red-600 dark:text-red-400',
    'decreasing': 'text-green-600 dark:text-green-400',
    'stable': 'text-gray-600 dark:text-gray-400'
  }
  return classes[trend as keyof typeof classes] || ''
}

const getTrendIcon = (trend: string) => {
  const icons = {
    'increasing': ArrowUpIcon,
    'decreasing': ArrowDownIcon,
    'stable': MinusIcon
  }
  return icons[trend as keyof typeof icons] || MinusIcon
}

const getTrendDescription = (trend: string, change: number): string => {
  const direction = trend === 'increasing' ? '上升' : trend === 'decreasing' ? '下降' : '稳定'
  return `预计${direction} ${Math.abs(change).toFixed(1)}%`
}

const getRiskIcon = (level: string) => {
  const icons = {
    'high': ExclamationCircleIcon,
    'medium': ExclamationTriangleIcon,
    'low': InformationCircleIcon
  }
  return icons[level as keyof typeof icons] || InformationCircleIcon
}

onMounted(() => {
  // Initialize forecast chart
  // This would use Chart.js to create a forecast chart with historical and predicted data
})
</script>

<style scoped>
.predictive-analysis {
  @apply space-y-6;
}

.analysis-header {
  @apply text-center space-y-2;
}

.analysis-title {
  @apply text-lg font-medium text-gray-900 dark:text-white;
}

.analysis-description {
  @apply text-sm text-gray-600 dark:text-gray-400;
}

.prediction-grid {
  @apply grid grid-cols-1 lg:grid-cols-2 gap-6;
}

.section-title {
  @apply font-medium text-gray-700 dark:text-gray-300 mb-4;
}

.predictions-list {
  @apply space-y-4;
}

.prediction-card {
  @apply bg-gray-50 dark:bg-gray-900 rounded-lg p-4 space-y-3;
}

.prediction-header {
  @apply flex items-center justify-between;
}

.prediction-metric {
  @apply font-medium text-gray-900 dark:text-white;
}

.prediction-confidence {
  @apply text-xs px-2 py-1 rounded-full;
}

.prediction-confidence.high-confidence {
  @apply bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200;
}

.prediction-confidence.medium-confidence {
  @apply bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200;
}

.prediction-confidence.low-confidence {
  @apply bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200;
}

.prediction-content {
  @apply flex items-center justify-between;
}

.prediction-value {
  @apply text-center;
}

.current-label, .predicted-label {
  @apply block text-xs text-gray-500 dark:text-gray-400;
}

.current-value, .predicted-value {
  @apply block font-semibold;
}

.prediction-arrow {
  @apply text-gray-400;
}

.prediction-trend {
  @apply flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400;
}

.forecast-section {
  @apply space-y-4;
}

.forecast-canvas {
  @apply w-full h-64 bg-gray-50 dark:bg-gray-900 rounded-lg;
}

.risk-assessment {
  @apply space-y-4;
}

.risk-grid {
  @apply space-y-3;
}

.risk-item {
  @apply flex items-start space-x-3 p-4 rounded-lg border;
}

.risk-item.high {
  @apply border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20;
}

.risk-item.medium {
  @apply border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/20;
}

.risk-item.low {
  @apply border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20;
}

.risk-icon {
  @apply flex-shrink-0;
}

.risk-content {
  @apply space-y-1;
}

.risk-factor {
  @apply font-medium text-gray-900 dark:text-white;
}

.risk-description {
  @apply text-sm text-gray-600 dark:text-gray-400;
}

.risk-probability {
  @apply text-xs font-medium;
}

.recommendations {
  @apply space-y-4;
}

.recommendations-list {
  @apply space-y-3;
}

.recommendation-item {
  @apply flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg;
}

.recommendation-content {
  @apply space-y-1;
}

.recommendation-text {
  @apply text-sm text-gray-700 dark:text-gray-300;
}

.recommendation-timeline {
  @apply text-xs text-gray-500 dark:text-gray-400;
}
</style>