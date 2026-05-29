import apiClient from './index'
import type { UploadResponse, MarkdownUploadResponse, UploadStatus, UploadProgressCallback, TaskStatus } from '@/types/api'

/**
 * 上传 Markdown ZIP 文件
 */
export function uploadMarkdown(
  file: File,
  title: string,
  textbookId: number | null = null,
  onProgress?: UploadProgressCallback
): Promise<{ task_id: string }> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('title', title)
  formData.append('auto_publish', 'false')
  if (textbookId) {
    formData.append('textbook_id', String(textbookId))
  }

  return apiClient.post('/upload/markdown', formData, {
    timeout: 300000,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(percent, progressEvent.loaded, progressEvent.total)
      }
    }
  })
}

/**
 * 上传单个图片
 */
export function uploadImage(
  file: File,
  textbookId: number,
  chapterId?: number | null
): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('textbook_id', String(textbookId))
  if (chapterId != null) {
    formData.append('chapter_id', String(chapterId))
  }

  return apiClient.post('/upload/image', formData, {
    timeout: 300000,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 上传单个 Markdown 文件，自动从文件名提取标题并创建章节
 */
export function uploadSingleMarkdown(
  file: File,
  textbookId: number,
  parentId?: number,
): Promise<{ id: number; title: string }> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('textbook_id', String(textbookId))
  if (parentId != null) {
    formData.append('parent_id', String(parentId))
  }

  return apiClient.post('/upload/markdown-single', formData, {
    timeout: 300000,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/**
 * 获取上传处理状态
 */
export function getUploadStatus(taskId: string): Promise<TaskStatus> {
  return apiClient.get(`/upload/status/${taskId}`)
}

/**
 * 轮询上传处理状态直到完成或失败
 */
export function pollUploadStatus(
  taskId: string,
  onUpdate: (status: TaskStatus) => void,
  intervalMs: number = 1000
): Promise<TaskStatus> {
  return new Promise((resolve, reject) => {
    const poll = setInterval(async () => {
      try {
        const status = await getUploadStatus(taskId)
        onUpdate(status)
        if (status.status === 'done') {
          clearInterval(poll)
          resolve(status)
        } else if (status.status === 'failed') {
          clearInterval(poll)
          reject(new Error(status.error || '处理失败'))
        }
      } catch (e) {
        clearInterval(poll)
        reject(e)
      }
    }, intervalMs)
  })
}
