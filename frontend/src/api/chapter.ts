import apiClient from './index'
import type {
  Chapter,
  ChapterTreeResponse,
  CreateChapterParams,
  UpdateChapterParams,
  ChapterReorderItem,
  SortPreviewResponse,
  SortApplyResponse,
  OrderItem
} from '@/types/api'

/**
 * 获取教材的章节树结构
 */
export function getChapters(textbookId: number): Promise<ChapterTreeResponse> {
  return apiClient.get(`/chapters/textbook/${textbookId}`)
}

/**
 * 获取章节详情
 */
export function getChapterById(id: number): Promise<Chapter> {
  return apiClient.get(`/chapters/${id}`)
}

/**
 * 创建章节
 */
export function createChapter(data: CreateChapterParams): Promise<Chapter> {
  return apiClient.post('/chapters', data)
}

/**
 * 更新章节
 */
export function updateChapter(id: number, data: UpdateChapterParams): Promise<Chapter> {
  return apiClient.put(`/chapters/${id}`, data)
}

/**
 * 删除章节
 */
export function deleteChapter(id: number): Promise<void> {
  return apiClient.delete(`/chapters/${id}`)
}

/**
 * 调整章节顺序
 */
export function reorderChapters(textbookId: number, orders: ChapterReorderItem[]): Promise<void> {
  return apiClient.put('/chapters/reorder', { textbook_id: textbookId, orders })
}

/**
 * 预览智能排序结果
 */
export function previewSort(textbookId: number, selectedIds?: number[] | null): Promise<SortPreviewResponse> {
  return apiClient.post('/chapters/sort/preview', {
    textbook_id: textbookId,
    selected_ids: selectedIds
  })
}

/**
 * 应用智能排序
 */
export function applySort(
  textbookId: number,
  selectedIds?: number[] | null,
  orders?: OrderItem[],
  deletedIds?: number[],
  deletedFolderNumbers?: number[]
): Promise<SortApplyResponse> {
  return apiClient.post('/chapters/sort/apply', {
    textbook_id: textbookId,
    selected_ids: selectedIds,
    orders,
    deleted_ids: deletedIds || [],
    deleted_folder_numbers: deletedFolderNumbers || []
  })
}

/**
 * 撤销智能排序
 */
export function undoSort(textbookId: number): Promise<void> {
  return apiClient.post('/chapters/sort/undo', {
    textbook_id: textbookId
  })
}
