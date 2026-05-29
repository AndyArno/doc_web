import apiClient from './index'
import type { Version, VersionListResponse, PaginationParams, VersionDiffResponse } from '@/types/api'

/**
 * 获取章节版本历史列表
 */
export function getVersionHistory(
  chapterId: number,
  params?: PaginationParams
): Promise<VersionListResponse> {
  return apiClient.get(`/chapters/${chapterId}/versions`, { params })
}

/**
 * 获取版本详情
 */
export function getVersionDetail(chapterId: number, versionId: number): Promise<Version> {
  return apiClient.get(`/chapters/${chapterId}/versions/${versionId}`)
}

/**
 * 恢复章节到指定版本
 */
export function restoreVersion(chapterId: number, versionId: number): Promise<void> {
  return apiClient.post(`/chapters/${chapterId}/versions/${versionId}/restore`)
}

/**
 * 对比两个版本的内容差异
 */
export function compareVersions(
  chapterId: number,
  fromVersionId: number,
  toVersionId: number
): Promise<VersionDiffResponse> {
  return apiClient.get(`/chapters/${chapterId}/versions/compare`, {
    params: {
      from_version_id: fromVersionId,
      to_version_id: toVersionId,
    },
  })
}

/**
 * 手动保存章节版本
 */
export function saveVersion(chapterId: number): Promise<Version> {
  return apiClient.post(`/chapters/${chapterId}/versions/save`)
}
