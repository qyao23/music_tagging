<template>
  <div class="home-container">
    <el-card class="welcome-card">
      <template #header>
        <div class="card-header">
          <span>欢迎使用音乐打标平台</span>
        </div>
      </template>
      <div class="welcome-content">
        <p>当前用户：{{ userStore.user?.username }}</p>
        <p>角色：{{ getRoleText(userStore.user?.role) }}</p>
      </div>
    </el-card>

    <div class="stats-container">
      <el-row :gutter="20">
        <el-col :span="6" v-if="userStore.isAdmin">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-label">音乐总数</div>
              <div class="stat-value">{{ musicCount }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-label">打标记录</div>
              <div class="stat-value">{{ recordCount }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6" v-if="userStore.isTagger">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-label">待打标</div>
              <div class="stat-value">{{ pendingCount }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6" v-if="userStore.isReviewer">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-label">待审核</div>
              <div class="stat-value">{{ taggedCount }}</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import { getMusicList } from '../api/music'
import { getTaggingTaskList } from '../api/tagging'
import { UserRoleEnum, TaggingStatusEnum } from '../types/enums'

const userStore = useUserStore()
const musicCount = ref(0)
const recordCount = ref(0)
const pendingCount = ref(0)
const taggedCount = ref(0)

// 获取角色文本
const getRoleText = (role?: UserRoleEnum) => {
  if (!role) return ''
  const map: Record<UserRoleEnum, string> = {
    [UserRoleEnum.TAGGER]: '打标员',
    [UserRoleEnum.REVIEWER]: '审核员',
    [UserRoleEnum.ADMIN]: '管理员'
  }
  return map[role] || role
}

// 加载统计数据
const loadStats = async () => {
  // 加载音乐总数（仅管理员）
  if (userStore.isAdmin) {
    try {
      const response = await getMusicList()
      if (response.data) {
        musicCount.value = response.data.length
      }
    } catch (error) {
      // 错误已在拦截器中处理
    }
  }

  // 加载打标记录统计
  try {
    const response = await getTaggingTaskList()
    if (response.data) {
      recordCount.value = response.data.length
      pendingCount.value = response.data.filter(
        r => r.status === TaggingStatusEnum.PENDING || r.status === TaggingStatusEnum.REJECTED
      ).length
      taggedCount.value = response.data.filter(
        r => r.status === TaggingStatusEnum.TAGGED
      ).length
    }
  } catch (error) {
    // 错误已在拦截器中处理
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.home-container {
  padding: 20px;
}

.welcome-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #409eff;
}

.welcome-content {
  font-size: 16px;
  line-height: 2;
}

.stats-container {
  margin-top: 20px;
}

.stat-card {
  text-align: center;
}

.stat-item {
  padding: 20px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: #409eff;
}
</style>
