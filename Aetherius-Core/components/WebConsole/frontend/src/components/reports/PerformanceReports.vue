<template>
  <div class="performance-reports">
    <!-- Header -->
    <div class="reports-header">
      <div class="header-content">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">
          性能报告中心
        </h2>
        <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
          生成和管理服务器性能报告
        </p>
      </div>
      
      <div class="header-actions">
        <button 
          @click="showCreateReportModal = true"
          class="btn btn-primary"
        >
          <DocumentPlusIcon class="w-4 h-4 mr-2" />
          创建报告
        </button>
      </div>
    </div>
    
    <!-- Quick Reports -->
    <div class="quick-reports">
      <h3 class="section-title">快速报告</h3>
      <div class="quick-reports-grid">
        <div 
          v-for="quickReport in quickReports"
          :key="quickReport.id"
          class="quick-report-card"
          @click="generateQuickReport(quickReport)"
        >
          <div class="report-icon">
            <component :is="quickReport.icon" class="w-6 h-6" />
          </div>
          <div class="report-info">
            <div class="report-title">{{ quickReport.title }}</div>
            <div class="report-description">{{ quickReport.description }}</div>
          </div>
          <div class="report-arrow">
            <ChevronRightIcon class="w-5 h-5" />
          </div>
        </div>
      </div>
    </div>
    
    <!-- Generated Reports -->
    <div class="generated-reports">
      <div class="section-header">
        <h3 class="section-title">生成的报告</h3>
        <div class="filter-controls">
          <select v-model="reportFilter" class="form-select text-sm">
            <option value="">全部类型</option>
            <option value="daily">日报</option>
            <option value="weekly">周报</option>
            <option value="monthly">月报</option>
            <option value="custom">自定义</option>
          </select>
          <select v-model="statusFilter" class="form-select text-sm ml-2">
            <option value="">全部状态</option>
            <option value="completed">已完成</option>
            <option value="pending">生成中</option>
            <option value="failed">失败</option>
          </select>
        </div>
      </div>
      
      <div class="reports-table">
        <div class="table-header">
          <div class="header-cell">报告名称</div>
          <div class="header-cell">类型</div>
          <div class="header-cell">时间范围</div>
          <div class="header-cell">状态</div>
          <div class="header-cell">生成时间</div>
          <div class="header-cell">操作</div>
        </div>
        
        <div v-if="filteredReports.length === 0" class="empty-state">
          <DocumentIcon class="w-8 h-8 text-gray-400 mx-auto mb-2" />
          <p class="text-sm text-gray-500 dark:text-gray-400">
            暂无报告
          </p>
        </div>
        
        <div
          v-for="report in filteredReports"
          :key="report.id"
          class="table-row"
        >
          <div class="cell">
            <div class="report-name">{{ report.name }}</div>
          </div>
          
          <div class="cell">
            <span class="type-badge" :class="report.type">
              {{ getTypeText(report.type) }}
            </span>
          </div>
          
          <div class="cell">
            <div class="date-range">
              <div>{{ formatDate(report.startDate) }}</div>
              <div class="text-xs text-gray-500">至</div>
              <div>{{ formatDate(report.endDate) }}</div>
            </div>
          </div>
          
          <div class="cell">
            <span class="status-badge" :class="report.status">
              {{ getStatusText(report.status) }}
            </span>
          </div>
          
          <div class="cell">
            <div class="generated-time">{{ formatTime(report.generatedAt) }}</div>
          </div>
          
          <div class="cell">
            <div class="action-buttons">
              <button 
                @click="downloadReport(report)"
                :disabled="report.status !== 'completed'"
                class="action-btn"
                title="下载"
              >
                <ArrowDownTrayIcon class="w-4 h-4" />
              </button>
              <button 
                @click="shareReport(report)"
                :disabled="report.status !== 'completed'"
                class="action-btn"
                title="分享"
              >
                <ShareIcon class="w-4 h-4" />
              </button>
              <button 
                @click="deleteReport(report)"
                class="action-btn text-red-500"
                title="删除"
              >
                <TrashIcon class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Report Templates -->
    <div class="report-templates">
      <h3 class="section-title">报告模板</h3>
      <div class="templates-grid">
        <div 
          v-for="template in reportTemplates"
          :key="template.id"
          class="template-card"
        >
          <div class="template-header">
            <div class="template-icon">
              <component :is="template.icon" class="w-5 h-5" />
            </div>
            <div class="template-actions">
              <button 
                @click="editTemplate(template)"
                class="template-action-btn"
              >
                <PencilIcon class="w-4 h-4" />
              </button>
            </div>
          </div>
          
          <div class="template-content">
            <div class="template-title">{{ template.name }}</div>
            <div class="template-description">{{ template.description }}</div>
            
            <div class="template-metrics">
              <div class="metrics-label">包含指标:</div>
              <div class="metrics-list">
                <span 
                  v-for="metric in template.metrics.slice(0, 3)"
                  :key="metric"
                  class="metric-tag"
                >
                  {{ getMetricDisplayName(metric) }}
                </span>
                <span v-if="template.metrics.length > 3" class="metric-more">
                  +{{ template.metrics.length - 3 }}
                </span>
              </div>
            </div>
          </div>
          
          <div class="template-footer">
            <button 
              @click="useTemplate(template)"
              class="use-template-btn"
            >
              使用模板
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Create Report Modal -->
    <CreateReportModal
      v-if="showCreateReportModal"
      @save="createReport"
      @close="showCreateReportModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  DocumentPlusIcon,
  DocumentIcon,
  ChevronRightIcon,
  ArrowDownTrayIcon,
  ShareIcon,
  TrashIcon,
  PencilIcon,
  ChartBarIcon,
  ClockIcon,
  CalendarIcon,
  Cog6ToothIcon
} from '@heroicons/vue/24/outline'
import CreateReportModal from './CreateReportModal.vue'

