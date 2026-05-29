<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900">媒体库</h1>
      <p class="text-sm text-gray-500 mt-1">管理已上传的图片和文件</p>
    </div>

    <!-- 标签页切换 -->
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <div class="flex border-b border-gray-100">
        <button
          @click="activeTab = 'media'"
          class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
          :class="activeTab === 'media' ? 'border-brand-600 text-brand-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
        >
          媒体列表
        </button>
        <button
          @click="activeTab = 'trash'"
          class="px-6 py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2"
          :class="activeTab === 'trash' ? 'border-brand-600 text-brand-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
        >
          回收站
          <span 
            v-if="trashTotal > 0"
            class="px-1.5 py-0.5 text-xs font-bold bg-red-50 text-red-600 rounded-full"
          >
            {{ trashTotal }}
          </span>
        </button>
      </div>

      <!-- 媒体列表标签页 -->
      <div v-show="activeTab === 'media'">
        <!-- 筛选栏 -->
        <div class="p-4 border-b border-gray-100 flex flex-col md:flex-row gap-4">
          <div class="flex-1">
            <select
              v-model="queryParams.textbook_id"
              class="w-full md:w-auto px-4 py-2 bg-gray-50 border border-gray-100 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 appearance-none cursor-pointer"
              @change="handleSearch"
            >
              <option value="">全部教材</option>
              <option v-for="textbook in textbooks" :key="textbook.id" :value="textbook.id">
                {{ textbook.title }}
              </option>
            </select>
          </div>
          <div class="flex gap-2">
            <select
              v-model="queryParams.file_type"
              class="px-4 py-2 bg-gray-50 border border-gray-100 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 appearance-none cursor-pointer"
              @change="handleSearch"
            >
              <option value="">全部类型</option>
              <option value="image">图片</option>
              <option value="document">文档</option>
              <option value="other">其他</option>
            </select>
            <div class="group relative inline-flex">
              <button
                @click="triggerImageUpload"
                :disabled="uploadLoading || !queryParams.textbook_id"
                class="flex items-center gap-2 px-4 py-2 bg-brand-600 text-white rounded-xl text-sm font-bold hover:bg-brand-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <UploadCloud class="w-4 h-4" />
                上传图片
              </button>
              <div
                v-if="!queryParams.textbook_id && !uploadLoading"
                class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-gray-900 text-white text-xs rounded-lg whitespace-nowrap pointer-events-none z-10 opacity-0 group-hover:opacity-100"
              >
                请先选择教材
                <div class="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-gray-900" />
              </div>
            </div>
            <input
              ref="imageFileInput"
              type="file"
              accept="image/*"
              class="hidden"
              @change="handleImageSelected"
            />
            <button
              @click="isMultiSelectMode = !isMultiSelectMode; selectedIds.clear()"
              :class="isMultiSelectMode 
                ? 'px-4 py-2 bg-brand-600 text-white rounded-xl text-sm font-bold' 
                : 'px-4 py-2 bg-gray-100 text-gray-700 rounded-xl text-sm font-bold hover:bg-gray-200'"
            >
              {{ isMultiSelectMode ? '取消多选' : '多选模式' }}
            </button>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="py-20 flex flex-col items-center justify-center">
          <LoadingSpinner size="lg" />
          <p class="text-gray-400 text-sm mt-4 animate-pulse">正在加载媒体数据...</p>
        </div>

        <!-- 媒体列表内容 -->
        <template v-else>
          <!-- 桌面端表格 (md 以上显示) -->
          <div class="hidden md:block">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-gray-50/50 border-b border-gray-100">
                  <th class="px-6 py-4 w-12">
                    <input 
                      v-if="isMultiSelectMode"
                      type="checkbox" 
                      :checked="selectedIds.size === mediaList.length && mediaList.length > 0"
                      @change="toggleSelectAll"
                      class="w-4 h-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500 cursor-pointer"
                    />
                  </th>
                  <th class="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">预览</th>
                  <th class="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">文件信息</th>
                  <th class="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">关联教材</th>
                  <th class="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">类型</th>
                  <th class="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">大小</th>
                  <th class="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider text-right">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-50">
                <tr v-for="media in mediaList" :key="media.id" class="hover:bg-gray-50/50 transition-colors group">
                  <td class="px-6 py-4 w-12">
                    <input 
                      v-if="isMultiSelectMode"
                      type="checkbox" 
                      :checked="selectedIds.has(media.id)"
                      @change="toggleSelect(media.id)"
                      class="w-4 h-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500 cursor-pointer"
                    />
                  </td>
                  <td class="px-6 py-4">
                    <div class="w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center overflow-hidden border border-gray-100">
                      <img
                        v-if="isImage(media.file_type)"
                        :src="media.url"
                        class="w-full h-full object-cover"
                        :alt="media.original_name"
                      />
                      <File v-else class="w-6 h-6 text-gray-400" />
                    </div>
                  </td>
                  <td class="px-6 py-4">
                    <div class="text-sm font-medium text-gray-900 truncate max-w-[200px]" :title="media.original_name">
                      {{ media.original_name }}
                    </div>
                    <div class="text-xs text-gray-400 mt-0.5">
                      {{ formatDate(media.created_at) }}
                    </div>
                  </td>
                  <td class="px-6 py-4">
                    <span class="text-sm text-gray-600">
                      {{ media.textbook_title ?? '' }}
                    </span>
                  </td>
                  <td class="px-6 py-4">
                    <span
                      class="px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider border"
                      :class="getFileTypeBadgeClass(media.file_type)"
                    >
                      {{ getFileTypeName(media.file_type) }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-500">
                    {{ formatFileSize(media.file_size) }}
                  </td>
                  <td class="px-6 py-4 text-right">
                    <div class="flex items-center justify-end gap-2">
                      <button
                        @click="previewMedia(media)"
                        class="p-2 text-gray-400 hover:text-brand-600 hover:bg-brand-50 rounded-lg transition-all"
                        title="预览"
                      >
                        <Eye class="w-4 h-4" />
                      </button>
                      <button
                        @click="handleDelete(media)"
                        class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                        title="删除"
                      >
                        <Trash2 class="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 移动端卡片 -->
          <div class="md:hidden space-y-4">
            <div
              v-for="media in mediaList"
              :key="media.id"
              class="bg-white rounded-xl border border-gray-100 p-4 hover:border-brand-200 transition-colors cursor-pointer"
              @click="previewMedia(media)"
            >
              <div class="flex items-start gap-3">
                <div class="w-14 h-14 rounded-lg bg-gray-100 flex items-center justify-center overflow-hidden border border-gray-100 flex-shrink-0">
                  <img
                    v-if="isImage(media.file_type)"
                    :src="media.url"
                    class="w-full h-full object-cover"
                    :alt="media.original_name"
                  />
                  <File v-else class="w-6 h-6 text-gray-400" />
                </div>
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-medium text-gray-900 truncate" :title="media.original_name">
                    {{ media.original_name }}
                  </div>
                  <div class="flex items-center gap-2 mt-1">
                    <span
                      class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border"
                      :class="getFileTypeBadgeClass(media.file_type)"
                    >
                      {{ getFileTypeName(media.file_type) }}
                    </span>
                    <span class="text-xs text-gray-400">{{ formatFileSize(media.file_size) }}</span>
                  </div>
                  <div class="text-xs text-gray-400 mt-1">
                    {{ media.textbook_title ?? '' }} · {{ formatDate(media.created_at) }}
                  </div>
                </div>
              </div>
              <div class="flex justify-end gap-2 mt-3 pt-3 border-t border-gray-50">
                <button
                  @click="previewMedia(media)"
                  class="px-3 py-1.5 text-brand-600 bg-brand-50 rounded-lg text-sm font-bold transition-all"
                >
                  预览
                </button>
                <button
                  @click="handleDelete(media)"
                  class="px-3 py-1.5 text-red-600 bg-red-50 rounded-lg text-sm font-bold transition-all"
                >
                  删除
                </button>
              </div>
            </div>
          </div>

          <!-- 多选操作栏 -->
          <div 
            v-if="isMultiSelectMode && selectedIds.size > 0" 
            class="fixed bottom-4 left-1/2 -translate-x-1/2 bg-white rounded-xl shadow-lg border border-gray-100 px-6 py-3 flex items-center gap-4 z-50"
          >
            <span class="text-sm text-gray-600">已选择 {{ selectedIds.size }} 项</span>
            <button 
              @click="selectedIds.clear()" 
              class="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-all"
            >
              取消选择
            </button>
            <button 
              @click="handleBatchDelete" 
              class="px-3 py-1.5 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all"
            >
              批量删除
            </button>
          </div>

          <!-- 无数据 -->
          <div v-if="mediaList.length === 0" class="py-20 text-center">
            <div class="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <Image class="w-8 h-8 text-gray-300" />
            </div>
            <p class="text-gray-400 font-medium">没有找到媒体文件</p>
          </div>

          <!-- 分页 -->
          <div v-if="total > queryParams.page_size" class="p-4 border-t border-gray-100 flex items-center justify-center gap-4">
            <!-- 每页数量选择器 -->
            <select
              :value="pageSize"
              @change="handlePageSizeChange($event)"
              class="px-3 py-1.5 bg-gray-50 border border-gray-100 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 appearance-none cursor-pointer"
            >
              <option v-for="size in pageSizeOptions" :key="size" :value="size">
                每页 {{ size }} 条
              </option>
            </select>
            <button
              :disabled="queryParams.page === 1"
              @click="changePage(queryParams.page - 1)"
              class="p-2 rounded-xl border border-gray-200 disabled:opacity-30 hover:bg-gray-50 transition-all"
            >
              <ChevronLeft class="w-5 h-5" />
            </button>
            <span class="text-sm font-bold text-gray-600">{{ queryParams.page }} / {{ totalPages }}</span>
            <button
              :disabled="queryParams.page >= totalPages"
              @click="changePage(queryParams.page + 1)"
              class="p-2 rounded-xl border border-gray-200 disabled:opacity-30 hover:bg-gray-50 transition-all"
            >
              <ChevronRight class="w-5 h-5" />
            </button>
          </div>
        </template>
      </div>

      <!-- 回收站标签页 -->
      <div v-show="activeTab === 'trash'">
        <!-- 加载状态 -->
        <div v-if="trashLoading" class="py-20 flex flex-col items-center justify-center">
          <LoadingSpinner size="lg" />
          <p class="text-gray-400 text-sm mt-4 animate-pulse">正在加载回收站数据...</p>
        </div>

        <!-- 回收站内容 -->
        <template v-else>
          <!-- 回收站操作栏 -->
          <div v-if="trashList.length > 0" class="p-4 border-b border-gray-100 flex items-center justify-between">
            <div class="text-sm text-gray-500">
              共 {{ trashTotal }} 项 · {{ formatFileSize(trashTotalSize * 1024 * 1024) }}
            </div>
            <div class="flex items-center gap-2">
              <button
                @click="isMultiSelectMode = !isMultiSelectMode; selectedIds.clear()"
                :class="isMultiSelectMode 
                  ? 'px-4 py-2 bg-brand-600 text-white rounded-xl text-sm font-bold' 
                  : 'px-4 py-2 bg-gray-100 text-gray-700 rounded-xl text-sm font-bold hover:bg-gray-200'"
              >
                {{ isMultiSelectMode ? '取消多选' : '多选模式' }}
              </button>
              <button
                @click="handleClearTrash"
                class="flex items-center gap-2 px-4 py-2 text-sm font-bold text-red-600 bg-red-50 rounded-xl hover:bg-red-100 transition-all"
              >
                <Trash class="w-4 h-4" />
                清空回收站
              </button>
            </div>
          </div>

          <!-- 桌面端表格 (md 以上显示) -->
          <div class="hidden md:block">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-gray-50/50 border-b border-gray-100">
                  <th class="px-6 py-4 w-12">
                    <input 
                      v-if="isMultiSelectMode"
                      type="checkbox" 
                      :checked="selectedIds.size === trashList.length && trashList.length > 0"
                      @change="toggleSelectAllTrash"
                      class="w-4 h-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500 cursor-pointer"
                    />
                  </th>
                  <th class="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">预览</th>
                  <th class="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">文件信息</th>
                  <th class="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">删除时间</th>
                  <th class="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider text-right">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-50">
                <tr v-for="media in trashList" :key="media.id" class="hover:bg-gray-50/50 transition-colors group">
                  <td class="px-6 py-4 w-12">
                    <input 
                      v-if="isMultiSelectMode"
                      type="checkbox" 
                      :checked="selectedIds.has(media.id)"
                      @change="toggleSelect(media.id)"
                      class="w-4 h-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500 cursor-pointer"
                    />
                  </td>
                  <td class="px-6 py-4">
                    <div class="w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center overflow-hidden border border-gray-100">
                      <img
                        v-if="isImage(media.file_type)"
                        :src="media.url"
                        class="w-full h-full object-cover opacity-50"
                        :alt="media.original_name"
                      />
                      <File v-else class="w-6 h-6 text-gray-400" />
                    </div>
                  </td>
                  <td class="px-6 py-4">
                    <div class="text-sm font-medium text-gray-900 truncate max-w-[200px]" :title="media.original_name">
                      {{ media.original_name }}
                    </div>
                    <div class="text-xs text-gray-400 mt-0.5">
                      {{ formatFileSize(media.file_size) }}
                    </div>
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-500">
                    {{ media.deleted_at ? formatDate(media.deleted_at) : '-' }}
                  </td>
                  <td class="px-6 py-4 text-right">
                    <div class="flex items-center justify-end gap-2">
                      <button
                        @click="handleRestore(media)"
                        class="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-all"
                        title="恢复"
                      >
                        <RotateCcw class="w-4 h-4" />
                      </button>
                      <button
                        @click="handlePermanentDelete(media)"
                        class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                        title="永久删除"
                      >
                        <Trash2 class="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 移动端卡片列表 (md 以下显示) -->
          <div class="md:hidden divide-y divide-gray-50">
            <div
              v-for="media in trashList"
              :key="media.id"
              class="p-4 hover:bg-gray-50/50 transition-colors"
            >
              <div class="flex items-start gap-3">
                <input 
                  v-if="isMultiSelectMode"
                  type="checkbox" 
                  :checked="selectedIds.has(media.id)"
                  @change="toggleSelect(media.id)"
                  class="w-4 h-4 mt-1 rounded border-gray-300 text-brand-600 focus:ring-brand-500 cursor-pointer flex-shrink-0"
                />
                <div class="w-14 h-14 rounded-lg bg-gray-100 flex items-center justify-center overflow-hidden border border-gray-100 flex-shrink-0">
                  <img
                    v-if="isImage(media.file_type)"
                    :src="media.url"
                    class="w-full h-full object-cover opacity-50"
                    :alt="media.original_name"
                  />
                  <File v-else class="w-6 h-6 text-gray-400" />
                </div>
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-medium text-gray-900 truncate" :title="media.original_name">
                    {{ media.original_name }}
                  </div>
                  <div class="text-xs text-gray-400 mt-1">
                    {{ formatFileSize(media.file_size) }} · {{ media.deleted_at ? formatDate(media.deleted_at) : '-' }}
                  </div>
                </div>
              </div>
              <div class="flex justify-end gap-2 mt-3 pt-3 border-t border-gray-50">
                <button
                  @click="handleRestore(media)"
                  class="px-3 py-1.5 text-green-600 bg-green-50 rounded-lg text-sm font-bold transition-all"
                >
                  恢复
                </button>
                <button
                  @click="handlePermanentDelete(media)"
                  class="px-3 py-1.5 text-red-600 bg-red-50 rounded-lg text-sm font-bold transition-all"
                >
                  永久删除
                </button>
              </div>
            </div>
          </div>

          <!-- 无数据 -->
          <div v-if="trashList.length === 0" class="py-20 text-center">
            <div class="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <Trash class="w-8 h-8 text-gray-300" />
            </div>
            <p class="text-gray-400 font-medium">回收站是空的</p>
          </div>

          <!-- 分页 -->
          <div v-if="trashTotal > trashQueryParams.page_size" class="p-4 border-t border-gray-100 flex items-center justify-center gap-4">
            <!-- 每页数量选择器 -->
            <select
              :value="pageSize"
              @change="handleTrashPageSizeChange($event)"
              class="px-3 py-1.5 bg-gray-50 border border-gray-100 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 appearance-none cursor-pointer"
            >
              <option v-for="size in pageSizeOptions" :key="size" :value="size">
                每页 {{ size }} 条
              </option>
            </select>
            <button
              :disabled="trashQueryParams.page === 1"
              @click="changeTrashPage(trashQueryParams.page - 1)"
              class="p-2 rounded-xl border border-gray-200 disabled:opacity-30 hover:bg-gray-50 transition-all"
            >
              <ChevronLeft class="w-5 h-5" />
            </button>
            <span class="text-sm font-bold text-gray-600">{{ trashQueryParams.page }} / {{ trashTotalPages }}</span>
            <button
              :disabled="trashQueryParams.page >= trashTotalPages"
              @click="changeTrashPage(trashQueryParams.page + 1)"
              class="p-2 rounded-xl border border-gray-200 disabled:opacity-30 hover:bg-gray-50 transition-all"
            >
              <ChevronRight class="w-5 h-5" />
            </button>
          </div>

          <!-- 多选操作栏 -->
          <div 
            v-if="isMultiSelectMode && selectedIds.size > 0" 
            class="fixed bottom-4 left-1/2 -translate-x-1/2 bg-white rounded-xl shadow-lg border border-gray-100 px-6 py-3 flex items-center gap-4 z-50"
          >
            <span class="text-sm text-gray-600">已选择 {{ selectedIds.size }} 项</span>
            <button 
              @click="selectedIds.clear()" 
              class="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-all"
            >
              取消选择
            </button>
            <button 
              v-if="activeTab === 'trash'"
              @click="handleBatchRestore" 
              class="px-3 py-1.5 text-sm bg-brand-600 text-white rounded-lg hover:bg-brand-500 transition-all"
            >
              批量恢复
            </button>
            <button 
              @click="handleBatchDelete" 
              class="px-3 py-1.5 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all"
            >
              {{ activeTab === 'trash' ? '批量永久删除' : '批量删除' }}
            </button>
          </div>
        </template>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <ConfirmDialog
      v-model:visible="deleteConfirmVisible"
      title="删除媒体"
      :message="deleteTarget ? `确定要删除「${deleteTarget.original_name}」吗？文件将移入回收站。` : ''"
      type="warning"
      confirm-text="确认删除"
      @confirm="confirmDelete"
    />

    <!-- 永久删除确认对话框 -->
    <ConfirmDialog
      v-model:visible="permanentDeleteConfirmVisible"
      title="永久删除"
      :message="permanentDeleteTarget ? `确定要永久删除「${permanentDeleteTarget.original_name}」吗？此操作不可撤销。` : ''"
      type="danger"
      confirm-text="永久删除"
      @confirm="confirmPermanentDelete"
    />

    <!-- 清空回收站确认对话框 -->
    <ConfirmDialog
      v-model:visible="clearTrashConfirmVisible"
      title="清空回收站"
      :message="`确定要清空回收站吗？将永久删除 ${trashTotal} 个文件，此操作不可撤销。`"
      type="danger"
      confirm-text="清空回收站"
      @confirm="confirmClearTrash"
    />

    <!-- 同名文件警告对话框 -->
    <ConfirmDialog
      v-model:visible="sameNameWarningVisible"
      title="同名文件警告"
      :message="lastUploadedMedia ? `已存在同名文件「${lastUploadedMedia.original_name}」，新文件已上传。是否删除新上传的文件？` : ''"
      type="warning"
      confirm-text="删除新文件"
      cancel-text="保留"
      @confirm="handleDeleteUploadedFile"
      @cancel="sameNameWarningVisible = false"
    />

    <!-- 图片预览弹窗 -->
    <Modal v-model:visible="previewModalVisible" title="预览" width="800px">
      <div v-if="previewTarget" class="space-y-4">
        <div class="bg-gray-50 rounded-xl overflow-hidden flex items-center justify-center min-h-[300px]">
          <img
            v-if="isImage(previewTarget.file_type)"
            :src="previewTarget.url"
            class="max-w-full max-h-[500px] object-contain"
            :alt="previewTarget.original_name"
          />
          <div v-else class="py-12 text-center">
            <File class="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p class="text-gray-400">无法预览此文件类型</p>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span class="text-gray-400">文件名：</span>
            <span class="text-gray-900">{{ previewTarget.original_name }}</span>
          </div>
          <div>
            <span class="text-gray-400">大小：</span>
            <span class="text-gray-900">{{ formatFileSize(previewTarget.file_size) }}</span>
          </div>
          <div>
            <span class="text-gray-400">类型：</span>
            <span class="text-gray-900">{{ previewTarget.file_type }}</span>
          </div>
          <div>
            <span class="text-gray-400">上传时间：</span>
            <span class="text-gray-900">{{ formatDate(previewTarget.created_at) }}</span>
          </div>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup lang="ts">
/**
 * @file MediaLibrary.vue
 * @description 媒体库管理页面，实现媒体列表展示、筛选、删除、回收站等功能
 */
import { ref, reactive, computed, onMounted, watch } from 'vue'
import {
  Image,
  File,
  Eye,
  Trash2,
  Trash,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  UploadCloud
} from 'lucide-vue-next'
import {
  getMedia,
  deleteMedia,
  getTrashList,
  restoreMedia,
  permanentlyDeleteMedia,
  clearTrash
} from '@/api/media'
import { getTextbooks } from '@/api/textbook'
import { uploadImage } from '@/api/upload'
import type { Media } from '@/types/api'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Modal from '@/components/Modal.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { useToast } from '@/composables/useToast'
import { usePageSize } from '@/composables/usePageSize'
import type { PageSizeOption } from '@/composables/usePageSize'

const toast = useToast()

// ==================== 每页数量管理 ====================

/** 每页数量选择器 */
const { pageSize, setPageSize, pageSizeOptions } = usePageSize()

// ==================== 状态定义 ====================

/** 当前激活的标签页 */
const activeTab = ref<'media' | 'trash'>('media')

/** 教材列表 */
const textbooks = ref<{ id: number; title: string }[]>([])

/** 媒体列表相关 */
const loading = ref(true)
const mediaList = ref<Media[]>([])
const total = ref(0)

const queryParams = reactive({
  page: 1,
  page_size: pageSize.value,
  textbook_id: '' as string | number,
  file_type: ''
})

/** 回收站相关 */
const trashLoading = ref(false)
const trashList = ref<Media[]>([])
const trashTotal = ref(0)
const trashTotalSize = ref(0)

/** 回收站查询参数 */
const trashQueryParams = reactive({
  page: 1,
  page_size: pageSize.value  // 使用共享的 pageSize
})

/** 删除确认相关 */
const deleteConfirmVisible = ref(false)
const deleteTarget = ref<Media | null>(null)

/** 永久删除确认相关 */
const permanentDeleteConfirmVisible = ref(false)
const permanentDeleteTarget = ref<Media | null>(null)

/** 清空回收站确认相关 */
const clearTrashConfirmVisible = ref(false)

/** 预览相关 */
const previewModalVisible = ref(false)
const previewTarget = ref<Media | null>(null)

/** 上传相关 */
const imageFileInput = ref<HTMLInputElement | null>(null)
const uploadLoading = ref(false)
const lastUploadedMedia = ref<Media | null>(null)

/** 同名文件警告对话框 */
const sameNameWarningVisible = ref(false)

/** 多选模式相关 */
const isMultiSelectMode = ref(false)
const selectedIds = ref<Set<number>>(new Set())

// ==================== 计算属性 ====================

const totalPages = computed(() => Math.ceil(total.value / queryParams.page_size))

const trashTotalPages = computed(() => Math.ceil(trashTotal.value / trashQueryParams.page_size))

// ==================== 数据加载 ====================

/**
 * 加载教材列表
 */
const loadTextbooks = async () => {
  try {
    const data = await getTextbooks({ page_size: 100 })
    textbooks.value = data.items
  } catch (error) {
    // API 拦截器已处理错误
  }
}

/**
 * 加载媒体列表
 */
const loadMediaList = async () => {
  loading.value = true
  try {
    const params = {
      ...queryParams,
      textbook_id: queryParams.textbook_id ? Number(queryParams.textbook_id) : undefined
    }
    const data = await getMedia(params)
    mediaList.value = data.items
    total.value = data.total
  } catch (error) {
    // API 拦截器已处理错误
  } finally {
    loading.value = false
  }
}

/**
 * 加载回收站列表
 */
const loadTrashList = async () => {
  trashLoading.value = true
  try {
    const data = await getTrashList({ 
      page: trashQueryParams.page, 
      page_size: trashQueryParams.page_size 
    })
    trashList.value = data.items
    trashTotal.value = data.total
    trashTotalSize.value = data.total_size_mb
  } catch (error) {
    // API 拦截器已处理错误
  } finally {
    trashLoading.value = false
  }
}

// ==================== 事件处理 ====================

/**
 * 搜索处理
 */
const handleSearch = () => {
  queryParams.page = 1
  loadMediaList()
}

/**
 * 分页处理
 */
const changePage = (newPage: number) => {
  queryParams.page = newPage
  loadMediaList()
}

/**
 * 每页数量变更处理
 */
const handlePageSizeChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  const newSize = parseInt(target.value, 10) as PageSizeOption
  setPageSize(newSize)
  queryParams.page_size = newSize
  queryParams.page = 1  // 重置页码
  loadMediaList()
}

