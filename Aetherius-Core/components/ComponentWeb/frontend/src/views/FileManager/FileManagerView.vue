<template>
  <div class="file-manager-view">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="breadcrumb-section">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item>
            <el-button type="text" size="small" @click="navigateToPath('.')">
              <el-icon><House /></el-icon>
              根目录
            </el-button>
          </el-breadcrumb-item>
          <el-breadcrumb-item 
            v-for="(part, index) in pathParts" 
            :key="index"
          >
            <el-button 
              type="text" 
              size="small" 
              @click="navigateToPath(pathParts.slice(0, index + 1).join('/'))"
              v-if="index < pathParts.length - 1"
            >
              {{ part }}
            </el-button>
            <span v-else class="current-folder">{{ part }}</span>
          </el-breadcrumb-item>
        </el-breadcrumb>
      </div>

      <div class="toolbar-actions">
        <!-- 搜索框 -->
        <el-input
          v-model="searchQuery"
          placeholder="搜索文件..."
          size="small"
          class="search-input"
          clearable
          @keyup.enter="performSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <!-- 视图切换 -->
        <el-button-group size="small">
          <el-button 
            :type="viewMode === 'list' ? 'primary' : 'default'"
            @click="viewMode = 'list'"
          >
            <el-icon><List /></el-icon>
          </el-button>
          <el-button 
            :type="viewMode === 'grid' ? 'primary' : 'default'"
            @click="viewMode = 'grid'"
          >
            <el-icon><Grid /></el-icon>
          </el-button>
        </el-button-group>

        <!-- 上传按钮 -->
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleFileSelect"
          multiple
        >
          <el-button type="primary" size="small">
            <el-icon><Upload /></el-icon>
            上传文件
          </el-button>
        </el-upload>

        <!-- 新建按钮 -->
        <el-dropdown @command="handleCreateCommand">
          <el-button type="success" size="small">
            <el-icon><Plus /></el-icon>
            新建
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="folder">
                <el-icon><Folder /></el-icon>
                新建文件夹
              </el-dropdown-item>
              <el-dropdown-item command="file">
                <el-icon><Document /></el-icon>
                新建文件
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- 刷新按钮 -->
        <el-button 
          size="small" 
          @click="refreshCurrentPath"
          :loading="loading"
        >
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 文件列表区域 -->
    <div class="file-content" v-loading="loading">
      <!-- 列表视图 -->
      <div v-if="viewMode === 'list'" class="file-list">
        <el-table
          :data="allItems"
          @row-dblclick="handleItemDoubleClick"
          @selection-change="handleSelectionChange"
          height="100%"
          row-key="path"
        >
          <el-table-column type="selection" width="55" />
          
          <el-table-column label="名称" min-width="300">
            <template #default="{ row }">
              <div class="file-name-cell">
                <el-icon class="file-icon" :class="getFileIconClass(row)">
                  <component :is="getFileIcon(row)" />
                </el-icon>
                <span class="file-name">{{ row.name }}</span>
                <el-tag 
                  v-if="row.is_directory" 
                  size="small" 
                  type="info"
                  class="folder-tag"
                >
                  文件夹
                </el-tag>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="大小" width="120" align="right">
            <template #default="{ row }">
              <span v-if="!row.is_directory">{{ formatFileSize(row.size) }}</span>
              <span v-else class="text-muted">--</span>
            </template>
          </el-table-column>

          <el-table-column label="修改时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.modified_time) }}
            </template>
          </el-table-column>

          <el-table-column label="权限" width="100">
            <template #default="{ row }">
              <el-tag size="small" type="info">{{ row.permissions }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button-group size="small">
                <el-button 
                  type="primary" 
                  size="small"
                  @click="openFileEditor(row)"
                  v-if="!row.is_directory"
                  title="编辑文件"
                >
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button 
                  type="primary" 
                  size="small"
                  @click="handleItemDoubleClick(row)"
                  v-if="row.is_directory"
                  title="打开文件夹"
                >
                  <el-icon><View /></el-icon>
                </el-button>
                <el-button 
                  type="success" 
                  size="small"
                  @click="downloadFile(row)"
                  v-if="!row.is_directory"
                >
                  <el-icon><Download /></el-icon>
                </el-button>
                <el-button 
                  type="warning" 
                  size="small"
                  @click="showRenameDialog(row)"
                >
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button 
                  type="danger" 
                  size="small"
                  @click="deleteFile(row)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-button-group>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 网格视图 -->
      <div v-else class="file-grid">
        <div 
          v-for="item in allItems" 
          :key="item.path"
          class="file-grid-item"
          @dblclick="handleItemDoubleClick(item)"
          @click="handleItemClick(item)"
          :class="{ selected: selectedItems.includes(item) }"
        >
          <div class="file-grid-icon">
            <el-icon :class="getFileIconClass(item)">
              <component :is="getFileIcon(item)" />
            </el-icon>
          </div>
          <div class="file-grid-name">{{ item.name }}</div>
          <div class="file-grid-info">
            <span v-if="!item.is_directory">{{ formatFileSize(item.size) }}</span>
            <span v-else class="text-muted">文件夹</span>
          </div>
        </div>
      </div>


      <!-- 空状态 -->
      <el-empty 
        v-if="!loading && allItems.length === 0 && fileList.success"
        description="此目录为空"
        :image-size="120"
      />
    </div>

    <!-- 状态栏 -->
    <div class="status-bar">
      <div class="status-info">
        <span>{{ fileList.directories.length }} 个文件夹</span>
        <span>{{ fileList.files.length }} 个文件</span>
        <span v-if="selectedItems.length > 0">
          已选择 {{ selectedItems.length }} 项
        </span>
      </div>
      <div class="status-actions">
        <el-button 
          v-if="selectedItems.length > 0"
          type="danger" 
          size="small"
          @click="deleteSelectedFiles"
        >
          删除选中项
        </el-button>
      </div>
    </div>

    <!-- 创建文件/文件夹对话框 -->
    <el-dialog
      v-model="createDialog.visible"
      :title="`新建${createDialog.type === 'folder' ? '文件夹' : '文件'}`"
      width="400px"
    >
      <el-form :model="createDialog.form" label-width="80px">
        <el-form-item label="名称">
          <el-input
            v-model="createDialog.form.name"
            :placeholder="`请输入${createDialog.type === 'folder' ? '文件夹' : '文件'}名称`"
            @keyup.enter="confirmCreate"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="confirmCreate">确认</el-button>
      </template>
    </el-dialog>

    <!-- 重命名对话框 -->
    <el-dialog
      v-model="renameDialog.visible"
      title="重命名"
      width="400px"
    >
      <el-form :model="renameDialog.form" label-width="80px">
        <el-form-item label="新名称">
          <el-input
            v-model="renameDialog.form.name"
            placeholder="请输入新名称"
            @keyup.enter="confirmRename"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="renameDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="confirmRename">确认</el-button>
      </template>
    </el-dialog>

    <!-- 搜索结果对话框 -->
    <el-dialog
      v-model="searchDialog.visible"
      title="搜索结果"
      width="800px"
      :close-on-click-modal="false"
    >
      <div class="search-results">
        <div class="search-summary">
          找到 {{ searchResults.length }} 个结果 (搜索: "{{ searchDialog.query }}")
        </div>
        <el-table :data="searchResults" height="400px">
          <el-table-column label="名称" min-width="200">
            <template #default="{ row }">
              <div class="file-name-cell">
                <el-icon class="file-icon" :class="getFileIconClass(row)">
                  <component :is="getFileIcon(row)" />
                </el-icon>
                <span class="file-name">{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="路径" min-width="300" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.path }}
            </template>
          </el-table-column>
          <el-table-column label="大小" width="120" align="right">
            <template #default="{ row }">
              <span v-if="!row.is_directory">{{ formatFileSize(row.size) }}</span>
              <span v-else class="text-muted">--</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                size="small"
                @click="navigateToFile(row)"
              >
                打开
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- 文件编辑器对话框 -->
    <FileEditorDialog
      v-model:visible="editorDialog.visible"
      :file="editorDialog.file"
      @file-saved="handleFileSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox, type UploadInstance } from 'element-plus'
