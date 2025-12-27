/**
 * 打标相关 API
 */
import api from './index'
import axios from 'axios'
import type {
  ApiResponse,
  TaggingQuestionOperate,
  TaggingQuestionResponse,
  TaggingTaskOperate,
  TaggingTaskResponse,
  TaggingRecordUpdate
} from '../types/interfaces'
import { OperationEnum, TaggingStatusEnum } from '../types/enums'

/**
 * 操作打标题目（创建/更新/删除）
 */
export const operateTaggingQuestion = (data: TaggingQuestionOperate): Promise<ApiResponse<number>> => {
  return api.post('/tagging/question/operate', data)
}

/**
 * 获取打标题目列表
 */
export const getTaggingQuestionList = (): Promise<ApiResponse<TaggingQuestionResponse[]>> => {
  return api.get('/tagging/question/list')
}

/**
 * 操作打标任务（创建/删除/完成/审核）
 */
export const operateTaggingTask = (data: TaggingTaskOperate): Promise<ApiResponse<number | number[]>> => {
  return api.post('/tagging/task/operate', data)
}

/**
 * 获取打标任务列表
 */
export const getTaggingTaskList = (params?: {
  keyword?: string
  status?: TaggingStatusEnum
  tagger_id?: number
  reviewer_id?: number
}): Promise<ApiResponse<TaggingTaskResponse[]>> => {
  return api.get('/tagging/task/list', { params })
}

/**
 * 打标（更新打标记录）
 */
export const tagMusic = (data: TaggingRecordUpdate): Promise<ApiResponse> => {
  return api.post('/tagging/tag', data)
}

/**
 * 下载打标记录（JSON文件）
 */
export const downloadTaggingRecords = async (musicIds: number[]): Promise<Blob> => {
  const token = localStorage.getItem('token')
  // FastAPI 期望多个同名查询参数 music_ids=1&music_ids=2
  // 使用 URLSearchParams 构建查询字符串
  const params = new URLSearchParams()
  musicIds.forEach(id => {
    params.append('music_ids', id.toString())
  })
  
  try {
    const response = await axios.get(`http://127.0.0.1:8000/tagging/download?${params.toString()}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      },
      responseType: 'blob',
      validateStatus: (status) => status === 200 // 只有 200 才算成功
    })
    
    return response.data
  } catch (error: any) {
    // 如果是错误响应，尝试解析错误信息
    if (error.response && error.response.data instanceof Blob) {
      try {
        const text = await error.response.data.text()
        const errorData = JSON.parse(text)
        const errorMessage = errorData.detail || errorData.error || `下载失败: HTTP ${error.response.status}`
        throw new Error(errorMessage)
      } catch (parseError) {
        throw new Error(`下载失败: HTTP ${error.response.status}`)
      }
    }
    throw error
  }
}

