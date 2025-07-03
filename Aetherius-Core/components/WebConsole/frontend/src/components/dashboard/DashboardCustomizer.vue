<template>
  <div class="dashboard-customizer">
    <!-- Header -->
    <div class="customizer-header">
      <div class="header-content">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">
          仪表板自定义
        </h2>
        <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
          拖拽、调整和配置您的监控组件
        </p>
      </div>
      
      <div class="header-actions">
        <button 
          @click="resetLayout"
          class="btn btn-secondary"
        >
          重置布局
        </button>
        <button 
          @click="saveLayout"
          :disabled="!hasChanges"
          class="btn btn-primary"
        >
          保存配置
        </button>
      </div>
    </div>
    
    <!-- Layout Configuration -->
    <div class="layout-config">
      <div class="config-section">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">
          布局设置
        </h3>
        
        <div class="config-grid">
          <!-- Layout Name -->
          <div class="config-item">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              布局名称
            </label>
            <input
              v-model="layoutConfig.layout_name"
              type="text"
              class="form-input"
              placeholder="我的自定义布局"
            />
          </div>
          
          <!-- Refresh Interval -->
          <div class="config-item">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              刷新间隔
            </label>
            <select v-model="layoutConfig.refresh_interval" class="form-select">
              <option :value="15">15秒</option>
              <option :value="30">30秒</option>
              <option :value="60">1分钟</option>
              <option :value="300">5分钟</option>
            </select>
          </div>
          
          <!-- Theme -->
          <div class="config-item">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              主题
            </label>
            <select v-model="layoutConfig.theme" class="form-select">
              <option value="auto">自动</option>
              <option value="light">浅色</option>
              <option value="dark">深色</option>
            </select>
          </div>
          
          <!-- Grid Size -->
          <div class="config-item">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              网格密度
            </label>
            <select v-model="gridSize" @change="onGridSizeChange" class="form-select">
              <option :value="12">标准 (12列)</option>
              <option :value="16">密集 (16列)</option>
              <option :value="24">超密集 (24列)</option>
            </select>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Widget Library -->
    <div class="widget-library">
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">
        组件库
      </h3>
      
      <div class="widgets-grid">
        <div 
          v-for="widgetType in availableWidgets"
          :key="widgetType.type"
          class="widget-item"
          draggable="true"
          @dragstart="onDragStart($event, widgetType)"
        >
          <div class="widget-icon">
            <component :is="widgetType.icon" class="w-6 h-6" />
          </div>
          <div class="widget-info">
            <div class="widget-title">{{ widgetType.title }}</div>
            <div class="widget-description">{{ widgetType.description }}</div>
          </div>
          <button 
            @click="addWidget(widgetType)"
            class="widget-add-btn"
          >
            <PlusIcon class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
    
    <!-- Dashboard Preview -->
    <div class="dashboard-preview">
      <div class="preview-header">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">
          布局预览
        </h3>
        <div class="preview-controls">
          <button 
            @click="previewMode = !previewMode"
            class="btn btn-sm btn-secondary"
            :class="{ 'btn-primary': previewMode }"
          >
            {{ previewMode ? '编辑模式' : '预览模式' }}
          </button>
        </div>
      </div>
      
      <!-- Grid Layout -->
      <div 
        class="grid-container"
        :style="{ gridTemplateColumns: `repeat(${gridSize}, 1fr)` }"
        @drop="onDrop"
        @dragover="onDragOver"
      >
        <!-- Grid Guidelines -->
        <div 
          v-if="!previewMode"
          v-for="i in gridSize * 8" 
          :key="`grid-${i}`"
          class="grid-cell"
        ></div>
        
        <!-- Widgets -->
        <div
          v-for="widget in layoutConfig.widgets"
          :key="widget.id"
          class="widget-container"
          :class="{ 'preview-mode': previewMode }"
          :style="{
            gridColumn: `${widget.position.x + 1} / span ${widget.size.width}`,
            gridRow: `${widget.position.y + 1} / span ${widget.size.height}`,
          }"
          @mousedown="!previewMode && startResize(widget, $event)"
        >
          <!-- Widget Header -->
          <div v-if="!previewMode" class="widget-header">
            <div class="widget-title-input">
              <input
                v-model="widget.title"
                class="form-input-sm"
                @change="markChanged"
              />
            </div>
            <div class="widget-controls">
              <button 
                @click="configureWidget(widget)"
                class="widget-control-btn"
              >
                <CogIcon class="w-4 h-4" />
              </button>
              <button 
                @click="removeWidget(widget.id)"
                class="widget-control-btn text-red-500"
              >
                <XMarkIcon class="w-4 h-4" />
              </button>
            </div>
          </div>
          
          <!-- Widget Content -->
          <div class="widget-content">
            <component 
              :is="getWidgetComponent(widget.type)"
              v-bind="widget.config"
              :preview-mode="previewMode"
              :widget-id="widget.id"
              @config-change="onWidgetConfigChange(widget.id, $event)"
            />
          </div>
          
          <!-- Resize Handle -->
          <div 
            v-if="!previewMode"
            class="resize-handle"
            @mousedown="startResize(widget, $event)"
          >
            <ArrowsPointingOutIcon class="w-4 h-4" />
          </div>
        </div>
      </div>
    </div>
    
    <!-- Widget Configuration Modal -->
    <WidgetConfigModal 
      v-if="configModal.show"
      :widget="configModal.widget"
      @save="onWidgetConfigSave"
      @close="configModal.show = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  PlusIcon,
  CogIcon,
  XMarkIcon,
  ArrowsPointingOutIcon,
  ChartBarIcon,
  CpuChipIcon,
  CircleStackIcon,
  ClockIcon,
  UsersIcon,
  ExclamationTriangleIcon,
  LightBulbIcon,
  ServerIcon
} from '@heroicons/vue/24/outline'
import WidgetConfigModal from './WidgetConfigModal.vue'
import { apiClient } from '@/services/api'

