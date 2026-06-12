<template>
  <div
    class="portal-page"
    :class="{
      'is-sidebar-collapsed': isSidebarCollapsed,
      'is-review-panel-resizing': isReviewPanelResizing,
    }"
    :style="{ '--review-panel-width': reviewPanelWidthStyle }"
  >
    <aside class="portal-sidebar">
      <div class="portal-brand">
        <div class="brand-mark" aria-hidden="true">
          <el-icon><Connection /></el-icon>
        </div>
        <div class="brand-copy">
          <strong>智审</strong>
          <span>AI Legal Review</span>
        </div>
        <button
          class="sidebar-toggle"
          type="button"
          :aria-label="isSidebarCollapsed ? '展开侧边栏' : '收起侧边栏'"
          :title="isSidebarCollapsed ? '展开侧边栏' : '收起侧边栏'"
          @click="toggleSidebar"
        >
          <el-icon>
            <Expand v-if="isSidebarCollapsed" />
            <Fold v-else />
          </el-icon>
        </button>
      </div>

      <nav class="global-nav" aria-label="全局导航">
        <button
          v-for="item in navItems"
          :key="item.key"
          class="nav-item"
          :class="{ active: activeNav === item.key }"
          type="button"
          @click="activeNav = item.key"
        >
          <el-icon>
            <component :is="item.icon" />
          </el-icon>
          <span>{{ item.label }}</span>
        </button>
      </nav>

      <div class="profile-card">
        <el-avatar :size="28" class="profile-avatar">FR</el-avatar>
        <div class="profile-copy">
          <span>法务审核员</span>
          <strong>ID: FR-2026-008</strong>
        </div>
      </div>
    </aside>

    <main class="document-workplace">
      <header class="workplace-toolbar">
        <div class="file-meta">
          <el-tag v-if="uploadedDocument" class="file-tag" effect="plain">
            <el-icon><DocumentChecked /></el-icon>
            {{ currentFileName }}
          </el-tag>
          <span>智能审查任务</span>
        </div>
        <el-button type="primary" class="upload-button" :loading="uploadLoading" @click="openUploadDialog">
          <el-icon><Plus /></el-icon>
          上传文档
        </el-button>
        <input
          ref="fileInputRef"
          class="upload-input"
          type="file"
          accept=".docx,.pdf,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          @change="handleFileChange"
        />
      </header>

      <section class="document-stage" aria-label="文档预览">
        <div class="paper-scale-shell" :style="{ '--preview-scale': previewScale }">
          <article class="document-paper" :class="{ 'is-uploaded-preview': uploadedDocument }">
            <template v-if="uploadedDocument">
              <div class="paper-header">
                <span>{{ uploadedDocument.name }}</span>
                <span>第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
              </div>
              <template v-if="currentPreviewPage?.type === 'pdf_image'">
                <img
                  class="pdf-page-image"
                  :src="resolveApiUrl(currentPreviewPage.image_url)"
                  :alt="`${uploadedDocument.name} 第 ${currentPage} 页`"
                />
              </template>
              <div
                v-else
                class="docx-preview-page"
                v-html="currentPreviewPage?.html || '<p>该页没有可预览内容。</p>'"
              ></div>
            </template>
            <template v-else>
              <div class="blank-paper"></div>
            </template>
          </article>
        </div>
      </section>

      <footer class="document-status">
        <div class="status-group">
          <div class="page-control" aria-label="文档分页">
            <button
              class="page-action"
              type="button"
              :disabled="!uploadedDocument || currentPage === 1"
              @click="goPrevPage"
            >
              <span>上一页</span>
              <span class="page-chevron" aria-hidden="true">&lt;</span>
            </button>
            <span class="page-counter">
              <strong>{{ displayCurrentPage }}</strong><span>/{{ totalPages }}</span>
            </span>
            <button
              class="page-action"
              type="button"
              :disabled="!uploadedDocument || currentPage === totalPages"
              @click="goNextPage"
            >
              <span class="page-chevron" aria-hidden="true">&gt;</span>
              <span>下一页</span>
            </button>
          </div>
          <span>字数 <strong>{{ wordCount }}</strong></span>
          <span>拼写检查: 中文</span>
        </div>
        <div class="zoom-control">
          <el-button
            circle
            size="small"
            aria-label="缩小"
            :disabled="zoom <= minZoom"
            @click="zoomOut"
          >
            <el-icon><Minus /></el-icon>
          </el-button>
          <el-slider
            v-model="zoom"
            :min="minZoom"
            :max="maxZoom"
            :step="zoomStep"
            :show-tooltip="false"
            class="zoom-slider"
          />
          <el-button
            circle
            size="small"
            aria-label="放大"
            :disabled="zoom >= maxZoom"
            @click="zoomIn"
          >
            <el-icon><Plus /></el-icon>
          </el-button>
          <strong>{{ zoom }}%</strong>
        </div>
      </footer>
    </main>

    <el-dialog
      v-model="uploadDialogVisible"
      class="document-upload-dialog"
      width="360px"
      :show-close="false"
      destroy-on-close
    >
      <button class="dialog-close" type="button" aria-label="关闭上传弹窗" @click="closeUploadDialog">
        ×
      </button>
      <div
        class="upload-drop-zone"
        :class="{ 'is-dragover': isDragOver, 'has-file': pendingFile }"
        role="button"
        tabindex="0"
        @click="openFileDialog"
        @keydown.enter.prevent="openFileDialog"
        @keydown.space.prevent="openFileDialog"
        @dragenter.prevent="isDragOver = true"
        @dragover.prevent="isDragOver = true"
        @dragleave.prevent="isDragOver = false"
        @drop.prevent="handleFileDrop"
      >
        <div class="upload-icon-bubble">
          <el-icon><Upload /></el-icon>
        </div>
        <template v-if="pendingFile">
          <h2>{{ pendingFile.name }}</h2>
          <p>
            已选择文档，点击“确认上传”后开始上传
            <span>{{ formatFileSize(pendingFile.size) }}</span>
          </p>
        </template>
        <template v-else>
          <h2>点击或将文档拖拽到这里上传</h2>
          <p>单个文档不超过20MB，格式支持：pdf/docx</p>
        </template>
      </div>
      <template #footer>
        <div class="upload-dialog-footer">
          <el-button @click="closeUploadDialog">取消</el-button>
          <el-button type="primary" :disabled="!pendingFile" :loading="uploadLoading" @click="confirmUpload">
            确认上传
          </el-button>
        </div>
      </template>
    </el-dialog>

    <aside class="review-panel">
      <div
        class="review-panel-resizer"
        role="separator"
        aria-label="拖动调整右侧审查栏宽度"
        aria-orientation="vertical"
        :aria-valuemin="reviewPanelMinWidth"
        :aria-valuemax="reviewPanelMaxWidth"
        :aria-valuenow="reviewPanelWidth"
        title="拖动调整右侧审查栏宽度"
        @pointerdown="startReviewPanelResize"
      ></div>
      <div class="panel-scroll">
        <section class="workflow-card">
          <el-steps :active="0" align-center>
            <el-step title="文档概览" />
            <el-step title="审查清单" />
            <el-step title="审查结果" />
          </el-steps>
        </section>

        <el-card class="config-card" shadow="never">
          <template #header>
            <div class="card-title">
              <el-icon><Operation /></el-icon>
              <span>审查方式</span>
            </div>
          </template>

          <el-form label-position="top" class="review-form">
            <el-form-item label="文档类型">
              <el-select v-model="contractType" class="full-control">
                <el-option label="买卖文档" value="sale" />
                <el-option label="服务文档" value="service" />
                <el-option label="租赁文档" value="lease" />
                <el-option label="劳动文档" value="labor" />
              </el-select>
            </el-form-item>

            <el-form-item label="审查尺度">
              <el-radio-group v-model="strictness" class="segmented-group">
                <el-radio-button label="strong">强势</el-radio-button>
                <el-radio-button label="weak">弱势</el-radio-button>
                <el-radio-button label="balanced">均衡</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="选择审查清单">
              <div class="checklist-actions">
                <button class="checklist-action active" type="button">
                  <span class="action-icon">
                    <el-icon><MagicStick /></el-icon>
                  </span>
                  <strong>AI 智能生成</strong>
                  <small>基于文档上下文自动构建</small>
                </button>
                <button class="checklist-action pro" type="button">
                  <span class="action-icon">
                    <el-icon><Grid /></el-icon>
                  </span>
                  <strong>从知识库选择 <em>PRO</em></strong>
                  <small>调用企业标准审查模板</small>
                </button>
              </div>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="overview-card" shadow="never">
          <template #header>
            <div class="card-title">
              <el-icon><Memo /></el-icon>
              <span>文档概览</span>
            </div>
          </template>

          <div
            class="overview-copy"
            :class="{ 'is-loading': overviewLoading, 'is-error': overviewError }"
          >
            {{ overviewDisplayText }}
          </div>

          <div class="pipeline">
            <div class="pipeline-track" :style="{ '--overview-fill-right': overviewFillRight }">
              <div class="pipeline-fill"></div>
              <div
                v-for="(stage, index) in pipelineStages"
                :key="stage"
                class="pipeline-node"
                :class="{
                  done: isOverviewStageDone(index),
                  active: isOverviewStageActive(index),
                  error: overviewError && index === overviewStageIndex,
                }"
              >
                <span>
                  <el-icon v-if="isOverviewStageDone(index)"><Check /></el-icon>
                  <el-icon v-else-if="isOverviewStageActive(index)" class="spin"><Loading /></el-icon>
                  <span v-else>{{ index + 1 }}</span>
                </span>
                <strong>{{ stage }}</strong>
              </div>
            </div>
            <el-progress :percentage="overviewProgress" :stroke-width="10" :show-text="false" />
          </div>
        </el-card>
      </div>

      <footer class="review-footer">
        <el-button type="primary" class="generate-button" :loading="isGenerating">
          生成审查清单
        </el-button>
      </footer>
    </aside>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Check,
  Collection,
  Connection,
  Document,
  DocumentChecked,
  Expand,
  Fold,
  Grid,
  Loading,
  MagicStick,
  Memo,
  Minus,
  Operation,
  Plus,
  Reading,
  Upload,
} from '@element-plus/icons-vue'

