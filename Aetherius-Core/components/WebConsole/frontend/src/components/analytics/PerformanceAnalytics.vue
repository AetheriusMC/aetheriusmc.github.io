<template>
  <div class="performance-analytics">
    <!-- Header -->
    <div class="analytics-header">
      <div class="header-content">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">
          性能分析
        </h2>
        <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
          深度分析服务器性能趋势和模式
        </p>
      </div>
      
      <div class="header-controls">
        <select v-model="analysisPeriod" class="form-select">
          <option value="24h">24小时</option>
          <option value="7d">7天</option>
          <option value="30d">30天</option>
        </select>
        
        <button 
          @click="runAnalysis"
          :disabled="loading"
          class="btn btn-primary"
        >
          <BeakerIcon class="w-4 h-4 mr-2" />
          {{ loading ? '分析中...' : '运行分析' }}
        </button>
      </div>
    </div>
    
    <!-- Analysis Summary -->
    <div class="analysis-summary">
      <div class="summary-cards">
        <div class="summary-card">
          <div class="card-header">
            <h3 class="card-title">总体评分</h3>
            <TrophyIcon class="w-5 h-5 text-yellow-500" />
          </div>
          <div class="score-display">
            <div class="score-value" :class="getScoreClass(overallScore)">
              {{ overallScore }}
            </div>
            <div class="score-label">/ 100</div>
          </div>
          <div class="score-description">
            {{ getScoreDescription(overallScore) }}
          </div>
        </div>
        
        <div class="summary-card">
          <div class="card-header">
            <h3 class="card-title">性能趋势</h3>
            <TrendingUpIcon class="w-5 h-5 text-blue-500" />
          </div>
          <div class="trend-display">
            <div class="trend-value" :class="trendDirection">
              <component :is="getTrendIcon()" class="w-4 h-4" />
              {{ Math.abs(trendValue).toFixed(1) }}%
            </div>
          </div>
          <div class="trend-description">
            {{ getTrendDescription() }}
          </div>
        </div>
        
        <div class="summary-card">
          <div class="card-header">
            <h3 class="card-title">异常检测</h3>
            <ExclamationTriangleIcon class="w-5 h-5 text-red-500" />
          </div>
          <div class="anomaly-display">
            <div class="anomaly-count">{{ anomalyCount }}</div>
            <div class="anomaly-label">个异常</div>
          </div>
          <div class="anomaly-description">
            {{ anomalyCount > 0 ? '需要关注' : '运行正常' }}
          </div>
        </div>
        
        <div class="summary-card">
          <div class="card-header">
            <h3 class="card-title">资源效率</h3>
            <CpuChipIcon class="w-5 h-5 text-green-500" />
          </div>
          <div class="efficiency-display">
            <div class="efficiency-value">{{ resourceEfficiency }}%</div>
          </div>
          <div class="efficiency-description">
            {{ getEfficiencyDescription(resourceEfficiency) }}
          </div>
        </div>
      </div>
    </div>
    
    <!-- Analysis Charts -->
    <div class="analysis-charts">
      <!-- Performance Correlation -->
      <div class="chart-section">
        <div class="chart-header">
          <h3 class="chart-title">性能相关性分析</h3>
          <p class="chart-description">分析不同指标之间的相关性</p>
        </div>
        <div class="correlation-matrix">
          <div class="matrix-labels">
            <div class="label-row">
              <div class="empty-cell"></div>
              <div v-for="metric in correlationMetrics" :key="metric" class="label-cell">
                {{ getMetricShortName(metric) }}
              </div>
            </div>
          </div>
          <div class="matrix-data">
            <div 
              v-for="(row, i) in correlationMatrix" 
              :key="i"
              class="matrix-row"
            >
              <div class="label-cell">{{ getMetricShortName(correlationMetrics[i]) }}</div>
              <div 
                v-for="(value, j) in row" 
                :key="j"
                class="correlation-cell"
                :class="getCorrelationClass(value)"
                :title="`相关性: ${value.toFixed(2)}`"
              >
                {{ value.toFixed(2) }}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Resource Usage Pattern -->
      <div class="chart-section">
        <div class="chart-header">
          <h3 class="chart-title">资源使用模式</h3>
          <p class="chart-description">24小时资源使用热力图</p>
        </div>
        <div class="heatmap-container">
          <canvas ref="heatmapCanvas" class="heatmap-canvas"></canvas>
        </div>
      </div>
    </div>
    
    <!-- Detailed Analysis -->
    <div class="detailed-analysis">
      <div class="analysis-tabs">
        <button
          v-for="tab in analysisTabs"
          :key="tab.key"
          @click="activeAnalysisTab = tab.key"
          class="tab-button"
          :class="{ active: activeAnalysisTab === tab.key }"
        >
          {{ tab.label }}
        </button>
      </div>
      
      <!-- CPU Analysis -->
      <div v-show="activeAnalysisTab === 'cpu'" class="analysis-content">
        <MetricAnalysis
          metric="cpu_percent"
          title="CPU性能分析"
          :data="cpuAnalysisData"
        />
      </div>
      
      <!-- Memory Analysis -->
      <div v-show="activeAnalysisTab === 'memory'" class="analysis-content">
        <MetricAnalysis
          metric="memory_percent"
          title="内存性能分析"
          :data="memoryAnalysisData"
        />
      </div>
      
      <!-- TPS Analysis -->
      <div v-show="activeAnalysisTab === 'tps'" class="analysis-content">
        <MetricAnalysis
          metric="tps"
          title="TPS性能分析"
          :data="tpsAnalysisData"
        />
      </div>
      
      <!-- Predictive Analysis -->
      <div v-show="activeAnalysisTab === 'predictive'" class="analysis-content">
        <PredictiveAnalysis :period="analysisPeriod" />
      </div>
    </div>
    
    <!-- Recommendations -->
    <div class="recommendations-section">
      <h3 class="section-title">优化建议</h3>
      <div class="recommendations-list">
        <div
          v-for="(recommendation, index) in recommendations"
          :key="index"
          class="recommendation-item"
          :class="recommendation.priority"
        >
          <div class="recommendation-icon">
            <component :is="getRecommendationIcon(recommendation.priority)" class="w-5 h-5" />
          </div>
          <div class="recommendation-content">
            <div class="recommendation-title">{{ recommendation.title }}</div>
            <div class="recommendation-description">{{ recommendation.description }}</div>
            <div class="recommendation-impact">
              预期改善: {{ recommendation.impact }}
            </div>
          </div>
          <div class="recommendation-actions">
            <button class="action-btn">
              查看详情
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  BeakerIcon,
  TrophyIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  ExclamationTriangleIcon,
  CpuChipIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  LightBulbIcon,
  ExclamationCircleIcon,
  InformationCircleIcon
} from '@heroicons/vue/24/outline'
import MetricAnalysis from './MetricAnalysis.vue'
import PredictiveAnalysis from './PredictiveAnalysis.vue'