interface Widget {
  id: string
  type: string
  title: string
  position: { x: number; y: number }
  size: { width: number; height: number }
  config: Record<string, any>
  enabled: boolean
}

interface LayoutConfig {
  user_id: string
  layout_name: string
  widgets: Widget[]
  refresh_interval: number
  theme: string
}

interface WidgetType {
  type: string
  title: string
  description: string
  icon: any
  defaultSize: { width: number; height: number }
  defaultConfig: Record<string, any>
}

// State
const layoutConfig = ref<LayoutConfig>({
  user_id: '',
  layout_name: '默认布局',
  widgets: [],
  refresh_interval: 30,
  theme: 'auto'
})

const gridSize = ref(12)
const previewMode = ref(false)
const hasChanges = ref(false)
const draggedWidget = ref<WidgetType | null>(null)
const resizingWidget = ref<Widget | null>(null)

const configModal = ref({
  show: false,
  widget: null as Widget | null
})

// Available widget types
const availableWidgets: WidgetType[] = [
  {
    type: 'metric_chart',
    title: '指标图表',
    description: '显示性能指标的实时图表',
    icon: ChartBarIcon,
    defaultSize: { width: 6, height: 4 },
    defaultConfig: {
      metric: 'cpu_percent',
      chartType: 'line',
      timeRange: '1h',
      showStats: true
    }
  },
  {
    type: 'server_status',
    title: '服务器状态',
    description: '显示服务器基本状态信息',
    icon: ServerIcon,
    defaultSize: { width: 4, height: 3 },
    defaultConfig: {
      showUptime: true,
      showPlayers: true,
      showVersion: true
    }
  },
  {
    type: 'resource_usage',
    title: '资源使用',
    description: '显示CPU、内存等资源使用情况',
    icon: CpuChipIcon,
    defaultSize: { width: 4, height: 3 },
    defaultConfig: {
      resources: ['cpu', 'memory', 'disk'],
      displayType: 'gauge'
    }
  },
  {
    type: 'player_list',
    title: '在线玩家',
    description: '显示当前在线玩家列表',
    icon: UsersIcon,
    defaultSize: { width: 4, height: 6 },
    defaultConfig: {
      maxPlayers: 10,
      showAvatar: true,
      showLocation: true
    }
  },
  {
    type: 'alerts',
    title: '系统警报',
    description: '显示系统警报和通知',
    icon: ExclamationTriangleIcon,
    defaultSize: { width: 6, height: 4 },
    defaultConfig: {
      maxAlerts: 5,
      autoHide: true,
      severityFilter: ['warning', 'error']
    }
  },
  {
    type: 'performance_summary',
    title: '性能摘要',
    description: '显示关键性能指标摘要',
    icon: CircleStackIcon,
    defaultSize: { width: 8, height: 3 },
    defaultConfig: {
      metrics: ['tps', 'cpu_percent', 'memory_percent'],
      layout: 'horizontal'
    }
  }
]

