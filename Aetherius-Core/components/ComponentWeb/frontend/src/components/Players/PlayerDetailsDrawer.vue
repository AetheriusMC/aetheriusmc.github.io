<template>
  <el-drawer
    v-model="isVisible"
    title="玩家详情"
    :size="500"
    direction="rtl"
    :before-close="handleClose"
  >
    <div v-if="player" class="player-details">
      <!-- Player Header -->
      <div class="player-header">
        <el-avatar :size="64" class="player-avatar">
          {{ player.name.charAt(0).toUpperCase() }}
        </el-avatar>
        <div class="player-info">
          <h2 class="player-name">{{ player.name }}</h2>
          <div class="player-status">
            <el-tag v-if="player.online" type="success">在线</el-tag>
            <el-tag v-else type="info">离线</el-tag>
            <el-tag v-if="player.is_op" type="warning">OP</el-tag>
            <el-tag v-if="player.is_banned" type="danger">已封禁</el-tag>
          </div>
          <div class="player-uuid">{{ player.uuid }}</div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="quick-actions">
        <el-button
          v-if="player.online"
          type="warning"
          size="small"
          @click="handleQuickAction('kick')"
        >
          踢出
        </el-button>
        
        <el-button
          v-if="!player.is_banned"
          type="danger"
          size="small"
          @click="handleQuickAction('ban')"
        >
          封禁
        </el-button>
        
        <el-button
          v-if="player.is_banned"
          type="success"
          size="small"
          @click="handleQuickAction('unban')"
        >
          解封
        </el-button>
        
        <el-button
          v-if="!player.is_op"
          type="primary"
          size="small"
          @click="handleQuickAction('op')"
        >
          给予OP
        </el-button>
        
        <el-button
          v-if="player.is_op"
          type="info"
          size="small"
          @click="handleQuickAction('deop')"
        >
          移除OP
        </el-button>
      </div>

      <!-- Player Details Tabs -->
      <el-tabs v-model="activeTab" class="player-tabs">
        <!-- Basic Info -->
        <el-tab-pane label="基本信息" name="basic">
          <div class="detail-section">
            <div class="detail-item">
              <span class="label">游戏模式:</span>
              <el-tag :type="getGameModeType(player.game_mode)">
                {{ getGameModeText(player.game_mode) }}
              </el-tag>
            </div>
            
            <div class="detail-item">
              <span class="label">等级:</span>
              <span class="value">{{ player.level }}</span>
            </div>
            
            <div class="detail-item">
              <span class="label">经验值:</span>
              <span class="value">{{ player.experience }}</span>
            </div>
            
            <div class="detail-item" v-if="player.health !== undefined">
              <span class="label">生命值:</span>
              <el-progress 
                :percentage="(player.health / 20) * 100" 
                :color="getHealthColor(player.health)"
                :show-text="false"
                style="width: 100px"
              />
              <span class="value">{{ player.health }}/20</span>
            </div>
            
            <div class="detail-item" v-if="player.food_level !== undefined">
              <span class="label">饥饿值:</span>
              <el-progress 
                :percentage="(player.food_level / 20) * 100" 
                color="#f56c6c"
                :show-text="false"
                style="width: 100px"
              />
              <span class="value">{{ player.food_level }}/20</span>
            </div>
            
            <div class="detail-item" v-if="player.playtime_hours">
              <span class="label">游戏时长:</span>
              <span class="value">{{ formatPlaytime(player.playtime_hours) }}</span>
            </div>
          </div>
        </el-tab-pane>

        <!-- Location & Inventory -->
        <el-tab-pane label="位置信息" name="location">
          <div class="detail-section">
            <div v-if="player.location" class="location-info">
              <div class="detail-item">
                <span class="label">世界:</span>
                <span class="value">{{ player.location.world }}</span>
              </div>
              
              <div class="detail-item">
                <span class="label">坐标:</span>
                <span class="value coordinate">
                  X: {{ player.location.x.toFixed(1) }}, 
                  Y: {{ player.location.y.toFixed(1) }}, 
                  Z: {{ player.location.z.toFixed(1) }}
                </span>
              </div>
              
              <div class="map-placeholder">
                <el-icon size="48"><Location /></el-icon>
                <p>地图视图开发中...</p>
              </div>
            </div>
            
            <div v-else class="no-location">
              <el-empty description="位置信息不可用" />
            </div>
            
            <div v-if="player.inventory_size !== undefined" class="detail-item">
              <span class="label">背包使用:</span>
              <span class="value">{{ player.inventory_size }}/36 格</span>
            </div>
          </div>
        </el-tab-pane>

        <!-- Connection Info -->
        <el-tab-pane label="连接信息" name="connection">
          <div class="detail-section">
            <div class="detail-item">
              <span class="label">IP地址:</span>
              <span class="value ip-address">{{ player.ip_address || '未知' }}</span>
            </div>
            
            <div class="detail-item">
              <span class="label">最后登录:</span>
              <span class="value">
                {{ player.last_login ? formatDateTime(player.last_login) : '从未登录' }}
              </span>
            </div>
            
            <div class="detail-item" v-if="player.last_logout">
              <span class="label">最后离线:</span>
              <span class="value">{{ formatDateTime(player.last_logout) }}</span>
            </div>
            
            <div class="detail-item" v-if="player.online">
              <span class="label">在线时长:</span>
              <span class="value">{{ calculateOnlineTime() }}</span>
            </div>
          </div>
        </el-tab-pane>

        <!-- Ban Info -->
        <el-tab-pane v-if="player.is_banned" label="封禁信息" name="ban">
          <div class="detail-section">
            <div class="ban-warning">
              <el-alert
                title="该玩家已被封禁"
                type="error"
                :closable="false"
                show-icon
              />
            </div>
            
            <div class="detail-item" v-if="player.ban_reason">
              <span class="label">封禁原因:</span>
              <span class="value">{{ player.ban_reason }}</span>
            </div>
            
            <div class="detail-item" v-if="player.ban_expires">
              <span class="label">解封时间:</span>
              <span class="value">{{ formatDateTime(player.ban_expires) }}</span>
            </div>
            
            <div class="detail-item" v-else>
              <span class="label">封禁类型:</span>
              <span class="value">永久封禁</span>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>

      <!-- Action Buttons -->
      <div class="action-buttons">
        <el-button type="primary" @click="showStatistics">
          查看统计
        </el-button>
        <el-button @click="showOperationHistory">
          操作历史
        </el-button>
        <el-button v-if="player.online" @click="handleQuickAction('teleport')">
          传送到出生点
        </el-button>
        <el-button v-if="player.online" @click="handleQuickAction('heal')">
          治疗玩家
        </el-button>
      </div>
    </div>

    <!-- Operation Dialog -->
    <PlayerOperationDialog
      v-model:visible="operationDialogVisible"
      :player="player"
      :operation="pendingOperation"
      @confirm="executeOperation"
    />
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Location } from '@element-plus/icons-vue'
import PlayerOperationDialog from './PlayerOperationDialog.vue'
import type { PlayerResponse } from '@/types'