import {
  House, Search, List, Grid, Upload, Plus, ArrowDown,
  Folder, Document, Refresh, View, Download, Edit, Delete
} from '@element-plus/icons-vue'

import { ApiClient, handleApiError } from '@/utils/api'
import type { 
  FileInfo, 
  FileListResponse, 
  FileOperationResponse, 
  FileSearchResponse 
} from '@/types'
import FileEditorDialog from '@/components/FileManager/FileEditorDialog.vue'

// 响应式数据
const loading = ref(false)
const currentPath = ref('.')
const viewMode = ref<'list' | 'grid'>('list')
const searchQuery = ref('')
const selectedItems = ref<FileInfo[]>([])

const fileList = reactive<FileListResponse>({
  success: false,
  path: '.',
  parent_path: undefined,
  directories: [],
  files: [],
  total_directories: 0,
  total_files: 0
})

const searchResults = ref<FileInfo[]>([])

// 对话框状态
const createDialog = reactive({
  visible: false,
  type: 'folder' as 'folder' | 'file',
  form: {
    name: ''
  }
})

const renameDialog = reactive({
  visible: false,
  target: null as FileInfo | null,
  form: {
    name: ''
  }
})

const searchDialog = reactive({
  visible: false,
  query: ''
})

const editorDialog = reactive({
  visible: false,
  file: null as FileInfo | null
})

