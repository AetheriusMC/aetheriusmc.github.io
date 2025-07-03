<template>
  <div class="players-view">
    <!-- Search and Filter Section -->
    <el-card class="search-section" shadow="never">
      <div class="search-controls">
        <div class="search-row">
          <el-input
            v-model="searchQuery"
            placeholder="搜索玩家名称..."
            :prefix-icon="Search"
            clearable
            class="search-input"
            @input="onSearchChange"
          />
          
          <el-select
            v-model="filters.gameMode"
            placeholder="游戏模式"
            clearable
            class="filter-select"
            @change="applyFilters"
          >
            <el-option label="全部" value="" />
            <el-option label="生存模式" value="survival" />
            <el-option label="创造模式" value="creative" />
            <el-option label="冒险模式" value="adventure" />
            <el-option label="观察者模式" value="spectator" />
          </el-select>
          
          <el-checkbox v-model="filters.onlineOnly" @change="applyFilters">
            仅显示在线玩家
          </el-checkbox>
          
          <el-button type="primary" :icon="Refresh" @click="refreshData">
            刷新
          </el-button>
        </div>
        
        <div class="advanced-filters" v-show="showAdvancedFilters">
          <el-row :gutter="10">
            <el-col :span="6">
              <el-input-number
                v-model="filters.minLevel"
                placeholder="最低等级"
                :min="0"
                :max="100"
                controls-position="right"
                @change="applyFilters"
              />
            </el-col>
            <el-col :span="6">
              <el-input-number
                v-model="filters.maxLevel"
                placeholder="最高等级"
                :min="0"
                :max="100"
                controls-position="right"
                @change="applyFilters"
              />
            </el-col>
            <el-col :span="6">
              <el-select v-model="sortBy" @change="applyFilters">
                <el-option label="最近登录" value="last_login" />
                <el-option label="玩家名称" value="name" />
                <el-option label="等级" value="level" />
                <el-option label="游戏时长" value="playtime_hours" />
              </el-select>
            </el-col>
            <el-col :span="6">
              <el-select v-model="sortOrder" @change="applyFilters">
                <el-option label="降序" value="desc" />
                <el-option label="升序" value="asc" />
              </el-select>
            </el-col>
          </el-row>
        </div>
        
        <div class="filter-actions">
          <el-button
            type="text"
            @click="showAdvancedFilters = !showAdvancedFilters"
          >
            {{ showAdvancedFilters ? '隐藏高级筛选' : '显示高级筛选' }}
          </el-button>
          
          <el-button
            type="text"
            @click="clearFilters"
          >
            清除筛选
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- Batch Operations -->
    <el-card v-if="selectedPlayers.length > 0" class="batch-operations" shadow="never">
      <div class="batch-header">
        <span>已选择 {{ selectedPlayers.length }} 个玩家</span>
        <div class="batch-actions">
          <el-button size="small" @click="clearSelection">取消选择</el-button>
          <el-dropdown @command="handleBatchOperation">
            <el-button type="primary" size="small">
              批量操作<el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="kick">踢出服务器</el-dropdown-item>
                <el-dropdown-item command="ban" divided>封禁玩家</el-dropdown-item>
                <el-dropdown-item command="tempban">临时封禁</el-dropdown-item>
                <el-dropdown-item command="op" divided>给予OP权限</el-dropdown-item>
                <el-dropdown-item command="deop">移除OP权限</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </el-card>

    <!-- Players Table -->
    <el-card class="players-table-card">
      <template #header>
        <div class="table-header">
          <span>玩家列表</span>
          <div class="table-stats">
            <el-tag v-if="searchResults.total_count">
              共 {{ searchResults.total_count }} 个玩家
            </el-tag>
            <el-tag type="success" v-if="onlinePlayersCount">
              {{ onlinePlayersCount }} 人在线
            </el-tag>
          </div>
        </div>
      </template>
      
      <el-table
        v-loading="loading"
        :data="searchResults.players"
        @selection-change="handleSelectionChange"
        @row-click="handleRowClick"
        stripe
        class="players-table"
      >
        <el-table-column type="selection" width="50" />
        
        <el-table-column label="玩家" min-width="180">
          <template #default="{ row }">
            <div class="player-cell">
              <el-avatar :size="32" class="player-avatar">
                {{ row.name.charAt(0).toUpperCase() }}
              </el-avatar>
              <div class="player-info">
                <div class="player-name">
                  {{ row.name }}
                  <el-tag v-if="row.online" type="success" size="small">在线</el-tag>
                  <el-tag v-if="row.is_op" type="warning" size="small">OP</el-tag>
                  <el-tag v-if="row.is_banned" type="danger" size="small">已封禁</el-tag>
                </div>
                <div class="player-uuid">{{ row.uuid }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="等级" prop="level" width="80" sortable>
          <template #default="{ row }">
            <el-tag type="info">Lv.{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="游戏模式" prop="game_mode" width="100">
          <template #default="{ row }">
            <el-tag :type="getGameModeType(row.game_mode)" size="small">
              {{ getGameModeText(row.game_mode) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="游戏时长" width="120">
          <template #default="{ row }">
            {{ formatPlaytime(row.playtime_hours) }}
          </template>
        </el-table-column>
        
        <el-table-column label="最后登录" width="160">
          <template #default="{ row }">
            <div v-if="row.last_login">
              {{ formatTime(row.last_login) }}
            </div>
            <span v-else class="text-muted">从未登录</span>
          </template>
        </el-table-column>
        
        <el-table-column label="IP地址" width="140">
          <template #default="{ row }">
            <span v-if="row.ip_address" class="ip-address">{{ row.ip_address }}</span>
            <span v-else class="text-muted">未知</span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                v-if="row.online"
                type="warning"
                size="small"
                @click.stop="showOperationDialog(row, 'kick')"
              >
                踢出
              </el-button>
              
              <el-button
                v-if="!row.is_banned"
                type="danger"
                size="small"
                @click.stop="showOperationDialog(row, 'ban')"
              >
                封禁
              </el-button>
              
              <el-button
                v-if="row.is_banned"
                type="success"
                size="small"
                @click.stop="showOperationDialog(row, 'unban')"
              >
                解封
              </el-button>
              
              <el-dropdown @command="(cmd) => handleSingleOperation(row, cmd)" trigger="click">
                <el-button size="small">
                  更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="details">查看详情</el-dropdown-item>
                    <el-dropdown-item command="statistics">统计信息</el-dropdown-item>
                    <el-dropdown-item divided command="op" v-if="!row.is_op">给予OP</el-dropdown-item>
                    <el-dropdown-item command="deop" v-if="row.is_op">移除OP</el-dropdown-item>
                    <el-dropdown-item divided command="teleport" v-if="row.online">传送到出生点</el-dropdown-item>
                    <el-dropdown-item command="heal" v-if="row.online">治疗玩家</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- Pagination -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="searchResults.total_count"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- Player Details Drawer -->
    <PlayerDetailsDrawer
      v-model:visible="detailsDrawerVisible"
      :player="selectedPlayerForDetails"
      @operation="handlePlayerOperation"
    />

    <!-- Operation Dialog -->
    <PlayerOperationDialog
      v-model:visible="operationDialogVisible"
      :player="selectedPlayerForOperation"
      :operation="pendingOperation"
      @confirm="executeOperation"
    />

    <!-- Batch Operation Dialog -->
    <BatchOperationDialog
      v-model:visible="batchOperationDialogVisible"
      :players="selectedPlayers"
      :operation="pendingBatchOperation"
      @confirm="executeBatchOperation"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  ArrowDown,
  User,
  Setting
} from '@element-plus/icons-vue'
import PlayerDetailsDrawer from '@/components/Players/PlayerDetailsDrawer.vue'
import PlayerOperationDialog from '@/components/Players/PlayerOperationDialog.vue'
import BatchOperationDialog from '@/components/Players/BatchOperationDialog.vue'
import { usePlayersStore } from '@/stores/players'
import type { PlayerResponse } from '@/types'

const playersStore = usePlayersStore()

// Search and filtering
const searchQuery = ref('')
const showAdvancedFilters = ref(false)
const filters = ref({
  gameMode: '',
  onlineOnly: false,
  minLevel: null as number | null,
  maxLevel: null as number | null
})
const sortBy = ref('last_login')
const sortOrder = ref('desc')

// Pagination
const currentPage = ref(1)
const pageSize = ref(20)

// Table selection
const selectedPlayers = ref<PlayerResponse[]>([])

// Dialogs and drawers
const detailsDrawerVisible = ref(false)
const operationDialogVisible = ref(false)
const batchOperationDialogVisible = ref(false)
const selectedPlayerForDetails = ref<PlayerResponse | null>(null)
const selectedPlayerForOperation = ref<PlayerResponse | null>(null)
const pendingOperation = ref('')
const pendingBatchOperation = ref('')

// Loading state
const loading = computed(() => playersStore.loading)
const searchResults = computed(() => playersStore.searchResults)
const onlinePlayersCount = computed(() => 
  searchResults.value.players.filter(p => p.online).length
)

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

const formatPlaytime = (hours: number | null) => {
  if (!hours) return '0小时'
  
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

const formatTime = (timeString: string) => {
  const date = new Date(timeString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

// Search and filter handlers
const onSearchChange = () => {
  // Debounced search
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    applyFilters()
  }, 500)
}

let searchTimeout: number

const applyFilters = async () => {
  currentPage.value = 1
  await loadPlayers()
}

const clearFilters = () => {
  searchQuery.value = ''
  filters.value = {
    gameMode: '',
    onlineOnly: false,
    minLevel: null,
    maxLevel: null
  }
  sortBy.value = 'last_login'
  sortOrder.value = 'desc'
  applyFilters()
}

const refreshData = () => {
  loadPlayers()
}

// Table handlers
const handleSelectionChange = (selection: PlayerResponse[]) => {
  selectedPlayers.value = selection
}

const handleRowClick = (player: PlayerResponse) => {
  selectedPlayerForDetails.value = player
  detailsDrawerVisible.value = true
}

const clearSelection = () => {
  selectedPlayers.value = []
}

// Pagination handlers
const handlePageChange = (page: number) => {
  currentPage.value = page
  loadPlayers()
}

const handlePageSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadPlayers()
}

// Operation handlers
const showOperationDialog = (player: PlayerResponse, operation: string) => {
  selectedPlayerForOperation.value = player
  pendingOperation.value = operation
  operationDialogVisible.value = true
}

const handleSingleOperation = (player: PlayerResponse, operation: string) => {
  if (operation === 'details') {
    selectedPlayerForDetails.value = player
    detailsDrawerVisible.value = true
  } else if (operation === 'statistics') {
    // TODO: Show statistics modal
    ElMessage.info('统计功能开发中...')
  } else {
    showOperationDialog(player, operation)
  }
}

const handleBatchOperation = (operation: string) => {
  pendingBatchOperation.value = operation
  batchOperationDialogVisible.value = true
}

const executeOperation = async (operationData: any) => {
  try {
    await playersStore.executePlayerAction(
      selectedPlayerForOperation.value!.uuid,
      operationData.action,
      operationData.reason,
      operationData.duration
    )
    
    ElMessage.success('操作执行成功')
    operationDialogVisible.value = false
    
    // Refresh data if needed
    if (['kick', 'ban', 'unban'].includes(operationData.action)) {
      await loadPlayers()
    }
  } catch (error) {
    ElMessage.error(`操作失败: ${error}`)
  }
}

const executeBatchOperation = async (operationData: any) => {
  try {
    const playerUuids = selectedPlayers.value.map(p => p.uuid)
    
    await playersStore.executeBatchPlayerAction(
      playerUuids,
      operationData.action,
      operationData.reason,
      operationData.duration
    )
    
    ElMessage.success('批量操作执行成功')
    batchOperationDialogVisible.value = false
    clearSelection()
    
    // Refresh data
    await loadPlayers()
  } catch (error) {
    ElMessage.error(`批量操作失败: ${error}`)
  }
}

const handlePlayerOperation = async (operationData: any) => {
  await executeOperation(operationData)
}

// Data loading
const loadPlayers = async () => {
  try {
    await playersStore.searchPlayers({
      query: searchQuery.value,
      page: currentPage.value,
      per_page: pageSize.value,
      online_only: filters.value.onlineOnly,
      game_mode: filters.value.gameMode,
      min_level: filters.value.minLevel,
      max_level: filters.value.maxLevel,
      sort_by: sortBy.value,
      sort_order: sortOrder.value
    })
  } catch (error) {
    ElMessage.error('加载玩家数据失败')
  }
}

// Lifecycle
onMounted(() => {
  loadPlayers()
})
</script>

<style scoped>
.players-view {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.search-section {
  margin-bottom: 20px;
}

.search-controls {
  space-y: 15px;
}

.search-row {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.search-input {
  width: 300px;
}

.filter-select {
  width: 150px;
}

.advanced-filters {
  margin-bottom: 15px;
}

.filter-actions {
  display: flex;
  gap: 15px;
}

.batch-operations {
  margin-bottom: 20px;
  background-color: #e6f3ff;
}

.batch-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.batch-actions {
  display: flex;
  gap: 10px;
}

.players-table-card {
  margin-bottom: 20px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-stats {
  display: flex;
  gap: 10px;
}

.players-table {
  width: 100%;
}

.player-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.player-avatar {
  background: linear-gradient(45deg, #409eff, #67c23a);
  color: white;
  font-weight: 600;
  flex-shrink: 0;
}

.player-info {
  flex: 1;
  min-width: 0;
}

.player-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.player-uuid {
  font-size: 12px;
  color: #909399;
  font-family: monospace;
  overflow: hidden;
  text-overflow: ellipsis;
}

.action-buttons {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.ip-address {
  font-family: monospace;
  font-size: 13px;
}

.text-muted {
  color: #909399;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}
</style>