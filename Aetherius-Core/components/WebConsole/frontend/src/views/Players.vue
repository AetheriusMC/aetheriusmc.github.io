<template>
  <div class="space-y-6">
    <!-- Players Header -->
    <div class="card p-6">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 class="text-xl font-semibold text-gray-900 dark:text-white">玩家管理</h2>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            管理服务器玩家，查看在线状态和执行管理操作
          </p>
        </div>
        
        <div class="mt-4 sm:mt-0 flex space-x-3">
          <button
            @click="refreshPlayers"
            class="btn btn-secondary"
            :disabled="loading"
          >
            <ArrowPathIcon class="w-4 h-4 mr-2" />
            刷新
          </button>
          
          <button
            @click="showBulkActions = !showBulkActions"
            class="btn btn-secondary"
            :class="{ 'bg-gray-200 dark:bg-gray-600': showBulkActions }"
          >
            <Cog6ToothIcon class="w-4 h-4 mr-2" />
            批量操作
          </button>
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
      <div class="card p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <UsersIcon class="h-8 w-8 text-green-600 dark:text-green-400" />
          </div>
          <div class="ml-5 w-0 flex-1">
            <dl>
              <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">在线玩家</dt>
              <dd class="text-lg font-medium text-gray-900 dark:text-white">{{ onlinePlayers.length }}</dd>
            </dl>
          </div>
        </div>
      </div>

      <div class="card p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <UserGroupIcon class="h-8 w-8 text-blue-600 dark:text-blue-400" />
          </div>
          <div class="ml-5 w-0 flex-1">
            <dl>
              <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">总玩家</dt>
              <dd class="text-lg font-medium text-gray-900 dark:text-white">{{ totalPlayers }}</dd>
            </dl>
          </div>
        </div>
      </div>

      <div class="card p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <NoSymbolIcon class="h-8 w-8 text-red-600 dark:text-red-400" />
          </div>
          <div class="ml-5 w-0 flex-1">
            <dl>
              <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">封禁玩家</dt>
              <dd class="text-lg font-medium text-gray-900 dark:text-white">{{ bannedPlayers.length }}</dd>
            </dl>
          </div>
        </div>
      </div>

      <div class="card p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <ClockIcon class="h-8 w-8 text-purple-600 dark:text-purple-400" />
          </div>
          <div class="ml-5 w-0 flex-1">
            <dl>
              <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">新玩家</dt>
              <dd class="text-lg font-medium text-gray-900 dark:text-white">{{ newPlayers.length }}</dd>
            </dl>
          </div>
        </div>
      </div>
    </div>

    <!-- Search and Filters -->
    <div class="card p-6">
      <div class="flex flex-col sm:flex-row sm:items-center space-y-4 sm:space-y-0 sm:space-x-4">
        <div class="flex-1">
          <div class="relative">
            <MagnifyingGlassIcon class="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索玩家..."
              class="pl-10 input"
            />
          </div>
        </div>
        
        <div class="flex space-x-2">
          <select v-model="statusFilter" class="input">
            <option value="">所有状态</option>
            <option value="online">在线</option>
            <option value="offline">离线</option>
            <option value="banned">已封禁</option>
          </select>
          
          <select v-model="sortBy" class="input">
            <option value="username">用户名</option>
            <option value="last_seen">最后登录</option>
            <option value="playtime">游戏时长</option>
            <option value="level">等级</option>
          </select>
          
          <button
            @click="sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'"
            class="btn btn-secondary"
          >
            <ArrowUpIcon v-if="sortOrder === 'asc'" class="w-4 h-4" />
            <ArrowDownIcon v-else class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- Bulk Actions -->
    <div v-if="showBulkActions" class="card p-6 border-l-4 border-blue-500">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <label class="flex items-center">
            <input
              v-model="selectAll"
              type="checkbox"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              @change="toggleSelectAll"
            />
            <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">
              全选 ({{ selectedPlayers.length }}/{{ filteredPlayers.length }})
            </span>
          </label>
        </div>
        
        <div v-if="selectedPlayers.length > 0" class="flex space-x-2">
          <button
            @click="bulkKick"
            class="btn btn-secondary text-sm"
          >
            踢出玩家
          </button>
          <button
            @click="bulkBan"
            class="btn btn-danger text-sm"
          >
            封禁玩家
          </button>
        </div>
      </div>
    </div>

    <!-- Players Table -->
    <div class="card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="table">
          <thead>
            <tr>
              <th v-if="showBulkActions" class="w-12">
                <input
                  v-model="selectAll"
                  type="checkbox"
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  @change="toggleSelectAll"
                />
              </th>
              <th>玩家</th>
              <th>状态</th>
              <th>位置</th>
              <th>游戏模式</th>
              <th>等级</th>
              <th>最后登录</th>
              <th>游戏时长</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr
              v-for="player in paginatedPlayers"
              :key="player.uuid"
              class="hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              <td v-if="showBulkActions">
                <input
                  v-model="selectedPlayers"
                  :value="player.uuid"
                  type="checkbox"
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </td>
              
              <td>
                <div class="flex items-center space-x-3">
                  <img
                    :src="`https://crafthead.net/avatar/${player.uuid}/32`"
                    :alt="player.username"
                    class="w-8 h-8 rounded-lg"
                  />
                  <div>
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                      {{ player.display_name || player.username }}
                    </p>
                    <p class="text-xs text-gray-500 dark:text-gray-400">{{ player.username }}</p>
                  </div>
                </div>
              </td>
              
              <td>
                <span
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                  :class="getStatusClass(player)"
                >
                  <div class="w-1.5 h-1.5 rounded-full mr-1.5" :class="getStatusDotClass(player)"></div>
                  {{ getStatusText(player) }}
                </span>
              </td>
              
              <td>
                <div v-if="player.location && player.online" class="text-sm">
                  <p class="text-gray-900 dark:text-white">{{ player.location.world }}</p>
                  <p class="text-gray-500 dark:text-gray-400">
                    {{ Math.round(player.location.x) }}, {{ Math.round(player.location.y) }}, {{ Math.round(player.location.z) }}
                  </p>
                </div>
                <span v-else class="text-sm text-gray-500 dark:text-gray-400">-</span>
              </td>
              
              <td>
                <span class="text-sm text-gray-900 dark:text-white">
                  {{ player.gamemode || '-' }}
                </span>
              </td>
              
              <td>
                <span class="text-sm text-gray-900 dark:text-white">{{ player.level || 0 }}</span>
              </td>
              
              <td>
                <span class="text-sm text-gray-500 dark:text-gray-400">
                  {{ formatTime(player.last_seen) }}
                </span>
              </td>
              
              <td>
                <span class="text-sm text-gray-500 dark:text-gray-400">
                  {{ formatPlaytime(player.playtime) }}
                </span>
              </td>
              
              <td>
                <div class="flex items-center space-x-2">
                  <button
                    @click="viewPlayer(player)"
                    class="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                    title="查看详情"
                  >
                    <EyeIcon class="w-4 h-4" />
                  </button>
                  
                  <button
                    v-if="player.online"
                    @click="kickPlayer(player)"
                    class="text-orange-600 hover:text-orange-700 dark:text-orange-400 dark:hover:text-orange-300"
                    title="踢出服务器"
                  >
                    <ArrowRightOnRectangleIcon class="w-4 h-4" />
                  </button>
                  
                  <button
                    v-if="!player.banned"
                    @click="banPlayer(player)"
                    class="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                    title="封禁玩家"
                  >
                    <NoSymbolIcon class="w-4 h-4" />
                  </button>
                  
                  <button
                    v-else
                    @click="unbanPlayer(player)"
                    class="text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300"
                    title="解除封禁"
                  >
                    <CheckCircleIcon class="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- Pagination -->
      <div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <div class="text-sm text-gray-700 dark:text-gray-300">
            显示 {{ (currentPage - 1) * pageSize + 1 }} 到 {{ Math.min(currentPage * pageSize, filteredPlayers.length) }} 条，
            共 {{ filteredPlayers.length }} 条记录
          </div>
          
          <div class="flex items-center space-x-2">
            <button
              @click="currentPage--"
              :disabled="currentPage <= 1"
              class="btn btn-secondary text-sm"
            >
              上一页
            </button>
            
            <span class="text-sm text-gray-700 dark:text-gray-300">
              第 {{ currentPage }} 页，共 {{ totalPages }} 页
            </span>
            
            <button
              @click="currentPage++"
              :disabled="currentPage >= totalPages"
              class="btn btn-secondary text-sm"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  UsersIcon,
  UserGroupIcon,
  NoSymbolIcon,
  ClockIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
  Cog6ToothIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  EyeIcon,
  ArrowRightOnRectangleIcon,
  CheckCircleIcon
} from '@heroicons/vue/24/outline'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import type { Player } from '@/types'
import { apiClient } from '@/services/api'
import { useToast } from 'vue-toastification'