interface Report {
  id: string
  name: string
  type: 'daily' | 'weekly' | 'monthly' | 'custom'
  status: 'completed' | 'pending' | 'failed'
  startDate: string
  endDate: string
  generatedAt: string
}

interface ReportTemplate {
  id: string
  name: string
  description: string
  icon: any
  metrics: string[]
}

// State
const showCreateReportModal = ref(false)
const reportFilter = ref('')
const statusFilter = ref('')

// Quick reports
const quickReports = [
  {
    id: 'daily',
    title: '今日性能报告',
    description: '生成今日服务器性能概况',
    icon: ClockIcon
  },
  {
    id: 'weekly',
    title: '本周性能报告',
    description: '生成本周性能趋势分析',
    icon: CalendarIcon
  },
  {
    id: 'monthly',
    title: '本月性能报告',
    description: '生成本月完整性能报告',
    icon: ChartBarIcon
  }
]

// Mock reports data
const reports = ref<Report[]>([
  {
    id: '1',
    name: '2024年7月性能月报',
    type: 'monthly',
    status: 'completed',
    startDate: '2024-07-01',
    endDate: '2024-07-31',
    generatedAt: '2024-08-01T09:00:00Z'
  },
  {
    id: '2',
    name: '第30周性能周报',
    type: 'weekly',
    status: 'completed',
    startDate: '2024-07-22',
    endDate: '2024-07-28',
    generatedAt: '2024-07-29T08:00:00Z'
  },
  {
    id: '3',
    name: '自定义性能分析',
    type: 'custom',
    status: 'pending',
    startDate: '2024-07-01',
    endDate: '2024-07-15',
    generatedAt: '2024-07-30T10:30:00Z'
  }
])

// Report templates
const reportTemplates = ref<ReportTemplate[]>([
  {
    id: 'basic',
    name: '基础性能报告',
    description: '包含CPU、内存、TPS等基础指标',
    icon: ChartBarIcon,
    metrics: ['cpu_percent', 'memory_percent', 'tps']
  },
  {
    id: 'detailed',
    name: '详细性能报告',
    description: '包含所有监控指标的详细分析',
    icon: DocumentIcon,
    metrics: ['cpu_percent', 'memory_percent', 'tps', 'disk_percent', 'network_bytes']
  },
  {
    id: 'executive',
    name: '管理层摘要报告',
    description: '面向管理层的高层次概要报告',
    icon: Cog6ToothIcon,
    metrics: ['overall_score', 'uptime', 'player_activity']
  }
])

// Computed
const filteredReports = computed(() => {
  return reports.value.filter(report => {
    if (reportFilter.value && report.type !== reportFilter.value) return false
    if (statusFilter.value && report.status !== statusFilter.value) return false
    return true
  })
})

// Methods
const generateQuickReport = async (quickReport: any) => {
  // Implement quick report generation
  console.log('Generate quick report:', quickReport.id)
}

const createReport = (reportData: any) => {
  console.log('Create report:', reportData)
  showCreateReportModal.value = false
}

const downloadReport = (report: Report) => {
  console.log('Download report:', report.id)
}

const shareReport = (report: Report) => {
  console.log('Share report:', report.id)
}

const deleteReport = (report: Report) => {
  if (confirm(`确定要删除报告 "${report.name}" 吗？`)) {
    const index = reports.value.findIndex(r => r.id === report.id)
    if (index !== -1) {
      reports.value.splice(index, 1)
    }
  }
}

const editTemplate = (template: ReportTemplate) => {
  console.log('Edit template:', template.id)
}