const activeNav = ref('file-review')
const isSidebarCollapsed = ref(false)
const contractType = ref('sale')
const strictness = ref('strong')
const zoom = ref(75)
const isGenerating = ref(false)
const currentPage = ref(1)
const minZoom = 50
const maxZoom = 125
const zoomStep = 5
const reviewPanelMinWidth = 320
const reviewPanelDefaultWidth = 400
const reviewPanelWidth = ref(reviewPanelDefaultWidth)
const reviewPanelMaxWidth = ref(reviewPanelDefaultWidth)
const isReviewPanelResizing = ref(false)
const uploadLoading = ref(false)
const uploadedDocument = ref(null)
const overviewText = ref('')
const overviewLoading = ref(false)
const overviewError = ref('')
const uploadDialogVisible = ref(false)
const pendingFile = ref(null)
const isDragOver = ref(false)
const fileInputRef = ref(null)
const previewScale = computed(() => zoom.value / 100)
const reviewPanelWidthStyle = computed(() => `${reviewPanelWidth.value}px`)
const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const currentFileName = computed(() => uploadedDocument.value?.name || '')
const previewPages = computed(() => uploadedDocument.value?.pages || [])
const totalPages = computed(() => uploadedDocument.value?.page_count || 0)
const wordCount = computed(() => uploadedDocument.value?.word_count || 0)
const currentPreviewPage = computed(() => previewPages.value[currentPage.value - 1] || null)
const displayCurrentPage = computed(() => (uploadedDocument.value ? currentPage.value : 0))
const overviewStageIndex = computed(() => {
  if (!uploadedDocument.value) return 0
  if (overviewText.value) return pipelineStages.length
  if (overviewLoading.value) return 2
  if (overviewError.value) return 2
  return 1
})
const overviewProgress = computed(() => {
  if (overviewText.value) return 100
  if (overviewLoading.value) return 68
  if (overviewError.value) return 46
  if (uploadedDocument.value) return 28
  return 0
})
const overviewFillRight = computed(() => `${87.5 - overviewProgress.value * 0.75}%`)
const overviewDisplayText = computed(() => {
  if (overviewLoading.value) return '文档概览生成中，请稍候...'
  if (overviewError.value) return overviewError.value
  if (overviewText.value) return overviewText.value
  if (uploadedDocument.value) return '已上传文档，等待生成概览。'
  return '上传文档后将自动生成100到400字的文档概览。'
})

