<template>
  <el-dialog
    v-model="isVisible"
    :title="getDialogTitle()"
    width="600px"
    :before-close="handleClose"
    @close="resetForm"
  >
    <div class="batch-operation-dialog">
      <!-- Selected Players -->
      <div class="selected-players">
        <h4>选中的玩家 ({{ players.length }})</h4>
        <div class="players-list">
          <div 
            v-for="player in players" 
            :key="player.uuid"
            class="player-item"
          >
            <el-avatar :size="24" class="player-avatar">
              {{ player.name.charAt(0).toUpperCase() }}
            </el-avatar>
            <span class="player-name">{{ player.name }}</span>
            <div class="player-tags">
              <el-tag v-if="player.online" type="success" size="small">在线</el-tag>
              <el-tag v-if="player.is_op" type="warning" size="small">OP</el-tag>
              <el-tag v-if="player.is_banned" type="danger" size="small">已封禁</el-tag>
            </div>
          </div>
        </div>
      </div>

      <!-- Operation Form -->
      <el-form 
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
        class="operation-form"
      >
        <!-- Reason Input -->
        <el-form-item 
          v-if="needsReason(operation)" 
          label="原因" 
          prop="reason"
        >
          <el-input
            v-model="form.reason"
            type="textarea"
            :rows="3"
            :placeholder="getReasonPlaceholder()"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <!-- Duration Input for Temporary Ban -->
        <el-form-item 
          v-if="operation === 'tempban'" 
          label="时长" 
          prop="duration"
        >
          <el-input-number
            v-model="form.duration"
            :min="1"
            :max="43200"
            controls-position="right"
            style="width: 150px"
          />
          <span class="duration-unit">分钟</span>
          <div class="duration-hint">
            <span>常用: </span>
            <el-button size="small" text @click="form.duration = 60">1小时</el-button>
            <el-button size="small" text @click="form.duration = 1440">1天</el-button>
            <el-button size="small" text @click="form.duration = 10080">1周</el-button>
          </div>
        </el-form-item>

        <!-- Operation Warning -->
        <div v-if="getOperationWarning()" class="operation-warning">
          <el-alert
            :title="getOperationWarning()"
            :type="getWarningType()"
            show-icon
            :closable="false"
          />
        </div>

        <!-- Affected Players Summary -->
        <div class="affected-summary">
          <h5>受影响的玩家分析:</h5>
          <div class="summary-stats">
            <div class="stat-item">
              <span class="label">在线玩家:</span>
              <span class="value">{{ getOnlineCount() }}</span>
            </div>
            <div class="stat-item">
              <span class="label">OP玩家:</span>
              <span class="value">{{ getOpCount() }}</span>
            </div>
            <div class="stat-item" v-if="getBannedCount() > 0">
              <span class="label">已封禁:</span>
              <span class="value">{{ getBannedCount() }}</span>
            </div>
          </div>
          
          <!-- Special warnings for specific operations -->
          <div v-if="operation === 'deop' && getOpCount() > 0" class="special-warning">
            <el-alert
              :title="`将移除 ${getOpCount()} 个OP玩家的管理员权限`"
              type="warning"
              :closable="false"
              show-icon
            />
          </div>
          
          <div v-if="operation === 'ban' && getOnlineCount() > 0" class="special-warning">
            <el-alert
              :title="`将封禁 ${getOnlineCount()} 个在线玩家`"
              type="error"
              :closable="false"
              show-icon
            />
          </div>
        </div>

        <!-- Operation Description -->
        <div class="operation-description">
          <p>{{ getOperationDescription() }}</p>
        </div>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          :type="getConfirmButtonType()" 
          @click="handleConfirm"
          :loading="loading"
        >
          {{ getConfirmButtonText() }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import type { PlayerResponse } from '@/types'

interface Props {
  visible: boolean
  players: PlayerResponse[]
  operation: string
}

interface Emits {
  (e: 'update:visible', visible: boolean): void
  (e: 'confirm', operationData: {
    action: string
    reason?: string
    duration?: number
  }): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Local state
const isVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = ref({
  reason: '',
  duration: 60
})

// Form validation rules
const rules: FormRules = {
  reason: [
    { 
      required: true, 
      message: '请输入操作原因', 
      trigger: 'blur',
      validator: (rule, value, callback) => {
        if (needsReason(props.operation) && (!value || value.trim().length === 0)) {
          callback(new Error('请输入操作原因'))
        } else {
          callback()
        }
      }
    },
    { min: 2, max: 200, message: '原因长度应在2-200字符之间', trigger: 'blur' }
  ],
  duration: [
    { 
      required: true, 
      message: '请输入封禁时长', 
      trigger: 'blur',
      validator: (rule, value, callback) => {
        if (props.operation === 'tempban' && (!value || value < 1)) {
          callback(new Error('封禁时长必须大于0'))
        } else {
          callback()
        }
      }
    }
  ]
}

// Computed properties
const getDialogTitle = () => {
  const titles = {
    kick: '批量踢出玩家',
    ban: '批量封禁玩家',
    tempban: '批量临时封禁',
    unban: '批量解除封禁',
    op: '批量给予OP权限',
    deop: '批量移除OP权限'
  }
  return titles[props.operation as keyof typeof titles] || '批量玩家操作'
}

const needsReason = (operation: string) => {
  return ['kick', 'ban', 'tempban', 'unban'].includes(operation)
}

const getReasonPlaceholder = () => {
  const placeholders = {
    kick: '请输入批量踢出原因',
    ban: '请输入批量封禁原因',
    tempban: '请输入批量临时封禁原因',
    unban: '请输入批量解封原因'
  }
  return placeholders[props.operation as keyof typeof placeholders] || '请输入操作原因'
}

const getOperationDescription = () => {
  const count = props.players.length
  const descriptions = {
    kick: `将 ${count} 个玩家踢出服务器，玩家可以重新加入`,
    ban: `永久封禁 ${count} 个玩家，这些玩家将无法加入服务器`,
    tempban: `临时封禁 ${count} 个玩家，到期后自动解封`,
    unban: `解除 ${count} 个玩家的封禁状态`,
    op: `给予 ${count} 个玩家管理员权限`,
    deop: `移除 ${count} 个玩家的管理员权限`
  }
  return descriptions[props.operation as keyof typeof descriptions] || ''
}

const getOperationWarning = () => {
  const count = props.players.length
  const warnings = {
    ban: `即将永久封禁 ${count} 个玩家，此操作不可逆，请谨慎执行！`,
    tempban: `即将临时封禁 ${count} 个玩家，封禁期间这些玩家无法登录服务器`,
    op: `即将给予 ${count} 个玩家管理员权限，请确保这些玩家值得信任`,
    deop: `即将移除 ${count} 个玩家的管理员权限`
  }
  return warnings[props.operation as keyof typeof warnings] || null
}

const getWarningType = () => {
  const types = {
    ban: 'error',
    tempban: 'warning',
    op: 'warning',
    deop: 'info'
  }
  return types[props.operation as keyof typeof types] || 'info'
}

const getConfirmButtonType = () => {
  const types = {
    kick: 'warning',
    ban: 'danger',
    tempban: 'danger',
    unban: 'success',
    op: 'primary',
    deop: 'info'
  }
  return types[props.operation as keyof typeof types] || 'primary'
}

const getConfirmButtonText = () => {
  const count = props.players.length
  const texts = {
    kick: `踢出 ${count} 个玩家`,
    ban: `封禁 ${count} 个玩家`,
    tempban: `临时封禁 ${count} 个玩家`,
    unban: `解封 ${count} 个玩家`,
    op: `给予 ${count} 个玩家OP`,
    deop: `移除 ${count} 个玩家OP`
  }
  return texts[props.operation as keyof typeof texts] || '确认执行'
}

// Statistics
const getOnlineCount = () => {
  return props.players.filter(p => p.online).length
}

const getOpCount = () => {
  return props.players.filter(p => p.is_op).length
}

const getBannedCount = () => {
  return props.players.filter(p => p.is_banned).length
}

// Event handlers
const handleClose = () => {
  emit('update:visible', false)
}

const resetForm = () => {
  form.value = {
    reason: '',
    duration: 60
  }
  formRef.value?.clearValidate()
}

const handleConfirm = async () => {
  if (!formRef.value) return
  
  try {
    // Validate form if needed
    if (needsReason(props.operation) || props.operation === 'tempban') {
      await formRef.value.validate()
    }
    
    loading.value = true
    
    // Prepare operation data
    const operationData: any = {
      action: props.operation
    }
    
    if (needsReason(props.operation)) {
      operationData.reason = form.value.reason.trim()
    }
    
    if (props.operation === 'tempban') {
      operationData.duration = form.value.duration
    }
    
    // Emit the operation
    emit('confirm', operationData)
    
  } catch (error) {
    // Form validation failed
    console.log('Form validation failed:', error)
  } finally {
    loading.value = false
  }
}

// Reset form when dialog opens/closes
watch(() => props.visible, (visible) => {
  if (!visible) {
    resetForm()
  }
})

// Pre-fill reason based on operation type
watch(() => props.operation, (operation) => {
  const defaultReasons = {
    kick: '批量管理操作',
    ban: '批量违规处理',
    tempban: '批量临时处理',
    unban: '批量解封处理'
  }
  
  if (needsReason(operation)) {
    form.value.reason = defaultReasons[operation as keyof typeof defaultReasons] || ''
  }
})
</script>

<style scoped>
.batch-operation-dialog {
  padding: 10px 0;
}

.selected-players {
  margin-bottom: 24px;
}

.selected-players h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.players-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 8px;
  background-color: #fafbfc;
}

.player-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  margin-bottom: 4px;
  background-color: white;
  border-radius: 4px;
  border: 1px solid #f0f0f0;
}