// 引用
const uploadRef = ref<UploadInstance>()

// 计算属性
const pathParts = computed(() => {
  if (currentPath.value === '.') return []
  return currentPath.value.split('/').filter(Boolean)
})

const allItems = computed(() => {
  return [...fileList.directories, ...fileList.files]
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

const formatDateTime = (dateTimeStr: string): string => {
  const date = new Date(dateTimeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getFileIcon = (item: FileInfo) => {
  if (item.is_directory) return Folder
  
  const ext = item.name.split('.').pop()?.toLowerCase()
  
  // 根据文件扩展名返回不同图标
  switch (ext) {
    case 'txt':
    case 'md':
    case 'yml':
    case 'yaml':
    case 'json':
    case 'xml':
    case 'properties':
      return Document
    default:
      return Document
  }
}

const getFileIconClass = (item: FileInfo): string => {
  if (item.is_directory) return 'folder-icon'
  
  const ext = item.name.split('.').pop()?.toLowerCase()
  
  switch (ext) {
    case 'txt':
    case 'md':
      return 'text-file-icon'
    case 'yml':
    case 'yaml':
    case 'json':
    case 'xml':
      return 'config-file-icon'
    case 'properties':
      return 'properties-file-icon'
    default:
      return 'default-file-icon'
  }
}

// 核心函数
const loadFileList = async (path: string = '.') => {
  loading.value = true
  selectedItems.value = [] // 清空选中项
  
  try {
    const response = await ApiClient.listFiles({ path })
    Object.assign(fileList, response)
    currentPath.value = response.path
    
    // 清空搜索查询
    searchQuery.value = ''
  } catch (error) {
    const apiError = handleApiError(error)
    ElMessage.error(`加载文件列表失败: ${apiError.error}`)
    
    // 在错误情况下，重置为空状态
    Object.assign(fileList, {
      success: false,
      path: path,
      parent_path: undefined,
      directories: [],
      files: [],
      total_directories: 0,
      total_files: 0
    })
  } finally {
    loading.value = false
  }
}

const navigateToPath = async (path: string) => {
  await loadFileList(path)
}

const refreshCurrentPath = () => {
  loadFileList(currentPath.value)
}

// 事件处理
const handleItemDoubleClick = (item: FileInfo) => {
  if (item.is_directory) {
    navigateToPath(item.path)
  } else {
    openFileEditor(item)
  }
}

const handleItemClick = (item: FileInfo) => {
  const index = selectedItems.value.findIndex(selected => selected.path === item.path)
  if (index > -1) {
    selectedItems.value.splice(index, 1)
  } else {
    selectedItems.value.push(item)
  }
}

const handleSelectionChange = (selection: FileInfo[]) => {
  selectedItems.value = selection
}

const handleCreateCommand = (command: string) => {
  createDialog.type = command as 'folder' | 'file'
  createDialog.form.name = ''
  createDialog.visible = true
}

const handleFileSelect = async (file: any) => {
  try {
    loading.value = true
    await ApiClient.uploadFile(file.raw, currentPath.value, false)
    ElMessage.success(`文件 ${file.name} 上传成功`)
    await refreshCurrentPath()
  } catch (error) {
    const apiError = handleApiError(error)
    ElMessage.error(`上传失败: ${apiError.error}`)
  } finally {
    loading.value = false
  }
}

const confirmCreate = async () => {
  if (!createDialog.form.name.trim()) {
    ElMessage.warning('请输入名称')
    return
  }

  try {
    const targetPath = currentPath.value === '.' 
      ? createDialog.form.name 
      : `${currentPath.value}/${createDialog.form.name}`

    if (createDialog.type === 'folder') {
      await ApiClient.fileOperation('create_directory', targetPath)
      ElMessage.success('文件夹创建成功')
    } else {
      await ApiClient.saveFileContent(targetPath, '', 'utf-8', false)
      ElMessage.success('文件创建成功')
    }

    createDialog.visible = false
    await refreshCurrentPath()
  } catch (error) {
    const apiError = handleApiError(error)
    ElMessage.error(`创建失败: ${apiError.error}`)
  }
}

const showRenameDialog = (item: FileInfo) => {
  renameDialog.target = item
  renameDialog.form.name = item.name
  renameDialog.visible = true
}

const confirmRename = async () => {
  if (!renameDialog.target || !renameDialog.form.name.trim()) {
    return
  }

  try {
    const newPath = renameDialog.target.path.replace(
      renameDialog.target.name, 
      renameDialog.form.name
    )
    
    await ApiClient.fileOperation('move', renameDialog.target.path, newPath)
    ElMessage.success('重命名成功')
    renameDialog.visible = false
    await refreshCurrentPath()
  } catch (error) {
    const apiError = handleApiError(error)
    ElMessage.error(`重命名失败: ${apiError.error}`)
  }
}

const deleteFile = async (item: FileInfo) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 "${item.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await ApiClient.fileOperation('delete', item.path)
    ElMessage.success('删除成功')
    await refreshCurrentPath()
  } catch (error: any) {
    if (error !== 'cancel') {
      const apiError = handleApiError(error)
      ElMessage.error(`删除失败: ${apiError.error}`)
    }
  }
}

const deleteSelectedFiles = async () => {
  if (selectedItems.value.length === 0) return

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedItems.value.length} 个项目吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    loading.value = true
    for (const item of selectedItems.value) {
      await ApiClient.fileOperation('delete', item.path)
    }
    
    ElMessage.success(`成功删除 ${selectedItems.value.length} 个项目`)
    selectedItems.value = []
    await refreshCurrentPath()
  } catch (error: any) {
    if (error !== 'cancel') {
      const apiError = handleApiError(error)
      ElMessage.error(`删除失败: ${apiError.error}`)
    }
  } finally {
    loading.value = false
  }
}