const router = useRouter()
const toast = useToast()

const players = ref<Player[]>([])
const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const sortBy = ref('username')
const sortOrder = ref<'asc' | 'desc'>('asc')
const currentPage = ref(1)
const pageSize = ref(20)
const showBulkActions = ref(false)
const selectedPlayers = ref<string[]>([])
const selectAll = ref(false)

const onlinePlayers = computed(() => players.value.filter(p => p.online))
const totalPlayers = computed(() => players.value.length)
const bannedPlayers = computed(() => players.value.filter(p => p.banned))
const newPlayers = computed(() => {
  const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
  return players.value.filter(p => new Date(p.first_join) > weekAgo)
})

const filteredPlayers = computed(() => {
  let filtered = players.value

  // Search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(p => 
      p.username.toLowerCase().includes(query) ||
      p.display_name?.toLowerCase().includes(query)
    )
  }

  // Status filter
  if (statusFilter.value) {
    filtered = filtered.filter(p => {
      switch (statusFilter.value) {
        case 'online':
          return p.online
        case 'offline':
          return !p.online
        case 'banned':
          return p.banned
        default:
          return true
      }
    })
  }

  // Sort
  filtered.sort((a, b) => {
    let aValue: any, bValue: any
    
    switch (sortBy.value) {
      case 'username':
        aValue = a.username.toLowerCase()
        bValue = b.username.toLowerCase()
        break
      case 'last_seen':
        aValue = new Date(a.last_seen)
        bValue = new Date(b.last_seen)
        break
      case 'playtime':
        aValue = a.playtime
        bValue = b.playtime
        break
      case 'level':
        aValue = a.level
        bValue = b.level
        break
      default:
        return 0
    }
    
    if (aValue < bValue) return sortOrder.value === 'asc' ? -1 : 1
    if (aValue > bValue) return sortOrder.value === 'asc' ? 1 : -1
    return 0
  })

  return filtered
})

