import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// Configure NProgress
NProgress.configure({
  showSpinner: false,
  minimum: 0.1,
  speed: 200,
  trickleSpeed: 200
})

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: {
        requiresAuth: false,
        title: '登录'
      }
    },
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      meta: {
        requiresAuth: true
      },
      children: [
        {
          path: '',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue'),
          meta: {
            title: '仪表板',
            icon: 'chart-bar'
          }
        },
        {
          path: '/console',
          name: 'Console',
          component: () => import('@/views/Console.vue'),
          meta: {
            title: '控制台',
            icon: 'terminal',
            permissions: ['console.read']
          }
        },
        {
          path: '/players',
          name: 'Players',
          component: () => import('@/views/Players.vue'),
          meta: {
            title: '玩家管理',
            icon: 'users',
            permissions: ['players.read']
          }
        },
        {
          path: '/players/:uuid',
          name: 'PlayerDetail',
          component: () => import('@/views/PlayerDetail.vue'),
          meta: {
            title: '玩家详情',
            permissions: ['players.read']
          }
        },
        {
          path: '/files',
          name: 'Files',
          component: () => import('@/views/Files.vue'),
          meta: {
            title: '文件管理',
            icon: 'folder',
            permissions: ['files.read']
          }
        },
        {
          path: '/plugins',
          name: 'Plugins',
          component: () => import('@/views/Plugins.vue'),
          meta: {
            title: '插件管理',
            icon: 'puzzle-piece',
            permissions: ['plugins.read']
          }
        },
        {
          path: '/worlds',
          name: 'Worlds',
          component: () => import('@/views/Worlds.vue'),
          meta: {
            title: '世界管理',
            icon: 'globe',
            permissions: ['worlds.read']
          }
        },
        {
          path: '/backups',
          name: 'Backups',
          component: () => import('@/views/Backups.vue'),
          meta: {
            title: '备份管理',
            icon: 'archive',
            permissions: ['backups.read']
          }
        },
        {
          path: '/monitoring',
          name: 'Monitoring',
          component: () => import('@/views/Monitoring.vue'),
          meta: {
            title: '监控中心',
            icon: 'chart-line',
            permissions: ['monitoring.read']
          }
        },
        {
          path: '/logs',
          name: 'Logs',
          component: () => import('@/views/Logs.vue'),
          meta: {
            title: '日志查看',
            icon: 'document-text',
            permissions: ['logs.read']
          }
        },
        {
          path: '/settings',
          name: 'Settings',
          component: () => import('@/views/Settings.vue'),
          meta: {
            title: '系统设置',
            icon: 'cog',
            permissions: ['settings.read']
          }
        },
        {
          path: '/users',
          name: 'Users',
          component: () => import('@/views/Users.vue'),
          meta: {
            title: '用户管理',
            icon: 'user-group',
            permissions: ['users.read'],
            requiresAdmin: true
          }
        },
        {
          path: '/profile',
          name: 'Profile',
          component: () => import('@/views/Profile.vue'),
          meta: {
            title: '个人资料',
            icon: 'user'
          }
        }
      ]
    },
    {
      path: '/403',
      name: 'Forbidden',
      component: () => import('@/views/error/403.vue'),
      meta: {
        title: '访问被拒绝'
      }
    },
    {
      path: '/404',
      name: 'NotFound',
      component: () => import('@/views/error/404.vue'),
      meta: {
        title: '页面未找到'
      }
    },
    {
      path: '/500',
      name: 'ServerError',
      component: () => import('@/views/error/500.vue'),
      meta: {
        title: '服务器错误'
      }
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/404'
    }
  ]
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  NProgress.start()
  
  try {
    const authStore = useAuthStore()
    const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)
    const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin === true)
    
    // Check authentication
    if (requiresAuth && !authStore.isAuthenticated) {
      // Redirect to login page
      next({
        name: 'Login',
        query: { redirect: to.fullPath }
      })
      return
    }
  } catch (error) {
    console.warn('Auth store not available during navigation, allowing access:', error)
    // 如果auth store不可用，允许访问（通常是登录页面）
    if (to.name !== 'Login') {
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
  }
  
  try {
    const authStore = useAuthStore()
    
    // Check if user is trying to access login page while authenticated
    if (to.name === 'Login' && authStore.isAuthenticated) {
      next({ name: 'Dashboard' })
      return
    }
    
    // Check admin permissions
    const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin === true)
    if (requiresAdmin && !authStore.isAdmin) {
      next({ name: 'Forbidden' })
      return
    }
  } catch (error) {
    // Auth store not available, continue navigation
    console.warn('Auth store not available for admin check, continuing:', error)
  }
  
  // Check specific permissions
  const requiredPermissions = to.meta.permissions as string[]
  if (requiredPermissions && requiredPermissions.length > 0) {
    // For now, we'll skip permission checking as it depends on backend implementation
    // In a real implementation, you would check user permissions here
    // const hasPermission = requiredPermissions.some(permission => 
    //   authStore.user?.permissions?.includes(permission)
    // )
    // if (!hasPermission) {
    //   next({ name: 'Forbidden' })
    //   return
    // }
  }
  
  // Set document title
  if (to.meta.title) {
    document.title = `${to.meta.title} - Aetherius WebConsole`
  } else {
    document.title = 'Aetherius WebConsole'
  }
  
  next()
})

router.afterEach(() => {
  NProgress.done()
})

router.onError((error) => {
  console.error('Router error:', error)
  NProgress.done()
})

export default router