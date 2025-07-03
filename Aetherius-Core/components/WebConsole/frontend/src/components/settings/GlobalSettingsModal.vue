<template>
  <div class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-container" @click.stop>
      <!-- Modal Header -->
      <div class="modal-header">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">
          全局设置
        </h3>
        <button @click="$emit('close')" class="modal-close-btn">
          <XMarkIcon class="w-5 h-5" />
        </button>
      </div>
      
      <!-- Modal Body -->
      <div class="modal-body">
        <div class="settings-tabs">
          <button
            v-for="tab in settingsTabs"
            :key="tab.key"
            @click="activeTab = tab.key"
            class="tab-button"
            :class="{ active: activeTab === tab.key }"
          >
            <component :is="tab.icon" class="w-4 h-4" />
            {{ tab.label }}
          </button>
        </div>
        
        <div class="settings-content">
          <!-- General Settings -->
          <div v-show="activeTab === 'general'" class="settings-section">
            <h4 class="section-title">常规设置</h4>
            <div class="settings-grid">
              <div class="setting-item">
                <label class="setting-label">自动刷新间隔</label>
                <select v-model="settings.refreshInterval" class="form-select">
                  <option :value="15">15秒</option>
                  <option :value="30">30秒</option>
                  <option :value="60">1分钟</option>
                  <option :value="300">5分钟</option>
                </select>
              </div>
              
              <div class="setting-item">
                <label class="setting-label">数据保留天数</label>
                <input
                  v-model.number="settings.dataRetentionDays"
                  type="number"
                  min="1"
                  max="365"
                  class="form-input"
                />
              </div>
              
              <div class="setting-item">
                <label class="checkbox-item">
                  <input
                    v-model="settings.enableNotifications"
                    type="checkbox"
                    class="form-checkbox"
                  />
                  <span>启用桌面通知</span>
                </label>
              </div>
              
              <div class="setting-item">
                <label class="checkbox-item">
                  <input
                    v-model="settings.autoStartMonitoring"
                    type="checkbox"
                    class="form-checkbox"
                  />
                  <span>启动时自动开始监控</span>
                </label>
              </div>
            </div>
          </div>
          
          <!-- Performance Settings -->
          <div v-show="activeTab === 'performance'" class="settings-section">
            <h4 class="section-title">性能设置</h4>
            <div class="settings-grid">
              <div class="setting-item">
                <label class="setting-label">监控精度</label>
                <select v-model="settings.monitoringPrecision" class="form-select">
                  <option value="low">低 - 节省资源</option>
                  <option value="medium">中 - 平衡</option>
                  <option value="high">高 - 最详细</option>
                </select>
              </div>
              
              <div class="setting-item">
                <label class="setting-label">最大并发连接</label>
                <input
                  v-model.number="settings.maxConnections"
                  type="number"
                  min="1"
                  max="1000"
                  class="form-input"
                />
              </div>
              
              <div class="setting-item">
                <label class="checkbox-item">
                  <input
                    v-model="settings.enableCaching"
                    type="checkbox"
                    class="form-checkbox"
                  />
                  <span>启用数据缓存</span>
                </label>
              </div>
              
              <div class="setting-item">
                <label class="checkbox-item">
                  <input
                    v-model="settings.enableCompression"
                    type="checkbox"
                    class="form-checkbox"
                  />
                  <span>启用数据压缩</span>
                </label>
              </div>
            </div>
          </div>
          
          <!-- Alerts Settings -->
          <div v-show="activeTab === 'alerts'" class="settings-section">
            <h4 class="section-title">告警设置</h4>
            <div class="settings-grid">
              <div class="setting-item">
                <label class="setting-label">默认告警级别</label>
                <select v-model="settings.defaultAlertLevel" class="form-select">
                  <option value="info">信息</option>
                  <option value="warning">警告</option>
                  <option value="error">错误</option>
                  <option value="critical">严重</option>
                </select>
              </div>
              
              <div class="setting-item">
                <label class="setting-label">告警冷却时间 (秒)</label>
                <input
                  v-model.number="settings.alertCooldown"
                  type="number"
                  min="0"
                  max="3600"
                  class="form-input"
                />
              </div>
              
              <div class="setting-item">
                <label class="checkbox-item">
                  <input
                    v-model="settings.enableEmailAlerts"
                    type="checkbox"
                    class="form-checkbox"
                  />
                  <span>启用邮件告警</span>
                </label>
              </div>
              
              <div class="setting-item">
                <label class="checkbox-item">
                  <input
                    v-model="settings.enableWebhookAlerts"
                    type="checkbox"
                    class="form-checkbox"
                  />
                  <span>启用Webhook告警</span>
                </label>
              </div>
            </div>
          </div>
          
          <!-- Theme Settings -->
          <div v-show="activeTab === 'theme'" class="settings-section">
            <h4 class="section-title">主题设置</h4>
            <div class="settings-grid">
              <div class="setting-item">
                <label class="setting-label">主题模式</label>
                <select v-model="settings.theme" class="form-select">
                  <option value="auto">自动</option>
                  <option value="light">浅色</option>
                  <option value="dark">深色</option>
                </select>
              </div>
              
              <div class="setting-item">
                <label class="setting-label">主色调</label>
                <div class="color-options">
                  <label
                    v-for="color in colorOptions"
                    :key="color.value"
                    class="color-option"
                    :class="{ active: settings.primaryColor === color.value }"
                  >
                    <input
                      v-model="settings.primaryColor"
                      type="radio"
                      :value="color.value"
                      class="sr-only"
                    />
                    <div class="color-swatch" :style="{ backgroundColor: color.color }"></div>
                    <span class="color-name">{{ color.name }}</span>
                  </label>
                </div>
              </div>
              
              <div class="setting-item">
                <label class="checkbox-item">
                  <input
                    v-model="settings.enableAnimations"
                    type="checkbox"
                    class="form-checkbox"
                  />
                  <span>启用动画效果</span>
                </label>
              </div>
              
              <div class="setting-item">
                <label class="checkbox-item">
                  <input
                    v-model="settings.compactMode"
                    type="checkbox"
                    class="form-checkbox"
                  />
                  <span>紧凑模式</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Modal Footer -->
      <div class="modal-footer">
        <div class="footer-left">
          <button @click="resetToDefaults" class="btn btn-secondary">
            重置默认值
          </button>
        </div>
        
        <div class="footer-actions">
          <button @click="$emit('close')" class="btn btn-secondary">
            取消
          </button>
          <button @click="saveSettings" class="btn btn-primary">
            保存设置
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
  Cog6ToothIcon,
  BoltIcon,
  BellIcon,
  PaintBrushIcon
} from '@heroicons/vue/24/outline'

