<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="(val) => emit('update:visible', val)"
    :title="dialogTitle"
    width="90%"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    @close="handleClose"
    class="file-editor-dialog"
  >
    <div class="editor-container">
      <!-- 编辑器工具栏 -->
      <div class="editor-toolbar">
        <div class="file-info">
          <el-icon class="file-icon"><Document /></el-icon>
          <span class="file-path">{{ currentFile?.path }}</span>
          <el-tag 
            v-if="isModified" 
            type="warning" 
            size="small"
            class="modified-tag"
          >
            已修改
          </el-tag>
        </div>

        <div class="toolbar-actions">
          <!-- 编码选择 -->
          <el-select
            v-model="encoding"
            size="small"
            class="encoding-select"
          >
            <el-option label="UTF-8" value="utf-8" />
            <el-option label="GBK" value="gbk" />
            <el-option label="ASCII" value="ascii" />
          </el-select>

          <!-- 语言模式 -->
          <el-select
            v-model="language"
            size="small"
            class="language-select"
            @change="updateEditorLanguage"
          >
            <el-option 
              v-for="lang in supportedLanguages" 
              :key="lang.value"
              :label="lang.label"
              :value="lang.value"
            />
          </el-select>

          <!-- 操作按钮 -->
          <el-button-group size="small">
            <el-button @click="formatDocument">
              <el-icon><Setting /></el-icon>
              格式化
            </el-button>
            <el-button @click="findAndReplace">
              <el-icon><Search /></el-icon>
              查找
            </el-button>
            <el-button @click="showShortcuts">
              <el-icon><QuestionFilled /></el-icon>
              快捷键
            </el-button>
          </el-button-group>

          <el-button 
            type="primary" 
            size="small"
            @click="saveFile"
            :loading="saving"
            :disabled="!isModified"
          >
            <el-icon><Check /></el-icon>
            保存 (Ctrl+S)
          </el-button>
        </div>
      </div>

      <!-- Monaco编辑器 -->
      <div class="editor-wrapper" ref="editorContainer"></div>

      <!-- 状态栏 -->
      <div class="editor-status-bar">
        <div class="status-left">
          <span>行 {{ cursorPosition.line }}, 列 {{ cursorPosition.column }}</span>
          <span>选中 {{ selectionInfo.selected }} 个字符</span>
          <span>总共 {{ contentStats.lines }} 行, {{ contentStats.characters }} 个字符</span>
        </div>
        <div class="status-right">
          <span>{{ language.toUpperCase() }}</span>
          <span>{{ encoding.toUpperCase() }}</span>
          <el-tag 
            :type="currentFile?.size && currentFile.size > 1024 * 1024 ? 'warning' : 'success'"
            size="small"
          >
            {{ formatFileSize(currentFile?.size) }}
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 对话框底部按钮 -->
    <template #footer>
      <el-button @click="handleClose">
        取消
      </el-button>
      <el-button 
        type="primary" 
        @click="saveAndClose"
        :loading="saving"
      >
        保存并关闭
      </el-button>
    </template>

    <!-- 快捷键对话框 -->
    <el-dialog
      :model-value="shortcutsDialog.visible"
      @update:model-value="(val) => shortcutsDialog.visible = val"
      title="编辑器快捷键"
      width="500px"
      append-to-body
    >
      <div class="shortcuts-list">
        <div 
          v-for="(shortcut, index) in shortcuts" 
          :key="index"
          class="shortcut-item"
        >
          <div class="shortcut-keys">
            <el-tag 
              v-for="key in shortcut.keys" 
              :key="key"
              size="small"
              class="key-tag"
            >
              {{ key }}
            </el-tag>
          </div>
          <div class="shortcut-desc">{{ shortcut.description }}</div>
        </div>
      </div>
    </el-dialog>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document, Setting, Search, QuestionFilled, Check
} from '@element-plus/icons-vue'
import * as monaco from 'monaco-editor'

import { ApiClient, handleApiError } from '@/utils/api'
import type { FileInfo, FileContentResponse } from '@/types'

// Props & Emits
interface Props {
  visible: boolean
  file: FileInfo | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'file-saved', file: FileInfo): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const currentFile = ref<FileInfo | null>(null)
const originalContent = ref('')
const currentContent = ref('')
const encoding = ref('utf-8')
const language = ref('plaintext')
const saving = ref(false)
const isModified = ref(false)

const cursorPosition = reactive({
  line: 1,
  column: 1
})

const selectionInfo = reactive({
  selected: 0,
  total: 0
})

const contentStats = reactive({
  lines: 0,
  characters: 0
})

const shortcutsDialog = reactive({
  visible: false
})

// 编辑器相关
const editorContainer = ref<HTMLElement>()
let editor: monaco.editor.IStandaloneCodeEditor | null = null