const navItems = shallowRef([
  { key: 'file-review', label: '文件审查', icon: Document },
  { key: 'text-reading', label: '文本阅读', icon: Reading },
  { key: 'knowledge-base', label: '知识库', icon: Collection },
])

const pipelineStages = ['理解文档', '提取信息', '总结内容', '完成']
let overviewRequestId = 0

const getReviewPanelMaxWidth = () => {
  if (typeof window === 'undefined') return reviewPanelDefaultWidth
  return Math.max(reviewPanelMinWidth, Math.floor(window.innerWidth / 3))
}

const clampReviewPanelWidth = (width) => {
  return Math.min(Math.max(Math.round(width), reviewPanelMinWidth), reviewPanelMaxWidth.value)
}

const refreshReviewPanelLimits = () => {
  reviewPanelMaxWidth.value = getReviewPanelMaxWidth()
  reviewPanelWidth.value = clampReviewPanelWidth(reviewPanelWidth.value)
}

const handleReviewPanelPointerMove = (event) => {
  if (!isReviewPanelResizing.value) return
  reviewPanelWidth.value = clampReviewPanelWidth(window.innerWidth - event.clientX)
}

const stopReviewPanelResize = () => {
  if (!isReviewPanelResizing.value) return
  isReviewPanelResizing.value = false
  document.removeEventListener('pointermove', handleReviewPanelPointerMove)
  document.removeEventListener('pointerup', stopReviewPanelResize)
  document.removeEventListener('pointercancel', stopReviewPanelResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

const startReviewPanelResize = (event) => {
  if (event.button !== undefined && event.button !== 0) return
  if (window.matchMedia('(max-width: 980px)').matches) return
  event.preventDefault()
  refreshReviewPanelLimits()
  isReviewPanelResizing.value = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  reviewPanelWidth.value = clampReviewPanelWidth(window.innerWidth - event.clientX)
  document.addEventListener('pointermove', handleReviewPanelPointerMove)
  document.addEventListener('pointerup', stopReviewPanelResize)
  document.addEventListener('pointercancel', stopReviewPanelResize)
}

onMounted(() => {
  refreshReviewPanelLimits()
  window.addEventListener('resize', refreshReviewPanelLimits)
})

onBeforeUnmount(() => {
  stopReviewPanelResize()
  window.removeEventListener('resize', refreshReviewPanelLimits)
})

const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}

const openUploadDialog = () => {
  uploadDialogVisible.value = true
  pendingFile.value = null
  isDragOver.value = false
}

const closeUploadDialog = () => {
  if (uploadLoading.value) return
  uploadDialogVisible.value = false
  pendingFile.value = null
  isDragOver.value = false
}

const resolveApiUrl = (path) => {
  if (!path) return ''
  if (/^https?:\/\//i.test(path)) return path
  return `${apiBaseUrl}${path.startsWith('/') ? path : `/${path}`}`
}

const openFileDialog = () => {
  fileInputRef.value?.click()
}

const validateUploadFile = (file) => {
  const extension = file.name.split('.').pop()?.toLowerCase()
  if (!['docx', 'pdf'].includes(extension)) {
    ElMessage.error('仅支持上传 DOCX、PDF 文件')
    return false
  }
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 20MB')
    return false
  }
  return true
}

const setPendingFile = (file) => {
  if (!validateUploadFile(file)) return
  pendingFile.value = file
}

const handleFileChange = (event) => {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  setPendingFile(file)
}

const handleFileDrop = (event) => {
  isDragOver.value = false
  const file = event.dataTransfer?.files?.[0]
  if (!file) return
  setPendingFile(file)
}

const formatFileSize = (size) => {
  if (size < 1024 * 1024) return `${Math.max(1, Math.round(size / 1024))}KB`
  return `${(size / 1024 / 1024).toFixed(1)}MB`
}

const collectDocumentText = (document) => {
  return (document?.pages || [])
    .map((page) => page?.text || '')
    .filter((text) => text.trim())
    .join('\n\n')
}

const isOverviewStageDone = (index) => {
  return Boolean(overviewText.value) || index < overviewStageIndex.value
}

const isOverviewStageActive = (index) => {
  return overviewLoading.value && index === overviewStageIndex.value
}

const generateDocumentOverview = async (document) => {
  const requestId = ++overviewRequestId
  const content = collectDocumentText(document)
  overviewText.value = ''
  overviewError.value = ''
  if (!content.trim()) {
    overviewError.value = '文档没有可用于生成概览的文本内容。'
    return
  }

  overviewLoading.value = true
  try {
    const response = await fetch(resolveApiUrl('/api/portal/ai/document-overview/'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        document_id: document.id,
        document_name: document.name,
        content,
      }),
    })
    const payload = await response.json().catch(() => ({}))
    if (!response.ok || !payload.success) {
      throw new Error(payload.detail || payload.error || payload.message || '文档概览生成失败')
    }
    if (requestId !== overviewRequestId) return
    overviewText.value = payload.overview || payload.response || ''
    if (!overviewText.value) {
      throw new Error('文档概览生成结果为空')
    }
  } catch (error) {
    if (requestId !== overviewRequestId) return
    overviewError.value = error.message || '文档概览生成失败'
  } finally {
    if (requestId === overviewRequestId) {
      overviewLoading.value = false
    }
  }
}

