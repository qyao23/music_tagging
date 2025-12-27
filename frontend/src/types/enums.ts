/**
 * 枚举类型定义
 */

/**
 * 用户角色枚举
 */
export enum UserRoleEnum {
  TAGGER = 'tagger',    // 打标员
  REVIEWER = 'reviewer', // 审核员
  ADMIN = 'admin'        // 管理员
}

/**
 * 打标状态枚举
 */
export enum TaggingStatusEnum {
  PENDING = 'pending',   // 待打标
  TAGGED = 'tagged',     // 已打标
  REVIEWED = 'reviewed', // 已审核通过
  REJECTED = 'rejected' // 审核未通过
}

/**
 * 审核结果枚举
 */
export enum ReviewResultEnum {
  AGREED = 'agreed',     // 同意
  DISAGREED = 'disagreed' // 不同意
}

/**
 * 操作类型枚举
 */
export enum OperationEnum {
  CREATE = 'create',    // 创建
  DELETE = 'delete',    // 删除
  UPDATE = 'update',    // 更新
  FINISH = 'finish',    // 完成
  REVIEW = 'review'     // 审核
}

