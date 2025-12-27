<template>
  <el-container class="layout-container">
    <el-header class="header">
      <div class="header-left">
        <h1 class="logo">音乐打标平台</h1>
      </div>
      <div class="header-right">
        <span class="username">{{ userStore.user?.username }}</span>
        <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
      </div>
    </el-header>
    <el-container>
      <el-aside width="200px" class="aside">
        <el-menu
          :default-active="activeMenu"
          router
          class="menu"
        >
          <el-menu-item index="/">
            <el-icon><HomeFilled /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-menu-item index="/music">
            <el-icon><VideoPlay /></el-icon>
            <span>音乐管理</span>
          </el-menu-item>
          <el-menu-item v-if="userStore.isAdmin" index="/tagging-question">
            <el-icon><Document /></el-icon>
            <span>题目管理</span>
          </el-menu-item>
          <el-menu-item index="/tagging-task">
            <el-icon><Edit /></el-icon>
            <span>打标任务</span>
          </el-menu-item>
          <el-menu-item v-if="userStore.isAdmin" index="/user">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { HomeFilled, VideoPlay, Document, List, User, Edit } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 当前激活的菜单项
const activeMenu = computed(() => route.path)

// 退出登录
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    userStore.logout()
    // 使用 replace 而不是 push，避免返回时回到已登录状态
    router.replace('/login')
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #409eff;
  color: white;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.username {
  font-size: 14px;
}

.aside {
  background: #f5f7fa;
}

.menu {
  border-right: none;
  height: 100%;
}

.main {
  background: #f0f2f5;
  padding: 20px;
}
</style>