const confirmUpload = async () => {
  if (!pendingFile.value || !validateUploadFile(pendingFile.value)) return
  const formData = new FormData()
  formData.append('file', pendingFile.value)
  uploadLoading.value = true
  try {
    const response = await fetch(resolveApiUrl('/api/portal/documents/upload/'), {
      method: 'POST',
      body: formData,
    })
    const payload = await response.json().catch(() => ({}))
    if (!response.ok || !payload.success) {
      throw new Error(payload.detail || payload.error || payload.message || '文件上传失败')
    }
    uploadedDocument.value = payload.document
    currentPage.value = 1
    zoom.value = 75
    uploadDialogVisible.value = false
    pendingFile.value = null
    ElMessage.success('文件上传成功')
    generateDocumentOverview(payload.document)
  } catch (error) {
    ElMessage.error(error.message || '文件上传失败')
  } finally {
    uploadLoading.value = false
  }
}

const goPrevPage = () => {
  currentPage.value = Math.max(1, currentPage.value - 1)
}

const goNextPage = () => {
  currentPage.value = Math.min(totalPages.value, currentPage.value + 1)
}

const zoomOut = () => {
  zoom.value = Math.max(minZoom, zoom.value - zoomStep)
}

const zoomIn = () => {
  zoom.value = Math.min(maxZoom, zoom.value + zoomStep)
}
</script>

<style scoped>
.portal-page {
  --portal-primary: #1677ff;
  --portal-primary-dark: #0958d9;
  --portal-primary-soft: #edf5ff;
  --portal-primary-mist: #f7fbff;
  --portal-accent: #4096ff;
  --portal-success: #74b99f;
  --portal-success-soft: #f0faf5;
  --portal-lavender: #8a8dbf;
  --portal-lavender-soft: #f5f6fb;
  --portal-border: #e8edf5;
  --portal-border-strong: #d6deec;
  --portal-text: #1f2937;
  --portal-muted: #667085;
  --portal-faint: #98a2b3;
  --portal-card-shadow: 0 18px 48px rgba(15, 23, 42, 0.06);
  --portal-soft-shadow: 0 10px 30px rgba(15, 23, 42, 0.045);
  --review-panel-width: 400px;
  --el-font-size-base: 13px;
  --el-font-size-small: 12px;
  --el-component-size: 34px;
  --el-color-primary: var(--portal-primary);
  --el-color-primary-dark-2: var(--portal-primary-dark);
  --el-color-primary-light-3: #5aa8ff;
  --el-color-primary-light-5: #8fc5ff;
  --el-color-primary-light-7: #c7e1ff;
  --el-color-primary-light-8: #dcebff;
  --el-color-primary-light-9: var(--portal-primary-soft);
  --el-border-radius-base: 7px;
  --el-border-radius-small: 6px;
  min-height: 100vh;
  display: grid;
  grid-template-columns: 220px minmax(560px, 1fr) minmax(320px, var(--review-panel-width));
  background: #f6f8fb;
  color: var(--portal-text);
  font-size: 13px;
  overflow: hidden;
  transition: grid-template-columns 0.2s ease;
}

.portal-page.is-sidebar-collapsed {
  grid-template-columns: 72px minmax(560px, 1fr) minmax(320px, var(--review-panel-width));
}

.portal-page.is-review-panel-resizing {
  cursor: col-resize;
  user-select: none;
  transition: none;
}

.portal-page.is-review-panel-resizing * {
  cursor: col-resize !important;
}

