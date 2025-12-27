/**
 * 用户状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserResponse } from '../types/interfaces'
import { UserRoleEnum } from '../types/enums'
import { login, getCurrentUser } from '../api/user'
import { ElMessage } from 'element-plus'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<UserResponse | null>(null)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === UserRoleEnum.ADMIN)
  const isTagger = computed(() => user.value?.role === UserRoleEnum.TAGGER || user.value?.role === UserRoleEnum.ADMIN)
  const isReviewer = computed(() => user.value?.role === UserRoleEnum.REVIEWER || user.value?.role === UserRoleEnum.ADMIN)

  // 登录
  const loginUser = async (username: string, password: string) => {
    try {
      const response = await login({ username, password })
      if (response.data) {
        token.value = response.data
        localStorage.setItem('token', response.data)
        await fetchUserInfo()
        ElMessage.success('登录成功')
        return true
      }
      return false
    } catch (error) {
      return false
    }
  }

  // 获取用户信息
  const fetchUserInfo = async () => {
    try {
      const response = await getCurrentUser()
      if (response.data) {
        user.value = response.data
      }
    } catch (error) {
      // 如果获取失败，清除 token
      logout()
    }
  }

  // 登出
  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  // 初始化时如果有 token，获取用户信息
  if (token.value) {
    fetchUserInfo()
  }

  return {
    token,
    user,
    isLoggedIn,
    isAdmin,
    isTagger,
    isReviewer,
    loginUser,
    fetchUserInfo,
    logout
  }
})

