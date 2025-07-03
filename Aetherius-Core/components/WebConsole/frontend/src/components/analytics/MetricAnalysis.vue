<template>
  <div class="metric-analysis">
    <div class="analysis-header">
      <h4 class="analysis-title">{{ title }}</h4>
      <div class="metric-badge">{{ getMetricDisplayName(metric) }}</div>
    </div>
    
    <div class="analysis-grid">
      <!-- Statistics -->
      <div class="stats-section">
        <h5 class="section-title">统计信息</h5>
        <div class="stats-list">
          <div class="stat-item">
            <span class="stat-label">平均值:</span>
            <span class="stat-value">{{ formatValue(data.average) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">峰值:</span>
            <span class="stat-value">{{ formatValue(data.peak) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">方差:</span>
            <span class="stat-value">{{ data.variance.toFixed(2) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">趋势:</span>
            <span class="stat-value" :class="getTrendClass(data.trend)">
              {{ getTrendText(data.trend) }}
            </span>
          </div>
        </div>
      </div>
      
      <!-- Patterns -->
      <div class="patterns-section">
        <h5 class="section-title">行为模式</h5>
        <div class="patterns-list">
          <div 
            v-for="(pattern, index) in data.patterns"
            :key="index"
            class="pattern-item"
          >
            <CheckCircleIcon class="w-4 h-4 text-green-500" />
            <span>{{ pattern }}</span>
          </div>
        </div>
      </div>
      
      <!-- Distribution Chart -->
      <div class="chart-section">
        <h5 class="section-title">数值分布</h5>
        <canvas ref="distributionChart" class="chart-canvas"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { CheckCircleIcon } from '@heroicons/vue/24/outline'

interface Props {
  metric: string
  title: string
  data: {
    average: number
    peak: number
    variance: number
    trend: string
    patterns: string[]
  }
}

const props = defineProps<Props>()
const distributionChart = ref<HTMLCanvasElement>()

const getMetricDisplayName = (metric: string): string => {
  const names: Record<string, string> = {
    'cpu_percent': 'CPU使用率',
    'memory_percent': '内存使用率',
    'tps': 'TPS'
  }
  return names[metric] || metric
}

const formatValue = (value: number): string => {
  if (props.metric.includes('percent')) {
    return `${value.toFixed(1)}%`
  }
  return value.toFixed(1)
}

const getTrendClass = (trend: string): string => {
  const classes = {
    'increasing': 'text-red-600',
    'decreasing': 'text-blue-600',
    'stable': 'text-green-600'
  }
  return classes[trend as keyof typeof classes] || ''
}

const getTrendText = (trend: string): string => {
  const texts = {
    'increasing': '上升',
    'decreasing': '下降',
    'stable': '稳定'
  }
  return texts[trend as keyof typeof texts] || trend
}

onMounted(() => {
  // Initialize distribution chart
  // This would use Chart.js to create a distribution chart
})
</script>

<style scoped>
.metric-analysis {
  @apply space-y-4;
}

.analysis-header {
  @apply flex items-center justify-between;
}

.analysis-title {
  @apply text-lg font-medium text-gray-900 dark:text-white;
}

.metric-badge {
  @apply px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-sm font-medium;
}

.analysis-grid {
  @apply grid grid-cols-1 md:grid-cols-3 gap-6;
}

.stats-section, .patterns-section, .chart-section {
  @apply space-y-3;
}

.section-title {
  @apply font-medium text-gray-700 dark:text-gray-300;
}

.stats-list {
  @apply space-y-2;
}

.stat-item {
  @apply flex justify-between;
}

.stat-label {
  @apply text-sm text-gray-500 dark:text-gray-400;
}

.stat-value {
  @apply text-sm font-medium text-gray-900 dark:text-white;
}

.patterns-list {
  @apply space-y-2;
}

.pattern-item {
  @apply flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300;
}

.chart-canvas {
  @apply w-full h-32;
}
</style>