<template>
  <div class="advanced-monitoring">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">高级性能监控</h1>
        <p class="page-description">
          企业级性能监控和告警管理平台
        </p>
      </div>
      
      <div class="header-actions">
        <button 
          @click="refreshAll"
          :disabled="globalLoading"
          class="btn btn-secondary"
        >
          <ArrowPathIcon 
            class="w-4 h-4 mr-2" 
            :class="{ 'animate-spin': globalLoading }"
          />
          全部刷新
        </button>
        <button 
          @click="showSettings = true"
          class="btn btn-primary"
        >
          <Cog6ToothIcon class="w-4 h-4 mr-2" />
          设置
        </button>
      </div>
    </div>
    
    <!-- Navigation Tabs -->
    <div class="navigation-tabs">
      <nav class="tab-nav">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="activeTab = tab.key"
          class="tab-button"
          :class="{ active: activeTab === tab.key }"
        >
          <component :is="tab.icon" class="w-5 h-5" />
          <span>{{ tab.label }}</span>
          <span v-if="tab.badge" class="tab-badge">{{ tab.badge }}</span>
        </button>
      </nav>
    </div>
    
    <!-- Content Area -->
    <div class="content-area">
      <!-- Dashboard Tab -->
      <div v-show="activeTab === 'dashboard'" class="tab-content">
        <MultiMetricsDashboard />
      </div>
      
      <!-- Customizer Tab -->
      <div v-show="activeTab === 'customizer'" class="tab-content">
        <DashboardCustomizer />
      </div>
      
      <!-- Baseline Tab -->
      <div v-show="activeTab === 'baseline'" class="tab-content">
        <PerformanceBaseline />
      </div>
      
      <!-- Alerts Tab -->
      <div v-show="activeTab === 'alerts'" class="tab-content">
        <AlertManager />
      </div>
      
      <!-- Analytics Tab -->
      <div v-show="activeTab === 'analytics'" class="tab-content">
        <PerformanceAnalytics />
      </div>
      
      <!-- Reports Tab -->
      <div v-show="activeTab === 'reports'" class="tab-content">
        <PerformanceReports />
      </div>
    </div>
    
    <!-- Global Settings Modal -->
    <GlobalSettingsModal
      v-if="showSettings"
      @save="saveGlobalSettings"
      @close="showSettings = false"
    />
    
    <!-- Status Bar -->
    <div class="status-bar">
      <div class="status-left">
        <div class="status-item">
          <div class="status-indicator" :class="systemHealthStatus"></div>
          <span class="status-text">系统状态: {{ systemHealthText }}</span>
        </div>
        <div class="status-item">
          <ClockIcon class="w-4 h-4" />
          <span class="status-text">上次更新: {{ lastUpdateTime }}</span>
        </div>
      </div>
      
      <div class="status-right">
        <div class="status-item">
          <BellIcon class="w-4 h-4" />
          <span class="status-text">活跃告警: {{ activeAlertsCount }}</span>
        </div>
        <div class="status-item">
          <EyeIcon class="w-4 h-4" />
          <span class="status-text">监控指标: {{ activeMetricsCount }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  ArrowPathIcon,
  Cog6ToothIcon,
  ChartBarIcon,
  PaintBrushIcon,
  AdjustmentsHorizontalIcon,
  BellIcon,
  DocumentChartBarIcon,
  ClipboardDocumentListIcon,
  ClockIcon,
  EyeIcon
} from '@heroicons/vue/24/outline'

// Component imports
import MultiMetricsDashboard from '@/components/dashboard/MultiMetricsDashboard.vue'
import DashboardCustomizer from '@/components/dashboard/DashboardCustomizer.vue'
import PerformanceBaseline from '@/components/monitoring/PerformanceBaseline.vue'
import AlertManager from '@/components/alerts/AlertManager.vue'
import PerformanceAnalytics from '@/components/analytics/PerformanceAnalytics.vue'
import PerformanceReports from '@/components/reports/PerformanceReports.vue'
import GlobalSettingsModal from '@/components/settings/GlobalSettingsModal.vue'