// 支持的语言列表
const supportedLanguages = [
  { label: 'Plain Text', value: 'plaintext' },
  { label: 'JSON', value: 'json' },
  { label: 'YAML', value: 'yaml' },
  { label: 'XML', value: 'xml' },
  { label: 'Properties', value: 'properties' },
  { label: 'JavaScript', value: 'javascript' },
  { label: 'TypeScript', value: 'typescript' },
  { label: 'Python', value: 'python' },
  { label: 'Java', value: 'java' },
  { label: 'Markdown', value: 'markdown' },
  { label: 'HTML', value: 'html' },
  { label: 'CSS', value: 'css' },
  { label: 'SQL', value: 'sql' },
  { label: 'Shell', value: 'shell' }
]

// 快捷键列表
const shortcuts = [
  { keys: ['Ctrl', 'S'], description: '保存文件' },
  { keys: ['Ctrl', 'F'], description: '查找' },
  { keys: ['Ctrl', 'H'], description: '查找并替换' },
  { keys: ['Ctrl', 'Z'], description: '撤销' },
  { keys: ['Ctrl', 'Y'], description: '重做' },
  { keys: ['Ctrl', 'A'], description: '全选' },
  { keys: ['Ctrl', 'C'], description: '复制' },
  { keys: ['Ctrl', 'V'], description: '粘贴' },
  { keys: ['Ctrl', 'X'], description: '剪切' },
  { keys: ['Ctrl', '+'], description: '放大' },
  { keys: ['Ctrl', '-'], description: '缩小' },
  { keys: ['Alt', 'Shift', 'F'], description: '格式化文档' },
  { keys: ['Ctrl', 'G'], description: '跳转到行' },
  { keys: ['F11'], description: '全屏切换' }
]

// 计算属性
const dialogTitle = computed(() => {
  if (!currentFile.value) return '文件编辑器'
  return `编辑文件: ${currentFile.value.name}`
})

