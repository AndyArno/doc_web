import apiClient from './index'
import type {
  Textbook,
  TextbookListResponse,
  TextbookQueryParams,
  CreateTextbookParams,
  UpdateTextbookParams
} from '@/types/api'

/**
 * 获取教材列表
 */
export function getTextbooks(params: TextbookQueryParams = {}): Promise<TextbookListResponse> {
  const filteredParams = Object.fromEntries(
    Object.entries(params).filter(([_, v]) => v !== '' && v !== null && v !== undefined)
  )
  return apiClient.get('/textbooks', { params: filteredParams })
}

/**
 * 获取教材详情
 */
export function getTextbookById(id: number): Promise<Textbook> {
  return apiClient.get(`/textbooks/${id}`)
}

/**
 * 创建教材
 */
export function createTextbook(data: CreateTextbookParams): Promise<Textbook> {
  return apiClient.post('/textbooks', data)
}

/**
 * 更新教材
 */
export function updateTextbook(id: number, data: UpdateTextbookParams): Promise<Textbook> {
  return apiClient.put(`/textbooks/${id}`, data)
}

/**
 * 删除教材
 */
export function deleteTextbook(id: number): Promise<void> {
  return apiClient.delete(`/textbooks/${id}`)
}

/**
 * 发布教材
 */
export function publishTextbook(id: number): Promise<Textbook> {
  return apiClient.put(`/textbooks/${id}/publish`)
}

/**
 * 取消发布教材
 */
export function unpublishTextbook(id: number): Promise<Textbook> {
  return apiClient.put(`/textbooks/${id}/unpublish`)
}
