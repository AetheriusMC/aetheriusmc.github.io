import { createRouter, createWebHistory } from 'vue-router'
import LoginBasic from '@/views/LoginBasic.vue'
import DashboardTest from '@/views/DashboardTest.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: LoginBasic
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: DashboardTest
    },
    {
      path: '/',
      redirect: '/login'
    }
  ]
})

// 简化的路由守卫，不使用有问题的store
router.beforeEach((to, from, next) => {
  console.log('路由导航:', to.path)
  next()
})

export default router