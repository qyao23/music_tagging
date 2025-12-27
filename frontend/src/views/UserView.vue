<template>
  <div class="user-container">
    <div class="header">
      <h2>用户管理</h2>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索用户名或ID"
        clearable
        style="width: 250px"
        @clear="handleSearch"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select
        v-model="filterRole"
        placeholder="角色"
        clearable
        style="width: 150px"
      >
        <el-option label="打标员" value="tagger" />
        <el-option label="审核员" value="reviewer" />
        <el-option label="管理员" value="admin" />
      </el-select>
      <el-button type="primary" @click="handleSearch">搜索</el-button>
    </div>

    <el-table
      :data="userList"
      v-loading="loading"
      stripe
      style="width: 100%"
    >
      <el-table-column prop="username" label="用户名" />
      <el-table-column label="角色" width="120">
        <template #default="{ row }">
          <el-tag :type="getRoleType(row.role)">
            {{ getRoleText(row.role) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="create_time" label="创建时间" width="180" />
    </el-table>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { getUserList } from '../api/user'
import type { UserResponse } from '../types/interfaces'
import { UserRoleEnum } from '../types/enums'

const userList = ref<UserResponse[]>([])
const loading = ref(false)
const searchKeyword = ref('')
const filterRole = ref<string>('')

// 加载用户列表
const loadUserList = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (filterRole.value) params.role = filterRole.value as UserRoleEnum
    
    const response = await getUserList(params)
    if (response.data) {
      userList.value = response.data
    }
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  loadUserList()
}

// 获取角色文本
const getRoleText = (role: UserRoleEnum) => {
  const map: Record<UserRoleEnum, string> = {
    [UserRoleEnum.TAGGER]: '打标员',
    [UserRoleEnum.REVIEWER]: '审核员',
    [UserRoleEnum.ADMIN]: '管理员'
  }
  return map[role] || role
}

// 获取角色类型
const getRoleType = (role: UserRoleEnum) => {
  const map: Record<UserRoleEnum, string> = {
    [UserRoleEnum.TAGGER]: 'primary',
    [UserRoleEnum.REVIEWER]: 'success',
    [UserRoleEnum.ADMIN]: 'warning'
  }
  return map[role] || ''
}

onMounted(() => {
  loadUserList()
})
</script>

<style scoped>
.user-container {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  color: #409eff;
}

.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
</style>

