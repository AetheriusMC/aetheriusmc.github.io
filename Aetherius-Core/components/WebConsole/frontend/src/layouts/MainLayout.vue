<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Sidebar -->
    <div class="fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0"
         :class="{ '-translate-x-full': !sidebarOpen }">
      <div class="flex flex-col h-full">
        <!-- Logo -->
        <div class="flex items-center justify-center h-16 px-4 bg-blue-600 dark:bg-blue-700">
          <h1 class="text-xl font-bold text-white">Aetherius Console</h1>
        </div>
        
        <!-- Navigation -->
        <nav class="flex-1 px-4 py-4 space-y-2 overflow-y-auto">
          <router-link
            v-for="item in navigation"
            :key="item.name"
            :to="item.to"
            class="flex items-center px-4 py-2 text-sm font-medium rounded-md transition-colors"
            :class="[
              $route.name === item.name
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200'
                : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white'
            ]"
          >
            <component :is="item.icon" class="w-5 h-5 mr-3" />
            {{ item.label }}
          </router-link>
        </nav>
        
        <!-- User menu -->
        <div class="p-4 border-t border-gray-200 dark:border-gray-700">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <img class="w-8 h-8 rounded-full" :src="userAvatar" :alt="user?.username" />
            </div>
            <div class="ml-3">
              <p class="text-sm font-medium text-gray-700 dark:text-gray-200">{{ user?.username }}</p>
              <p class="text-xs text-gray-500 dark:text-gray-400">{{ user?.role }}</p>
            </div>
            <button
              @click="logout"
              class="ml-auto p-1 text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
              title="退出登录"
            >
              <ArrowRightOnRectangleIcon class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Mobile sidebar overlay -->
    <div
      v-if="sidebarOpen"
      class="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
      @click="sidebarOpen = false"
    ></div>

    <!-- Main content -->
    <div class="lg:ml-64">
      <!-- Top bar -->
      <header class="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between px-4 py-4">
          <div class="flex items-center">
            <button
              @click="sidebarOpen = !sidebarOpen"
              class="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 lg:hidden"
            >
              <Bars3Icon class="w-6 h-6" />
            </button>
            
            <h1 class="ml-4 text-xl font-semibold text-gray-900 dark:text-white lg:ml-0">
              {{ $route.meta.title || 'Aetherius WebConsole' }}
            </h1>
          </div>

          <div class="flex items-center space-x-4">
            <!-- Server status -->
            <div class="flex items-center space-x-2">
              <div class="w-2 h-2 rounded-full" :class="serverStatusColor"></div>
              <span class="text-sm text-gray-600 dark:text-gray-300">{{ serverStatusText }}</span>
            </div>

            <!-- Notifications -->
            <button
              @click="showNotifications = !showNotifications"
              class="p-2 text-gray-400 hover:text-gray-500 dark:hover:text-gray-300 relative"
            >
              <BellIcon class="w-6 h-6" />
              <span
                v-if="unreadNotifications > 0"
                class="absolute -top-1 -right-1 h-4 w-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center"
              >
                {{ unreadNotifications > 99 ? '99+' : unreadNotifications }}
              </span>
            </button>

            <!-- Theme toggle -->
            <button
              @click="toggleTheme"
              class="p-2 text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
              title="切换主题"
            >
              <SunIcon v-if="isDark" class="w-6 h-6" />
              <MoonIcon v-else class="w-6 h-6" />
            </button>
          </div>
        </div>
      </header>

      <!-- Page content -->
      <main class="p-6">
        <router-view />
      </main>
    </div>

    <!-- Notifications panel -->
    <NotificationPanel v-model:show="showNotifications" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useServerStore } from '@/stores/server'
import {
  Bars3Icon,
  BellIcon,
  SunIcon,
  MoonIcon,
  ArrowRightOnRectangleIcon,
  ChartBarIcon,
  TerminalIcon,
  UsersIcon,
  FolderIcon,
  PuzzlePieceIcon,
  GlobeAltIcon,
  ArchiveBoxIcon,
  ChartLineIcon,
  DocumentTextIcon,
  CogIcon,
  UserGroupIcon,
  UserIcon
} from '@heroicons/vue/24/outline'
import NotificationPanel from '@/components/NotificationPanel.vue'

const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()
const serverStore = useServerStore()

const sidebarOpen = ref(false)
const showNotifications = ref(false)
const unreadNotifications = ref(0)

const user = computed(() => authStore.user)
const isDark = computed(() => themeStore.isDark)

const userAvatar = computed(() => {
  return user.value?.avatar || `https://ui-avatars.com/api/?name=${user.value?.username}&background=3b82f6&color=fff`
})

const serverStatusColor = computed(() => {
  switch (serverStore.status?.status) {
    case 'online':
      return 'bg-green-500'
    case 'offline':
      return 'bg-red-500'
    case 'starting':
    case 'stopping':
      return 'bg-yellow-500'
    default:
      return 'bg-gray-500'
  }
})

const serverStatusText = computed(() => {
  const status = serverStore.status?.status
  switch (status) {
    case 'online':
      return `在线 (${serverStore.playerCount}/${serverStore.maxPlayers})`
    case 'offline':
      return '离线'
    case 'starting':
      return '启动中'
    case 'stopping':
      return '关闭中'
    default:
      return '未知'
  }
})

const navigation = [
  { name: 'Dashboard', to: '/', label: '仪表板', icon: ChartBarIcon },
  { name: 'Console', to: '/console', label: '控制台', icon: TerminalIcon },
  { name: 'Players', to: '/players', label: '玩家管理', icon: UsersIcon },
  { name: 'Files', to: '/files', label: '文件管理', icon: FolderIcon },
  { name: 'Plugins', to: '/plugins', label: '插件管理', icon: PuzzlePieceIcon },
  { name: 'Worlds', to: '/worlds', label: '世界管理', icon: GlobeAltIcon },
  { name: 'Backups', to: '/backups', label: '备份管理', icon: ArchiveBoxIcon },
  { name: 'Monitoring', to: '/monitoring', label: '监控中心', icon: ChartLineIcon },
  { name: 'Logs', to: '/logs', label: '日志查看', icon: DocumentTextIcon },
  { name: 'Settings', to: '/settings', label: '系统设置', icon: CogIcon },
  { name: 'Users', to: '/users', label: '用户管理', icon: UserGroupIcon },
  { name: 'Profile', to: '/profile', label: '个人资料', icon: UserIcon }
]

const toggleTheme = () => {
  const newTheme = isDark.value ? 'light' : 'dark'
  themeStore.setTheme(newTheme)
}

const logout = async () => {
  await authStore.logout()
  router.push('/login')
}

let statusInterval: NodeJS.Timeout

onMounted(() => {
  // Fetch initial server status
  serverStore.fetchServerStatus()
  
  // Set up periodic status updates
  statusInterval = setInterval(() => {
    serverStore.fetchServerStatus()
  }, 10000) // Update every 10 seconds
})

onUnmounted(() => {
  if (statusInterval) {
    clearInterval(statusInterval)
  }
})
</script>