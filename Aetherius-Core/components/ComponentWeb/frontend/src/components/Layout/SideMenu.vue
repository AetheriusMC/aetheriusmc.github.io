<template>
  <el-menu
    :default-active="activeMenu"
    class="side-menu"
    router
    :collapse="false"
  >
    <template v-for="route in menuRoutes" :key="route.path">
      <el-menu-item :index="route.path" class="menu-item">
        <el-icon>
          <component :is="route.meta.icon" />
        </el-icon>
        <span>{{ route.meta.title }}</span>
      </el-menu-item>
    </template>
  </el-menu>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { RouteRecordNormalized } from 'vue-router'

const route = useRoute()
const router = useRouter()

// Get menu routes from router
const menuRoutes = computed(() => {
  return router.getRoutes().filter(route => 
    route.meta?.title && route.path !== '/'
  ) as RouteRecordNormalized[]
})

// Active menu item
const activeMenu = computed(() => route.path)
</script>

<style scoped>
.side-menu {
  height: calc(100vh - 60px);
  border-right: none;
  background-color: #f5f7fa;
}

.menu-item {
  margin: 4px 8px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.menu-item:hover {
  background-color: #e1f3ff !important;
  color: #409EFF !important;
}

:deep(.el-menu-item.is-active) {
  background-color: #409EFF !important;
  color: white !important;
  border-radius: 6px;
}

:deep(.el-menu-item.is-active .el-icon) {
  color: white !important;
}

:deep(.el-menu-item) {
  border-radius: 6px;
  margin: 4px 8px;
  width: calc(100% - 16px);
}

:deep(.el-menu-item .el-icon) {
  width: 20px;
  height: 20px;
  margin-right: 8px;
}
</style>