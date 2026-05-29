import apiClient from './index'
import type { Media, MediaListResponse, MediaQueryParams, TrashListResponse, ClearTrashResponse } from '@/types/api'

/**
 * 获取媒体列表
 */
export function getMedia(params: MediaQueryParams = {}): Promise<MediaListResponse> {
  const filteredParams = Object.fromEntries(
    Object.entries(params).filter(([_, v]) => v !== '' && v !== null && v !== undefined)
  )
  return apiClient.get('/media', { params: filteredParams })
}

/**
 * 获取媒体详情
 */
export function getMediaById(id: number): Promise<Media> {
  return apiClient.get(`/media/${id}`)
}

/**
 * 删除媒体（移入回收站）
 */
export function deleteMedia(id: number): Promise<void> {
  return apiClient.delete(`/media/${id}`)
}

/**
 * 获取回收站媒体列表
 */
export function getTrashList(params: { page?: number; page_size?: number } = {}): Promise<TrashListResponse> {
  return apiClient.get('/media/trash', { params })
}

/**
 * 从回收站恢复媒体
 */
export function restoreMedia(id: number): Promise<void> {
  return apiClient.post(`/media/${id}/restore`)
}

/**
 * 彻底删除媒体
 */
export function permanentlyDeleteMedia(id: number): Promise<void> {
  return apiClient.delete(`/media/${id}/permanent`)
}

/**
 * 清空回收站
 */
export function clearTrash(): Promise<ClearTrashResponse> {
  return apiClient.delete('/media/trash/clear')
}
