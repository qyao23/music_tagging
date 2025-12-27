/**
 * 接口类型定义
 */
import { UserRoleEnum, TaggingStatusEnum, ReviewResultEnum, OperationEnum } from './enums'

/**
 * API 响应基础结构
 */
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
}

/**
 * 用户相关接口
 */
export interface UserCreate {
  username: string
  password: string
  role: UserRoleEnum
}

export interface UserLogin {
  username: string
  password: string
}

export interface UserResponse {
  id: number
  username: string
  role: UserRoleEnum
  create_time: string
}

/**
 * 音乐相关接口
 */
export interface MusicResponse {
  id: number
  filepath: string
  filename: string
  duration: number
  valid_tagging_count: number
  create_time: string
}

/**
 * 打标题目相关接口
 */
export interface TaggingQuestionOperate {
  operation: OperationEnum
  id?: number
  title?: string
  description?: string
  is_multiple_choice?: boolean
  options?: string[]
}

export interface TaggingQuestionResponse {
  id: number
  title: string
  description?: string
  is_multiple_choice: boolean
  options: string[]
  create_time: string
}

/**
 * 打标项相关接口（已废弃，使用TaggingQuestion）
 */
export interface TaggingItemCreate {
  name: string
  description: string
}

export interface TaggingItemResponse {
  id: number
  name: string
  description: string
  create_time: string
}

/**
 * 打标记录相关接口
 */
export interface TaggingRecordOperate {
  operation: OperationEnum
  id?: number
  music_id?: number
  tagger_id?: number
  tagger_ids?: number[]  // 支持多个打标员
  question_ids?: number[]  // 题目ID列表
  reviewer_id?: number
}

export interface TaggingTaskOperate {
  operation: OperationEnum
  id?: number
  music_id?: number
  question_ids?: number[]
  tagger_id?: number
  tagger_ids?: number[]
  reviewer_id?: number
  review_result?: ReviewResultEnum
  review_comment?: string
}

export interface TaggingRecordReview {
  id: number
  result: ReviewResultEnum
  comment?: string
}

export interface TaggingRecordUpdate {
  id: number
  selected_options: string[]
}

export interface TaggingRecordResponse {
  id: number
  question: TaggingQuestionResponse
  selected_options: string[]
}

export interface TaggingTaskResponse {
  id: number
  music: MusicResponse
  status: TaggingStatusEnum
  tagger: UserResponse
  tagging_time?: string
  reviewer?: UserResponse
  review_time?: string
  creator: UserResponse
  create_time: string
  records: TaggingRecordResponse[]
}

