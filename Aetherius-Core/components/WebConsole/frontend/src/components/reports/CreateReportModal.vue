<template>
  <div class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-container" @click.stop>
      <!-- Modal Header -->
      <div class="modal-header">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">
          创建性能报告
        </h3>
        <button @click="$emit('close')" class="modal-close-btn">
          <XMarkIcon class="w-5 h-5" />
        </button>
      </div>
      
      <!-- Modal Body -->
      <div class="modal-body">
        <form @submit.prevent="saveReport" class="space-y-6">
          <!-- Basic Information -->
          <div class="form-section">
            <h4 class="section-title">基本信息</h4>
            <div class="form-grid">
              <div class="form-group">
                <label class="form-label">报告名称 *</label>
                <input
                  v-model="formData.name"
                  type="text"
                  class="form-input"
                  placeholder="输入报告名称"
                  required
                />
              </div>
              
              <div class="form-group">
                <label class="form-label">报告类型 *</label>
                <select v-model="formData.type" class="form-select" required>
                  <option value="">选择报告类型</option>
                  <option value="daily">日报</option>
                  <option value="weekly">周报</option>
                  <option value="monthly">月报</option>
                  <option value="custom">自定义</option>
                </select>
              </div>
            </div>
            
            <div class="form-group">
              <label class="form-label">描述</label>
              <textarea
                v-model="formData.description"
                class="form-textarea"
                rows="3"
                placeholder="输入报告描述（可选）"
              ></textarea>
            </div>
          </div>
          
          <!-- Time Range -->
          <div class="form-section">
            <h4 class="section-title">时间范围</h4>
            <div class="form-grid">
              <div class="form-group">
                <label class="form-label">开始日期 *</label>
                <input
                  v-model="formData.startDate"
                  type="date"
                  class="form-input"
                  required
                />
              </div>
              
              <div class="form-group">
                <label class="form-label">结束日期 *</label>
                <input
                  v-model="formData.endDate"
                  type="date"
                  class="form-input"
                  required
                />
              </div>
            </div>
          </div>
          
          <!-- Metrics Selection -->
          <div class="form-section">
            <h4 class="section-title">包含指标</h4>
            <div class="metrics-grid">
              <label
                v-for="metric in availableMetrics"
                :key="metric.key"
                class="metric-option"
              >
                <input
                  v-model="formData.metrics"
                  type="checkbox"
                  :value="metric.key"
                  class="form-checkbox"
                />
                <div class="metric-info">
                  <div class="metric-name">{{ metric.name }}</div>
                  <div class="metric-description">{{ metric.description }}</div>
                </div>
              </label>
            </div>
          </div>
          
          <!-- Output Format -->
          <div class="form-section">
            <h4 class="section-title">输出格式</h4>
            <div class="format-options">
              <label
                v-for="format in outputFormats"
                :key="format.key"
                class="format-option"
                :class="{ active: formData.format === format.key }"
              >
                <input
                  v-model="formData.format"
                  type="radio"
                  :value="format.key"
                  class="sr-only"
                />
                <div class="format-icon">
                  <component :is="format.icon" class="w-6 h-6" />
                </div>
                <div class="format-info">
                  <div class="format-name">{{ format.name }}</div>
                  <div class="format-description">{{ format.description }}</div>
                </div>
              </label>
            </div>
          </div>
        </form>
      </div>
      
      <!-- Modal Footer -->
      <div class="modal-footer">
        <div class="footer-info">
          <InformationCircleIcon class="w-5 h-5 text-blue-500" />
          <span class="text-sm text-gray-600 dark:text-gray-400">
            报告生成可能需要几分钟时间
          </span>
        </div>
        
        <div class="footer-actions">
          <button @click="$emit('close')" class="btn btn-secondary">
            取消
          </button>
          <button @click="saveReport" class="btn btn-primary">
            创建报告
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  XMarkIcon,
  InformationCircleIcon,
  DocumentTextIcon,
  DocumentArrowDownIcon,
  PresentationChartBarIcon
} from '@heroicons/vue/24/outline'

const emit = defineEmits<{
  save: [data: any]
  close: []
}>()

// Form data
const formData = ref({
  name: '',
  type: '',
  description: '',
  startDate: '',
  endDate: '',
  metrics: [],
  format: 'pdf'
})

// Available metrics
const availableMetrics = [
  {
    key: 'cpu_percent',
    name: 'CPU使用率',
    description: '服务器CPU使用情况'
  },
  {
    key: 'memory_percent',
    name: '内存使用率',
    description: '系统内存使用情况'
  },
  {
    key: 'tps',
    name: 'TPS',
    description: '服务器tick性能'
  },
  {
    key: 'disk_usage',
    name: '磁盘使用',
    description: '磁盘空间和I/O'
  },
  {
    key: 'network_traffic',
    name: '网络流量',
    description: '网络I/O统计'
  },
  {
    key: 'player_activity',
    name: '玩家活动',
    description: '玩家在线和活动统计'
  }
]

// Output formats
const outputFormats = [
  {
    key: 'pdf',
    name: 'PDF报告',
    description: '适合打印和分享',
    icon: DocumentTextIcon
  },
  {
    key: 'excel',
    name: 'Excel表格',
    description: '便于数据分析',
    icon: DocumentArrowDownIcon
  },
  {
    key: 'dashboard',
    name: '在线仪表板',
    description: '交互式在线查看',
    icon: PresentationChartBarIcon
  }
]

const saveReport = () => {
  emit('save', { ...formData.value })
}

const handleOverlayClick = () => {
  emit('close')
}
</script>

<style scoped>
.modal-overlay {
  @apply fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50;
}

.modal-container {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-3xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col;
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

.form-section {
  @apply space-y-4;
}

.section-title {
  @apply text-lg font-medium text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-700 pb-2;
}

.form-grid {
  @apply grid grid-cols-1 md:grid-cols-2 gap-4;
}

.form-group {
  @apply space-y-2;
}

.form-label {
  @apply block text-sm font-medium text-gray-700 dark:text-gray-300;
}

.form-input, .form-select, .form-textarea {
  @apply w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500;
}

.form-checkbox {
  @apply rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500;
}

.metrics-grid {
  @apply grid grid-cols-1 md:grid-cols-2 gap-3;
}

.metric-option {
  @apply flex items-start space-x-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-300 dark:hover:border-blue-600 cursor-pointer;
}

.metric-info {
  @apply flex-1;
}

.metric-name {
  @apply font-medium text-gray-900 dark:text-white;
}

.metric-description {
  @apply text-sm text-gray-500 dark:text-gray-400;
}

.format-options {
  @apply grid grid-cols-1 md:grid-cols-3 gap-4;
}

.format-option {
  @apply flex flex-col items-center text-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-300 dark:hover:border-blue-600 cursor-pointer transition-colors;
}

.format-option.active {
  @apply border-blue-500 bg-blue-50 dark:bg-blue-900/20;
}

.format-icon {
  @apply mb-2 p-2 bg-gray-100 dark:bg-gray-700 rounded-lg;
}

.format-info {
  @apply space-y-1;
}

.format-name {
  @apply font-medium text-gray-900 dark:text-white;
}

.format-description {
  @apply text-sm text-gray-500 dark:text-gray-400;
}
</style>