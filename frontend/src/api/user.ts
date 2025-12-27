/**
 * 用户相关 API
 */
import api from './index'
import type { ApiResponse, UserCreate, UserLogin, UserResponse } from '../types/interfaces'
import { UserRoleEnum } from '../types/enums'

/**
 * 用户注册
 */
export const register = (data: UserCreate): Promise<ApiResponse<number>> => {
  return api.post('/user/register', data)
}

/**
 * 用户登录
 */
export const login = (data: UserLogin): Promise<ApiResponse<string>> => {
  return api.post('/user/login', data)
}

/**
 * 获取当前用户信息
 */
export const getCurrentUser = (): Promise<ApiResponse<UserResponse>> => {
  return api.get('/user/')
}

/**
 * 获取用户列表
 */
export const getUserList = (params?: {
  keyword?: string
  role?: UserRoleEnum
}): Promise<ApiResponse<UserResponse[]>> => {
  return api.get('/user/list', { params })
}