// State
const loading = ref(false)
const analysisPeriod = ref('24h')
const activeAnalysisTab = ref('cpu')

// Analysis data
const overallScore = ref(85)
const trendValue = ref(12.5)
const trendDirection = ref('positive')
const anomalyCount = ref(3)
const resourceEfficiency = ref(78)

// Correlation data
const correlationMetrics = ['CPU', 'Memory', 'TPS', 'Disk']
const correlationMatrix = ref([
  [1.00, 0.65, -0.32, 0.18],
  [0.65, 1.00, -0.45, 0.23],
  [-0.32, -0.45, 1.00, -0.12],
  [0.18, 0.23, -0.12, 1.00]
])

// Analysis tabs
const analysisTabs = [
  { key: 'cpu', label: 'CPU分析' },
  { key: 'memory', label: '内存分析' },
  { key: 'tps', label: 'TPS分析' },
  { key: 'predictive', label: '预测分析' }
]

// Mock analysis data
const cpuAnalysisData = ref({
  average: 45.2,
  peak: 89.1,
  variance: 12.3,
  trend: 'stable',
  patterns: ['工作时间高峰', '夜间稳定']
})

const memoryAnalysisData = ref({
  average: 62.8,
  peak: 87.5,
  variance: 8.7,
  trend: 'increasing',
  patterns: ['缓慢增长', '周期性回收']
})