// State
const activeTab = ref('dashboard')
const globalLoading = ref(false)
const showSettings = ref(false)
const lastUpdateTime = ref(new Date().toLocaleTimeString('zh-CN'))
const systemHealthStatus = ref('healthy')
const activeAlertsCount = ref(2)
const activeMetricsCount = ref(12)

// Tab configuration
const tabs = [
  {
    key: 'dashboard',
    label: '监控仪表板',
    icon: ChartBarIcon,
    badge: null
  },
  {
    key: 'customizer',
    label: '自定义配置',
    icon: PaintBrushIcon,
    badge: null
  },
  {
    key: 'baseline',
    label: '性能基线',
    icon: AdjustmentsHorizontalIcon,
    badge: null
  },
  {
    key: 'alerts',
    label: '告警管理',
    icon: BellIcon,
    badge: activeAlertsCount.value > 0 ? activeAlertsCount.value : null
  },
  {
    key: 'analytics',
    label: '性能分析',
    icon: DocumentChartBarIcon,
    badge: null
  },
  {
    key: 'reports',
    label: '报告中心',
    icon: ClipboardDocumentListIcon,
    badge: null
  }
]

// Computed
const systemHealthText = computed(() => {
  const statusMap: Record<string, string> = {
    'healthy': '健康',
    'warning': '警告',
    'error': '错误',
    'critical': '严重'
  }
  return statusMap[systemHealthStatus.value] || '未知'
})

// Methods
const refreshAll = async () => {
  globalLoading.value = true
  try {
    // Simulate refresh delay
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // Update last update time
    lastUpdateTime.value = new Date().toLocaleTimeString('zh-CN')
    
    // Emit refresh event to all child components
    window.dispatchEvent(new CustomEvent('global-refresh'))
    
  } finally {
    globalLoading.value = false
  }
}

const saveGlobalSettings = (settings: any) => {
  console.log('Save global settings:', settings)
  showSettings.value = false
}

const updateSystemHealth = () => {
  // Mock system health update
  const statuses = ['healthy', 'warning', 'error']
  const randomIndex = Math.floor(Math.random() * statuses.length)
  systemHealthStatus.value = statuses[randomIndex]
  
  // Update alert count
  activeAlertsCount.value = Math.floor(Math.random() * 5)
  
  // Update metrics count
  activeMetricsCount.value = 10 + Math.floor(Math.random() * 10)
}

// Auto-refresh timer
let refreshTimer: NodeJS.Timeout | null = null

const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    lastUpdateTime.value = new Date().toLocaleTimeString('zh-CN')
    updateSystemHealth()
  }, 30000) // Update every 30 seconds
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// Lifecycle
onMounted(() => {
  startAutoRefresh()
  updateSystemHealth()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.advanced-monitoring {
  @apply min-h-screen bg-gray-50 dark:bg-gray-900;
}

.page-header {
  @apply bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4;
}

.page-header {
  @apply flex items-start justify-between;
}

.header-content h1 {
  @apply text-2xl font-bold text-gray-900 dark:text-white;
}

.page-description {
  @apply text-gray-600 dark:text-gray-400 mt-1;
}

.header-actions {
  @apply flex space-x-3;
}

.navigation-tabs {
  @apply bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6;
}

.tab-nav {
  @apply flex space-x-8 overflow-x-auto;
}

.tab-button {
  @apply flex items-center space-x-2 py-4 px-1 border-b-2 border-transparent text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600 transition-colors whitespace-nowrap;
}

.tab-button.active {
  @apply border-blue-500 text-blue-600 dark:text-blue-400;
}

.tab-badge {
  @apply inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200;
}

.content-area {
  @apply flex-1 p-6;
}

.tab-content {
  @apply space-y-6;
}

.status-bar {
  @apply bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-3 flex items-center justify-between text-sm;
}

.status-left, .status-right {
  @apply flex items-center space-x-6;
}

.status-item {
  @apply flex items-center space-x-2 text-gray-600 dark:text-gray-400;
}

.status-indicator {
  @apply w-2 h-2 rounded-full;
}

.status-indicator.healthy {
  @apply bg-green-500;
}

.status-indicator.warning {
  @apply bg-yellow-500;
}

.status-indicator.error {
  @apply bg-red-500;
}

.status-indicator.critical {
  @apply bg-purple-500;
}

.status-text {
  @apply text-sm;
}
</style>