/**
 * 回收站分页处理
 */
const changeTrashPage = (newPage: number) => {
  trashQueryParams.page = newPage
  loadTrashList()
}

/**
 * 回收站每页数量变更处理
 */
const handleTrashPageSizeChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  const newSize = parseInt(target.value, 10) as PageSizeOption
  setPageSize(newSize)
  trashQueryParams.page_size = newSize
  trashQueryParams.page = 1  // 重置页码
  loadTrashList()
}

/**
 * 预览媒体
 */
const previewMedia = (media: Media) => {
  previewTarget.value = media
  previewModalVisible.value = true
}

/**
 * 删除媒体
 */
const handleDelete = (media: Media) => {
  deleteTarget.value = media
  deleteConfirmVisible.value = true
}

const confirmDelete = async () => {
  if (!deleteTarget.value) return
  try {
    await deleteMedia(deleteTarget.value.id)
    toast.success('文件已移入回收站')
    loadMediaList()
    // 刷新回收站数量
    loadTrashList()
  } catch (error) {
    // API 拦截器已处理错误
  }
}

/**
 * 恢复媒体
 */
const handleRestore = async (media: Media) => {
  try {
    await restoreMedia(media.id)
    toast.success('文件已恢复')
    loadTrashList()
    // 如果在媒体列表页，刷新列表
    if (activeTab.value === 'media') {
      loadMediaList()
    }
  } catch (error) {
    // API 拦截器已处理错误
  }
}

