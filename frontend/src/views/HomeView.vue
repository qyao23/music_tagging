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
              <div class="stat-value">{{ musicCount ?? 0 }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-label">打标记录</div>
              <div class="stat-value">{{ recordCount ?? 0 }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6" v-if="userStore.isTagger">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-label">待打标</div>
              <div class="stat-value">{{ pendingCount ?? 0 }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6" v-if="userStore.isReviewer">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-label">待审核</div>
              <div class="stat-value">{{ taggedCount ?? 0 }}</div>
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
      const response = await getMusicList({ page: 1, page_size: 1 })
      if (response && response.data) {
        // response 是 ApiResponse，response.data 是分页数据
        const total = response.data.total
        musicCount.value = typeof total === 'number' ? total : 0
      } else {
        musicCount.value = 0
      }
    } catch (error) {
      console.error('加载音乐总数失败:', error)
      musicCount.value = 0
    }
  }

  // 加载打标记录统计
  try {
    // 使用 page_size: 100 获取第一页数据用于统计
    const response = await getTaggingTaskList({ page: 1, page_size: 100 })
    if (response && response.data) {
      // response 是 ApiResponse，response.data 是分页数据
      const items = response.data.items || []
      const total = response.data.total
      recordCount.value = typeof total === 'number' ? total : items.length
      // 只统计第一页的数据（最多100条），如果需要精确统计所有数据，需要分页获取
      pendingCount.value = items.filter(
        r => r.status === TaggingStatusEnum.PENDING || r.status === TaggingStatusEnum.REJECTED
      ).length
      taggedCount.value = items.filter(
        r => r.status === TaggingStatusEnum.TAGGED
      ).length
    } else {
      recordCount.value = 0
      pendingCount.value = 0
      taggedCount.value = 0
    }
  } catch (error) {
    console.error('加载打标记录统计失败:', error)
    recordCount.value = 0
    pendingCount.value = 0
    taggedCount.value = 0
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
