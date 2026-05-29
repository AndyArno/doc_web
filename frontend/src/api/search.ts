import apiClient from './index'
import type { SearchResponseData, SearchQueryParams } from '@/types/api'

/**
 * 搜索章节内容
 */
export function searchContent(params: SearchQueryParams): Promise<SearchResponseData> {
  return apiClient.get('/search', { params })
}