/**
 * 永久删除媒体
 */
const handlePermanentDelete = (media: Media) => {
  permanentDeleteTarget.value = media
  permanentDeleteConfirmVisible.value = true
}

const confirmPermanentDelete = async () => {
  if (!permanentDeleteTarget.value) return
  try {
    await permanentlyDeleteMedia(permanentDeleteTarget.value.id)
    toast.success('文件已永久删除')
    loadTrashList()
  } catch (error) {
    // API 拦截器已处理错误
  }
}

/**
 * 清空回收站
 */
const handleClearTrash = () => {
  clearTrashConfirmVisible.value = true
}

const confirmClearTrash = async () => {
  try {
    const result = await clearTrash()
    toast.success(`已清空回收站，共删除 ${result.deleted_count} 个文件`)
    loadTrashList()
  } catch (error) {
    // API 拦截器已处理错误
  }
}

/**
 * 触发图片上传
 */
const triggerImageUpload = () => {
  if (!queryParams.textbook_id) {
    toast.error('请先选择教材')
    return
  }
  imageFileInput.value?.click()
}

/**
 * 处理图片选择
 */
const handleImageSelected = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  
  target.value = ''
  
  uploadLoading.value = true
  try {
    const result = await uploadImage(file, Number(queryParams.textbook_id))
    toast.success('上传成功')
    loadMediaList()
    
    if (result.warning === 'same_name_exists') {
      lastUploadedMedia.value = {
        id: result.id,
        textbook_id: Number(queryParams.textbook_id),
        chapter_id: null,
        filename: result.filename,
        original_name: result.original_name,
        file_path: result.file_path,
        file_size: result.file_size,
        file_size_mb: result.file_size / (1024 * 1024),
        url: result.url,
        file_type: result.file_type,
        is_deleted: false,
        deleted_at: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
      sameNameWarningVisible.value = true
    }
  } catch (error) {
    // API 拦截器已处理错误
  } finally {
    uploadLoading.value = false
  }
}

