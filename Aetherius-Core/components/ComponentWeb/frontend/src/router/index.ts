import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard/DashboardView.vue'
import Console from '@/views/Console/ConsoleView.vue'
import Players from '@/views/Players/PlayersView.vue'
import FileManager from '@/views/FileManager/FileManagerView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: Dashboard,
      meta: {
        title: '仪表盘',
        icon: 'Dashboard'
      }
    },
    {
      path: '/console',
      name: 'console',
      component: Console,
      meta: {
        title: '实时控制台',
        icon: 'Monitor'
      }
    },
    {
      path: '/players',
      name: 'players',
      component: Players,
      meta: {
        title: '玩家管理',
        icon: 'User'
      }
    },
    {
      path: '/files',
      name: 'files',
      component: FileManager,
      meta: {
        title: '文件管理',
        icon: 'Folder'
      }
    }
  ]
})

export default router