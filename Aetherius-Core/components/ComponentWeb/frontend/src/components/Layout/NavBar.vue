<template>
  <div class="navbar">
    <div class="navbar-left">
      <el-icon class="navbar-logo" :size="24">
        <Connection />
      </el-icon>
      <span class="navbar-title">Aetherius Web Console</span>
    </div>
    
    <div class="navbar-center">
      <el-tag 
        :type="serverStatusType" 
        :effect="serverStatusEffect"
        class="server-status-tag"
      >
        <el-icon class="status-icon">
          <component :is="serverStatusIcon" />
        </el-icon>
        {{ serverStatusText }}
      </el-tag>
    </div>
    
    <div class="navbar-right">
      <el-space>
        <!-- Connection Status -->
        <el-tooltip content="WebSocket连接状态">
          <el-tag 
            :type="wsConnectionType" 
            size="small"
            class="connection-indicator"
          >
            <el-icon>
              <component :is="wsConnectionIcon" />
            </el-icon>
          </el-tag>
        </el-tooltip>
        
        <!-- Auto Refresh Toggle -->
        <el-tooltip content="自动刷新">
          <el-switch
            v-model="autoRefresh"
            @change="handleAutoRefreshChange"
            size="small"
            :active-icon="Refresh"
            :inactive-icon="VideoPause"
          />
        </el-tooltip>
        
        <!-- Settings -->
        <el-dropdown @command="handleCommand">
          <el-button type="text" class="navbar-button">
            <el-icon :size="18">
              <Setting />
            </el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="settings">设置</el-dropdown-item>
              <el-dropdown-item command="about">关于</el-dropdown-item>
              <el-dropdown-item divided command="logout">退出</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-space>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { 
  Connection, 
  Setting, 
  Refresh, 
  VideoPause,
  SuccessFilled,
  WarningFilled,
  CircleCloseFilled,
  Close
} from '@element-plus/icons-vue'
import { useDashboardStore } from '@/stores/dashboard'
import { useWebSocketStore } from '@/stores/websocket'

const dashboardStore = useDashboardStore()
const wsStore = useWebSocketStore()

// Server Status
const serverStatusType = computed(() => {
  if (!dashboardStore.serverStatus) return 'info'
  return dashboardStore.isServerRunning ? 'success' : 'danger'
})

const serverStatusEffect = computed(() => {
  return dashboardStore.isServerRunning ? 'dark' : 'plain'
})

const serverStatusIcon = computed(() => {
  if (!dashboardStore.serverStatus) return WarningFilled
  return dashboardStore.isServerRunning ? SuccessFilled : CircleCloseFilled
})

const serverStatusText = computed(() => {
  if (!dashboardStore.serverStatus) return '未知'
  return dashboardStore.isServerRunning ? '运行中' : '已停止'
})

// WebSocket Connection Status
const wsConnectionType = computed(() => {
  if (wsStore.isConsoleConnected) return 'success'
  if (wsStore.consoleStatus.reconnecting) return 'warning'
  return 'danger'
})

const wsConnectionIcon = computed(() => {
  if (wsStore.isConsoleConnected) return Connection
  return Close
})

// Auto Refresh
const autoRefresh = computed({
  get: () => dashboardStore.autoRefresh,
  set: (value) => dashboardStore.setAutoRefresh(value)
})

function handleAutoRefreshChange(enabled: boolean) {
  dashboardStore.setAutoRefresh(enabled)
}

function handleCommand(command: string) {
  switch (command) {
    case 'settings':
      // TODO: Open settings dialog
      console.log('Open settings')
      break
    case 'about':
      // TODO: Open about dialog  
      console.log('Open about')
      break
    case 'logout':
      // TODO: Handle logout
      console.log('Logout')
      break
  }
}
</script>

<style scoped>
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 20px;
  background: linear-gradient(135deg, #409EFF 0%, #5cb3ff 100%);
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.navbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.navbar-logo {
  color: white;
}

.navbar-title {
  font-size: 18px;
  font-weight: 600;
}

.navbar-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.server-status-tag {
  font-weight: 500;
}

.status-icon {
  margin-right: 4px;
}

.navbar-right {
  display: flex;
  align-items: center;
}

.connection-indicator {
  margin-right: 8px;
}

.navbar-button {
  color: white !important;
  border: none;
  background: none;
}

.navbar-button:hover {
  background: rgba(255, 255, 255, 0.1) !important;
}

:deep(.el-switch__core) {
  border-color: rgba(255, 255, 255, 0.3);
}

:deep(.el-switch.is-checked .el-switch__core) {
  border-color: white;
  background-color: rgba(255, 255, 255, 0.2);
}
</style>