const useTemplate = (template: ReportTemplate) => {
  console.log('Use template:', template.id)
  showCreateReportModal.value = true
}

const getTypeText = (type: string): string => {
  const types = {
    'daily': '日报',
    'weekly': '周报',
    'monthly': '月报',
    'custom': '自定义'
  }
  return types[type as keyof typeof types] || type
}

const getStatusText = (status: string): string => {
  const statuses = {
    'completed': '已完成',
    'pending': '生成中',
    'failed': '失败'
  }
  return statuses[status as keyof typeof statuses] || status
}

const getMetricDisplayName = (metric: string): string => {
  const names: Record<string, string> = {
    'cpu_percent': 'CPU',
    'memory_percent': '内存',
    'tps': 'TPS',
    'disk_percent': '磁盘',
    'network_bytes': '网络'
  }
  return names[metric] || metric
}

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const formatTime = (timeString: string): string => {
  return new Date(timeString).toLocaleString('zh-CN')
}
</script>

<style scoped>
.performance-reports {
  @apply space-y-6;
}

.reports-header {
  @apply flex items-start justify-between;
}

.section-title {
  @apply text-lg font-medium text-gray-900 dark:text-white mb-4;
}

.quick-reports {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6;
}

.quick-reports-grid {
  @apply grid grid-cols-1 md:grid-cols-3 gap-4;
}

.quick-report-card {
  @apply flex items-center space-x-4 p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-300 dark:hover:border-blue-600 cursor-pointer transition-colors;
}

.report-icon {
  @apply flex-shrink-0 p-2 bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400 rounded-lg;
}

.report-info {
  @apply flex-1;
}

.report-title {
  @apply font-medium text-gray-900 dark:text-white;
}

.report-description {
  @apply text-sm text-gray-500 dark:text-gray-400;
}

.report-arrow {
  @apply text-gray-400;
}

.generated-reports {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6;
}

.section-header {
  @apply flex items-center justify-between mb-4;
}

.filter-controls {
  @apply flex items-center space-x-2;
}

.form-select {
  @apply bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500;
}

.reports-table {
  @apply border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden;
}

.table-header {
  @apply grid grid-cols-6 gap-4 bg-gray-50 dark:bg-gray-900 p-4 text-sm font-medium text-gray-700 dark:text-gray-300;
}

.table-row {
  @apply grid grid-cols-6 gap-4 p-4 border-t border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-900;
}

.header-cell, .cell {
  @apply flex items-center;
}

.empty-state {
  @apply p-8 text-center;
}

.report-name {
  @apply font-medium text-gray-900 dark:text-white;
}

.type-badge, .status-badge {
  @apply inline-flex items-center px-2 py-1 rounded-full text-xs font-medium;
}

.type-badge.daily {
  @apply bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200;
}

.type-badge.weekly {
  @apply bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200;
}

.type-badge.monthly {
  @apply bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200;
}

.type-badge.custom {
  @apply bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200;
}

.status-badge.completed {
  @apply bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200;
}

.status-badge.pending {
  @apply bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200;
}

.status-badge.failed {
  @apply bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200;
}

.date-range {
  @apply text-sm text-gray-600 dark:text-gray-400;
}

.generated-time {
  @apply text-sm text-gray-600 dark:text-gray-400;
}

.action-buttons {
  @apply flex space-x-1;
}

.action-btn {
  @apply p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors;
}

.action-btn:disabled {
  @apply opacity-50 cursor-not-allowed;
}

.report-templates {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6;
}

.templates-grid {
  @apply grid grid-cols-1 md:grid-cols-3 gap-4;
}

.template-card {
  @apply border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-4;
}

.template-header {
  @apply flex items-center justify-between;
}

.template-icon {
  @apply p-2 bg-gray-100 dark:bg-gray-700 rounded-lg;
}

.template-actions {
  @apply flex space-x-1;
}

.template-action-btn {
  @apply p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded;
}

.template-content {
  @apply space-y-3;
}

.template-title {
  @apply font-medium text-gray-900 dark:text-white;
}

.template-description {
  @apply text-sm text-gray-600 dark:text-gray-400;
}

.template-metrics {
  @apply space-y-2;
}

.metrics-label {
  @apply text-xs font-medium text-gray-500 dark:text-gray-400;
}

.metrics-list {
  @apply flex flex-wrap gap-1;
}

.metric-tag {
  @apply inline-flex items-center px-2 py-1 rounded text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200;
}

.metric-more {
  @apply inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400;
}

.template-footer {
  @apply pt-4 border-t border-gray-200 dark:border-gray-700;
}

.use-template-btn {
  @apply w-full btn btn-sm btn-primary;
}
</style>