.portal-page :deep(.el-button),
.portal-page :deep(.el-input__inner),
.portal-page :deep(.el-select__placeholder),
.portal-page :deep(.el-radio-button__inner),
.portal-page :deep(.el-tag) {
  font-size: 13px;
}

.portal-page :deep(.el-button) {
  border-radius: 7px;
}

.portal-page :deep(.el-input__wrapper),
.portal-page :deep(.el-select__wrapper) {
  border-radius: 7px;
}

.portal-sidebar {
  min-width: 0;
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 18px 14px;
  border-right: 1px solid var(--portal-border);
  background:
    linear-gradient(180deg, rgba(22, 119, 255, 0.045), rgba(255, 255, 255, 0) 46%),
    #fbfcff;
}

.portal-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 50px;
  margin-bottom: 22px;
}

.is-sidebar-collapsed .portal-sidebar {
  padding: 18px 10px;
}

.is-sidebar-collapsed .portal-brand {
  justify-content: center;
  margin-bottom: 22px;
}

.brand-mark {
  width: 42px;
  height: 42px;
  aspect-ratio: 1 / 1;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  color: #fff;
  font-size: 20px;
  overflow: hidden;
  border-radius: 12px;
  background: linear-gradient(150deg, var(--portal-primary), var(--portal-accent));
  box-shadow: 0 12px 24px rgba(22, 119, 255, 0.16);
}

.brand-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.brand-copy strong {
  color: var(--portal-primary);
  font-size: 22px;
  line-height: 1;
}

.brand-copy span {
  color: var(--portal-faint);
  font-size: 12px;
}

.sidebar-toggle {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  margin-left: auto;
  color: #7b8497;
  font-size: 15px;
  border: 1px solid #dfe4f0;
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.72);
  cursor: pointer;
  transition:
    color 0.18s ease,
    border-color 0.18s ease,
    background-color 0.18s ease;
}

.sidebar-toggle:hover {
  color: var(--portal-primary);
  border-color: rgba(22, 119, 255, 0.28);
  background: #fff;
}

.is-sidebar-collapsed .brand-copy {
  display: none;
}

.is-sidebar-collapsed .brand-mark {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  font-size: 18px;
}

.is-sidebar-collapsed .sidebar-toggle {
  position: absolute;
  top: 62px;
  right: 8px;
  width: 24px;
  height: 24px;
  font-size: 13px;
  border-radius: 6px;
}

.global-nav {
  display: grid;
  gap: 6px;
}

.nav-item {
  width: 100%;
  height: 44px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 12px;
  color: #3b4254;
  font-size: 13px;
  font-weight: 650;
  text-align: left;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  transition: all 0.18s ease;
}

.nav-item .el-icon {
  font-size: 18px;
}

.is-sidebar-collapsed .nav-item {
  justify-content: center;
  padding: 0;
}

.is-sidebar-collapsed .nav-item span {
  display: none;
}

.nav-item:hover {
  color: var(--portal-primary);
  background: rgba(255, 255, 255, 0.82);
}

.nav-item.active {
  color: var(--portal-primary);
  border-color: rgba(22, 119, 255, 0.18);
  background: #fff;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.045);
}

.profile-card {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: auto;
  padding: 8px 4px;
  border-radius: 6px;
  background: transparent;
}

.profile-avatar {
  --el-avatar-bg-color: #dde8f7;
  color: #667085;
  flex: 0 0 auto;
  font-size: 11px;
  font-weight: 700;
}

.profile-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.profile-copy span {
  color: #626b7e;
  font-size: 12px;
  font-weight: 600;
}

.profile-copy strong {
  color: #a0a8b8;
  font-size: 11px;
  font-weight: 600;
}

.is-sidebar-collapsed .profile-card {
  justify-content: center;
  padding: 8px 0;
}

.is-sidebar-collapsed .profile-copy {
  display: none;
}

.document-workplace {
  min-width: 0;
  height: 100vh;
  display: grid;
  grid-template-rows: 64px minmax(0, 1fr) 52px;
  background:
    linear-gradient(180deg, #ffffff 0, #ffffff 64px, #f6f8fb 64px),
    #f6f8fb;
}

.workplace-toolbar,
.document-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 0 24px;
  background: #fff;
}

.workplace-toolbar {
  border-bottom: 1px solid var(--portal-border);
}

.file-meta {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--portal-muted);
  font-size: 12px;
}

.file-tag {
  max-width: min(320px, 44vw);
  height: 30px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  overflow: hidden;
  color: var(--portal-primary);
  border-color: rgba(22, 119, 255, 0.2);
  background: var(--portal-primary-soft);
}

.upload-button {
  min-width: 124px;
  height: 36px;
  border-color: var(--portal-primary);
  border-radius: 7px;
  background: var(--portal-primary);
  box-shadow: 0 8px 18px rgba(22, 119, 255, 0.16);
}

.upload-button:hover,
.upload-button:focus {
  border-color: var(--portal-primary-dark);
  background: var(--portal-primary-dark);
}

.upload-input {
  display: none;
}

.document-upload-dialog {
  height: 360px;
  display: flex;
  flex-direction: column;
  border-radius: 8px;
  overflow: hidden;
}

.document-upload-dialog :deep(.el-dialog__header) {
  display: none;
}