const tpsAnalysisData = ref({
  average: 19.2,
  peak: 20.0,
  variance: 0.8,
  trend: 'stable',
  patterns: ['稳定运行', '偶发下降']
})

// Recommendations
const recommendations = ref([
  {
    title: '优化内存配置',
    description: '当前JVM堆内存配置可能不够优化，建议调整初始和最大堆大小',
    impact: '减少GC频率 15-20%',
    priority: 'high'
  },
  {
    title: '升级硬盘存储',
    description: '磁盘I/O成为瓶颈，考虑升级到SSD或增加缓存',
    impact: '提升TPS 10-15%',
    priority: 'medium'
  },
  {
    title: '调整插件配置',
    description: '某些插件在高峰期消耗过多CPU资源',
    impact: '降低CPU使用率 8-12%',
    priority: 'low'
  }
])

// Methods
const getScoreClass = (score: number): string => {
  if (score >= 90) return 'excellent'
  if (score >= 75) return 'good'
  if (score >= 60) return 'fair'
  return 'poor'
}

const getScoreDescription = (score: number): string => {
  if (score >= 90) return '性能优秀'
  if (score >= 75) return '性能良好'
  if (score >= 60) return '性能一般'
  return '需要优化'
}

const getTrendIcon = () => {
  return trendDirection.value === 'positive' ? ArrowUpIcon : ArrowDownIcon
}

const getTrendDescription = (): string => {
  const direction = trendDirection.value === 'positive' ? '改善' : '下降'
  return `相比上期${direction} ${Math.abs(trendValue.value).toFixed(1)}%`
}

const getEfficiencyDescription = (efficiency: number): string => {
  if (efficiency >= 85) return '资源利用率高'
  if (efficiency >= 70) return '资源利用合理'
  if (efficiency >= 55) return '有优化空间'
  return '利用率偏低'
}

const getMetricShortName = (metric: string): string => {
  const names: Record<string, string> = {
    'CPU': 'CPU',
    'Memory': '内存',
    'TPS': 'TPS',
    'Disk': '磁盘'
  }
  return names[metric] || metric
}

const getCorrelationClass = (value: number): string => {
  const abs = Math.abs(value)
  if (abs >= 0.7) return 'high-correlation'
  if (abs >= 0.3) return 'medium-correlation'
  return 'low-correlation'
}

const getRecommendationIcon = (priority: string) => {
  const icons = {
    high: ExclamationCircleIcon,
    medium: ExclamationTriangleIcon,
    low: InformationCircleIcon
  }
  return icons[priority as keyof typeof icons] || LightBulbIcon
}

const runAnalysis = async () => {
  loading.value = true
  try {
    // Simulate analysis
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // Update analysis results
    overallScore.value = 80 + Math.random() * 20
    trendValue.value = (Math.random() - 0.5) * 30
    trendDirection.value = trendValue.value > 0 ? 'positive' : 'negative'
    anomalyCount.value = Math.floor(Math.random() * 6)
    resourceEfficiency.value = 60 + Math.random() * 35
    
  } finally {
    loading.value = false
  }
}

// Initialize
onMounted(() => {
  runAnalysis()
})
</script>

<style scoped>
.performance-analytics {
  @apply space-y-6;
}

.analytics-header {
  @apply flex items-start justify-between;
}

.header-controls {
  @apply flex items-center space-x-3;
}

.form-select {
  @apply bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500;
}

.analysis-summary {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6;
}

.summary-cards {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6;
}

.summary-card {
  @apply text-center space-y-3;
}

.card-header {
  @apply flex items-center justify-center space-x-2;
}

