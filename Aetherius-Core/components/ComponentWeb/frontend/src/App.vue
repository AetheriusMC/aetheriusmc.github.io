<template>
  <div id="app">
    <el-container class="app-container">
      <el-header class="app-header">
        <NavBar />
      </el-header>
      <el-container>
        <el-aside width="250px" class="app-sidebar">
          <SideMenu />
        </el-aside>
        <el-main class="app-main">
          <RouterView />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import NavBar from '@/components/Layout/NavBar.vue'
import SideMenu from '@/components/Layout/SideMenu.vue'
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.app-header {
  background-color: #409EFF;
  color: white;
  padding: 0;
  border-bottom: 1px solid #e4e7ed;
}

.app-sidebar {
  background-color: #f5f7fa;
  border-right: 1px solid #e4e7ed;
  padding: 0;
}

.app-main {
  background-color: #ffffff;
  padding: 20px;
  overflow-y: auto;
}
</style>