.document-upload-dialog :deep(.el-dialog__body) {
  position: relative;
  display: flex;
  min-height: 0;
  flex: 1;
  padding: 0;
}

.document-upload-dialog :deep(.el-dialog__footer) {
  flex: 0 0 auto;
  padding: 12px 18px 16px;
  border-top: 1px solid #eef1f7;
  background: #fff;
}

.dialog-close {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 2;
  width: 24px;
  height: 24px;
  color: #9aa2b2;
  font-size: 16px;
  line-height: 24px;
  border: none;
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
  transition:
    color 0.18s ease,
    background-color 0.18s ease;
}

.dialog-close:hover {
  color: #303747;
  background: rgba(34, 40, 58, 0.06);
}

.upload-drop-zone {
  width: 100%;
  min-height: 0;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 12px;
  padding: 32px 28px 30px;
  color: #151923;
  text-align: center;
  border: 1px dashed transparent;
  background: #f8fbff;
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    background-color 0.18s ease,
    box-shadow 0.18s ease;
}

.upload-drop-zone:hover,
.upload-drop-zone.is-dragover {
  border-color: rgba(22, 119, 255, 0.38);
  background: #f4f9ff;
  box-shadow: inset 0 0 0 1px rgba(22, 119, 255, 0.08);
}

.upload-drop-zone.has-file {
  background: #f7fbff;
}

.upload-icon-bubble {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  color: var(--portal-primary);
  font-size: 18px;
  border-radius: 999px;
  background: #fff;
  box-shadow: 0 12px 28px rgba(22, 119, 255, 0.1);
}

.upload-drop-zone h2 {
  max-width: 420px;
  margin: 6px 0 0;
  color: #171b26;
  font-size: 14px;
  line-height: 1.45;
  font-weight: 800;
}

.upload-drop-zone p {
  margin: 0;
  color: #555b76;
  font-size: 12px;
  line-height: 1.55;
  font-weight: 600;
}

.upload-drop-zone p span {
  display: block;
  margin-top: 4px;
  color: #8d95a8;
  font-size: 13px;
  font-weight: 500;
}

.upload-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.document-stage {
  --paper-base-width: 880px;
  --paper-base-height: 1106px;
  --paper-pad-y: 64px;
  --paper-pad-x: 72px;
  min-height: 0;
  overflow: auto;
  padding: 26px 28px 34px;
  background: #f5f7fb;
}

.paper-scale-shell {
  width: calc(var(--paper-base-width) * var(--preview-scale));
  min-height: calc(var(--paper-base-height) * var(--preview-scale));
  margin: 0 auto;
}

.document-paper {
  width: var(--paper-base-width);
  min-height: var(--paper-base-height);
  padding: var(--paper-pad-y) var(--paper-pad-x);
  border: 1px solid #edf2f7;
  background: #fff;
  box-shadow: var(--portal-card-shadow);
  transform: scale(var(--preview-scale));
  transform-origin: top left;
  transition: transform 0.18s ease;
}

.document-paper.is-uploaded-preview {
  overflow: hidden;
}

.blank-paper {
  width: 100%;
  min-height: calc(var(--paper-base-height) - var(--paper-pad-y) * 2);
}

.pdf-page-image {
  width: 100%;
  display: block;
  border: 1px solid #edf2f7;
  background: #fff;
}

.docx-preview-page {
  color: #303747;
  font-size: 18px;
  line-height: 1.85;
}

.docx-preview-page :deep(p) {
  margin: 0 0 16px;
}

.docx-preview-page :deep(h2) {
  margin: 22px 0 10px;
  color: #1f2433;
  font-size: 22px;
}

.docx-preview-page :deep(.docx-preview-table) {
  width: 100%;
  margin: 18px 0;
  border-collapse: collapse;
  font-size: 16px;
}

.docx-preview-page :deep(.docx-preview-table td) {
  padding: 8px 10px;
  border: 1px solid #dfe4ef;
  vertical-align: top;
}

.paper-header {
  display: flex;
  justify-content: space-between;
  color: #8b95a7;
  font-size: 14.6px;
  border-bottom: 1px solid #edf2f7;
  padding-bottom: 16px;
  margin-bottom: 32px;
}

.document-paper h1 {
  color: #171b26;
  font-size: 30.6px;
  text-align: center;
  margin-bottom: 29px;
}

.paper-intro,
.contract-section p {
  color: #353b4a;
  font-size: 18px;
  line-height: 1.85;
}

.paper-intro {
  margin-bottom: 24px;
}

.contract-section {
  margin-top: 21px;
}

.contract-section h2 {
  color: #1f2433;
  font-size: 19.3px;
  margin-bottom: 8px;
}

.contract-section :deep(mark) {
  padding: 2px 4px;
  border-radius: 4px;
  color: #211b08;
  background: linear-gradient(180deg, transparent 18%, rgba(255, 220, 81, 0.5) 18%);
}

.risk-note {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-top: 32px;
  padding: 13px 16px;
  color: #5f6f36;
  font-size: 16px;
  border: 1px solid #dce9b8;
  border-radius: 8px;
  background: #fbfdef;
}

.document-status {
  min-width: 0;
  color: var(--portal-muted);
  border-top: 1px solid var(--portal-border);
  box-shadow: 0 -8px 24px rgba(31, 45, 61, 0.04);
  font-size: 12px;
}

.status-group,
.zoom-control {
  display: flex;
  align-items: center;
  gap: 14px;
}