// Computed
const nextPosition = computed(() => {
  // Find the next available position for a new widget
  const occupiedPositions = new Set()
  
  layoutConfig.value.widgets.forEach(widget => {
    for (let x = widget.position.x; x < widget.position.x + widget.size.width; x++) {
      for (let y = widget.position.y; y < widget.position.y + widget.size.height; y++) {
        occupiedPositions.add(`${x},${y}`)
      }
    }
  })
  
  // Find first available position
  for (let y = 0; y < 20; y++) {
    for (let x = 0; x < gridSize.value; x++) {
      if (!occupiedPositions.has(`${x},${y}`)) {
        return { x, y }
      }
    }
  }
  
  return { x: 0, y: 0 }
})

// Methods
const addWidget = (widgetType: WidgetType) => {
  const newWidget: Widget = {
    id: generateWidgetId(),
    type: widgetType.type,
    title: widgetType.title,
    position: nextPosition.value,
    size: { ...widgetType.defaultSize },
    config: { ...widgetType.defaultConfig },
    enabled: true
  }
  
  layoutConfig.value.widgets.push(newWidget)
  markChanged()
}

const removeWidget = (widgetId: string) => {
  const index = layoutConfig.value.widgets.findIndex(w => w.id === widgetId)
  if (index !== -1) {
    layoutConfig.value.widgets.splice(index, 1)
    markChanged()
  }
}

const configureWidget = (widget: Widget) => {
  configModal.value.widget = widget
  configModal.value.show = true
}

const generateWidgetId = (): string => {
  return 'widget_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9)
}

const markChanged = () => {
  hasChanges.value = true
}

const getWidgetComponent = (type: string) => {
  // Return appropriate component based on widget type
  // This would be dynamically imported components
  return 'div' // Placeholder
}

// Drag and drop handlers
const onDragStart = (event: DragEvent, widgetType: WidgetType) => {
  draggedWidget.value = widgetType
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'copy'
  }
}

const onDragOver = (event: DragEvent) => {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'copy'
  }
}

const onDrop = (event: DragEvent) => {
  event.preventDefault()
  
  if (draggedWidget.value) {
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
    const x = Math.floor((event.clientX - rect.left) / (rect.width / gridSize.value))
    const y = Math.floor((event.clientY - rect.top) / 60) // Assuming 60px row height
    
    const newWidget: Widget = {
      id: generateWidgetId(),
      type: draggedWidget.value.type,
      title: draggedWidget.value.title,
      position: { x: Math.max(0, x), y: Math.max(0, y) },
      size: { ...draggedWidget.value.defaultSize },
      config: { ...draggedWidget.value.defaultConfig },
      enabled: true
    }
    
    layoutConfig.value.widgets.push(newWidget)
    markChanged()
    draggedWidget.value = null
  }
}

