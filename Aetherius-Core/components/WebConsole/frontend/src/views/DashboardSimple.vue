<template>
  <div class="min-h-screen bg-gray-100">
    <div class="bg-white shadow">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-6">
          <h1 class="text-2xl font-bold text-gray-900">Aetherius 仪表板</h1>
          <button 
            @click="handleLogout"
            class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded"
          >
            退出登录
          </button>
        </div>
      </div>
    </div>

    <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div class="px-4 py-6 sm:px-0">
        <div class="border-4 border-dashed border-gray-200 rounded-lg p-8">
          <div class="text-center">
            <h2 class="text-xl font-semibold text-gray-900 mb-4">欢迎使用 Aetherius WebConsole</h2>
            <p class="text-gray-600 mb-6">企业级Minecraft服务器管理平台</p>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
              <div class="bg-white p-6 rounded-lg shadow">
                <h3 class="text-lg font-medium text-gray-900 mb-2">服务器状态</h3>
                <p class="text-green-600 font-semibold">在线</p>
              </div>
              
              <div class="bg-white p-6 rounded-lg shadow">
                <h3 class="text-lg font-medium text-gray-900 mb-2">在线玩家</h3>
                <p class="text-blue-600 font-semibold">0 / 20</p>
              </div>
              
              <div class="bg-white p-6 rounded-lg shadow">
                <h3 class="text-lg font-medium text-gray-900 mb-2">CPU 使用率</h3>
                <p class="text-purple-600 font-semibold">15%</p>
              </div>
            </div>

            <div class="mt-8">
              <h3 class="text-lg font-medium text-gray-900 mb-4">快速操作</h3>
              <div class="space-x-4">
                <button class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded">
                  查看控制台
                </button>
                <button class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded">
                  管理插件
                </button>
                <button class="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded">
                  查看日志
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

console.log('DashboardSimple.vue 加载成功')

const router = useRouter()

const handleLogout = () => {
  console.log('退出登录')
  // 简单的登出逻辑 - 跳转回登录页
  router.push('/login')
}
</script>