// 工具函数
const formatFileSize = (bytes?: number): string => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let size = bytes
  let unitIndex = 0
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`
}

const detectLanguageFromFilename = (filename: string): string => {
  const ext = filename.split('.').pop()?.toLowerCase()
  
  const languageMap: Record<string, string> = {
    'json': 'json',
    'yml': 'yaml',
    'yaml': 'yaml',
    'xml': 'xml',
    'properties': 'properties',
    'js': 'javascript',
    'jsx': 'javascript',
    'ts': 'typescript',
    'tsx': 'typescript',
    'py': 'python',
    'java': 'java',
    'md': 'markdown',
    'html': 'html',
    'htm': 'html',
    'css': 'css',
    'scss': 'scss',
    'less': 'less',
    'sql': 'sql',
    'sh': 'shell',
    'bash': 'shell',
    'bat': 'bat',
    'cmd': 'bat'
  }
  
  return languageMap[ext || ''] || 'plaintext'
}

const updateContentStats = () => {
  if (!editor) return
  
  const model = editor.getModel()
  if (!model) return
  
  const content = model.getValue()
  contentStats.lines = model.getLineCount()
  contentStats.characters = content.length
  
  // 检查是否修改
  isModified.value = content !== originalContent.value
  currentContent.value = content
}

const updateCursorPosition = () => {
  if (!editor) return
  
  const position = editor.getPosition()
  if (position) {
    cursorPosition.line = position.lineNumber
    cursorPosition.column = position.column
  }
}

const updateSelectionInfo = () => {
  if (!editor) return
  
  const selection = editor.getSelection()
  if (selection) {
    const model = editor.getModel()
    if (model) {
      const selectedText = model.getValueInRange(selection)
      selectionInfo.selected = selectedText.length
    }
  }
}

// 编辑器操作
const initializeEditor = async () => {
  if (!editorContainer.value) return
  
  // 创建编辑器
  editor = monaco.editor.create(editorContainer.value, {
    value: currentContent.value,
    language: language.value,
    theme: 'vs-dark',
    automaticLayout: true,
    minimap: { enabled: true },
    fontSize: 14,
    wordWrap: 'on',
    lineNumbers: 'on',
    folding: true,
    find: {
      addExtraSpaceOnTop: false,
      autoFindInSelection: 'never',
      seedSearchStringFromSelection: 'always'
    },
    scrollBeyondLastLine: false,
    renderWhitespace: 'selection',
    contextmenu: true,
    mouseWheelZoom: true
  })
  
  // 绑定事件
  editor.onDidChangeModelContent(() => {
    updateContentStats()
  })
  
  editor.onDidChangeCursorPosition(() => {
    updateCursorPosition()
  })
  
  editor.onDidChangeCursorSelection(() => {
    updateSelectionInfo()
  })
  
  // 添加保存快捷键
  editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
    saveFile()
  })
  
  // 初始化状态
  updateContentStats()
  updateCursorPosition()
  updateSelectionInfo()
}

const updateEditorLanguage = () => {
  if (!editor) return
  
  const model = editor.getModel()
  if (model) {
    monaco.editor.setModelLanguage(model, language.value)
  }
}

const formatDocument = () => {
  if (!editor) return
  
  editor.getAction('editor.action.formatDocument')?.run()
}

const findAndReplace = () => {
  if (!editor) return
  
  editor.getAction('actions.find')?.run()
}

const showShortcuts = () => {
  shortcutsDialog.visible = true
}

// 文件操作
const loadFileContent = async (file: FileInfo) => {
  if (!file || file.is_directory) return
  
  // 检查文件大小限制 (10MB)
  if (file.size && file.size > 10 * 1024 * 1024) {
    ElMessage.warning('文件过大，无法在编辑器中打开（最大10MB）')
    return
  }
  
  try {
    const response = await ApiClient.getFileContent(file.path, encoding.value)
    currentContent.value = response.content
    originalContent.value = response.content
    
    // 自动检测语言
    language.value = detectLanguageFromFilename(file.name)
    
    // 更新编辑器内容
    if (editor) {
      const model = editor.getModel()
      if (model) {
        model.setValue(currentContent.value)
        monaco.editor.setModelLanguage(model, language.value)
        
        // 重置编辑器状态
        editor.setPosition({ lineNumber: 1, column: 1 })
        editor.focus()
        
        // 清除撤销历史
        model.pushStackElement()
      }
    }
    
    isModified.value = false
    
  } catch (error) {
    const apiError = handleApiError(error)
    if (apiError.status_code === 413) {
      ElMessage.error('文件过大，无法加载')
    } else if (apiError.status_code === 400 && apiError.error.includes('decode')) {
      ElMessage.error('文件编码不支持，请尝试其他编码格式')
    } else {
      ElMessage.error(`加载文件失败: ${apiError.error}`)
    }
  }
}

const saveFile = async () => {
  if (!currentFile.value || !editor) return
  
  try {
    saving.value = true
    const content = editor.getModel()?.getValue() || ''
    
    await ApiClient.saveFileContent(
      currentFile.value.path,
      content,
      encoding.value,
      true // 创建备份
    )
    
    originalContent.value = content
    isModified.value = false
    
    ElMessage.success('文件保存成功')
    emit('file-saved', currentFile.value)
    
  } catch (error) {
    const apiError = handleApiError(error)
    ElMessage.error(`保存失败: ${apiError.error}`)
  } finally {
    saving.value = false
  }
}

const saveAndClose = async () => {
  if (isModified.value) {
    await saveFile()
  }
  handleClose()
}

const handleClose = async () => {
  if (isModified.value) {
    try {
      await ElMessageBox.confirm(
        '文件已修改但未保存，确定要关闭吗？',
        '确认关闭',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )
    } catch {
      return // 用户取消
    }
  }
  
  emit('update:visible', false)
}

// 监听器
watch(() => props.visible, (newVal) => {
  if (newVal && props.file) {
    currentFile.value = props.file
    nextTick(() => {
      initializeEditor()
      loadFileContent(props.file!)
    })
  } else if (!newVal) {
    // 清理编辑器
    if (editor) {
      editor.dispose()
      editor = null
    }
    currentFile.value = null
    isModified.value = false
  }
})

watch(() => props.file, (newFile) => {
  if (newFile && props.visible) {
    currentFile.value = newFile
    loadFileContent(newFile)
  }
})

// 生命周期
onBeforeUnmount(() => {
  if (editor) {
    editor.dispose()
  }
})
</script>

<style scoped>
.file-editor-dialog {
  .el-dialog__body {
    padding: 0;
  }
}

.editor-container {
  height: 70vh;
  display: flex;
  flex-direction: column;
}

.editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f6f8fa;
  border-bottom: 1px solid #e1e4e8;
  flex-shrink: 0;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.file-icon {
  font-size: 16px;
  color: #656d76;
}

.file-path {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 13px;
  color: #1f2328;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.modified-tag {
  margin-left: 8px;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.encoding-select,
.language-select {
  width: 100px;
}

.editor-wrapper {
  flex: 1;
  min-height: 0;
}

.editor-status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: #f6f8fa;
  border-top: 1px solid #e1e4e8;
  font-size: 12px;
  color: #656d76;
  flex-shrink: 0;
}

.status-left,
.status-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.shortcuts-list {
  max-height: 400px;
  overflow-y: auto;
}

.shortcut-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.shortcut-item:last-child {
  border-bottom: none;
}

.shortcut-keys {
  display: flex;
  gap: 4px;
}

.key-tag {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 11px;
  background: #f6f8fa;
  border: 1px solid #d1d9e0;
  color: #1f2328;
}

.shortcut-desc {
  color: #656d76;
  font-size: 13px;
}

:deep(.el-dialog) {
  margin-top: 5vh !important;
}

:deep(.el-dialog__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #e1e4e8;
}

:deep(.el-dialog__footer) {
  padding: 16px 20px;
  border-top: 1px solid #e1e4e8;
}
</style>