// Resize handlers
const startResize = (widget: Widget, event: MouseEvent) => {
  event.preventDefault()
  resizingWidget.value = widget
  
  const startX = event.clientX
  const startY = event.clientY
  const startWidth = widget.size.width
  const startHeight = widget.size.height
  
  const onMouseMove = (e: MouseEvent) => {
    const deltaX = Math.round((e.clientX - startX) / 80) // Assuming 80px column width
    const deltaY = Math.round((e.clientY - startY) / 60) // Assuming 60px row height
    
    widget.size.width = Math.max(1, startWidth + deltaX)
    widget.size.height = Math.max(1, startHeight + deltaY)
    markChanged()
  }
  
  const onMouseUp = () => {
    resizingWidget.value = null
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }
  
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

// Configuration handlers
const onWidgetConfigChange = (widgetId: string, config: Record<string, any>) => {
  const widget = layoutConfig.value.widgets.find(w => w.id === widgetId)
  if (widget) {
    widget.config = { ...widget.config, ...config }
    markChanged()
  }
}

const onWidgetConfigSave = (config: Record<string, any>) => {
  if (configModal.value.widget) {
    configModal.value.widget.config = { ...config }
    markChanged()
  }
  configModal.value.show = false
}

const onGridSizeChange = () => {
  // Adjust widget positions to fit new grid
  layoutConfig.value.widgets.forEach(widget => {
    widget.position.x = Math.min(widget.position.x, gridSize.value - widget.size.width)
    widget.size.width = Math.min(widget.size.width, gridSize.value)
  })
  markChanged()
}

// Layout management
const saveLayout = async () => {
  try {
    await apiClient.post('/enhanced-monitoring/dashboard/layout', layoutConfig.value)
    hasChanges.value = false
    alert('布局已保存')
  } catch (error) {
    console.error('Failed to save layout:', error)
    alert('保存失败')
  }
}

const loadLayout = async (layoutName: string) => {
  try {
    const response = await apiClient.get(`/enhanced-monitoring/dashboard/layout/${layoutName}`)
    layoutConfig.value = response.data
    hasChanges.value = false
  } catch (error) {
    console.error('Failed to load layout:', error)
  }
}

const resetLayout = () => {
  if (confirm('确定要重置布局吗？未保存的更改将丢失。')) {
    layoutConfig.value.widgets = []
    hasChanges.value = true
  }
}

// Lifecycle
onMounted(() => {
  // Load default layout
  loadLayout('default')
})

onUnmounted(() => {
  // Clean up event listeners
})
</script>

<style scoped>
.dashboard-customizer {
  @apply space-y-6;
}

.customizer-header {
  @apply flex items-start justify-between;
}

.header-actions {
  @apply flex space-x-3;
}

.layout-config {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6;
}

.config-grid {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4;
}

.config-item {
  @apply space-y-2;
}

.form-input, .form-select {
  @apply w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500;
}

.form-input-sm {
  @apply px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500;
}

.widget-library {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6;
}

.widgets-grid {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4;
}

.widget-item {
  @apply flex items-center space-x-3 p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-300 dark:hover:border-blue-600 cursor-move transition-colors;
}

.widget-icon {
  @apply flex-shrink-0 p-2 bg-gray-100 dark:bg-gray-700 rounded-lg;
}

.widget-info {
  @apply flex-1 min-w-0;
}

.widget-title {
  @apply font-medium text-gray-900 dark:text-white;
}

.widget-description {
  @apply text-sm text-gray-500 dark:text-gray-400;
}

.widget-add-btn {
  @apply flex-shrink-0 p-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors;
}

.dashboard-preview {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6;
}

.preview-header {
  @apply flex items-center justify-between mb-4;
}

.preview-controls {
  @apply flex space-x-2;
}

.grid-container {
  @apply relative min-h-96 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-4;
  display: grid;
  gap: 8px;
  grid-auto-rows: 60px;
}

.grid-cell {
  @apply border border-gray-100 dark:border-gray-700 rounded opacity-50;
}

.widget-container {
  @apply relative bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm;
}

.widget-container.preview-mode {
  @apply bg-gray-50 dark:bg-gray-900;
}

.widget-header {
  @apply flex items-center justify-between p-2 border-b border-gray-200 dark:border-gray-700;
}

.widget-controls {
  @apply flex space-x-1;
}

.widget-control-btn {
  @apply p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded;
}

.widget-content {
  @apply p-4 h-full;
}

.resize-handle {
  @apply absolute bottom-0 right-0 p-1 cursor-nw-resize text-gray-400 hover:text-gray-600;
}
</style>