const downloadFile = async (item: FileInfo) => {
  if (item.is_directory) return

  try {
    const blob = await ApiClient.downloadFile(item.path)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = item.name
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('下载开始')
  } catch (error) {
    const apiError = handleApiError(error)
    ElMessage.error(`下载失败: ${apiError.error}`)
  }
}

const performSearch = async () => {
  if (!searchQuery.value.trim()) return

  try {
    loading.value = true
    const response = await ApiClient.searchFiles({
      path: currentPath.value,
      query: searchQuery.value,
      max_results: 100
    })
    
    searchResults.value = response.results
    searchDialog.query = searchQuery.value
    searchDialog.visible = true
  } catch (error) {
    const apiError = handleApiError(error)
    ElMessage.error(`搜索失败: ${apiError.error}`)
  } finally {
    loading.value = false
  }
}

const navigateToFile = (item: FileInfo) => {
  searchDialog.visible = false
  const pathParts = item.path.split('/')
  const parentPath = pathParts.slice(0, -1).join('/') || '.'
  navigateToPath(parentPath)
}

const openFileEditor = (item: FileInfo) => {
  if (item.is_directory) return
  
  editorDialog.file = item
  editorDialog.visible = true
}

const handleFileSaved = (file: FileInfo) => {
  // 文件保存后刷新文件列表
  refreshCurrentPath()
}

// 生命周期
onMounted(async () => {
  try {
    await loadFileList()
  } catch (error) {
    console.error('Failed to load file list in mounted:', error)
    ElMessage.error('初始化文件管理器失败')
  }
})
</script>

<style scoped>
.file-manager-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: white;
  border-bottom: 1px solid #e1e4e8;
  flex-shrink: 0;
}

.breadcrumb-section {
  flex: 1;
  min-width: 0;
}

.current-folder {
  font-weight: 600;
  color: #1f2328;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.search-input {
  width: 200px;
}

.file-content {
  flex: 1;
  background: white;
  margin: 0 16px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.file-list {
  height: 100%;
}

.file-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-icon {
  font-size: 18px;
}

.folder-icon {
  color: #0969da;
}

.text-file-icon {
  color: #6f42c1;
}

.config-file-icon {
  color: #e36209;
}

.properties-file-icon {
  color: #1a7f37;
}

.default-file-icon {
  color: #656d76;
}

.folder-tag {
  margin-left: auto;
}

.file-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 16px;
  padding: 16px;
  height: 100%;
  overflow-y: auto;
}

.file-grid-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.file-grid-item:hover {
  background: #f6f8fa;
}

.file-grid-item.selected {
  background: #dbeafe;
  border-color: #3b82f6;
}

.file-grid-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.file-grid-name {
  font-size: 12px;
  text-align: center;
  word-break: break-word;
  margin-bottom: 4px;
  font-weight: 500;
}

.file-grid-info {
  font-size: 11px;
  color: #656d76;
  text-align: center;
}

.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: white;
  border-top: 1px solid #e1e4e8;
  flex-shrink: 0;
}

.status-info {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #656d76;
}

.search-results {
  max-height: 500px;
}

.search-summary {
  margin-bottom: 16px;
  padding: 12px;
  background: #f6f8fa;
  border-radius: 6px;
  font-size: 14px;
  color: #656d76;
}

.text-muted {
  color: #656d76;
}

:deep(.el-table .el-table__row:hover td) {
  background-color: #f5f7fa;
}

:deep(.el-upload) {
  display: inline-block;
}
</style>