/**
 * 删除刚上传的文件
 */
const handleDeleteUploadedFile = async () => {
  if (!lastUploadedMedia.value) return
  
  try {
    await deleteMedia(lastUploadedMedia.value.id)
    toast.success('已删除新上传的文件')
    loadMediaList()
    loadTrashList()
  } catch (error) {
    // API 拦截器已处理错误
  } finally {
    lastUploadedMedia.value = null
  }
}

/**
 * 切换单个选中状态
 */
const toggleSelect = (id: number) => {
  if (selectedIds.value.has(id)) {
    selectedIds.value.delete(id)
  } else {
    selectedIds.value.add(id)
  }
}

/**
 * 切换全选状态
 */
const toggleSelectAll = () => {
  if (selectedIds.value.size === mediaList.value.length) {
    selectedIds.value.clear()
  } else {
    mediaList.value.forEach((m: Media) => selectedIds.value.add(m.id))
  }
}

/**
 * 切换回收站全选状态
 */
const toggleSelectAllTrash = () => {
  if (selectedIds.value.size === trashList.value.length) {
    selectedIds.value.clear()
  } else {
    trashList.value.forEach((m: Media) => selectedIds.value.add(m.id))
  }
}

/**
 * 批量删除
 */
const handleBatchDelete = async () => {
  const count = selectedIds.value.size
  const isTrashTab = activeTab.value === 'trash'
  const actionText = isTrashTab ? '永久删除' : '删除'
  
  if (!confirm(`确定要${actionText}选中的 ${count} 个文件吗？${isTrashTab ? '此操作不可撤销。' : '文件将移入回收站。'}`)) return
  
  try {
    if (isTrashTab) {
      // 回收站使用永久删除
      await Promise.all(
        Array.from(selectedIds.value).map(id => permanentlyDeleteMedia(id))
      )
    } else {
      // 媒体列表使用软删除
      await Promise.all(
        Array.from(selectedIds.value).map(id => deleteMedia(id))
      )
    }
    toast.success(`成功${actionText} ${count} 个文件`)
    selectedIds.value.clear()
    isMultiSelectMode.value = false
    if (isTrashTab) {
      loadTrashList()
    } else {
      handleSearch()
      loadTrashList()
    }
  } catch (error) {
    // API 拦截器已处理错误 toast
  }
}