.page-control {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 2px;
  border: 1px solid #e8edf5;
  border-radius: 8px;
  background: var(--portal-primary-mist);
}

.page-action {
  height: 26px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0 7px;
  color: #667085;
  font-size: 12px;
  border: none;
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
}

.page-action:hover:not(:disabled) {
  color: var(--portal-primary);
  background: #fff;
}

.page-action:disabled {
  color: #b5bdcc;
  cursor: not-allowed;
}

.page-chevron {
  color: var(--portal-primary);
  font-size: 13px;
  font-weight: 800;
}

.page-action:disabled .page-chevron {
  color: #c2c8d4;
}

.page-counter {
  min-width: 42px;
  color: #6d7586;
  text-align: center;
}

.page-counter strong {
  color: #22283a;
}

.status-group strong,
.zoom-control strong {
  color: #303747;
}

.zoom-control {
  min-width: 250px;
}

.zoom-slider {
  width: 108px;
}

.review-panel {
  min-width: 0;
  position: relative;
  height: 100vh;
  display: flex;
  flex-direction: column;
  border-left: 1px solid var(--portal-border);
  background: #f7f9fc;
}

.review-panel-resizer {
  position: absolute;
  top: 0;
  bottom: 0;
  left: -6px;
  z-index: 8;
  width: 12px;
  cursor: col-resize;
  touch-action: none;
}

.review-panel-resizer::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 5px;
  width: 1px;
  background: transparent;
  transition:
    background-color 0.18s ease,
    box-shadow 0.18s ease,
    width 0.18s ease;
}

.review-panel-resizer:hover::before,
.portal-page.is-review-panel-resizing .review-panel-resizer::before {
  width: 2px;
  background: var(--portal-primary);
  box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.1);
}

.panel-scroll {
  min-height: 0;
  flex: 1;
  overflow: auto;
  padding: 18px 18px 14px;
}

.workflow-card {
  padding: 16px 12px 14px;
  margin-bottom: 14px;
  border: 1px solid var(--portal-border);
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
}

.workflow-card :deep(.el-step__title) {
  font-size: 11px;
  line-height: 1.3;
}

.workflow-card :deep(.el-step__head.is-process) {
  color: var(--portal-primary);
  border-color: var(--portal-primary);
}

.workflow-card :deep(.el-step__title.is-process) {
  color: var(--portal-primary);
  font-weight: 700;
}

.workflow-card :deep(.el-step__icon) {
  width: 26px;
  height: 26px;
}

.config-card,
.overview-card {
  margin-bottom: 14px;
  border-color: var(--portal-border);
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
}

.config-card :deep(.el-card__header),
.overview-card :deep(.el-card__header) {
  min-height: 52px;
  padding: 14px 16px;
  border-bottom-color: var(--portal-border);
}

.config-card :deep(.el-card__body),
.overview-card :deep(.el-card__body) {
  padding: 16px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #202638;
  font-size: 14px;
  font-weight: 750;
}

.card-title .el-icon {
  color: var(--portal-primary);
}

.review-form :deep(.el-form-item) {
  margin-bottom: 15px;
}

.review-form :deep(.el-form-item:last-child) {
  margin-bottom: 0;
}

.review-form :deep(.el-form-item__label) {
  color: #485266;
  font-size: 12px;
  font-weight: 700;
}

.full-control {
  width: 100%;
}

.segmented-group {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.segmented-group :deep(.el-radio-button__inner) {
  width: 100%;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-color: var(--portal-border-strong);
  box-shadow: none;
}

.segmented-group :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  border-color: var(--portal-primary);
  background: var(--portal-primary);
  box-shadow: -1px 0 0 0 var(--portal-primary);
}

.checklist-actions {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.checklist-action {
  min-height: 112px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 7px;
  padding: 14px;
  text-align: left;
  border: 1px solid var(--portal-border);
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.035);
  cursor: pointer;
}

