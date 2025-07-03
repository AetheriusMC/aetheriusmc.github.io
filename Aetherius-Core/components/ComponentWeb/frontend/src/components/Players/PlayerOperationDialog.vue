<template>
  <el-dialog
    v-model="isVisible"
    :title="getDialogTitle()"
    width="500px"
    :before-close="handleClose"
    @close="resetForm"
  >
    <div class="operation-dialog">
      <!-- Player Info -->
      <div v-if="player" class="player-info">
        <el-avatar :size="40" class="player-avatar">
          {{ player.name.charAt(0).toUpperCase() }}
        </el-avatar>
        <div class="player-details">
          <div class="player-name">{{ player.name }}</div>
          <div class="player-status">
            <el-tag v-if="player.online" type="success" size="small">在线</el-tag>
            <el-tag v-else type="info" size="small">离线</el-tag>
            <el-tag v-if="player.is_op" type="warning" size="small">OP</el-tag>
            <el-tag v-if="player.is_banned" type="danger" size="small">已封禁</el-tag>
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
  player: PlayerResponse | null
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
    kick: '踢出玩家',
    ban: '封禁玩家',
    tempban: '临时封禁',
    unban: '解除封禁',
    op: '给予OP权限',
    deop: '移除OP权限',
    teleport: '传送玩家',
    heal: '治疗玩家'
  }
  return titles[props.operation as keyof typeof titles] || '玩家操作'
}

const needsReason = (operation: string) => {
  return ['kick', 'ban', 'tempban', 'unban'].includes(operation)
}

const getReasonPlaceholder = () => {
  const placeholders = {
    kick: '请输入踢出原因，如：违反服务器规则',
    ban: '请输入封禁原因，如：恶意破坏、作弊等',
    tempban: '请输入临时封禁原因',
    unban: '请输入解封原因，如：申诉成功、误封等'
  }
  return placeholders[props.operation as keyof typeof placeholders] || '请输入操作原因'
}

const getOperationDescription = () => {
  if (!props.player) return ''
  
  const descriptions = {
    kick: `将玩家 ${props.player.name} 踢出服务器，玩家可以重新加入`,
    ban: `永久封禁玩家 ${props.player.name}，玩家将无法加入服务器`,
    tempban: `临时封禁玩家 ${props.player.name}，到期后自动解封`,
    unban: `解除玩家 ${props.player.name} 的封禁状态`,
    op: `给予玩家 ${props.player.name} 管理员权限`,
    deop: `移除玩家 ${props.player.name} 的管理员权限`,
    teleport: `将玩家 ${props.player.name} 传送到出生点`,
    heal: `恢复玩家 ${props.player.name} 的生命值和饥饿值`
  }
  return descriptions[props.operation as keyof typeof descriptions] || ''
}

const getOperationWarning = () => {
  const warnings = {
    ban: '永久封禁是不可逆操作，请谨慎执行！',
    tempban: '临时封禁期间玩家无法登录服务器',
    op: '给予OP权限后玩家将拥有管理员权限',
    deop: '移除OP权限后玩家将失去管理员权限'
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
    deop: 'info',
    teleport: 'primary',
    heal: 'success'
  }
  return types[props.operation as keyof typeof types] || 'primary'
}

const getConfirmButtonText = () => {
  const texts = {
    kick: '确认踢出',
    ban: '确认封禁',
    tempban: '确认临时封禁',
    unban: '确认解封',
    op: '确认给予OP',
    deop: '确认移除OP',
    teleport: '确认传送',
    heal: '确认治疗'
  }
  return texts[props.operation as keyof typeof texts] || '确认'
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
    kick: '违反服务器规则',
    ban: '严重违规行为',
    tempban: '违反服务器规则',
    unban: '申诉通过'
  }
  
  if (needsReason(operation)) {
    form.value.reason = defaultReasons[operation as keyof typeof defaultReasons] || ''
  }
})
</script>

<style scoped>
.operation-dialog {
  padding: 10px 0;
}

.player-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 20px;
}

.player-avatar {
  background: linear-gradient(45deg, #409eff, #67c23a);
  color: white;
  font-weight: 600;
}

.player-details {
  flex: 1;
}

.player-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.player-status {
  display: flex;
  gap: 8px;
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
</style>