const emit = defineEmits<{
  save: [settings: any]
  close: []
}>()

// Active tab
const activeTab = ref('general')

// Settings tabs
const settingsTabs = [
  { key: 'general', label: '常规', icon: Cog6ToothIcon },
  { key: 'performance', label: '性能', icon: BoltIcon },
  { key: 'alerts', label: '告警', icon: BellIcon },
  { key: 'theme', label: '主题', icon: PaintBrushIcon }
]

// Settings data
const settings = ref({
  // General
  refreshInterval: 30,
  dataRetentionDays: 90,
  enableNotifications: true,
  autoStartMonitoring: true,
  
  // Performance
  monitoringPrecision: 'medium',
  maxConnections: 100,
  enableCaching: true,
  enableCompression: true,
  
  // Alerts
  defaultAlertLevel: 'warning',
  alertCooldown: 300,
  enableEmailAlerts: false,
  enableWebhookAlerts: false,
  
  // Theme
  theme: 'auto',
  primaryColor: 'blue',
  enableAnimations: true,
  compactMode: false
})

// Color options
const colorOptions = [
  { value: 'blue', name: '蓝色', color: '#3b82f6' },
  { value: 'green', name: '绿色', color: '#10b981' },
  { value: 'purple', name: '紫色', color: '#8b5cf6' },
  { value: 'red', name: '红色', color: '#ef4444' },
  { value: 'yellow', name: '黄色', color: '#f59e0b' }
]

// Methods
const saveSettings = () => {
  emit('save', { ...settings.value })
}

const resetToDefaults = () => {
  settings.value = {
    refreshInterval: 30,
    dataRetentionDays: 90,
    enableNotifications: true,
    autoStartMonitoring: true,
    monitoringPrecision: 'medium',
    maxConnections: 100,
    enableCaching: true,
    enableCompression: true,
    defaultAlertLevel: 'warning',
    alertCooldown: 300,
    enableEmailAlerts: false,
    enableWebhookAlerts: false,
    theme: 'auto',
    primaryColor: 'blue',
    enableAnimations: true,
    compactMode: false
  }
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
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col;
}

.modal-header {
  @apply flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700;
}

.modal-close-btn {
  @apply p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded;
}

.modal-body {
  @apply flex-1 overflow-hidden flex;
}

.modal-footer {
  @apply flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900;
}

.footer-left {
  @apply flex items-center;
}

.footer-actions {
  @apply flex space-x-3;
}

.settings-tabs {
  @apply flex flex-col w-48 border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900;
}

.tab-button {
  @apply flex items-center space-x-3 px-4 py-3 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 border-r-2 border-transparent transition-colors;
}

.tab-button.active {
  @apply text-blue-600 dark:text-blue-400 bg-white dark:bg-gray-800 border-blue-500;
}

.settings-content {
  @apply flex-1 overflow-y-auto p-6;
}

.settings-section {
  @apply space-y-6;
}

.section-title {
  @apply text-lg font-medium text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-700 pb-2;
}

.settings-grid {
  @apply grid grid-cols-1 md:grid-cols-2 gap-6;
}

.setting-item {
  @apply space-y-2;
}

.setting-label {
  @apply block text-sm font-medium text-gray-700 dark:text-gray-300;
}

.form-input, .form-select {
  @apply w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500;
}

.form-checkbox {
  @apply rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500;
}

.checkbox-item {
  @apply flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300;
}

.color-options {
  @apply grid grid-cols-3 gap-3;
}

.color-option {
  @apply flex flex-col items-center text-center p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-300 dark:hover:border-blue-600 cursor-pointer transition-colors;
}

.color-option.active {
  @apply border-blue-500 bg-blue-50 dark:bg-blue-900/20;
}

.color-swatch {
  @apply w-8 h-8 rounded-full mb-2;
}

.color-name {
  @apply text-sm font-medium text-gray-700 dark:text-gray-300;
}
</style>