/**
 * 批量恢复
 */
const handleBatchRestore = async () => {
  if (!confirm(`确定要恢复选中的 ${selectedIds.value.size} 个文件吗？`)) return
  
  try {
    await Promise.all(
      Array.from(selectedIds.value).map(id => restoreMedia(id))
    )
    toast.success(`成功恢复 ${selectedIds.value.size} 个文件`)
    selectedIds.value.clear()
    isMultiSelectMode.value = false
    loadTrashList()
    loadMediaList()
  } catch (error) {
    // API 拦截器已处理错误 toast
  }
}

// ==================== 工具函数 ====================

/**
 * 判断是否为图片类型
 */
const isImage = (fileType: string): boolean => {
  return fileType.startsWith('image/')
}

/**
 * 格式化文件大小
 */
const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

/**
 * 格式化日期
 */
const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 获取教材标题
 */
const getTextbookTitle = (textbookId: number): string => {
  const textbook = textbooks.value.find(t => t.id === textbookId)
  return textbook?.title || `教材 #${textbookId}`
}

/**
 * 获取文件类型显示名称
 */
const getFileTypeName = (fileType: string): string => {
  if (fileType.startsWith('image/')) return '图片'
  if (fileType.includes('pdf') || fileType.includes('document') || fileType.includes('word')) return '文档'
  return '其他'
}

/**
 * 获取文件类型徽章样式
 */
const getFileTypeBadgeClass = (fileType: string): string => {
  switch (fileType) {
    case 'image':
      return 'bg-green-50 text-green-600 border-green-100'
    case 'document':
      return 'bg-blue-50 text-blue-600 border-blue-100'
    default:
      return 'bg-gray-50 text-gray-500 border-gray-100'
  }
}

// ==================== 生命周期 ====================

// 监听标签页切换
watch(activeTab, (newTab) => {
  if (newTab === 'trash') {
    // 确保使用最新的 pageSize
    trashQueryParams.page_size = pageSize.value
    trashQueryParams.page = 1
    loadTrashList()
  }
})

onMounted(() => {
  loadTextbooks()
  loadMediaList()
  // 预加载回收站数量
  loadTrashList()
})
</script>
