<template>
  <div class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-container" @click.stop>
      <!-- Modal Header -->
      <div class="modal-header">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">
          {{ rule ? '编辑告警规则' : '创建告警规则' }}
        </h3>
        <button @click="$emit('close')" class="modal-close-btn">
          <XMarkIcon class="w-5 h-5" />
        </button>
      </div>
      
      <!-- Modal Body -->
      <div class="modal-body">
        <form @submit.prevent="saveRule" class="space-y-6">
          <!-- Basic Information -->
          <div class="form-section">
            <h4 class="section-title">基本信息</h4>
            <div class="form-grid">
              <div class="form-group">
                <label class="form-label">规则名称 *</label>
                <input
                  v-model="formData.name"
                  type="text"
                  class="form-input"
                  placeholder="输入规则名称"
                  required
                />
                <div v-if="errors.name" class="form-error">{{ errors.name }}</div>
              </div>
              
              <div class="form-group">
                <label class="form-label">描述</label>
                <textarea
                  v-model="formData.description"
                  class="form-textarea"
                  rows="2"
                  placeholder="输入规则描述（可选）"
                ></textarea>
              </div>
            </div>
          </div>
          
          <!-- Metric Configuration -->
          <div class="form-section">
            <h4 class="section-title">监控配置</h4>
            <div class="form-grid">
              <div class="form-group">
                <label class="form-label">监控指标 *</label>
                <select v-model="formData.metric_name" class="form-select" required>
                  <option value="">选择监控指标</option>
                  <optgroup label="系统指标">
                    <option value="cpu_percent">CPU使用率 (%)</option>
                    <option value="memory_percent">内存使用率 (%)</option>
                    <option value="memory_mb">内存使用量 (MB)</option>
                    <option value="disk_percent">磁盘使用率 (%)</option>
                    <option value="disk_io_read">磁盘读取速率 (MB/s)</option>
                    <option value="disk_io_write">磁盘写入速率 (MB/s)</option>
                    <option value="network_bytes_sent">网络发送 (bytes/s)</option>
                    <option value="network_bytes_recv">网络接收 (bytes/s)</option>
                  </optgroup>
                  <optgroup label="服务器指标">
                    <option value="tps">TPS (tick/s)</option>
                    <option value="mspt">MSPT (ms)</option>
                    <option value="online_players">在线玩家数</option>
                    <option value="chunks_loaded">已加载区块数</option>
                    <option value="entities_count">实体数量</option>
                  </optgroup>
                  <optgroup label="JVM指标">
                    <option value="heap_memory_used">堆内存使用 (MB)</option>
                    <option value="heap_memory_percent">堆内存使用率 (%)</option>
                    <option value="gc_time">GC时间 (ms)</option>
                    <option value="gc_collections">GC次数</option>
                    <option value="thread_count">线程数</option>
                  </optgroup>
                </select>
                <div v-if="errors.metric_name" class="form-error">{{ errors.metric_name }}</div>
              </div>
              
              <div class="form-group">
                <label class="form-label">条件操作符 *</label>
                <select v-model="formData.operator" class="form-select" required>
                  <option value="">选择操作符</option>
                  <option value=">">&gt; 大于</option>
                  <option value=">=">&gt;= 大于等于</option>
                  <option value="<">&lt; 小于</option>
                  <option value="<=">&lt;= 小于等于</option>
                  <option value="==">=== 等于</option>
                  <option value="!=">&ne; 不等于</option>
                </select>
                <div v-if="errors.operator" class="form-error">{{ errors.operator }}</div>
              </div>
              
              <div class="form-group">
                <label class="form-label">
                  阈值 * 
                  <span v-if="getMetricUnit(formData.metric_name)" class="text-gray-500">
                    ({{ getMetricUnit(formData.metric_name) }})
                  </span>
                </label>
                <input
                  v-model.number="formData.threshold"
                  type="number"
                  step="0.1"
                  class="form-input"
                  placeholder="输入阈值"
                  required
                />
                <div v-if="errors.threshold" class="form-error">{{ errors.threshold }}</div>
              </div>
              
              <div class="form-group">
                <label class="form-label">持续时间 (秒) *</label>
                <select v-model.number="formData.duration" class="form-select" required>
                  <option :value="30">30秒</option>
                  <option :value="60">1分钟</option>
                  <option :value="120">2分钟</option>
                  <option :value="300">5分钟</option>
                  <option :value="600">10分钟</option>
                  <option :value="1800">30分钟</option>
                </select>
                <div class="help-text">条件满足多长时间后触发告警</div>
              </div>
            </div>
          </div>
          
          <!-- Alert Settings -->
          <div class="form-section">
            <h4 class="section-title">告警设置</h4>
            <div class="form-grid">
              <div class="form-group">
                <label class="form-label">严重级别 *</label>
                <div class="severity-options">
                  <label
                    v-for="severity in severityOptions"
                    :key="severity.value"
                    class="severity-option"
                    :class="{ active: formData.severity === severity.value }"
                  >
                    <input
                      v-model="formData.severity"
                      type="radio"
                      :value="severity.value"
                      class="sr-only"
                    />
                    <div class="severity-indicator" :class="severity.value"></div>
                    <span class="severity-label">{{ severity.label }}</span>
                  </label>
                </div>
              </div>
              
              <div class="form-group">
                <label class="form-label">冷却时间 (秒)</label>
                <select v-model.number="formData.cooldown_seconds" class="form-select">
                  <option :value="0">无冷却</option>
                  <option :value="300">5分钟</option>
                  <option :value="600">10分钟</option>
                  <option :value="900">15分钟</option>
                  <option :value="1800">30分钟</option>
                  <option :value="3600">1小时</option>
                </select>
                <div class="help-text">同一告警的最小间隔时间</div>
              </div>
            </div>
          </div>
          
          <!-- Notification Channels -->
          <div class="form-section">
            <h4 class="section-title">通知渠道</h4>
            <div class="notification-channels">
              <label
                v-for="channel in notificationChannels"
                :key="channel.value"
                class="channel-option"
              >
                <input
                  v-model="formData.notification_channels"
                  type="checkbox"
                  :value="channel.value"
                  class="form-checkbox"
                />
                <div class="channel-info">
                  <component :is="channel.icon" class="w-5 h-5" />
                  <span class="channel-label">{{ channel.label }}</span>
                </div>
                <div v-if="channel.description" class="channel-description">
                  {{ channel.description }}
                </div>
              </label>
            </div>
          </div>
          
          <!-- Advanced Settings -->
          <div class="form-section">
            <div class="section-header">
              <h4 class="section-title">高级设置</h4>
              <button
                type="button"
                @click="showAdvanced = !showAdvanced"
                class="toggle-advanced-btn"
              >
                {{ showAdvanced ? '收起' : '展开' }}
                <ChevronDownIcon 
                  class="w-4 h-4 ml-1 transition-transform"
                  :class="{ 'rotate-180': showAdvanced }"
                />
              </button>
            </div>
            
            <div v-show="showAdvanced" class="advanced-settings">
              <div class="form-grid">
                <div class="form-group">
                  <label class="form-label">聚合方式</label>
                  <select v-model="formData.aggregation" class="form-select">
                    <option value="avg">平均值</option>
                    <option value="max">最大值</option>
                    <option value="min">最小值</option>
                    <option value="sum">求和</option>
                    <option value="count">计数</option>
                  </select>
                  <div class="help-text">在持续时间内如何聚合指标值</div>
                </div>
                
                <div class="form-group">
                  <label class="form-label">条件表达式</label>
                  <textarea
                    v-model="formData.condition_expression"
                    class="form-textarea"
                    rows="3"
                    placeholder="高级条件表达式（可选）"
                  ></textarea>
                  <div class="help-text">使用JavaScript表达式定义复杂条件</div>
                </div>
              </div>
              
              <div class="form-group">
                <label class="checkbox-item">
                  <input
                    v-model="formData.auto_resolve"
                    type="checkbox"
                    class="form-checkbox"
                  />
                  <span>自动解决告警</span>
                </label>
                <div class="help-text">当条件不再满足时自动标记告警为已解决</div>
              </div>
            </div>
          </div>
          
          <!-- Rule Test -->
          <div class="form-section">
            <h4 class="section-title">规则测试</h4>
            <div class="test-section">
              <button
                type="button"
                @click="testRule"
                :disabled="!isFormValid || testing"
                class="btn btn-secondary"
              >
                <BeakerIcon class="w-4 h-4 mr-2" />
                {{ testing ? '测试中...' : '测试规则' }}
              </button>
              <div class="help-text">使用当前配置测试告警规则</div>
              
              <div v-if="testResult" class="test-result" :class="testResult.type">
                <div class="result-icon">
                  <CheckCircleIcon v-if="testResult.type === 'success'" class="w-5 h-5" />
                  <ExclamationTriangleIcon v-else class="w-5 h-5" />
                </div>
                <div class="result-content">
                  <div class="result-title">{{ testResult.title }}</div>
                  <div class="result-message">{{ testResult.message }}</div>
                </div>
              </div>
            </div>
          </div>
        </form>
      </div>
      
      <!-- Modal Footer -->
      <div class="modal-footer">
        <div class="footer-left">
          <label class="checkbox-item">
            <input
              v-model="formData.enabled"
              type="checkbox"
              class="form-checkbox"
            />
            <span>启用此规则</span>
          </label>
        </div>
        
        <div class="footer-actions">
          <button 
            type="button"
            @click="$emit('close')" 
            class="btn btn-secondary"
          >
            取消
          </button>
          <button 
            type="button"
            @click="saveRule"
            :disabled="!isFormValid"
            class="btn btn-primary"
          >
            {{ rule ? '更新规则' : '创建规则' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import {
  XMarkIcon,
  ChevronDownIcon,
  BeakerIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  BellIcon,
  EnvelopeIcon,
  ChatBubbleLeftIcon,
  DevicePhoneMobileIcon
} from '@heroicons/vue/24/outline'

interface AlertRule {
  id?: string
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
  aggregation?: string
  condition_expression?: string
  auto_resolve?: boolean
}

interface Props {
  rule?: AlertRule | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  save: [rule: AlertRule]
  close: []
}>()

// Form state
const formData = ref<AlertRule>({
  name: '',
  description: '',
  metric_name: '',
  operator: '',
  threshold: 0,
  duration: 300,
  severity: 'warning',
  enabled: true,
  notification_channels: ['web'],
  cooldown_seconds: 900,
  aggregation: 'avg',
  condition_expression: '',
  auto_resolve: true
})

const errors = ref<Record<string, string>>({})
const showAdvanced = ref(false)
const testing = ref(false)
const testResult = ref<any>(null)

// Options
const severityOptions = [
  { value: 'info', label: '信息', color: 'blue' },
  { value: 'warning', label: '警告', color: 'yellow' },
  { value: 'error', label: '错误', color: 'red' },
  { value: 'critical', label: '严重', color: 'purple' }
]

const notificationChannels = [
  {
    value: 'web',
    label: 'Web通知',
    description: '在Web界面显示通知',
    icon: BellIcon
  },
  {
    value: 'email',
    label: '邮件通知',
    description: '发送邮件到配置的地址',
    icon: EnvelopeIcon
  },
  {
    value: 'webhook',
    label: 'Webhook',
    description: '发送HTTP请求到指定URL',
    icon: ChatBubbleLeftIcon
  },
  {
    value: 'sms',
    label: '短信通知',
    description: '发送短信到管理员手机',
    icon: DevicePhoneMobileIcon
  }
]

// Computed
const isFormValid = computed(() => {
  return formData.value.name.trim() &&
         formData.value.metric_name &&
         formData.value.operator &&
         formData.value.threshold !== null &&
         formData.value.duration > 0 &&
         formData.value.severity &&
         formData.value.notification_channels.length > 0
})

// Methods
const getMetricUnit = (metric: string): string => {
  const units: Record<string, string> = {
    'cpu_percent': '%',
    'memory_percent': '%',
    'memory_mb': 'MB',
    'disk_percent': '%',
    'disk_io_read': 'MB/s',
    'disk_io_write': 'MB/s',
    'network_bytes_sent': 'bytes/s',
    'network_bytes_recv': 'bytes/s',
    'tps': 'tick/s',
    'mspt': 'ms',
    'online_players': '人',
    'chunks_loaded': '个',
    'entities_count': '个',
    'heap_memory_used': 'MB',
    'heap_memory_percent': '%',
    'gc_time': 'ms',
    'gc_collections': '次',
    'thread_count': '个'
  }
  return units[metric] || ''
}

const validateForm = (): boolean => {
  errors.value = {}
  
  if (!formData.value.name.trim()) {
    errors.value.name = '规则名称不能为空'
  }
  
  if (!formData.value.metric_name) {
    errors.value.metric_name = '请选择监控指标'
  }
  
  if (!formData.value.operator) {
    errors.value.operator = '请选择条件操作符'
  }
  
  if (formData.value.threshold === null || formData.value.threshold === undefined) {
    errors.value.threshold = '请输入阈值'
  }
  
  return Object.keys(errors.value).length === 0
}

const testRule = async () => {
  if (!validateForm()) return
  
  testing.value = true
  testResult.value = null
  
  try {
    // TODO: Implement API call to test rule
    await new Promise(resolve => setTimeout(resolve, 1000)) // Mock delay
    
    // Mock test result
    const wouldTrigger = Math.random() > 0.5
    
    testResult.value = {
      type: wouldTrigger ? 'warning' : 'success',
      title: wouldTrigger ? '规则会触发告警' : '规则测试通过',
      message: wouldTrigger 
        ? '基于当前数据，此规则会立即触发告警'
        : '基于当前数据，此规则不会触发告警'
    }
  } catch (error) {
    testResult.value = {
      type: 'error',
      title: '测试失败',
      message: '规则测试时发生错误，请检查配置'
    }
  } finally {
    testing.value = false
  }
}

const saveRule = () => {
  if (!validateForm()) return
  
  emit('save', { ...formData.value })
}

const handleOverlayClick = () => {
  emit('close')
}

// Initialize form data
watch(() => props.rule, (newRule) => {
  if (newRule) {
    formData.value = { ...newRule }
  } else {
    // Reset form for new rule
    formData.value = {
      name: '',
      description: '',
      metric_name: '',
      operator: '',
      threshold: 0,
      duration: 300,
      severity: 'warning',
      enabled: true,
      notification_channels: ['web'],
      cooldown_seconds: 900,
      aggregation: 'avg',
      condition_expression: '',
      auto_resolve: true
    }
  }
  errors.value = {}
  testResult.value = null
}, { immediate: true })
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

.footer-actions {
  @apply flex space-x-3;
}

.form-section {
  @apply space-y-4;
}

.section-title {
  @apply text-lg font-medium text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-700 pb-2;
}

.section-header {
  @apply flex items-center justify-between;
}

.toggle-advanced-btn {
  @apply flex items-center text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300;
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

.form-textarea {
  @apply resize-none;
}

.form-checkbox {
  @apply rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500;
}

.form-error {
  @apply text-sm text-red-600 dark:text-red-400;
}

.help-text {
  @apply text-xs text-gray-500 dark:text-gray-400;
}

.severity-options {
  @apply grid grid-cols-2 md:grid-cols-4 gap-2;
}

.severity-option {
  @apply flex items-center space-x-2 p-3 border border-gray-200 dark:border-gray-700 rounded-lg cursor-pointer hover:border-blue-300 dark:hover:border-blue-600 transition-colors;
}

.severity-option.active {
  @apply border-blue-500 bg-blue-50 dark:bg-blue-900/20;
}

.severity-indicator {
  @apply w-3 h-3 rounded-full;
}

.severity-indicator.info {
  @apply bg-gray-400;
}

.severity-indicator.warning {
  @apply bg-yellow-400;
}

.severity-indicator.error {
  @apply bg-red-400;
}

.severity-indicator.critical {
  @apply bg-purple-400;
}

.severity-label {
  @apply text-sm font-medium text-gray-700 dark:text-gray-300;
}

.notification-channels {
  @apply space-y-3;
}

.channel-option {
  @apply flex items-start space-x-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg;
}

.channel-info {
  @apply flex items-center space-x-2;
}

.channel-label {
  @apply font-medium text-gray-900 dark:text-white;
}

.channel-description {
  @apply text-sm text-gray-500 dark:text-gray-400 mt-1;
}

.advanced-settings {
  @apply mt-4 space-y-4;
}

.checkbox-item {
  @apply flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300;
}

.test-section {
  @apply space-y-3;
}

.test-result {
  @apply flex items-start space-x-3 p-3 rounded-lg border;
}

.test-result.success {
  @apply border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20;
}

.test-result.warning {
  @apply border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/20;
}

.test-result.error {
  @apply border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20;
}

.result-icon {
  @apply flex-shrink-0;
}

.result-content {
  @apply flex-1;
}

.result-title {
  @apply font-medium text-gray-900 dark:text-white;
}

.result-message {
  @apply text-sm text-gray-600 dark:text-gray-400 mt-1;
}
</style>