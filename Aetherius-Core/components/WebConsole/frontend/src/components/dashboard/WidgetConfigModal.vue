<template>
  <div class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-container" @click.stop>
      <!-- Modal Header -->
      <div class="modal-header">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">
          配置组件 - {{ widget?.title }}
        </h3>
        <button @click="$emit('close')" class="modal-close-btn">
          <XMarkIcon class="w-5 h-5" />
        </button>
      </div>
      
      <!-- Modal Body -->
      <div class="modal-body">
        <div v-if="widget" class="config-sections">
          <!-- Basic Settings -->
          <div class="config-section">
            <h4 class="section-title">基础设置</h4>
            <div class="config-grid">
              <!-- Widget Title -->
              <div class="config-item">
                <label class="config-label">组件标题</label>
                <input
                  v-model="localConfig.title"
                  type="text"
                  class="form-input"
                  placeholder="输入组件标题"
                />
              </div>
              
              <!-- Widget Size -->
              <div class="config-item">
                <label class="config-label">组件大小</label>
                <div class="size-controls">
                  <div class="size-control">
                    <label class="text-xs text-gray-500">宽度</label>
                    <input
                      v-model.number="localConfig.size.width"
                      type="number"
                      min="1"
                      max="12"
                      class="form-input-sm"
                    />
                  </div>
                  <div class="size-control">
                    <label class="text-xs text-gray-500">高度</label>
                    <input
                      v-model.number="localConfig.size.height"
                      type="number"
                      min="1"
                      max="10"
                      class="form-input-sm"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Widget-specific Configuration -->
          <div class="config-section">
            <h4 class="section-title">专用设置</h4>
            
            <!-- Metric Chart Configuration -->
            <div v-if="widget.type === 'metric_chart'" class="widget-config">
              <div class="config-grid">
                <div class="config-item">
                  <label class="config-label">监控指标</label>
                  <select v-model="localConfig.config.metric" class="form-select">
                    <option value="cpu_percent">CPU使用率</option>
                    <option value="memory_percent">内存使用率</option>
                    <option value="memory_mb">内存使用量</option>
                    <option value="tps">TPS</option>
                    <option value="mspt">MSPT</option>
                    <option value="disk_percent">磁盘使用率</option>
                    <option value="network_bytes">网络流量</option>
                  </select>
                </div>
                
                <div class="config-item">
                  <label class="config-label">图表类型</label>
                  <select v-model="localConfig.config.chartType" class="form-select">
                    <option value="line">线图</option>
                    <option value="area">面积图</option>
                    <option value="bar">柱状图</option>
                  </select>
                </div>
                
                <div class="config-item">
                  <label class="config-label">时间范围</label>
                  <select v-model="localConfig.config.timeRange" class="form-select">
                    <option value="5m">5分钟</option>
                    <option value="15m">15分钟</option>
                    <option value="1h">1小时</option>
                    <option value="6h">6小时</option>
                    <option value="24h">24小时</option>
                  </select>
                </div>
                
                <div class="config-item">
                  <label class="config-label">显示选项</label>
                  <div class="checkbox-group">
                    <label class="checkbox-item">
                      <input
                        v-model="localConfig.config.showStats"
                        type="checkbox"
                        class="form-checkbox"
                      />
                      <span>显示统计</span>
                    </label>
                    <label class="checkbox-item">
                      <input
                        v-model="localConfig.config.showLegend"
                        type="checkbox"
                        class="form-checkbox"
                      />
                      <span>显示图例</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Server Status Configuration -->
            <div v-else-if="widget.type === 'server_status'" class="widget-config">
              <div class="config-grid">
                <div class="config-item">
                  <label class="config-label">显示选项</label>
                  <div class="checkbox-group">
                    <label class="checkbox-item">
                      <input
                        v-model="localConfig.config.showUptime"
                        type="checkbox"
                        class="form-checkbox"
                      />
                      <span>显示运行时间</span>
                    </label>
                    <label class="checkbox-item">
                      <input
                        v-model="localConfig.config.showPlayers"
                        type="checkbox"
                        class="form-checkbox"
                      />
                      <span>显示玩家数</span>
                    </label>
                    <label class="checkbox-item">
                      <input
                        v-model="localConfig.config.showVersion"
                        type="checkbox"
                        class="form-checkbox"
                      />
                      <span>显示版本信息</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Resource Usage Configuration -->
            <div v-else-if="widget.type === 'resource_usage'" class="widget-config">
              <div class="config-grid">
                <div class="config-item">
                  <label class="config-label">监控资源</label>
                  <div class="checkbox-group">
                    <label class="checkbox-item">
                      <input
                        v-model="localConfig.config.resources"
                        type="checkbox"
                        value="cpu"
                        class="form-checkbox"
                      />
                      <span>CPU</span>
                    </label>
                    <label class="checkbox-item">
                      <input
                        v-model="localConfig.config.resources"
                        type="checkbox"
                        value="memory"
                        class="form-checkbox"
                      />
                      <span>内存</span>
                    </label>
                    <label class="checkbox-item">
                      <input
                        v-model="localConfig.config.resources"
                        type="checkbox"
                        value="disk"
                        class="form-checkbox"
                      />
                      <span>磁盘</span>
                    </label>
                  </div>
                </div>
                
                <div class="config-item">
                  <label class="config-label">显示类型</label>
                  <select v-model="localConfig.config.displayType" class="form-select">
                    <option value="gauge">仪表盘</option>
                    <option value="progress">进度条</option>
                    <option value="numeric">数值</option>
                  </select>
                </div>
              </div>
            </div>
            
            <!-- Player List Configuration -->
            <div v-else-if="widget.type === 'player_list'" class="widget-config">
              <div class="config-grid">
                <div class="config-item">
                  <label class="config-label">最大显示数量</label>
                  <input
                    v-model.number="localConfig.config.maxPlayers"
                    type="number"
                    min="1"
                    max="50"
                    class="form-input"
                  />
                </div>
                
                <div class="config-item">
                  <label class="config-label">显示选项</label>
                  <div class="checkbox-group">
                    <label class="checkbox-item">
                      <input
                        v-model="localConfig.config.showAvatar"
                        type="checkbox"
                        class="form-checkbox"
                      />
                      <span>显示头像</span>
                    </label>
                    <label class="checkbox-item">
                      <input
                        v-model="localConfig.config.showLocation"
                        type="checkbox"
                        class="form-checkbox"
                      />
                      <span>显示位置</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Alerts Configuration -->
            <div v-else-if="widget.type === 'alerts'" class="widget-config">
              <div class="config-grid">
                <div class="config-item">
                  <label class="config-label">最大显示数量</label>
                  <input
                    v-model.number="localConfig.config.maxAlerts"
                    type="number"
                    min="1"
                    max="20"
                    class="form-input"
                  />
                </div>
                
                <div class="config-item">
                  <label class="config-label">严重级别过滤</label>
                  <div class="checkbox-group">
                    <label class="checkbox-item">
                      <input
                        v-model="localConfig.config.severityFilter"
                        type="checkbox"
                        value="info"
                        class="form-checkbox"
                      />
                      <span>信息</span>
                    </label>
                    <label class="checkbox-item">
                      <input
                        v-model="localConfig.config.severityFilter"
                        type="checkbox"
                        value="warning"
                        class="form-checkbox"
                      />
                      <span>警告</span>
                    </label>
                    <label class="checkbox-item">
                      <input
                        v-model="localConfig.config.severityFilter"
                        type="checkbox"
                        value="error"
                        class="form-checkbox"
                      />
                      <span>错误</span>
                    </label>
                  </div>
                </div>
                
                <div class="config-item">
                  <label class="checkbox-item">
                    <input
                      v-model="localConfig.config.autoHide"
                      type="checkbox"
                      class="form-checkbox"
                    />
                    <span>自动隐藏已解决警报</span>
                  </label>
                </div>
              </div>
            </div>
            
            <!-- Performance Summary Configuration -->
            <div v-else-if="widget.type === 'performance_summary'" class="widget-config">
              <div class="config-grid">
                <div class="config-item">
                  <label class="config-label">显示指标</label>
                  <div class="checkbox-group">
                    <label class="checkbox-item">
                      <input
                        v-model="localConfig.config.metrics"
                        type="checkbox"
                        value="tps"
                        class="form-checkbox"
                      />
                      <span>TPS</span>
                    </label>
                    <label class="checkbox-item">
                      <input
                        v-model="localConfig.config.metrics"
                        type="checkbox"
                        value="cpu_percent"
                        class="form-checkbox"
                      />
                      <span>CPU使用率</span>
                    </label>
                    <label class="checkbox-item">
                      <input
                        v-model="localConfig.config.metrics"
                        type="checkbox"
                        value="memory_percent"
                        class="form-checkbox"
                      />
                      <span>内存使用率</span>
                    </label>
                  </div>
                </div>
                
                <div class="config-item">
                  <label class="config-label">布局方式</label>
                  <select v-model="localConfig.config.layout" class="form-select">
                    <option value="horizontal">水平布局</option>
                    <option value="vertical">垂直布局</option>
                    <option value="grid">网格布局</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Appearance Settings -->
          <div class="config-section">
            <h4 class="section-title">外观设置</h4>
            <div class="config-grid">
              <div class="config-item">
                <label class="config-label">边框样式</label>
                <select v-model="localConfig.config.borderStyle" class="form-select">
                  <option value="none">无边框</option>
                  <option value="solid">实线边框</option>
                  <option value="dashed">虚线边框</option>
                  <option value="rounded">圆角边框</option>
                </select>
              </div>
              
              <div class="config-item">
                <label class="config-label">背景透明度</label>
                <input
                  v-model.number="localConfig.config.opacity"
                  type="range"
                  min="0"
                  max="100"
                  class="form-range"
                />
                <span class="text-sm text-gray-500">{{ localConfig.config.opacity }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Modal Footer -->
      <div class="modal-footer">
        <button @click="resetToDefaults" class="btn btn-secondary">
          重置默认
        </button>
        <div class="footer-actions">
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
import { ref, computed, watch, onMounted } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'

interface Widget {
  id: string
  type: string
  title: string
  position: { x: number; y: number }
  size: { width: number; height: number }
  config: Record<string, any>
  enabled: boolean
}

interface Props {
  widget: Widget | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  save: [config: Record<string, any>]
  close: []
}>()

// Local configuration state
const localConfig = ref({
  title: '',
  size: { width: 4, height: 3 },
  config: {}
})

// Default configurations for each widget type
const defaultConfigs: Record<string, any> = {
  metric_chart: {
    metric: 'cpu_percent',
    chartType: 'line',
    timeRange: '1h',
    showStats: true,
    showLegend: false,
    borderStyle: 'solid',
    opacity: 100
  },
  server_status: {
    showUptime: true,
    showPlayers: true,
    showVersion: true,
    borderStyle: 'solid',
    opacity: 100
  },
  resource_usage: {
    resources: ['cpu', 'memory'],
    displayType: 'gauge',
    borderStyle: 'solid',
    opacity: 100
  },
  player_list: {
    maxPlayers: 10,
    showAvatar: true,
    showLocation: true,
    borderStyle: 'solid',
    opacity: 100
  },
  alerts: {
    maxAlerts: 5,
    autoHide: true,
    severityFilter: ['warning', 'error'],
    borderStyle: 'solid',
    opacity: 100
  },
  performance_summary: {
    metrics: ['tps', 'cpu_percent', 'memory_percent'],
    layout: 'horizontal',
    borderStyle: 'solid',
    opacity: 100
  }
}

// Initialize local config when widget changes
watch(() => props.widget, (newWidget) => {
  if (newWidget) {
    localConfig.value = {
      title: newWidget.title,
      size: { ...newWidget.size },
      config: { 
        ...defaultConfigs[newWidget.type], 
        ...newWidget.config 
      }
    }
  }
}, { immediate: true })

// Methods
const saveConfig = () => {
  const config = {
    title: localConfig.value.title,
    size: localConfig.value.size,
    config: localConfig.value.config
  }
  emit('save', config)
}

const resetToDefaults = () => {
  if (props.widget) {
    localConfig.value.config = { ...defaultConfigs[props.widget.type] }
  }
}

const handleOverlayClick = () => {
  emit('close')
}

// Validation
const isConfigValid = computed(() => {
  if (!localConfig.value.title.trim()) return false
  if (localConfig.value.size.width < 1 || localConfig.value.size.height < 1) return false
  return true
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

.footer-actions {
  @apply flex space-x-3;
}

.config-sections {
  @apply space-y-6;
}

.config-section {
  @apply space-y-4;
}

.section-title {
  @apply text-lg font-medium text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-700 pb-2;
}

.config-grid {
  @apply grid grid-cols-1 md:grid-cols-2 gap-4;
}

.config-item {
  @apply space-y-2;
}

.config-label {
  @apply block text-sm font-medium text-gray-700 dark:text-gray-300;
}

.form-input, .form-select {
  @apply w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500;
}

.form-input-sm {
  @apply w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500;
}

.form-checkbox {
  @apply rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500;
}

.form-range {
  @apply w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer;
}

.size-controls {
  @apply flex space-x-3;
}

.size-control {
  @apply flex-1 space-y-1;
}

.checkbox-group {
  @apply space-y-2;
}

.checkbox-item {
  @apply flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300;
}

.widget-config {
  @apply space-y-4;
}
</style>