interface Props {
  visible: boolean
  player: PlayerResponse | null
}

interface Emits {
  (e: 'update:visible', visible: boolean): void
  (e: 'operation', operationData: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Local state
const isVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const activeTab = ref('basic')
const operationDialogVisible = ref(false)
const pendingOperation = ref('')

// Utility functions
const getGameModeType = (mode: string) => {
  const types = {
    survival: 'success',
    creative: 'warning',
    adventure: 'info',
    spectator: 'info'
  }
  return types[mode as keyof typeof types] || 'info'
}

const getGameModeText = (mode: string) => {
  const texts = {
    survival: '生存',
    creative: '创造',
    adventure: '冒险',
    spectator: '观察'
  }
  return texts[mode as keyof typeof texts] || mode
}

const getHealthColor = (health: number) => {
  if (health > 15) return '#67c23a'
  if (health > 10) return '#e6a23c'
  if (health > 5) return '#f56c6c'
  return '#f56c6c'
}

const formatPlaytime = (hours: number) => {
  if (hours < 1) {
    return `${Math.round(hours * 60)}分钟`
  } else if (hours < 24) {
    return `${hours.toFixed(1)}小时`
  } else {
    const days = Math.floor(hours / 24)
    const remainingHours = Math.round(hours % 24)
    return `${days}天${remainingHours}小时`
  }
}

const formatDateTime = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

const calculateOnlineTime = () => {
  if (!props.player?.last_login) return '未知'
  
  const loginTime = new Date(props.player.last_login)
  const now = new Date()
  const diff = now.getTime() - loginTime.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟`
  } else {
    return `${minutes}分钟`
  }
}

// Event handlers
const handleClose = () => {
  emit('update:visible', false)
}

const handleQuickAction = (action: string) => {
  pendingOperation.value = action
  operationDialogVisible.value = true
}

const executeOperation = (operationData: any) => {
  emit('operation', operationData)
  operationDialogVisible.value = false
}

const showStatistics = () => {
  ElMessage.info('统计功能开发中...')
}

const showOperationHistory = () => {
  ElMessage.info('操作历史功能开发中...')
}

// Reset tab when player changes
watch(() => props.player, () => {
  activeTab.value = 'basic'
})
</script>

<style scoped>
.player-details {
  padding: 20px 0;
}

.player-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
}

.player-avatar {
  background: linear-gradient(45deg, #409eff, #67c23a);
  color: white;
  font-weight: 600;
  font-size: 24px;
}

.player-info {
  flex: 1;
}

.player-name {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 20px;
  font-weight: 600;
}

.player-status {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.player-uuid {
  font-size: 12px;
  color: #909399;
  font-family: monospace;
}

.quick-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
}

.player-tabs {
  margin-bottom: 20px;
}

.detail-section {
  padding: 10px 0;
}

.detail-item {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  gap: 12px;
}

.label {
  width: 80px;
  font-weight: 500;
  color: #606266;
  flex-shrink: 0;
}

.value {
  color: #303133;
  flex: 1;
}

.coordinate {
  font-family: monospace;
  font-size: 13px;
}

.ip-address {
  font-family: monospace;
  font-size: 13px;
}

.location-info {
  margin-bottom: 20px;
}

.map-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 120px;
  background-color: #f5f7fa;
  border-radius: 8px;
  color: #909399;
  margin-top: 16px;
}

.map-placeholder p {
  margin: 8px 0 0 0;
  font-size: 14px;
}

.no-location {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 120px;
}

.ban-warning {
  margin-bottom: 20px;
}

.action-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

:deep(.el-drawer__header) {
  margin-bottom: 0;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
}

:deep(.el-drawer__body) {
  padding: 0 20px 20px 20px;
}

:deep(.el-tabs__content) {
  padding: 20px 0 0 0;
}

:deep(.el-progress-bar__outer) {
  background-color: #f0f2f5;
}
</style>