.player-item:last-child {
  margin-bottom: 0;
}

.player-avatar {
  background: linear-gradient(45deg, #409eff, #67c23a);
  color: white;
  font-weight: 600;
  font-size: 12px;
}

.player-name {
  font-weight: 500;
  color: #303133;
  flex: 1;
}

.player-tags {
  display: flex;
  gap: 4px;
}

.operation-form {
  margin-bottom: 20px;
}

.duration-unit {
  margin-left: 8px;
  color: #909399;
}

.duration-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.duration-hint span {
  margin-right: 8px;
}

.operation-warning {
  margin: 16px 0;
}

.affected-summary {
  margin: 20px 0;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.affected-summary h5 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
}

.summary-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 12px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-item .label {
  color: #606266;
  font-size: 13px;
}

.stat-item .value {
  color: #303133;
  font-weight: 600;
}

.special-warning {
  margin-top: 12px;
}

.operation-description {
  padding: 12px;
  background-color: #f0f9ff;
  border-radius: 6px;
  margin-top: 16px;
}

.operation-description p {
  margin: 0;
  color: #4b5563;
  font-size: 14px;
  line-height: 1.5;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.el-dialog__body) {
  padding-top: 10px;
  padding-bottom: 10px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-alert) {
  margin: 0;
}

/* Scrollbar styling */
.players-list::-webkit-scrollbar {
  width: 4px;
}

.players-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 2px;
}

.players-list::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 2px;
}

.players-list::-webkit-scrollbar-thumb:hover {
  background: #a8abb2;
}
</style>