const paginatedPlayers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredPlayers.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(filteredPlayers.value.length / pageSize.value)
})

const getStatusClass = (player: Player) => {
  if (player.banned) {
    return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
  } else if (player.online) {
    return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
  } else {
    return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
  }
}

const getStatusDotClass = (player: Player) => {
  if (player.banned) {
    return 'bg-red-500'
  } else if (player.online) {
    return 'bg-green-500'
  } else {
    return 'bg-gray-500'
  }
}

const getStatusText = (player: Player) => {
  if (player.banned) return '已封禁'
  if (player.online) return '在线'
  return '离线'
}

const formatTime = (timestamp: string) => {
  return formatDistanceToNow(new Date(timestamp), {
    addSuffix: true,
    locale: zhCN
  })
}

const formatPlaytime = (minutes: number) => {
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  
  if (hours > 24) {
    const days = Math.floor(hours / 24)
    const remainingHours = hours % 24
    return `${days}天 ${remainingHours}小时`
  } else if (hours > 0) {
    return `${hours}小时 ${remainingMinutes}分钟`
  } else {
    return `${remainingMinutes}分钟`
  }
}

const refreshPlayers = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/players')
    if (response.data.success) {
      players.value = response.data.data
    }
  } catch (error) {
    console.error('Failed to fetch players:', error)
    toast.error('获取玩家列表失败')
  } finally {
    loading.value = false
  }
}

const toggleSelectAll = () => {
  if (selectAll.value) {
    selectedPlayers.value = filteredPlayers.value.map(p => p.uuid)
  } else {
    selectedPlayers.value = []
  }
}

const viewPlayer = (player: Player) => {
  router.push(`/players/${player.uuid}`)
}

const kickPlayer = async (player: Player) => {
  try {
    const response = await apiClient.post(`/players/${player.uuid}/kick`, {
      reason: '被管理员踢出'
    })
    
    if (response.data.success) {
      toast.success(`玩家 ${player.username} 已被踢出`)
      await refreshPlayers()
    }
  } catch (error) {
    console.error('Failed to kick player:', error)
    toast.error('踢出玩家失败')
  }
}

const banPlayer = async (player: Player) => {
  const reason = prompt('请输入封禁原因:')
  if (!reason) return
  
  try {
    const response = await apiClient.post(`/players/${player.uuid}/ban`, {
      reason,
      duration: null // Permanent ban
    })
    
    if (response.data.success) {
      toast.success(`玩家 ${player.username} 已被封禁`)
      await refreshPlayers()
    }
  } catch (error) {
    console.error('Failed to ban player:', error)
    toast.error('封禁玩家失败')
  }
}

const unbanPlayer = async (player: Player) => {
  try {
    const response = await apiClient.post(`/players/${player.uuid}/unban`)
    
    if (response.data.success) {
      toast.success(`玩家 ${player.username} 已解除封禁`)
      await refreshPlayers()
    }
  } catch (error) {
    console.error('Failed to unban player:', error)
    toast.error('解除封禁失败')
  }
}

const bulkKick = async () => {
  if (selectedPlayers.value.length === 0) return
  
  const reason = prompt('请输入踢出原因:')
  if (!reason) return
  
  try {
    const promises = selectedPlayers.value.map(uuid =>
      apiClient.post(`/players/${uuid}/kick`, { reason })
    )
    
    await Promise.all(promises)
    toast.success(`已踢出 ${selectedPlayers.value.length} 个玩家`)
    selectedPlayers.value = []
    selectAll.value = false
    await refreshPlayers()
  } catch (error) {
    console.error('Failed to kick players:', error)
    toast.error('批量踢出玩家失败')
  }
}

const bulkBan = async () => {
  if (selectedPlayers.value.length === 0) return
  
  const reason = prompt('请输入封禁原因:')
  if (!reason) return
  
  try {
    const promises = selectedPlayers.value.map(uuid =>
      apiClient.post(`/players/${uuid}/ban`, { reason, duration: null })
    )
    
    await Promise.all(promises)
    toast.success(`已封禁 ${selectedPlayers.value.length} 个玩家`)
    selectedPlayers.value = []
    selectAll.value = false
    await refreshPlayers()
  } catch (error) {
    console.error('Failed to ban players:', error)
    toast.error('批量封禁玩家失败')
  }
}

onMounted(() => {
  refreshPlayers()
})
</script>