.checklist-action.active {
  border-color: rgba(22, 119, 255, 0.45);
  background: linear-gradient(180deg, #fff, var(--portal-primary-mist));
  box-shadow: 0 10px 26px rgba(22, 119, 255, 0.1);
}

.action-icon {
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  color: var(--portal-primary);
  border-radius: 8px;
  background: var(--portal-primary-soft);
}

.checklist-action strong {
  color: #22283a;
  font-size: 12.5px;
  line-height: 1.35;
}

.checklist-action small {
  color: var(--portal-muted);
  font-size: 11.5px;
  line-height: 1.5;
}

.checklist-action em {
  display: inline-flex;
  margin-left: 4px;
  padding: 1px 5px;
  color: #6f719d;
  font-size: 10px;
  font-style: normal;
  border-radius: 5px;
  background: var(--portal-lavender-soft);
}

.overview-copy {
  color: var(--portal-muted);
  font-size: 12px;
  line-height: 1.65;
  padding: 10px 12px;
  border: 1px solid #edf2f7;
  border-radius: 8px;
  background: #fbfdff;
}

.overview-copy.is-loading {
  color: var(--portal-primary);
  border-color: rgba(22, 119, 255, 0.18);
  background: var(--portal-primary-mist);
}

.overview-copy.is-error {
  color: #b42318;
  border-color: #ffd4d0;
  background: #fff8f7;
}

.pipeline {
  margin-top: 16px;
}

.pipeline-track {
  position: relative;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 5px;
  margin-bottom: 16px;
}

.pipeline-track::before,
.pipeline-fill {
  content: '';
  position: absolute;
  left: 12.5%;
  right: 12.5%;
  top: 15px;
  height: 3px;
  border-radius: 999px;
}

.pipeline-track::before {
  background: #e4e9f2;
}

.pipeline-fill {
  right: var(--overview-fill-right, 37%);
  z-index: 1;
  background: linear-gradient(90deg, var(--portal-success), var(--portal-primary));
}

.pipeline-node {
  position: relative;
  z-index: 2;
  display: grid;
  justify-items: center;
  gap: 7px;
  color: var(--portal-faint);
  text-align: center;
}

.pipeline-node > span {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  color: #8b93a4;
  font-size: 12px;
  font-weight: 700;
  border: 1px solid #dce1ee;
  border-radius: 999px;
  background: #fff;
}

.pipeline-node strong {
  font-size: 11px;
  font-weight: 700;
}

.pipeline-node.done > span,
.pipeline-node.active > span {
  color: #fff;
  border-color: var(--portal-success);
  background: var(--portal-success);
}

.pipeline-node.active > span {
  border-color: var(--portal-lavender);
  background: var(--portal-lavender);
}

.pipeline-node.done,
.pipeline-node.active {
  color: #3c4354;
}

.pipeline-node.error {
  color: #7a271a;
}

.pipeline-node.error > span {
  color: #fff;
  border-color: #d92d20;
  background: #d92d20;
}

.spin {
  animation: portal-spin 1s linear infinite;
}

.review-footer {
  padding: 14px 18px 16px;
  border-top: 1px solid var(--portal-border);
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(10px);
  box-shadow: 0 -10px 28px rgba(15, 23, 42, 0.04);
}

.generate-button {
  width: 100%;
  height: 44px;
  border-color: var(--portal-primary);
  border-radius: 8px;
  background: var(--portal-primary);
  box-shadow: 0 10px 24px rgba(22, 119, 255, 0.18);
}

.generate-button:hover,
.generate-button:focus {
  border-color: var(--portal-primary-dark);
  background: var(--portal-primary-dark);
}

@keyframes portal-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1280px) {
  .portal-page {
    grid-template-columns: 200px minmax(460px, 1fr) minmax(320px, var(--review-panel-width));
  }

  .portal-page.is-sidebar-collapsed {
    grid-template-columns: 72px minmax(460px, 1fr) minmax(320px, var(--review-panel-width));
  }

  .portal-sidebar {
    padding: 18px 12px;
  }

  .portal-brand {
    justify-content: flex-start;
  }

  .nav-item {
    padding: 0 12px;
  }

  .profile-card {
    padding: 8px 4px;
  }
}

@media (max-width: 980px) {
  .portal-page {
    height: auto;
    min-height: 100vh;
    grid-template-columns: 1fr;
    overflow: auto;
  }

  .portal-page.is-sidebar-collapsed {
    grid-template-columns: 1fr;
  }

  .portal-sidebar {
    position: sticky;
    top: 0;
    z-index: 10;
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 14px;
    padding: 12px 16px;
    border-right: none;
    border-bottom: 1px solid var(--portal-border);
  }

  .portal-brand {
    margin: 0;
    justify-content: flex-start;
  }

  .sidebar-toggle {
    display: none;
  }

  .is-sidebar-collapsed .brand-mark {
    width: 40px;
    height: 40px;
    border-radius: 11px;
    font-size: 20px;
  }

  .brand-copy,
  .nav-item span,
  .profile-copy {
    display: flex;
  }

  .is-sidebar-collapsed .brand-copy,
  .is-sidebar-collapsed .nav-item span,
  .is-sidebar-collapsed .profile-copy {
    display: flex;
  }

  .global-nav {
    grid-auto-flow: column;
    grid-auto-columns: max-content;
    justify-content: center;
    overflow-x: auto;
  }

  .nav-item {
    width: auto;
    padding: 0 12px;
  }

  .is-sidebar-collapsed .nav-item {
    justify-content: flex-start;
    padding: 0 12px;
  }

  .profile-card {
    margin: 0;
    padding: 8px;
  }

  .is-sidebar-collapsed .profile-card {
    justify-content: flex-start;
    padding: 8px;
  }

  .document-workplace,
  .review-panel {
    height: auto;
    min-height: 640px;
  }

  .review-panel {
    border-left: none;
    border-top: 1px solid var(--portal-border);
  }

  .review-panel-resizer {
    display: none;
  }
}

@media (max-width: 720px) {
  .document-stage {
    --paper-base-width: 482px;
    --paper-base-height: 1013px;
    --paper-pad-y: 45px;
    --paper-pad-x: 37px;
  }

  .portal-sidebar {
    grid-template-columns: 1fr;
  }

  .global-nav {
    justify-content: start;
  }

  .profile-card {
    display: none;
  }

  .workplace-toolbar,
  .document-status {
    align-items: stretch;
    flex-direction: column;
    padding: 14px 16px;
  }

  .document-workplace {
    grid-template-rows: auto minmax(0, 1fr) auto;
  }

  .file-meta,
  .status-group,
  .zoom-control {
    flex-wrap: wrap;
  }

  .upload-button {
    width: 100%;
  }

  .document-stage {
    padding: 18px 14px 24px;
  }

  .checklist-actions {
    grid-template-columns: 1fr;
  }
}
</style>
