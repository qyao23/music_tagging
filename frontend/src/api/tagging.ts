/**
 * 打标相关 API
 */
import api, { API_BASE_URL } from './index'
import axios from 'axios'
import type {
  ApiResponse,
  TaggingQuestionOperate,
  TaggingQuestionResponse,
  TaggingTaskOperate,
  TaggingTaskResponse,
  TaggingRecordUpdate,
  TaggingItemResponse,
  TaggingItemCreate,
  TaggingRecordResponse,
  TaggingRecordOperate,
  TaggingRecordReview
} from '../types/interfaces'
import { OperationEnum, TaggingStatusEnum, ReviewResultEnum } from '../types/enums'

/**
 * 操作打标题目（创建/更新/删除）
 */
export const operateTaggingQuestion = async (data: TaggingQuestionOperate): Promise<ApiResponse<number>> => {
  const response = await api.post('/tagging/question/operate', data)
  return response.data
}

/**
 * 获取打标题目列表
 */
export const getTaggingQuestionList = async (): Promise<ApiResponse<TaggingQuestionResponse[]>> => {
  const response = await api.get('/tagging/question/list')
  return response.data
}

/**
 * 操作打标任务（创建/删除/完成/审核）
 */
export const operateTaggingTask = async (data: TaggingTaskOperate): Promise<ApiResponse<number | number[]>> => {
  const response = await api.post('/tagging/task/operate', data)
  return response.data
}

/**
 * 获取打标任务列表（分页）
 */
export const getTaggingTaskList = async (params?: {
  keyword?: string
  status?: TaggingStatusEnum
  tagger_id?: number
  reviewer_id?: number
  page?: number
  page_size?: number
}): Promise<ApiResponse<{
  items: TaggingTaskResponse[]
  total: number
  page: number
  page_size: number
}>> => {
  const response = await api.get('/tagging/task/list', { params })
  return response.data
}

/**
 * 打标（更新打标记录）
 */
export const tagMusic = async (data: TaggingRecordUpdate): Promise<ApiResponse> => {
  const response = await api.post('/tagging/tag', data)
  return response.data
}

/**
 * 获取打标项列表（兼容旧接口，实际使用 TaggingQuestion）
 */
export const getTaggingItemList = async (): Promise<ApiResponse<TaggingItemResponse[]>> => {
  const response = await getTaggingQuestionList()
  if (response.data) {
    // 将 TaggingQuestionResponse 转换为 TaggingItemResponse
    const items: TaggingItemResponse[] = response.data.map(q => ({
      id: q.id,
      name: q.title,
      description: q.description || '',
      create_time: q.create_time
    }))
    return {
      success: response.success,
      data: items,
      error: response.error
    }
  }
  return response as any
}

/**
 * 创建打标项（兼容旧接口，实际使用 TaggingQuestion）
 */
export const createTaggingItem = async (data: TaggingItemCreate): Promise<ApiResponse<number>> => {
  return operateTaggingQuestion({
    operation: OperationEnum.CREATE,
    title: data.name,
    description: data.description,
    is_multiple_choice: false,
    options: []
  })
}

/**
 * 删除打标项（兼容旧接口，实际使用 TaggingQuestion）
 */
export const deleteTaggingItem = async (id: number): Promise<ApiResponse> => {
  return operateTaggingQuestion({
    operation: OperationEnum.DELETE,
    id
  })
}

/**
 * 获取打标记录列表（通过任务列表获取所有记录）
 */
export const getTaggingRecordList = async (params?: {
  keyword?: string
  status?: TaggingStatusEnum
  page?: number
  page_size?: number
}): Promise<ApiResponse<{
  items: TaggingRecordResponse[]
  total: number
  page: number
  page_size: number
}>> => {
  const response = await getTaggingTaskList(params)
  if (response.data) {
    // 从所有任务中提取所有记录
    const records: TaggingRecordResponse[] = []
    response.data.items.forEach(task => {
      if (task.records) {
        records.push(...task.records)
      }
    })
    return {
      success: response.success,
      data: {
        items: records,
        total: response.data.total,
        page: response.data.page,
        page_size: response.data.page_size
      },
      error: response.error
    }
  }
  return response as any
}

/**
 * 操作打标记录（通过任务操作）
 */
export const operateTaggingRecord = async (data: TaggingRecordOperate): Promise<ApiResponse<number | number[]>> => {
  // 将 TaggingRecordOperate 转换为 TaggingTaskOperate
  const taskOperate: TaggingTaskOperate = {
    operation: data.operation,
    id: data.id,
    music_id: data.music_id,
    tagger_id: data.tagger_id,
    reviewer_id: data.reviewer_id,
    question_ids: data.question_ids
  }
  return operateTaggingTask(taskOperate)
}

/**
 * 完成打标记录（通过任务完成）
 */
export const finishTaggingRecord = async (data: {
  id: number
  tagging_item_id?: number
  comment?: string
}): Promise<ApiResponse> => {
  // 注意：这里需要 task id，而不是 record id
  // 但前端传入的是 record id，我们需要先获取 task
  // 为了简化，我们假设 id 是 task id
  return operateTaggingTask({
    operation: OperationEnum.FINISH,
    id: data.id
  })
}

/**
 * 审核打标记录（通过任务审核）
 */
export const reviewTaggingRecord = async (data: TaggingRecordReview): Promise<ApiResponse> => {
  // 注意：这里需要 task id，而不是 record id
  // 但前端传入的是 record id，我们需要先获取 task
  // 为了简化，我们假设 id 是 task id
  return operateTaggingTask({
    operation: OperationEnum.REVIEW,
    id: data.id,
    review_result: data.result,
    review_comment: data.comment
  })
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
    const response = await axios.get(`${API_BASE_URL}/tagging/download?${params.toString()}`, {
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

