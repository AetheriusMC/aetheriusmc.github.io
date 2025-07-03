<template>
  <transition
    enter-active-class="transform transition ease-in-out duration-300"
    enter-from-class="translate-x-full"
    enter-to-class="translate-x-0"
    leave-active-class="transform transition ease-in-out duration-300"
    leave-from-class="translate-x-0"
    leave-to-class="translate-x-full"
  >
    <div
      v-if="show"
      class="fixed inset-y-0 right-0 z-50 w-96 bg-white dark:bg-gray-800 shadow-xl border-l border-gray-200 dark:border-gray-700"
    >
      <div class="flex flex-col h-full">
        <!-- Header -->
        <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">通知</h2>
          <div class="flex items-center space-x-2">
            <button
              @click="markAllAsRead"
              class="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
            >
              全部标记为已读
            </button>
            <button
              @click="$emit('update:show', false)"
              class="p-1 text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
            >
              <XMarkIcon class="w-5 h-5" />
            </button>
          </div>
        </div>

        <!-- Notifications list -->
        <div class="flex-1 overflow-y-auto">
          <div v-if="notifications.length === 0" class="p-8 text-center">
            <BellIcon class="w-12 h-12 mx-auto text-gray-400 dark:text-gray-600" />
            <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">暂无通知</p>
          </div>
          
          <div v-else class="divide-y divide-gray-200 dark:divide-gray-700">
            <div
              v-for="notification in notifications"
              :key="notification.id"
              class="p-4 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
              :class="{ 'bg-blue-50 dark:bg-blue-900/20': !notification.read }"
              @click="markAsRead(notification.id)"
            >
              <div class="flex items-start space-x-3">
                <div class="flex-shrink-0">
                  <component
                    :is="getNotificationIcon(notification.type)"
                    class="w-6 h-6"
                    :class="getNotificationColor(notification.type, notification.priority)"
                  />
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-900 dark:text-white">
                    {{ notification.title }}
                  </p>
                  <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {{ notification.message }}
                  </p>
                  <div class="flex items-center mt-2 space-x-2">
                    <span class="text-xs text-gray-400 dark:text-gray-500">
                      {{ formatTime(notification.timestamp) }}
                    </span>
                    <span
                      v-if="notification.priority === 'high' || notification.priority === 'critical'"
                      class="px-2 py-1 text-xs rounded-full"
                      :class="getPriorityClass(notification.priority)"
                    >
                      {{ getPriorityText(notification.priority) }}
                    </span>
                  </div>
                </div>
                <div v-if="!notification.read" class="flex-shrink-0">
                  <div class="w-2 h-2 bg-blue-500 rounded-full"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            @click="clearAll"
            class="w-full text-sm text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
          >
            清除所有通知
          </button>
        </div>
      </div>
    </div>
  </transition>

  <!-- Overlay -->
  <div
    v-if="show"
    class="fixed inset-0 z-40 bg-gray-600 bg-opacity-75"
    @click="$emit('update:show', false)"
  ></div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import {
  XMarkIcon,
  BellIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  ShieldExclamationIcon,
  UsersIcon,
  ServerIcon,
  WrenchScrewdriverIcon
} from '@heroicons/vue/24/outline'
import type { NotificationData } from '@/types'
import { websocketService } from '@/services/websocket'
import { useToast } from 'vue-toastification'

const toast = useToast()

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
}>()

const notifications = ref<NotificationData[]>([])

const getNotificationIcon = (type: string) => {
  switch (type) {
    case 'system':
      return ServerIcon
    case 'security':
      return ShieldExclamationIcon
    case 'player':
      return UsersIcon
    case 'server':
      return ServerIcon
    case 'maintenance':
      return WrenchScrewdriverIcon
    case 'error':
      return XCircleIcon
    case 'warning':
      return ExclamationTriangleIcon
    case 'info':
    case 'alert':
    default:
      return InformationCircleIcon
  }
}

const getNotificationColor = (type: string, priority: string) => {
  if (priority === 'critical') return 'text-red-600 dark:text-red-400'
  if (priority === 'high') return 'text-orange-600 dark:text-orange-400'
  
  switch (type) {
    case 'error':
      return 'text-red-600 dark:text-red-400'
    case 'warning':
      return 'text-yellow-600 dark:text-yellow-400'
    case 'security':
      return 'text-purple-600 dark:text-purple-400'
    case 'system':
    case 'server':
      return 'text-blue-600 dark:text-blue-400'
    case 'player':
      return 'text-green-600 dark:text-green-400'
    default:
      return 'text-gray-600 dark:text-gray-400'
  }
}

const getPriorityClass = (priority: string) => {
  switch (priority) {
    case 'critical':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
    case 'high':
      return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
  }
}

const getPriorityText = (priority: string) => {
  switch (priority) {
    case 'critical':
      return '紧急'
    case 'high':
      return '高'
    case 'medium':
      return '中'
    case 'low':
      return '低'
    default:
      return priority
  }
}

const formatTime = (timestamp: string) => {
  return formatDistanceToNow(new Date(timestamp), {
    addSuffix: true,
    locale: zhCN
  })
}

const markAsRead = (notificationId: string) => {
  const notification = notifications.value.find(n => n.id === notificationId)
  if (notification && !notification.read) {
    notification.read = true
    websocketService.markNotificationsRead([notificationId])
  }
}

const markAllAsRead = () => {
  const unreadIds = notifications.value
    .filter(n => !n.read)
    .map(n => n.id)
  
  if (unreadIds.length > 0) {
    notifications.value.forEach(n => n.read = true)
    websocketService.markNotificationsRead(unreadIds)
    toast.success('所有通知已标记为已读')
  }
}

const clearAll = () => {
  notifications.value = []
  toast.success('所有通知已清除')
}

const handleNotification = (notification: NotificationData) => {
  // Add to notifications list
  notifications.value.unshift(notification)
  
  // Keep only last 100 notifications
  if (notifications.value.length > 100) {
    notifications.value = notifications.value.slice(0, 100)
  }
  
  // Show toast for important notifications
  if (notification.priority === 'critical' || notification.priority === 'high') {
    if (notification.type === 'error') {
      toast.error(notification.message)
    } else if (notification.type === 'warning') {
      toast.warning(notification.message)
    } else {
      toast.info(notification.message)
    }
  }
}

onMounted(() => {
  // Connect to notifications WebSocket
  websocketService.connectNotifications()
  
  // Subscribe to all notification types
  websocketService.subscribeToNotifications()
  
  // Listen for new notifications
  websocketService.on('notification', handleNotification)
})

onUnmounted(() => {
  // Clean up WebSocket listeners
  websocketService.off('notification', handleNotification)
})
</script>