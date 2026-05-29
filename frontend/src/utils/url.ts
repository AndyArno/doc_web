/**
 * URL 工具函数
 *
 * 提供媒体 URL 转换功能，处理相对路径、外部 URL 和 Base64 URI
 */

/**
 * 将相对路径转换为完整媒体 URL
 *
 * @param filePath - 文件路径（相对路径或完整 URL）
 * @returns 完整的媒体 URL
 *
 * @example
 * getMediaUrl('/uploads/images/test.jpg') // 'http://localhost:8000/uploads/images/test.jpg'
 * getMediaUrl('https://example.com/image.png') // 'https://example.com/image.png'
 * getMediaUrl('data:image/png;base64,...') // 'data:image/png;base64,...'
 */
export function getMediaUrl(filePath: string): string {
  // 外部 URL（http://, https://）
  if (filePath.startsWith('http://') || filePath.startsWith('https://')) {
    return filePath
  }

  // Base64 URI
  if (filePath.startsWith('data:')) {
    return filePath
  }

  // 相对路径：转换为完整 URL
  const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
  const staticUrl = baseUrl.replace(/\/api\/v1$/, '')
  const normalizedPath = filePath.startsWith('/') ? filePath : `/${filePath}`
  return `${staticUrl}${normalizedPath}`
}
