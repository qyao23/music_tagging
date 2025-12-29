/**
 * 用户相关 API
 */
import api from './index'
import type { ApiResponse, UserCreate, UserLogin, UserResponse } from '../types/interfaces'
import { UserRoleEnum } from '../types/enums'

/**
 * 用户注册
 */
export const register = async (data: UserCreate): Promise<ApiResponse<number>> => {
  const response = await api.post('/user/register', data)
  return response.data
}

/**
 * 用户登录
 */
export const login = async (data: UserLogin): Promise<ApiResponse<string>> => {
  const response = await api.post('/user/login', data)
  return response.data
}

/**
 * 获取当前用户信息
 */
export const getCurrentUser = async (): Promise<ApiResponse<UserResponse>> => {
  const response = await api.get('/user/')
  return response.data
}

/**
 * 获取用户列表
 */
export const getUserList = async (params?: {
  keyword?: string
  role?: UserRoleEnum
}): Promise<ApiResponse<UserResponse[]>> => {
  const response = await api.get('/user/list', { params })
  return response.data
}