.card-title {
  @apply text-sm font-medium text-gray-600 dark:text-gray-400;
}

.score-display {
  @apply flex items-baseline justify-center space-x-1;
}

.score-value {
  @apply text-3xl font-bold;
}

.score-value.excellent {
  @apply text-green-600 dark:text-green-400;
}

.score-value.good {
  @apply text-blue-600 dark:text-blue-400;
}

.score-value.fair {
  @apply text-yellow-600 dark:text-yellow-400;
}

.score-value.poor {
  @apply text-red-600 dark:text-red-400;
}

.score-label {
  @apply text-lg text-gray-500 dark:text-gray-400;
}

.score-description, .trend-description, .anomaly-description, .efficiency-description {
  @apply text-sm text-gray-600 dark:text-gray-400;
}

.trend-display, .anomaly-display, .efficiency-display {
  @apply flex items-center justify-center space-x-2;
}

.trend-value {
  @apply flex items-center space-x-1 text-xl font-semibold;
}

.trend-value.positive {
  @apply text-green-600 dark:text-green-400;
}

.trend-value.negative {
  @apply text-red-600 dark:text-red-400;
}

.anomaly-count, .efficiency-value {
  @apply text-2xl font-bold text-gray-900 dark:text-white;
}

.anomaly-label {
  @apply text-sm text-gray-500 dark:text-gray-400;
}

.analysis-charts {
  @apply grid grid-cols-1 lg:grid-cols-2 gap-6;
}

.chart-section {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6;
}

.chart-header {
  @apply mb-4;
}

.chart-title {
  @apply text-lg font-medium text-gray-900 dark:text-white;
}

.chart-description {
  @apply text-sm text-gray-600 dark:text-gray-400 mt-1;
}

.correlation-matrix {
  @apply space-y-2;
}

.matrix-labels, .matrix-data {
  @apply space-y-1;
}

.label-row, .matrix-row {
  @apply grid grid-cols-5 gap-2;
}

.empty-cell, .label-cell {
  @apply text-center text-sm font-medium text-gray-600 dark:text-gray-400 p-2;
}

.correlation-cell {
  @apply text-center text-sm p-2 rounded font-mono;
}

.correlation-cell.high-correlation {
  @apply bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200;
}

.correlation-cell.medium-correlation {
  @apply bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200;
}

.correlation-cell.low-correlation {
  @apply bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400;
}

.heatmap-container {
  @apply h-64 bg-gray-50 dark:bg-gray-900 rounded-lg;
}

.heatmap-canvas {
  @apply w-full h-full;
}

.detailed-analysis {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700;
}

.analysis-tabs {
  @apply flex border-b border-gray-200 dark:border-gray-700;
}

.tab-button {
  @apply px-6 py-3 text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 border-b-2 border-transparent hover:border-gray-300 dark:hover:border-gray-600 transition-colors;
}

.tab-button.active {
  @apply text-blue-600 dark:text-blue-400 border-blue-500;
}

.analysis-content {
  @apply p-6;
}

.recommendations-section {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6;
}

.section-title {
  @apply text-lg font-medium text-gray-900 dark:text-white mb-4;
}

.recommendations-list {
  @apply space-y-4;
}

.recommendation-item {
  @apply flex items-start space-x-4 p-4 rounded-lg border;
}

.recommendation-item.high {
  @apply border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20;
}

.recommendation-item.medium {
  @apply border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/20;
}

.recommendation-item.low {
  @apply border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20;
}

.recommendation-icon {
  @apply flex-shrink-0;
}

.recommendation-content {
  @apply flex-1 space-y-1;
}

.recommendation-title {
  @apply font-medium text-gray-900 dark:text-white;
}

.recommendation-description {
  @apply text-sm text-gray-600 dark:text-gray-400;
}

.recommendation-impact {
  @apply text-sm font-medium text-green-600 dark:text-green-400;
}

.recommendation-actions {
  @apply flex-shrink-0;
}

.action-btn {
  @apply px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors;
}
</style>