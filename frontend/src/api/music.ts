/**
 * 音乐相关 API
 */
import api from './index'
import type { ApiResponse, MusicResponse } from '../types/interfaces'

/**
 * 通过 JSON 文件上传音乐路径信息
 * JSON 文件格式：字符串数组，每个字符串是音乐文件的路径
 * 例如：["/path/to/music1.mp3", "/path/to/music2.wav"]
 */
export const createMusic = (file: File): Promise<ApiResponse<{
  success_count: number
  error_count: number
  success_ids: number[]
  error_paths: string[]
}>> => {
  const formData = new FormData()
  formData.append('file', file)
  
  // 不设置 Content-Type，让浏览器自动设置（包含 boundary）
  return api.post('/music/', formData)
}

/**
 * 删除音乐
 */
export const deleteMusic = (id: number): Promise<ApiResponse> => {
  return api.delete('/music/', { params: { id } })
}

/**
 * 获取音乐列表
 */
export const getMusicList = (params?: {
  filename?: string
}): Promise<ApiResponse<MusicResponse[]>> => {
  return api.get('/music/', { params })
}

