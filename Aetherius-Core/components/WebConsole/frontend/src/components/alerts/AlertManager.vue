<template>
  <div class="alert-manager">
    <!-- Header -->
    <div class="manager-header">
      <div class="header-content">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">
          告警管理
        </h2>
        <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
          配置和管理系统性能告警规则
        </p>
      </div>
      
      <div class="header-actions">
        <button 
          @click="showCreateRuleModal = true"
          class="btn btn-primary"
        >
          <PlusIcon class="w-4 h-4 mr-2" />
          创建规则
        </button>
      </div>
    </div>
    
    <!-- Alert Rules Table -->
    <div class="rules-section">
      <div class="section-header">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">
          告警规则
        </h3>
        <div class="filter-controls">
          <select v-model="filterStatus" class="form-select text-sm">
            <option value="">全部状态</option>
            <option value="enabled">已启用</option>
            <option value="disabled">已禁用</option>
          </select>
          <select v-model="filterSeverity" class="form-select text-sm ml-2">
            <option value="">全部级别</option>
            <option value="info">信息</option>
            <option value="warning">警告</option>
            <option value="error">错误</option>
            <option value="critical">严重</option>
          </select>
        </div>
      </div>
      
      <div class="rules-table">
        <div class="table-header">
          <div class="header-cell">规则名称</div>
          <div class="header-cell">监控指标</div>
          <div class="header-cell">条件</div>
          <div class="header-cell">严重级别</div>
          <div class="header-cell">状态</div>
          <div class="header-cell">操作</div>
        </div>
        
        <div v-if="filteredRules.length === 0" class="empty-state">
          <ExclamationTriangleIcon class="w-8 h-8 text-gray-400 mx-auto mb-2" />
          <p class="text-sm text-gray-500 dark:text-gray-400">
            暂无告警规则
          </p>
        </div>
        
        <div
          v-for="rule in filteredRules"
          :key="rule.id"
          class="table-row"
          :class="{ 'disabled': !rule.enabled }"
        >
          <div class="cell">
            <div class="rule-name">{{ rule.name }}</div>
            <div v-if="rule.description" class="rule-description">
              {{ rule.description }}
            </div>
          </div>
          
          <div class="cell">
            <span class="metric-badge">{{ getMetricDisplayName(rule.metric_name) }}</span>
          </div>
          
          <div class="cell">
            <span class="condition-text">
              {{ rule.operator }} {{ rule.threshold }}{{ getMetricUnit(rule.metric_name) }}
            </span>
            <div class="duration-text">
              持续 {{ rule.duration }}秒
            </div>
          </div>
          
          <div class="cell">
            <span class="severity-badge" :class="rule.severity">
              {{ getSeverityText(rule.severity) }}
            </span>
          </div>
          
          <div class="cell">
            <label class="toggle-switch">
              <input
                v-model="rule.enabled"
                type="checkbox"
                @change="toggleRule(rule)"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
          
          <div class="cell">
            <div class="action-buttons">
              <button 
                @click="editRule(rule)"
                class="action-btn"
                title="编辑"
              >
                <PencilIcon class="w-4 h-4" />
              </button>
              <button 
                @click="testRule(rule)"
                class="action-btn"
                title="测试"
              >
                <PlayIcon class="w-4 h-4" />
              </button>
              <button 
                @click="deleteRule(rule)"
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
    
    <!-- Performance Baselines -->
    <div class="baselines-section">
      <div class="section-header">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">
          性能基线
        </h3>
        <button 
          @click="refreshBaselines"
          class="btn btn-sm btn-secondary"
        >
          <ArrowPathIcon class="w-4 h-4 mr-2" />
          刷新
        </button>
      </div>
      
      <div class="baselines-grid">
        <div
          v-for="baseline in baselines"
          :key="baseline.metric_name"
          class="baseline-card"
        >
          <div class="baseline-header">
            <h4 class="baseline-title">{{ getMetricDisplayName(baseline.metric_name) }}</h4>
            <label class="toggle-switch">
              <input
                v-model="baseline.enabled"
                type="checkbox"
                @change="updateBaseline(baseline)"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
          
          <div class="baseline-content">
            <div class="baseline-value">
              <label class="text-xs text-gray-500">基线值</label>
              <input
                v-model.number="baseline.baseline_value"
                type="number"
                step="0.1"
                class="form-input-sm"
                @change="updateBaseline(baseline)"
              />
            </div>
            
            <div class="baseline-tolerance">
              <label class="text-xs text-gray-500">容差 (%)</label>
              <input
                v-model.number="baseline.tolerance_percent"
                type="number"
                step="1"
                min="1"
                max="50"
                class="form-input-sm"
                @change="updateBaseline(baseline)"
              />
            </div>
            
            <div class="baseline-window">
              <label class="text-xs text-gray-500">测量窗口 (秒)</label>
              <input
                v-model.number="baseline.measurement_window"
                type="number"
                step="60"
                min="60"
                max="3600"
                class="form-input-sm"
                @change="updateBaseline(baseline)"
              />
            </div>
          </div>
          
          <div class="baseline-status">
            <div class="status-indicator" :class="getBaselineStatus(baseline)">
              <div class="status-dot"></div>
              <span class="status-text">{{ getBaselineStatusText(baseline) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Recent Alerts -->
    <div class="recent-alerts-section">
      <div class="section-header">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">
          最近告警
        </h3>
        <button 
          @click="clearAllAlerts"
          class="btn btn-sm btn-secondary"
        >
          清除全部
        </button>
      </div>
      
      <div class="alerts-list">
        <div
          v-for="alert in recentAlerts"
          :key="alert.id"
          class="alert-item"
          :class="alert.severity"
        >
          <div class="alert-icon">
            <ExclamationTriangleIcon v-if="alert.severity === 'warning'" class="w-5 h-5" />
            <ExclamationCircleIcon v-else-if="alert.severity === 'error'" class="w-5 h-5" />
            <ShieldExclamationIcon v-else-if="alert.severity === 'critical'" class="w-5 h-5" />
            <InformationCircleIcon v-else class="w-5 h-5" />
          </div>
          
          <div class="alert-content">
            <div class="alert-title">{{ alert.title }}</div>
            <div class="alert-message">{{ alert.message }}</div>
            <div class="alert-time">{{ formatTime(alert.timestamp) }}</div>
          </div>
          
          <div class="alert-actions">
            <button 
              @click="acknowledgeAlert(alert.id)"
              class="action-btn"
              title="确认"
            >
              <CheckIcon class="w-4 h-4" />
            </button>
            <button 
              @click="dismissAlert(alert.id)"
              class="action-btn"
              title="忽略"
            >
              <XMarkIcon class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Create/Edit Rule Modal -->
    <AlertRuleModal
      v-if="showCreateRuleModal || editingRule"
      :rule="editingRule"
      @save="saveRule"
      @close="closeRuleModal"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  PlayIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  ExclamationCircleIcon,
  ShieldExclamationIcon,
  InformationCircleIcon,
  CheckIcon,
  XMarkIcon
} from '@heroicons/vue/24/outline'
import AlertRuleModal from './AlertRuleModal.vue'
import { apiClient } from '@/services/api'

interface AlertRule {
  id: string
  name: string
  description?: string
  metric_name: string
  operator: string
  threshold: number
  duration: number
  severity: 'info' | 'warning' | 'error' | 'critical'
  enabled: boolean
  notification_channels: string[]
  cooldown_seconds: number
}

interface PerformanceBaseline {
  metric_name: string
  baseline_value: number
  tolerance_percent: number
  measurement_window: number
  enabled: boolean
}

interface Alert {
  id: string
  title: string
  message: string
  severity: 'info' | 'warning' | 'error' | 'critical'
  timestamp: string
  acknowledged?: boolean
}

// State
const alertRules = ref<AlertRule[]>([])
const baselines = ref<PerformanceBaseline[]>([])
const recentAlerts = ref<Alert[]>([])
const loading = ref(false)

// Filters
const filterStatus = ref('')
const filterSeverity = ref('')

// Modals
const showCreateRuleModal = ref(false)
const editingRule = ref<AlertRule | null>(null)

// Computed
const filteredRules = computed(() => {
  return alertRules.value.filter(rule => {
    if (filterStatus.value) {
      const isEnabled = filterStatus.value === 'enabled'
      if (rule.enabled !== isEnabled) return false
    }
    
    if (filterSeverity.value && rule.severity !== filterSeverity.value) {
      return false
    }
    
    return true
  })
})

// Methods
const loadAlertRules = async () => {
  try {
    // TODO: Implement API call
    // const response = await apiClient.get('/enhanced-monitoring/alerts/rules')
    // alertRules.value = response.data.rules
    
    // Mock data for now
    alertRules.value = [
      {
        id: '1',
        name: 'CPU使用率过高',
        description: '检测CPU使用率是否超过80%',
        metric_name: 'cpu_percent',
        operator: '>',
        threshold: 80,
        duration: 300,
        severity: 'warning',
        enabled: true,
        notification_channels: ['web'],
        cooldown_seconds: 900
      },
      {
        id: '2',
        name: 'TPS过低告警',
        description: '检测TPS是否低于15',
        metric_name: 'tps',
        operator: '<',
        threshold: 15,
        duration: 120,
        severity: 'error',
        enabled: true,
        notification_channels: ['web', 'email'],
        cooldown_seconds: 600
      }
    ]
  } catch (error) {
    console.error('Failed to load alert rules:', error)
  }
}

const loadBaselines = async () => {
  try {
    const response = await apiClient.get('/enhanced-monitoring/performance/baseline')
    baselines.value = response.data
  } catch (error) {
    console.error('Failed to load baselines:', error)
  }
}

const loadRecentAlerts = async () => {
  try {
    // TODO: Implement API call
    // const response = await apiClient.get('/enhanced-monitoring/alerts/recent')
    // recentAlerts.value = response.data.alerts
    
    // Mock data for now
    recentAlerts.value = [
      {
        id: '1',
        title: 'CPU使用率过高',
        message: '当前CPU使用率为 85.2%，超过预设阈值',
        severity: 'warning',
        timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString()
      },
      {
        id: '2',
        title: '内存使用接近上限',
        message: '内存使用率达到 92.1%，建议检查内存泄漏',
        severity: 'error',
        timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString()
      }
    ]
  } catch (error) {
    console.error('Failed to load recent alerts:', error)
  }
}

const refreshBaselines = async () => {
  await loadBaselines()
}

const toggleRule = async (rule: AlertRule) => {
  try {
    // TODO: Implement API call
    console.log('Toggle rule:', rule.id, rule.enabled)
  } catch (error) {
    console.error('Failed to toggle rule:', error)
    // Revert on error
    rule.enabled = !rule.enabled
  }
}

const editRule = (rule: AlertRule) => {
  editingRule.value = { ...rule }
}

const deleteRule = async (rule: AlertRule) => {
  if (confirm(`确定要删除告警规则 "${rule.name}" 吗？`)) {
    try {
      // TODO: Implement API call
      const index = alertRules.value.findIndex(r => r.id === rule.id)
      if (index !== -1) {
        alertRules.value.splice(index, 1)
      }
    } catch (error) {
      console.error('Failed to delete rule:', error)
    }
  }
}

const testRule = async (rule: AlertRule) => {
  try {
    // TODO: Implement API call to test rule
    alert(`测试告警规则: ${rule.name}`)
  } catch (error) {
    console.error('Failed to test rule:', error)
  }
}

const updateBaseline = async (baseline: PerformanceBaseline) => {
  try {
    // TODO: Implement API call
    console.log('Update baseline:', baseline.metric_name, baseline)
  } catch (error) {
    console.error('Failed to update baseline:', error)
  }
}

const saveRule = async (ruleData: Partial<AlertRule>) => {
  try {
    if (editingRule.value) {
      // Update existing rule
      const index = alertRules.value.findIndex(r => r.id === editingRule.value!.id)
      if (index !== -1) {
        alertRules.value[index] = { ...alertRules.value[index], ...ruleData }
      }
    } else {
      // Create new rule
      const newRule: AlertRule = {
        id: Date.now().toString(),
        ...ruleData as AlertRule
      }
      alertRules.value.push(newRule)
    }
    
    closeRuleModal()
  } catch (error) {
    console.error('Failed to save rule:', error)
  }
}

const closeRuleModal = () => {
  showCreateRuleModal.value = false
  editingRule.value = null
}

const acknowledgeAlert = async (alertId: string) => {
  try {
    const alert = recentAlerts.value.find(a => a.id === alertId)
    if (alert) {
      alert.acknowledged = true
    }
  } catch (error) {
    console.error('Failed to acknowledge alert:', error)
  }
}

const dismissAlert = (alertId: string) => {
  const index = recentAlerts.value.findIndex(a => a.id === alertId)
  if (index !== -1) {
    recentAlerts.value.splice(index, 1)
  }
}

const clearAllAlerts = () => {
  if (confirm('确定要清除所有告警吗？')) {
    recentAlerts.value = []
  }
}

// Helper functions
const getMetricDisplayName = (metric: string): string => {
  const names: Record<string, string> = {
    'cpu_percent': 'CPU使用率',
    'memory_percent': '内存使用率',
    'memory_mb': '内存使用量',
    'tps': 'TPS',
    'mspt': 'MSPT',
    'disk_percent': '磁盘使用率'
  }
  return names[metric] || metric
}

const getMetricUnit = (metric: string): string => {
  const units: Record<string, string> = {
    'cpu_percent': '%',
    'memory_percent': '%',
    'memory_mb': 'MB',
    'tps': '',
    'mspt': 'ms',
    'disk_percent': '%'
  }
  return units[metric] || ''
}

const getSeverityText = (severity: string): string => {
  const texts: Record<string, string> = {
    'info': '信息',
    'warning': '警告',
    'error': '错误',
    'critical': '严重'
  }
  return texts[severity] || severity
}

const getBaselineStatus = (baseline: PerformanceBaseline): string => {
  if (!baseline.enabled) return 'disabled'
  // TODO: Compare with actual metrics
  return 'normal'
}

const getBaselineStatusText = (baseline: PerformanceBaseline): string => {
  const status = getBaselineStatus(baseline)
  const texts: Record<string, string> = {
    'normal': '正常',
    'warning': '偏离',
    'error': '异常',
    'disabled': '已禁用'
  }
  return texts[status] || '未知'
}

const formatTime = (timestamp: string): string => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

// Lifecycle
onMounted(() => {
  loadAlertRules()
  loadBaselines()
  loadRecentAlerts()
})
</script>

<style scoped>
.alert-manager {
  @apply space-y-6;
}

.manager-header {
  @apply flex items-start justify-between;
}

.header-actions {
  @apply flex space-x-3;
}

.rules-section, .baselines-section, .recent-alerts-section {
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

.rules-table {
  @apply border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden;
}

.table-header {
  @apply grid grid-cols-6 gap-4 bg-gray-50 dark:bg-gray-900 p-4 text-sm font-medium text-gray-700 dark:text-gray-300;
}

.table-row {
  @apply grid grid-cols-6 gap-4 p-4 border-t border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-900;
}

.table-row.disabled {
  @apply opacity-60;
}

.header-cell, .cell {
  @apply flex items-center;
}

.rule-name {
  @apply font-medium text-gray-900 dark:text-white;
}

.rule-description {
  @apply text-sm text-gray-500 dark:text-gray-400 mt-1;
}

.metric-badge {
  @apply inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200;
}

.condition-text {
  @apply font-mono text-sm text-gray-900 dark:text-white;
}

.duration-text {
  @apply text-xs text-gray-500 dark:text-gray-400 mt-1;
}

.severity-badge {
  @apply inline-flex items-center px-2 py-1 rounded-full text-xs font-medium;
}

.severity-badge.info {
  @apply bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200;
}

.severity-badge.warning {
  @apply bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200;
}

.severity-badge.error {
  @apply bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200;
}

.severity-badge.critical {
  @apply bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200;
}

.toggle-switch {
  @apply relative inline-flex items-center cursor-pointer;
}

.toggle-switch input {
  @apply sr-only;
}

.toggle-slider {
  @apply w-11 h-6 bg-gray-200 dark:bg-gray-700 rounded-full relative transition-colors duration-200;
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

.action-buttons {
  @apply flex space-x-1;
}

.action-btn {
  @apply p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded;
}

.empty-state {
  @apply p-8 text-center;
}

.baselines-grid {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4;
}

.baseline-card {
  @apply border border-gray-200 dark:border-gray-700 rounded-lg p-4;
}

.baseline-header {
  @apply flex items-center justify-between mb-3;
}

.baseline-title {
  @apply font-medium text-gray-900 dark:text-white;
}

.baseline-content {
  @apply space-y-3;
}

.baseline-value, .baseline-tolerance, .baseline-window {
  @apply space-y-1;
}

.form-input-sm {
  @apply w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500;
}

.baseline-status {
  @apply mt-3 pt-3 border-t border-gray-200 dark:border-gray-700;
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

.alert-item.critical {
  @apply border-purple-200 dark:border-purple-800 bg-purple-50 dark:bg-purple-900/20;
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

.alert-actions {
  @apply flex space-x-1;
}
</style>