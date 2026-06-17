<template>
  <section v-if="authChecking" class="portal-auth-page">
    <div class="portal-auth-card compact">
      <div class="auth-brand-mark">
        <el-icon><Loading /></el-icon>
      </div>
      <h1>正在校验登录状态</h1>
      <p>请稍候</p>
    </div>
  </section>

  <section v-else-if="!isAuthenticated" class="portal-auth-page">
    <el-card class="portal-login-card" shadow="never">
      <template #header>
        <div class="portal-login-header">
          <div class="auth-brand-mark">
            <el-icon><Connection /></el-icon>
          </div>
          <h1>智审门户</h1>
          <p>使用管理端账号登录</p>
        </div>
      </template>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        label-position="top"
        @submit.prevent
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="loginForm.username" placeholder="请输入用户名" autocomplete="username">
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            autocomplete="current-password"
            show-password
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-button type="primary" class="login-submit" :loading="loginLoading" @click="handleLogin">
          登录
        </el-button>
      </el-form>
    </el-card>
  </section>

  <div
    v-else
    class="portal-page"
    :class="{
      'is-sidebar-collapsed': isSidebarCollapsed,
      'is-knowledge-mode': activeNav === 'knowledge-base',
      'is-review-history-mode': activeNav === 'file-review' && fileReviewMode === 'history',
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
          @click="switchNav(item.key)"
        >
          <el-icon>
            <component :is="item.icon" />
          </el-icon>
          <span>{{ item.label }}</span>
        </button>
      </nav>

      <div class="profile-card">
        <el-avatar :size="28" class="profile-avatar">{{ userInitials }}</el-avatar>
        <div class="profile-copy">
          <span>{{ displayUserName }}</span>
          <strong>{{ displayUserMeta }}</strong>
        </div>
        <el-button class="logout-button" text :title="'退出登录'" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
        </el-button>
      </div>
    </aside>

    <main v-if="activeNav === 'file-review' && fileReviewMode === 'history'" class="review-history-workplace">
      <header class="review-history-header">
        <div>
          <span>文件审查</span>
          <h1>审查历史记录</h1>
        </div>
        <el-button type="primary" class="start-review-button" @click="startNewReview">
          <el-icon><Plus /></el-icon>
          发起审查
        </el-button>
      </header>

      <section class="review-history-section">
        <div class="review-history-toolbar">
          <el-input
            v-model="reviewHistoryKeyword"
            clearable
            class="review-history-search"
            placeholder="搜索文档名称或审查清单"
            @clear="handleReviewHistorySearch"
            @keyup.enter="handleReviewHistorySearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button @click="handleReviewHistorySearch">搜索</el-button>
        </div>

        <el-table
          :data="reviewHistoryItems"
          v-loading="reviewHistoryLoading"
          class="review-history-table"
          row-key="id"
          @row-dblclick="openReviewRecord"
        >
          <el-table-column prop="document_name" label="文档名称" min-width="260" show-overflow-tooltip />
          <el-table-column prop="checklist_name" label="审查清单" min-width="180" show-overflow-tooltip />
          <el-table-column label="风险等级" width="110">
            <template #default="{ row }">
              <el-tag :type="getRiskTagType(row.risk_level)" effect="plain" size="small">
                {{ getRiskText(row.risk_level) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="issue_count" label="问题数" width="90" />
          <el-table-column prop="page_count" label="页数" width="80" />
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag :type="getReviewStatusTagType(row.status)" effect="plain" size="small">
                {{ getReviewStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="发起时间" min-width="170">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="110" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openReviewRecord(row)">查看结果</el-button>
            </template>
          </el-table-column>
          <template #empty>
            <div class="review-history-empty">
              <el-icon><DocumentChecked /></el-icon>
              <strong>暂无审查记录</strong>
            </div>
          </template>
        </el-table>

        <div class="review-history-pagination">
          <el-pagination
            v-model:current-page="reviewHistoryPagination.page"
            v-model:page-size="reviewHistoryPagination.pageSize"
            :total="reviewHistoryPagination.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @size-change="fetchReviewHistory"
            @current-change="fetchReviewHistory"
          />
        </div>
      </section>
    </main>

    <template v-else-if="activeNav !== 'knowledge-base'">
    <main class="document-workplace">
      <header class="workplace-toolbar">
        <div class="file-meta">
          <el-tag v-if="uploadedDocument" class="file-tag" effect="plain">
            <el-icon><DocumentChecked /></el-icon>
            {{ currentFileName }}
          </el-tag>
          <span>智能审查任务</span>
        </div>
        <div class="workplace-actions">
          <el-button @click="openReviewHistory">历史记录</el-button>
          <el-button type="primary" class="upload-button" :loading="uploadLoading" @click="openUploadDialog">
            <el-icon><Plus /></el-icon>
            上传文档
          </el-button>
        </div>
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

    <el-dialog
      v-model="checklistPickerVisible"
      title="从知识库选择审查清单"
      width="840px"
      class="checklist-picker-dialog"
    >
      <div class="checklist-picker">
        <div class="checklist-picker-toolbar">
          <el-input
            v-model="checklistPickerKeyword"
            clearable
            class="checklist-picker-search"
            placeholder="请输入清单名称搜索"
            @clear="handleChecklistPickerSearch"
            @keyup.enter="handleChecklistPickerSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button @click="handleChecklistPickerSearch">搜索</el-button>
        </div>

        <el-table
          :data="checklistPickerItems"
          v-loading="checklistPickerLoading"
          class="checklist-picker-table"
          row-key="id"
        >
          <el-table-column prop="name" label="审查清单名称" min-width="260" />
          <el-table-column prop="rule_count" label="规则数量" width="120" />
          <el-table-column prop="updated_at" label="最后修改时间" min-width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.updated_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                :disabled="selectedReviewChecklist?.id === row.id"
                @click="selectReviewChecklist(row)"
              >
                {{ selectedReviewChecklist?.id === row.id ? '已选择' : '选择' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="checklist-picker-pagination">
          <el-pagination
            v-model:current-page="checklistPickerPagination.page"
            v-model:page-size="checklistPickerPagination.pageSize"
            :total="checklistPickerPagination.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @size-change="fetchChecklistPickerItems"
            @current-change="fetchChecklistPickerItems"
          />
        </div>
      </div>
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
          <el-steps :active="workflowActiveStep" align-center>
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
              <div v-if="selectedReviewChecklist" class="selected-checklist-card">
                <div>
                  <span>已选择</span>
                  <strong>{{ selectedReviewChecklist.name }}</strong>
                  <small>
                    {{ selectedReviewChecklist.rule_count || 0 }} 条规则 ·
                    {{ formatDateTime(selectedReviewChecklist.updated_at) }}
                  </small>
                </div>
                <el-button link type="primary" @click="openChecklistPicker">更换</el-button>
              </div>
              <div class="checklist-actions">
                <button class="checklist-action active" type="button" @click="openChecklistPicker">
                  <span class="action-icon">
                    <el-icon><Grid /></el-icon>
                  </span>
                  <strong>从知识库选择</strong>
                  <small>调用企业标准审查模板</small>
                </button>
              </div>
              <div v-if="selectedReviewChecklist?.rules?.length" class="selected-rule-preview">
                <span
                  v-for="rule in selectedReviewChecklist.rules.slice(0, 4)"
                  :key="rule.id"
                >
                  {{ rule.rule_name }}
                </span>
                <em v-if="selectedReviewChecklist.rules.length > 4">
                  +{{ selectedReviewChecklist.rules.length - 4 }}
                </em>
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

        <el-card class="review-result-card" shadow="never">
          <template #header>
            <div class="card-title">
              <el-icon><DocumentChecked /></el-icon>
              <span>审查结果</span>
            </div>
          </template>

          <div v-if="reviewLoading" class="review-running">
            <el-icon class="spin"><Loading /></el-icon>
            <span>正在按页结合审查规则调用大模型审查...</span>
          </div>

          <div v-else-if="reviewError" class="review-error">
            {{ reviewError }}
          </div>

          <div v-else-if="reviewResult" class="review-result">
            <div class="review-summary">
              <div>
                <span>风险等级</span>
                <strong>{{ getRiskText(reviewResult.summary?.risk_level) }}</strong>
              </div>
              <div>
                <span>问题数量</span>
                <strong>{{ reviewResult.summary?.issue_count || 0 }}</strong>
              </div>
              <div>
                <span>审查页数</span>
                <strong>{{ reviewResult.summary?.page_count || 0 }}</strong>
              </div>
            </div>

            <el-collapse v-model="activeReviewPages" class="review-pages">
              <el-collapse-item
                v-for="page in reviewResult.pages || []"
                :key="page.page_number"
                :name="String(page.page_number)"
              >
                <template #title>
                  <span class="review-page-title">
                    第 {{ page.page_number }} 页
                    <el-tag size="small" :type="getRiskTagType(page.risk_level)" effect="plain">
                      {{ getRiskText(page.risk_level) }}
                    </el-tag>
                    <em>{{ (page.issues || []).length }} 个问题</em>
                  </span>
                </template>
                <p class="review-page-summary">{{ page.summary || '本页未返回摘要。' }}</p>
                <div v-if="(page.issues || []).length" class="review-issue-list">
                  <article v-for="(issue, index) in page.issues" :key="index" class="review-issue">
                    <header>
                      <strong>{{ issue.rule_name || issue.rule_code || '审查规则' }}</strong>
                      <el-tag size="small" :type="getRiskTagType(issue.risk_level)" effect="plain">
                        {{ getRiskText(issue.risk_level) }}
                      </el-tag>
                    </header>
                    <p>{{ issue.issue || '-' }}</p>
                    <dl>
                      <div v-if="issue.clause">
                        <dt>原文依据</dt>
                        <dd>{{ issue.clause }}</dd>
                      </div>
                      <div v-if="issue.legal_basis">
                        <dt>规则依据</dt>
                        <dd>{{ issue.legal_basis }}</dd>
                      </div>
                      <div v-if="issue.suggestion">
                        <dt>修改建议</dt>
                        <dd>{{ issue.suggestion }}</dd>
                      </div>
                    </dl>
                  </article>
                </div>
                <div v-else class="review-page-empty">本页未发现命中规则的问题。</div>
              </el-collapse-item>
            </el-collapse>
          </div>

          <div v-else class="review-placeholder">
            上传文档并选择审查清单后，可按页结合规则进行大模型审查。
          </div>
        </el-card>
      </div>

      <footer class="review-footer">
        <el-button
          type="primary"
          class="generate-button"
          :loading="reviewLoading"
          :disabled="!selectedReviewChecklist"
          @click="applySelectedChecklist"
        >
          开始规则审查
        </el-button>
      </footer>
    </aside>
    </template>

    <main v-else class="knowledge-workplace">
      <header class="knowledge-header">
        <div>
          <span>知识库</span>
          <h1>文件审查知识库</h1>
        </div>
      </header>

      <div class="portal-knowledge-tabs">
        <button
          :class="{ active: knowledgeMode === 'checklists' }"
          type="button"
          @click="switchKnowledgeMode('checklists')"
        >
          文件审查清单
        </button>
        <button
          :class="{ active: knowledgeMode === 'rules' }"
          type="button"
          @click="switchKnowledgeMode('rules')"
        >
          审查规则库
        </button>
      </div>

      <section class="portal-knowledge-section">
        <template v-if="knowledgeMode === 'checklists'">
          <div class="knowledge-list-toolbar">
            <el-input
              v-model="knowledgeKeyword"
              clearable
              class="knowledge-search"
              placeholder="请输入清单名称搜索"
              @clear="handleKnowledgeSearch"
              @keyup.enter="handleKnowledgeSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>

          <el-table
            :data="portalChecklists"
            v-loading="checklistLoading"
            class="knowledge-table"
            row-key="id"
          >
            <el-table-column prop="name" label="审查清单名称" min-width="260" />
            <el-table-column prop="rule_count" label="规则数量" width="140" />
            <el-table-column prop="updated_at" label="最后修改时间" min-width="200">
              <template #default="{ row }">
                {{ formatDateTime(row.updated_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openChecklistDetail(row)">查看详情</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="knowledge-pagination">
            <el-pagination
              v-model:current-page="checklistPagination.page"
              v-model:page-size="checklistPagination.pageSize"
              :total="checklistPagination.total"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="fetchPortalChecklists"
              @current-change="fetchPortalChecklists"
            />
          </div>
        </template>

        <div v-else class="portal-rule-library" v-loading="rulesLoading">
          <aside class="portal-rule-type-panel">
            <div class="portal-panel-title">
              <h2>规则类型</h2>
            </div>
            <div class="portal-rule-type-list">
              <button
                v-for="category in ruleCategories"
                :key="category.name"
                :class="{ active: activeLibraryCategory === category.name }"
                type="button"
                @click="activeLibraryCategory = category.name"
              >
                <span>{{ category.name }}</span>
                <em>{{ category.count }}</em>
              </button>
            </div>
          </aside>

          <section class="portal-library-rule-panel">
            <div class="portal-panel-title with-search">
              <h2>审查规则</h2>
              <el-input
                v-model="knowledgeKeyword"
                clearable
                class="portal-rule-search"
                placeholder="搜索规则名称或描述"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </div>

            <div v-if="filteredLibraryRules.length" class="portal-library-rule-list">
              <button
                v-for="rule in filteredLibraryRules"
                :key="rule.id"
                :class="{ active: librarySelectedRule?.id === rule.id }"
                type="button"
                @click="librarySelectedRuleId = rule.id"
              >
                <span class="portal-library-rule-title">{{ rule.rule_name }}</span>
                <span class="portal-library-rule-meta">
                  <span>{{ rule.description || rule.rule_code || '暂无描述' }}</span>
                  <el-tag size="small" :type="getRiskTagType(rule.risk_level)" effect="plain">
                    {{ getRiskText(rule.risk_level) }}
                  </el-tag>
                </span>
              </button>
            </div>

            <div v-else class="portal-empty">
              <el-icon><Box /></el-icon>
              <strong>暂无数据</strong>
            </div>
          </section>

          <aside class="portal-library-detail-panel">
            <div class="portal-panel-title">
              <h2>规则详情</h2>
            </div>

            <div v-if="librarySelectedRule" class="portal-rule-detail">
              <div class="portal-detail-title-row">
                <h3>{{ librarySelectedRule.rule_name }}</h3>
                <el-tag :type="getRiskTagType(librarySelectedRule.risk_level)" effect="plain">
                  {{ getRiskText(librarySelectedRule.risk_level) }}
                </el-tag>
              </div>
              <dl>
                <div>
                  <dt>规则类型</dt>
                  <dd>{{ getRuleCategory(librarySelectedRule) }}</dd>
                </div>
                <div>
                  <dt>规则编码</dt>
                  <dd>{{ librarySelectedRule.rule_code || '-' }}</dd>
                </div>
                <div>
                  <dt>规则描述</dt>
                  <dd>{{ librarySelectedRule.description || '-' }}</dd>
                </div>
                <div>
                  <dt>法律依据</dt>
                  <dd>{{ librarySelectedRule.legal_basis || '-' }}</dd>
                </div>
                <div>
                  <dt>最后修改时间</dt>
                  <dd>{{ formatDateTime(librarySelectedRule.updated_at) }}</dd>
                </div>
              </dl>
            </div>

            <div v-else class="portal-empty detail-empty">
              <strong>点击规则查看详情</strong>
            </div>
          </aside>
        </div>
      </section>

      <el-dialog
        v-model="checklistDetailVisible"
        title="审查清单详情"
        width="860px"
        class="knowledge-detail-dialog"
      >
        <div v-loading="checklistDetailLoading" class="checklist-detail-view">
          <template v-if="currentChecklist">
            <div class="checklist-detail-header">
              <h2>{{ currentChecklist.name }}</h2>
              <span>共 {{ currentChecklist.rule_count || 0 }} 条规则</span>
            </div>
            <p class="checklist-description">{{ currentChecklist.description || '暂无描述' }}</p>

            <div class="checklist-rule-layout">
              <section class="checklist-rule-list">
                <button
                  v-for="rule in currentChecklist.rules || []"
                  :key="rule.id"
                  :class="{ active: selectedChecklistRule?.id === rule.id }"
                  type="button"
                  @click="selectedChecklistRuleId = rule.id"
                >
                  <span>{{ rule.rule_name }}</span>
                  <el-tag size="small" :type="getRiskTagType(rule.risk_level)" effect="plain">
                    {{ getRiskText(rule.risk_level) }}
                  </el-tag>
                </button>
                <div v-if="!(currentChecklist.rules || []).length" class="portal-empty compact">
                  暂无规则
                </div>
              </section>

              <section class="checklist-rule-detail">
                <div v-if="selectedChecklistRule" class="portal-rule-detail compact">
                  <div class="portal-detail-title-row">
                    <h3>{{ selectedChecklistRule.rule_name }}</h3>
                    <el-tag :type="getRiskTagType(selectedChecklistRule.risk_level)" effect="plain">
                      {{ getRiskText(selectedChecklistRule.risk_level) }}
                    </el-tag>
                  </div>
                  <dl>
                    <div>
                      <dt>规则类型</dt>
                      <dd>{{ getRuleCategory(selectedChecklistRule) }}</dd>
                    </div>
                    <div>
                      <dt>规则编码</dt>
                      <dd>{{ selectedChecklistRule.rule_code || '-' }}</dd>
                    </div>
                    <div>
                      <dt>规则描述</dt>
                      <dd>{{ selectedChecklistRule.description || '-' }}</dd>
                    </div>
                    <div>
                      <dt>法律依据</dt>
                      <dd>{{ selectedChecklistRule.legal_basis || '-' }}</dd>
                    </div>
                  </dl>
                </div>
                <div v-else class="portal-empty compact">暂无数据</div>
              </section>
            </div>
          </template>
        </div>
      </el-dialog>
    </main>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Box,
  Check,
  Collection,
  Connection,
  Document,
  DocumentChecked,
  Expand,
  Fold,
  Grid,
  Loading,
  Lock,
  Memo,
  Minus,
  Operation,
  Plus,
  Search,
  SwitchButton,
  Upload,
  User,
} from '@element-plus/icons-vue'

const TOKEN_KEY = 'token'
const activeNav = ref('file-review')
const fileReviewMode = ref('history')
const authChecking = ref(true)
const loginLoading = ref(false)
const currentUser = ref(null)
const loginFormRef = ref(null)
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
const reviewLoading = ref(false)
const reviewError = ref('')
const reviewResult = ref(null)
const activeReviewPages = ref([])
const uploadDialogVisible = ref(false)
const pendingFile = ref(null)
const isDragOver = ref(false)
const fileInputRef = ref(null)
const knowledgeMode = ref('checklists')
const knowledgeKeyword = ref('')
const checklistLoading = ref(false)
const rulesLoading = ref(false)
const checklistDetailVisible = ref(false)
const checklistDetailLoading = ref(false)
const checklistPickerVisible = ref(false)
const checklistPickerLoading = ref(false)
const checklistPickerKeyword = ref('')
const reviewHistoryLoading = ref(false)
const reviewHistoryKeyword = ref('')
const reviewHistoryItems = ref([])
const portalChecklists = ref([])
const portalRules = ref([])
const currentChecklist = ref(null)
const selectedChecklistRuleId = ref(null)
const selectedReviewChecklist = ref(null)
const activeLibraryCategory = ref('全部')
const librarySelectedRuleId = ref(null)
const checklistPickerItems = ref([])
const knowledgeLoaded = ref(false)
const previewScale = computed(() => zoom.value / 100)
const reviewPanelWidthStyle = computed(() => `${reviewPanelWidth.value}px`)
const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const isAuthenticated = computed(() => Boolean(currentUser.value && localStorage.getItem(TOKEN_KEY)))
const loginForm = reactive({
  username: '',
  password: '',
})
const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}
const displayUserName = computed(() => (
  currentUser.value?.real_name || currentUser.value?.username || '已登录用户'
))
const displayUserMeta = computed(() => {
  const role = currentUser.value?.role || 'portal'
  const username = currentUser.value?.username || '-'
  return `${role} · ${username}`
})
const userInitials = computed(() => {
  const source = displayUserName.value || 'U'
  return source.slice(0, 2).toUpperCase()
})
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
const workflowActiveStep = computed(() => {
  if (reviewResult.value) return 3
  if (selectedReviewChecklist.value) return 2
  if (uploadedDocument.value || overviewText.value || overviewLoading.value) return 1
  return 0
})
const checklistPagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})
const checklistPickerPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})
const reviewHistoryPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})
const ruleCategories = computed(() => {
  const counter = new Map()
  portalRules.value.forEach((rule) => {
    const category = getRuleCategory(rule)
    counter.set(category, (counter.get(category) || 0) + 1)
  })
  return [
    { name: '全部', count: portalRules.value.length },
    ...Array.from(counter.entries()).map(([name, count]) => ({ name, count })),
  ]
})
const filteredLibraryRules = computed(() => {
  const keyword = knowledgeKeyword.value.trim().toLowerCase()
  return portalRules.value
    .filter((rule) => activeLibraryCategory.value === '全部' || getRuleCategory(rule) === activeLibraryCategory.value)
    .filter((rule) => {
      if (!keyword) return true
      return [rule.rule_name, rule.description, rule.rule_code, rule.category]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(keyword))
    })
})
const librarySelectedRule = computed(() => {
  if (!filteredLibraryRules.value.length) return null
  return filteredLibraryRules.value.find((rule) => rule.id === librarySelectedRuleId.value) || filteredLibraryRules.value[0]
})
const selectedChecklistRule = computed(() => {
  const rules = currentChecklist.value?.rules || []
  if (!rules.length) return null
  return rules.find((rule) => rule.id === selectedChecklistRuleId.value) || rules[0]
})

const navItems = shallowRef([
  { key: 'file-review', label: '文件审查', icon: Document },
  { key: 'knowledge-base', label: '知识库', icon: Collection },
])

const pipelineStages = ['理解文档', '提取信息', '总结内容', '完成']
let overviewRequestId = 0
let reviewRequestId = 0

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

onMounted(async () => {
  await restoreSession()
  if (isAuthenticated.value) {
    await fetchReviewHistory()
  }
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

const switchNav = (key) => {
  activeNav.value = key
  if (key === 'file-review') {
    fileReviewMode.value = 'history'
    fetchReviewHistory()
    return
  }
  if (key === 'knowledge-base') {
    loadKnowledgeData()
  }
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

const clearReviewResult = (cancelPending = false) => {
  if (cancelPending) {
    reviewRequestId += 1
  }
  reviewLoading.value = false
  reviewError.value = ''
  reviewResult.value = null
  activeReviewPages.value = []
}

const resetReviewWorkspace = () => {
  uploadedDocument.value = null
  pendingFile.value = null
  currentPage.value = 1
  zoom.value = 75
  overviewText.value = ''
  overviewError.value = ''
  overviewLoading.value = false
  selectedReviewChecklist.value = null
  uploadDialogVisible.value = false
  checklistPickerVisible.value = false
  clearReviewResult(true)
}

const clearAuthState = () => {
  localStorage.removeItem(TOKEN_KEY)
  currentUser.value = null
  resetReviewWorkspace()
  fileReviewMode.value = 'history'
  reviewHistoryItems.value = []
  reviewHistoryKeyword.value = ''
  reviewHistoryPagination.page = 1
  reviewHistoryPagination.total = 0
}

const requestApi = async (path, options = {}) => {
  const {
    headers = {},
    auth = true,
    skipAuthError = false,
    ...fetchOptions
  } = options
  const token = localStorage.getItem(TOKEN_KEY)
  const requestHeaders = { ...headers }
  if (auth && token) {
    requestHeaders.Authorization = `Bearer ${token}`
  }

  const response = await fetch(resolveApiUrl(path), {
    ...fetchOptions,
    headers: requestHeaders,
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    if (response.status === 401) {
      clearAuthState()
      if (!skipAuthError) {
        ElMessage.error('登录已过期，请重新登录')
      }
    }
    throw new Error(payload.detail || payload.error || payload.message || '请求失败')
  }
  return payload
}

const fetchJson = (path) => requestApi(path)

const fetchCurrentUser = async (skipAuthError = false) => {
  currentUser.value = await requestApi('/api/users/users/me/', { skipAuthError })
}

const restoreSession = async () => {
  if (!localStorage.getItem(TOKEN_KEY)) {
    authChecking.value = false
    return
  }

  try {
    await fetchCurrentUser(true)
  } catch (error) {
    clearAuthState()
  } finally {
    authChecking.value = false
  }
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  const valid = await loginFormRef.value.validate().catch(() => false)
  if (!valid) return

  loginLoading.value = true
  try {
    const payload = await requestApi('/api/auth/login/', {
      method: 'POST',
      auth: false,
      skipAuthError: true,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: loginForm.username,
        password: loginForm.password,
      }),
    })
    localStorage.setItem(TOKEN_KEY, payload.access)
    await fetchCurrentUser()
    fileReviewMode.value = 'history'
    await fetchReviewHistory()
    loginForm.password = ''
    ElMessage.success('登录成功')
  } catch (error) {
    clearAuthState()
    ElMessage.error(error.message || '登录失败，请检查用户名和密码')
  } finally {
    loginLoading.value = false
  }
}

const handleLogout = () => {
  clearAuthState()
  knowledgeLoaded.value = false
  portalChecklists.value = []
  portalRules.value = []
  currentChecklist.value = null
  selectedReviewChecklist.value = null
  checklistPickerItems.value = []
  ElMessage.success('已退出登录')
}

const formatDateTime = (value) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = (num) => String(num).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

const getRuleTypeText = (type) => {
  const map = {
    general: '通用规则',
    industry: '行业规则',
    enterprise: '企业规则',
  }
  return map[type] || type || ''
}

const getRuleCategory = (rule) => {
  return rule?.category || getRuleTypeText(rule?.rule_type) || '未分类'
}

const getRiskText = (level) => {
  const map = {
    high: '高风险',
    medium: '中风险',
    low: '低风险',
  }
  return map[level] || level || '未设置'
}

const getRiskTagType = (level) => {
  const map = {
    high: 'danger',
    medium: 'warning',
    low: 'success',
  }
  return map[level] || 'info'
}

const getReviewStatusText = (status) => {
  const map = {
    processing: '审查中',
    completed: '已完成',
    failed: '失败',
  }
  return map[status] || status || '未知'
}

const getReviewStatusTagType = (status) => {
  const map = {
    processing: 'warning',
    completed: 'success',
    failed: 'danger',
  }
  return map[status] || 'info'
}

const fetchReviewHistory = async () => {
  if (!isAuthenticated.value) return
  reviewHistoryLoading.value = true
  try {
    const params = new URLSearchParams({
      page: String(reviewHistoryPagination.page),
      page_size: String(reviewHistoryPagination.pageSize),
      ordering: '-created_at',
    })
    const search = reviewHistoryKeyword.value.trim()
    if (search) params.set('search', search)
    const payload = await fetchJson(`/api/portal/reviews/history/?${params.toString()}`)
    reviewHistoryItems.value = payload.results || []
    reviewHistoryPagination.total = payload.count || 0
  } catch (error) {
    ElMessage.error(error.message || '获取审查历史失败')
  } finally {
    reviewHistoryLoading.value = false
  }
}

const handleReviewHistorySearch = () => {
  reviewHistoryPagination.page = 1
  fetchReviewHistory()
}

const startNewReview = () => {
  resetReviewWorkspace()
  fileReviewMode.value = 'review'
}

const openReviewHistory = () => {
  fileReviewMode.value = 'history'
  fetchReviewHistory()
}

const openReviewRecord = async (row) => {
  if (!row?.id) return
  reviewHistoryLoading.value = true
  try {
    const record = await fetchJson(`/api/portal/reviews/history/${row.id}/`)
    let documentPayload = null
    try {
      const preview = await fetchJson(`/api/portal/documents/${record.document_id}/preview/`)
      documentPayload = preview.document
    } catch (error) {
      documentPayload = {
        id: record.document_id,
        name: record.document_name,
        page_count: record.page_count || 0,
        word_count: record.word_count || 0,
        pages: [],
      }
    }

    resetReviewWorkspace()
    uploadedDocument.value = documentPayload
    selectedReviewChecklist.value = {
      id: record.checklist_id,
      name: record.checklist_name,
      rule_count: record.rule_count,
      updated_at: record.updated_at,
      rules: [],
    }
    reviewResult.value = {
      success: record.status === 'completed',
      model: record.model,
      document: {
        id: record.document_id,
        name: record.document_name,
        page_count: record.page_count,
      },
      checklist: {
        id: record.checklist_id,
        name: record.checklist_name,
        rule_count: record.rule_count,
      },
      summary: record.summary || {},
      pages: record.pages || [],
    }
    reviewError.value = record.status === 'failed' ? record.error_message || '历史审查失败' : ''
    activeReviewPages.value = (record.pages || [])
      .slice(0, 2)
      .map((page) => String(page.page_number))
    overviewText.value = '已加载历史审查记录，可查看文档预览和已保存的审查结果。'
    fileReviewMode.value = 'review'
    currentPage.value = 1
  } catch (error) {
    ElMessage.error(error.message || '获取审查记录失败')
  } finally {
    reviewHistoryLoading.value = false
  }
}

const fetchPortalChecklists = async () => {
  checklistLoading.value = true
  try {
    const params = new URLSearchParams({
      page: String(checklistPagination.page),
      page_size: String(checklistPagination.pageSize),
    })
    const search = knowledgeMode.value === 'checklists' ? knowledgeKeyword.value.trim() : ''
    if (search) params.set('search', search)
    const payload = await fetchJson(`/api/portal/knowledge/checklists/?${params.toString()}`)
    portalChecklists.value = payload.results || []
    checklistPagination.total = payload.count || 0
  } catch (error) {
    ElMessage.error(error.message || '获取审查清单失败')
  } finally {
    checklistLoading.value = false
  }
}

const fetchChecklistPickerItems = async () => {
  checklistPickerLoading.value = true
  try {
    const params = new URLSearchParams({
      page: String(checklistPickerPagination.page),
      page_size: String(checklistPickerPagination.pageSize),
    })
    const search = checklistPickerKeyword.value.trim()
    if (search) params.set('search', search)
    const payload = await fetchJson(`/api/portal/knowledge/checklists/?${params.toString()}`)
    checklistPickerItems.value = payload.results || []
    checklistPickerPagination.total = payload.count || 0
  } catch (error) {
    ElMessage.error(error.message || '获取审查清单失败')
  } finally {
    checklistPickerLoading.value = false
  }
}

const openChecklistPicker = async () => {
  checklistPickerVisible.value = true
  if (!checklistPickerItems.value.length) {
    await fetchChecklistPickerItems()
  }
}

const handleChecklistPickerSearch = () => {
  checklistPickerPagination.page = 1
  fetchChecklistPickerItems()
}

const selectReviewChecklist = async (row) => {
  checklistPickerLoading.value = true
  try {
    const payload = await fetchJson(`/api/portal/knowledge/checklists/${row.id}/`)
    selectedReviewChecklist.value = payload
    clearReviewResult(true)
    checklistPickerVisible.value = false
    ElMessage.success('已选择审查清单')
  } catch (error) {
    ElMessage.error(error.message || '选择审查清单失败')
  } finally {
    checklistPickerLoading.value = false
  }
}

const applySelectedChecklist = async () => {
  if (!uploadedDocument.value) {
    ElMessage.warning('请先上传文档')
    return
  }
  if (!selectedReviewChecklist.value) {
    ElMessage.warning('请先从知识库选择审查清单')
    return
  }

  const requestId = ++reviewRequestId
  reviewLoading.value = true
  reviewError.value = ''
  reviewResult.value = null
  activeReviewPages.value = []

  try {
    const payload = await requestApi('/api/portal/reviews/rule-review/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        document_id: uploadedDocument.value.id,
        checklist_id: selectedReviewChecklist.value.id,
      }),
    })
    if (!payload.success) throw new Error(payload.detail || payload.error || payload.message || '规则审查失败')
    if (requestId !== reviewRequestId) return
    reviewResult.value = payload
    activeReviewPages.value = (payload.pages || [])
      .slice(0, 2)
      .map((page) => String(page.page_number))
    fetchReviewHistory()
    ElMessage.success('规则审查完成')
  } catch (error) {
    if (requestId !== reviewRequestId) return
    reviewError.value = error.message || '规则审查失败'
    ElMessage.error(reviewError.value)
  } finally {
    if (requestId === reviewRequestId) {
      reviewLoading.value = false
    }
  }
}

const fetchPortalRules = async () => {
  rulesLoading.value = true
  try {
    const payload = await fetchJson('/api/portal/knowledge/rules/?page=1&page_size=1000&ordering=-priority')
    portalRules.value = payload.results || []
    if (!ruleCategories.value.some((category) => category.name === activeLibraryCategory.value)) {
      activeLibraryCategory.value = '全部'
    }
  } catch (error) {
    ElMessage.error(error.message || '获取审查规则失败')
  } finally {
    rulesLoading.value = false
  }
}

const loadKnowledgeData = async () => {
  if (knowledgeLoaded.value) return
  await Promise.all([fetchPortalChecklists(), fetchPortalRules()])
  knowledgeLoaded.value = true
}

const switchKnowledgeMode = (mode) => {
  knowledgeMode.value = mode
  knowledgeKeyword.value = ''
  if (mode === 'checklists') {
    checklistPagination.page = 1
    fetchPortalChecklists()
  } else if (!portalRules.value.length) {
    fetchPortalRules()
  }
}

const handleKnowledgeSearch = () => {
  if (knowledgeMode.value === 'checklists') {
    checklistPagination.page = 1
    fetchPortalChecklists()
  }
}

const openChecklistDetail = async (row) => {
  checklistDetailVisible.value = true
  checklistDetailLoading.value = true
  currentChecklist.value = null
  selectedChecklistRuleId.value = null
  try {
    const payload = await fetchJson(`/api/portal/knowledge/checklists/${row.id}/`)
    currentChecklist.value = payload
    selectedChecklistRuleId.value = payload.rules?.[0]?.id || null
  } catch (error) {
    checklistDetailVisible.value = false
    ElMessage.error(error.message || '获取清单详情失败')
  } finally {
    checklistDetailLoading.value = false
  }
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
    const payload = await requestApi('/api/portal/ai/document-overview/', {
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
    if (!payload.success) throw new Error(payload.detail || payload.error || payload.message || '文档概览生成失败')
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
    const payload = await requestApi('/api/portal/documents/upload/', {
      method: 'POST',
      body: formData,
    })
    if (!payload.success) throw new Error(payload.detail || payload.error || payload.message || '文件上传失败')
    uploadedDocument.value = payload.document
    clearReviewResult(true)
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
.portal-auth-page {
  --portal-primary: #1677ff;
  --portal-primary-dark: #0958d9;
  --portal-primary-soft: #edf5ff;
  --portal-border: #e8edf5;
  --portal-text: #1f2937;
  --portal-muted: #667085;
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    linear-gradient(180deg, rgba(22, 119, 255, 0.06), rgba(255, 255, 255, 0) 42%),
    #f6f8fb;
  color: var(--portal-text);
}

.portal-login-card,
.portal-auth-card {
  width: min(420px, 100%);
  border: 1px solid var(--portal-border);
  border-radius: 8px;
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.06);
}

.portal-auth-card {
  padding: 28px;
  text-align: center;
  background: #fff;
}

.portal-auth-card.compact {
  width: min(320px, 100%);
}

.portal-login-header {
  text-align: center;
}

.auth-brand-mark {
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  margin: 0 auto 14px;
  color: #fff;
  font-size: 22px;
  border-radius: 12px;
  background: linear-gradient(150deg, var(--portal-primary), #4096ff);
  box-shadow: 0 12px 24px rgba(22, 119, 255, 0.16);
}

.portal-auth-card .auth-brand-mark .el-icon {
  animation: portal-auth-spin 1s linear infinite;
}

.portal-login-header h1,
.portal-auth-card h1 {
  margin: 0;
  color: var(--portal-text);
  font-size: 20px;
  font-weight: 800;
}

.portal-login-header p,
.portal-auth-card p {
  margin: 6px 0 0;
  color: var(--portal-muted);
  font-size: 13px;
}

.login-submit {
  width: 100%;
  margin-top: 4px;
}

@keyframes portal-auth-spin {
  to {
    transform: rotate(360deg);
  }
}

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
  grid-template-columns: 264px minmax(560px, 1fr) minmax(320px, var(--review-panel-width));
  background: #f6f8fb;
  color: var(--portal-text);
  font-size: 13px;
  overflow: hidden;
  transition: grid-template-columns 0.2s ease;
}

.portal-page.is-sidebar-collapsed {
  grid-template-columns: 72px minmax(560px, 1fr) minmax(320px, var(--review-panel-width));
}

.portal-page.is-knowledge-mode {
  grid-template-columns: 264px minmax(0, 1fr);
}

.portal-page.is-knowledge-mode.is-sidebar-collapsed {
  grid-template-columns: 72px minmax(0, 1fr);
}

.portal-page.is-review-history-mode {
  grid-template-columns: 264px minmax(0, 1fr);
}

.portal-page.is-review-history-mode.is-sidebar-collapsed {
  grid-template-columns: 72px minmax(0, 1fr);
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

.logout-button {
  width: 28px;
  height: 28px;
  min-height: 28px;
  padding: 0;
  margin-left: auto;
  color: #8b95a7;
}

.logout-button:hover {
  color: var(--portal-primary);
  background: var(--portal-primary-soft);
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

.is-sidebar-collapsed .profile-avatar {
  display: none;
}

.is-sidebar-collapsed .logout-button {
  margin-left: 0;
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

.workplace-actions {
  display: flex;
  align-items: center;
  gap: 10px;
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

.review-history-workplace {
  min-width: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #fff;
  overflow: hidden;
}

.review-history-header {
  min-height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 28px;
  border-bottom: 1px solid var(--portal-border);
  background: linear-gradient(180deg, #f9fbff 0%, #fff 100%);
}

.review-history-header span {
  display: block;
  margin-bottom: 5px;
  color: var(--portal-muted);
  font-size: 12px;
  font-weight: 700;
}

.review-history-header h1 {
  margin: 0;
  color: #202638;
  font-size: 18px;
  font-weight: 800;
}

.start-review-button {
  min-width: 112px;
  height: 36px;
  border-radius: 7px;
}

.review-history-section {
  min-height: 0;
  flex: 1;
  overflow: auto;
  padding: 24px 28px 30px;
  background: #fff;
}

.review-history-toolbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}

.review-history-search {
  width: min(460px, 48vw);
}

.review-history-table {
  border: 1px solid #edf0f6;
  border-radius: 8px;
}

.review-history-pagination {
  display: flex;
  justify-content: flex-end;
  padding-top: 18px;
}

.knowledge-workplace {
  min-width: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #fff;
  overflow: hidden;
}

.knowledge-header {
  min-height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 28px;
  border-bottom: 1px solid var(--portal-border);
  background: linear-gradient(180deg, #f9fbff 0%, #fff 100%);
}

.knowledge-header span {
  display: block;
  margin-bottom: 5px;
  color: var(--portal-muted);
  font-size: 12px;
  font-weight: 700;
}

.knowledge-header h1 {
  margin: 0;
  color: #202638;
  font-size: 18px;
  font-weight: 800;
}

.portal-knowledge-tabs {
  min-height: 62px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 0 28px;
  border-bottom: 1px solid var(--portal-border);
  background: #fff;
}

.portal-knowledge-tabs button {
  height: 38px;
  padding: 0 18px;
  color: #2d3443;
  font-size: 14px;
  font-weight: 750;
  border: 0;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
}

.portal-knowledge-tabs button.active {
  color: var(--portal-primary);
  background: var(--portal-primary-soft);
}

.portal-knowledge-section {
  min-height: 0;
  flex: 1;
  overflow: auto;
  padding: 24px 28px 30px;
  background: #fff;
}

.knowledge-list-toolbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}

.knowledge-search {
  width: min(460px, 48vw);
}

.knowledge-table {
  border: 1px solid #edf0f6;
  border-radius: 8px;
}

.knowledge-pagination {
  display: flex;
  justify-content: flex-end;
  padding-top: 18px;
}

.portal-rule-library {
  display: grid;
  grid-template-columns: 240px minmax(360px, 1fr) 340px;
  min-height: calc(100vh - 188px);
  border: 1px solid #e4e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.portal-rule-type-panel,
.portal-library-rule-panel,
.portal-library-detail-panel {
  min-width: 0;
  padding: 22px;
}

.portal-rule-type-panel,
.portal-library-rule-panel {
  border-right: 1px solid #e4e8f0;
}

.portal-panel-title {
  min-height: 36px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.portal-panel-title h2 {
  margin: 0;
  color: #202638;
  font-size: 18px;
  font-weight: 800;
}

.portal-panel-title.with-search {
  align-items: flex-start;
  flex-direction: column;
}

.portal-rule-search {
  width: 100%;
  margin-top: 12px;
}

.portal-rule-type-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 18px;
}

.portal-rule-type-list button {
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  color: #667086;
  font-size: 14px;
  font-weight: 700;
  border: 0;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
}

.portal-rule-type-list button.active {
  color: var(--portal-primary);
  background: var(--portal-primary-soft);
}

.portal-rule-type-list em {
  color: inherit;
  font-size: 11px;
  font-style: normal;
}

.portal-library-rule-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 18px;
}

.portal-library-rule-list button {
  width: 100%;
  padding: 12px 14px;
  text-align: left;
  border: 1px solid #e8ecf3;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
}

.portal-library-rule-list button.active,
.portal-library-rule-list button:hover {
  border-color: #9ec5ff;
  background: #f7fbff;
}

.portal-library-rule-title {
  display: block;
  overflow: hidden;
  color: #202638;
  font-size: 13px;
  font-weight: 800;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.portal-library-rule-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 8px;
  color: var(--portal-muted);
  font-size: 12px;
}

.portal-library-rule-meta > span {
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.portal-empty {
  min-height: 280px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #717b8d;
  text-align: center;
}

.portal-empty .el-icon {
  color: #c6ccd6;
  font-size: 44px;
}

.portal-empty strong {
  color: #333a48;
  font-size: 14px;
}

.portal-empty.compact {
  min-height: 180px;
}

.portal-rule-detail {
  padding-top: 8px;
}

.portal-rule-detail.compact {
  padding-top: 0;
}

.portal-detail-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 18px;
}

.portal-detail-title-row h3 {
  margin: 0;
  color: #202638;
  font-size: 16px;
  font-weight: 800;
}

.portal-rule-detail dl {
  display: grid;
  gap: 12px;
  margin: 0;
}

.portal-rule-detail dl > div {
  padding: 12px 14px;
  border: 1px solid #ebeff5;
  border-radius: 8px;
  background: #fbfcff;
}

.portal-rule-detail dt {
  color: #8a94a6;
  font-size: 12px;
  font-weight: 700;
}

.portal-rule-detail dd {
  margin: 7px 0 0;
  color: #252b38;
  font-size: 12px;
  line-height: 1.6;
  word-break: break-word;
}

.checklist-detail-view {
  min-height: 420px;
}

.checklist-detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 10px;
}

.checklist-detail-header h2 {
  margin: 0;
  color: #202638;
  font-size: 18px;
  font-weight: 800;
}

.checklist-detail-header span,
.checklist-description {
  color: var(--portal-muted);
  font-size: 12px;
}

.checklist-description {
  margin: 0 0 16px;
  line-height: 1.6;
}

.checklist-rule-layout {
  display: grid;
  grid-template-columns: minmax(260px, 0.72fr) minmax(320px, 1fr);
  min-height: 340px;
  border: 1px solid #e4e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.checklist-rule-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
  padding: 18px;
  border-right: 1px solid #e4e8f0;
  background: #fbfcff;
}

.checklist-rule-list button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  padding: 12px 14px;
  text-align: left;
  border: 1px solid #e8ecf3;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
}

.checklist-rule-list button.active,
.checklist-rule-list button:hover {
  border-color: #9ec5ff;
  background: #f7fbff;
}

.checklist-rule-list button > span {
  min-width: 0;
  overflow: hidden;
  color: #202638;
  font-size: 12px;
  font-weight: 800;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.checklist-rule-detail {
  min-width: 0;
  padding: 18px;
}

.checklist-picker {
  min-height: 430px;
}

.checklist-picker-toolbar {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-bottom: 14px;
}

.checklist-picker-search {
  width: min(420px, 56vw);
}

.checklist-picker-table {
  border: 1px solid #edf0f6;
  border-radius: 8px;
}

.checklist-picker-pagination {
  display: flex;
  justify-content: flex-end;
  padding-top: 14px;
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
.overview-card,
.review-result-card {
  margin-bottom: 14px;
  border-color: var(--portal-border);
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
}

.config-card :deep(.el-card__header),
.overview-card :deep(.el-card__header),
.review-result-card :deep(.el-card__header) {
  min-height: 52px;
  padding: 14px 16px;
  border-bottom-color: var(--portal-border);
}

.config-card :deep(.el-card__body),
.overview-card :deep(.el-card__body),
.review-result-card :deep(.el-card__body) {
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
  gap: 10px;
}

.checklist-action {
  min-height: 82px;
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

.selected-checklist-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
  padding: 12px 14px;
  border: 1px solid rgba(22, 119, 255, 0.18);
  border-radius: 8px;
  background: var(--portal-primary-mist);
}

.selected-checklist-card > div {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.selected-checklist-card span,
.selected-checklist-card small {
  color: var(--portal-muted);
  font-size: 11.5px;
}

.selected-checklist-card strong {
  overflow: hidden;
  color: #202638;
  font-size: 13px;
  font-weight: 800;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.selected-rule-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.selected-rule-preview span,
.selected-rule-preview em {
  max-width: 100%;
  overflow: hidden;
  padding: 3px 7px;
  color: #526074;
  font-size: 11px;
  font-style: normal;
  white-space: nowrap;
  text-overflow: ellipsis;
  border-radius: 6px;
  background: #f2f6fb;
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

.review-running,
.review-placeholder,
.review-error {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 66px;
  padding: 12px;
  color: var(--portal-muted);
  font-size: 12px;
  line-height: 1.6;
  border: 1px solid #edf2f7;
  border-radius: 8px;
  background: #fbfdff;
}

.review-running {
  color: var(--portal-primary);
  border-color: rgba(22, 119, 255, 0.18);
  background: var(--portal-primary-mist);
}

.review-error {
  color: #b42318;
  border-color: #ffd4d0;
  background: #fff8f7;
}

.review-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.review-summary div {
  min-width: 0;
  padding: 10px;
  border: 1px solid #edf2f7;
  border-radius: 8px;
  background: #fbfdff;
}

.review-summary span {
  display: block;
  color: var(--portal-muted);
  font-size: 11px;
}

.review-summary strong {
  display: block;
  margin-top: 5px;
  color: #202638;
  font-size: 16px;
  font-weight: 800;
  line-height: 1.2;
}

.review-pages {
  margin-top: 12px;
}

.review-pages :deep(.el-collapse-item__header) {
  min-height: 42px;
  height: auto;
  line-height: 1.4;
}

.review-pages :deep(.el-collapse-item__content) {
  padding-bottom: 14px;
}

.review-page-title {
  width: 100%;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding-right: 8px;
  color: #202638;
  font-size: 12px;
  font-weight: 750;
}

.review-page-title em {
  margin-left: auto;
  color: var(--portal-muted);
  font-size: 11px;
  font-style: normal;
  font-weight: 600;
}

.review-page-summary {
  margin: 0 0 10px;
  padding: 9px 10px;
  color: #4f5b70;
  font-size: 12px;
  line-height: 1.6;
  border-radius: 7px;
  background: #f7f9fc;
}

.review-issue-list {
  display: grid;
  gap: 10px;
}

.review-issue {
  padding: 11px 12px;
  border: 1px solid #e8ecf3;
  border-radius: 8px;
  background: #fff;
}

.review-issue header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.review-issue header strong {
  min-width: 0;
  color: #202638;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.5;
  word-break: break-word;
}

.review-issue p {
  margin: 8px 0 0;
  color: #2d3443;
  font-size: 12px;
  line-height: 1.65;
  word-break: break-word;
}

.review-issue dl {
  display: grid;
  gap: 8px;
  margin: 10px 0 0;
}

.review-issue dl > div {
  padding: 9px 10px;
  border-radius: 7px;
  background: #f8fafc;
}

.review-issue dt {
  color: var(--portal-muted);
  font-size: 11px;
  font-weight: 700;
}

.review-issue dd {
  margin: 5px 0 0;
  color: #364154;
  font-size: 12px;
  line-height: 1.6;
  word-break: break-word;
}

.review-page-empty {
  padding: 10px 12px;
  color: var(--portal-muted);
  font-size: 12px;
  line-height: 1.6;
  border-radius: 7px;
  background: #f7f9fc;
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

/* Enterprise portal visual refresh: preserve IA, tighten hierarchy and reduce template-style gloss. */
.portal-auth-page {
  --portal-primary: #1d4ed8;
  --portal-primary-dark: #1e3a8a;
  --portal-primary-soft: #eaf2ff;
  --portal-border: #dbe4f0;
  --portal-text: #172033;
  --portal-muted: #64748b;
  background:
    linear-gradient(180deg, #f8fafc 0%, #eef3f8 100%);
}

.portal-login-card,
.portal-auth-card {
  border-color: rgba(148, 163, 184, 0.28);
  border-radius: 12px;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.10);
}

.portal-login-card :deep(.el-card__header) {
  padding: 28px 28px 18px;
  border-bottom: 0;
}

.portal-login-card :deep(.el-card__body) {
  padding: 18px 28px 30px;
}

.auth-brand-mark {
  border-radius: 11px;
  background: #1d4ed8;
  box-shadow: 0 14px 32px rgba(29, 78, 216, 0.20);
}

.portal-page {
  --portal-primary: #1d4ed8;
  --portal-primary-dark: #1e3a8a;
  --portal-primary-soft: #eaf2ff;
  --portal-primary-mist: #f8fafc;
  --portal-accent: #2563eb;
  --portal-success: #168a5b;
  --portal-success-soft: #edf8f2;
  --portal-lavender: #5f6f89;
  --portal-lavender-soft: #f3f6fa;
  --portal-border: #dbe4f0;
  --portal-border-strong: #c8d3e2;
  --portal-text: #172033;
  --portal-muted: #64748b;
  --portal-faint: #94a3b8;
  --portal-app-bg: #ffffff;
  --portal-surface: #ffffff;
  --portal-surface-subtle: #f7f8fa;
  --portal-radius-card: 10px;
  --portal-radius-control: 8px;
  --portal-card-shadow: 0 18px 44px rgba(15, 23, 42, 0.08);
  --portal-soft-shadow: 0 10px 26px rgba(15, 23, 42, 0.055);
  background: var(--portal-app-bg);
  color: var(--portal-text);
}

.portal-page :deep(.el-button) {
  border-radius: var(--portal-radius-control);
  font-weight: 650;
  transition:
    transform 0.14s ease,
    background-color 0.18s ease,
    border-color 0.18s ease,
    box-shadow 0.18s ease;
}

.portal-page :deep(.el-button:active) {
  transform: translateY(1px);
}

.portal-page :deep(.el-button--primary:not(.is-link):not(.is-text)) {
  border-color: var(--portal-primary);
  background: var(--portal-primary);
  box-shadow: 0 8px 18px rgba(29, 78, 216, 0.16);
}

.portal-page :deep(.el-button--primary:not(.is-link):not(.is-text):hover),
.portal-page :deep(.el-button--primary:not(.is-link):not(.is-text):focus) {
  border-color: var(--portal-primary-dark);
  background: var(--portal-primary-dark);
  box-shadow: 0 10px 24px rgba(29, 78, 216, 0.18);
}

.portal-page :deep(.el-button.is-link),
.portal-page :deep(.el-button.is-text) {
  width: auto;
  min-width: 0;
  height: auto;
  padding: 0;
  border: 0;
  background: transparent;
  box-shadow: none;
}

.portal-page :deep(.el-button--primary.is-link),
.portal-page :deep(.el-button--primary.is-text) {
  color: var(--portal-primary);
}

.portal-page :deep(.el-button--primary.is-link:hover),
.portal-page :deep(.el-button--primary.is-link:focus),
.portal-page :deep(.el-button--primary.is-text:hover),
.portal-page :deep(.el-button--primary.is-text:focus) {
  color: var(--portal-primary-dark);
  background: transparent;
  box-shadow: none;
}

.portal-page :deep(.el-button.is-disabled) {
  box-shadow: none;
  transform: none;
}

.portal-page :deep(.el-input__wrapper),
.portal-page :deep(.el-select__wrapper) {
  border-radius: var(--portal-radius-control);
  box-shadow: 0 0 0 1px var(--portal-border) inset;
  background: #fff;
}

.portal-page :deep(.el-input__wrapper.is-focus),
.portal-page :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 1px var(--portal-primary) inset,
    0 0 0 3px rgba(29, 78, 216, 0.11);
}

.portal-page :deep(.el-tag) {
  border-radius: 999px;
  font-weight: 650;
}

.portal-page :deep(.el-table) {
  --el-table-header-bg-color: #f8fafc;
  --el-table-header-text-color: #475569;
  --el-table-row-hover-bg-color: #f5f8fc;
  color: #263244;
  border-radius: var(--portal-radius-card);
}

.portal-page :deep(.el-table th.el-table__cell) {
  height: 44px;
  background: #f8fafc;
  border-bottom-color: #dbe4f0;
  font-weight: 750;
}

.portal-page :deep(.el-table td.el-table__cell) {
  height: 48px;
  border-bottom-color: #edf2f7;
}

.portal-page :deep(.el-pagination button),
.portal-page :deep(.el-pagination .el-pager li) {
  border-radius: 7px;
}

.portal-sidebar {
  padding: 20px 12px;
  border-right: 1px solid #e2e8f0;
  background: #f6f8fc;
  box-shadow: none;
}

.portal-brand {
  min-height: 42px;
  margin-bottom: 18px;
  padding: 0 4px;
}

.brand-mark {
  width: 36px;
  height: 36px;
  color: #1d4ed8;
  font-size: 18px;
  border: 1px solid #dce6f4;
  border-radius: 10px;
  background: #ffffff;
  box-shadow: none;
}

.brand-copy strong {
  color: #182235;
  font-size: 20px;
  letter-spacing: 0;
}

.brand-copy span {
  color: #8a97ab;
  font-size: 11px;
}

.sidebar-toggle {
  width: 28px;
  height: 28px;
  color: #7b8798;
  border-color: #dce4ef;
  background: #ffffff;
}

.sidebar-toggle:hover {
  color: var(--portal-primary);
  border-color: #bfd2f5;
  background: #f0f5ff;
}

.global-nav {
  gap: 4px;
}

.nav-item {
  position: relative;
  height: 40px;
  padding: 0 10px;
  color: #56657a;
  border: 0;
  border-radius: 8px;
  background: transparent;
  transition:
    color 0.18s ease,
    background-color 0.18s ease,
    transform 0.14s ease;
}

.nav-item::before {
  content: '';
  position: absolute;
  top: 9px;
  bottom: 9px;
  left: 0;
  width: 3px;
  border-radius: 999px;
  background: transparent;
}

.nav-item .el-icon {
  color: #8a97ab;
  font-size: 17px;
}

.nav-item:hover {
  color: #182235;
  background: #ffffff;
}

.nav-item:hover .el-icon {
  color: var(--portal-primary);
}

.nav-item:active {
  transform: translateY(1px);
}

.nav-item.active {
  color: var(--portal-primary);
  border-color: transparent;
  background: #eaf2ff;
  box-shadow: none;
}

.nav-item.active::before {
  background: var(--portal-primary);
}

.nav-item.active .el-icon {
  color: var(--portal-primary);
}

.profile-card {
  gap: 9px;
  margin: auto 2px 0;
  padding: 12px 4px 0;
  border: 0;
  border-top: 1px solid #e5ebf3;
  border-radius: 0;
  background: transparent;
}

.profile-avatar {
  --el-avatar-bg-color: #edf2f8;
  color: #52627a;
}

.profile-copy span {
  color: #283449;
}

.profile-copy strong {
  color: #8a97ab;
}

.logout-button {
  color: #8a97ab;
}

.logout-button:hover {
  color: var(--portal-primary);
  background: #eaf2ff;
}

.review-history-workplace,
.knowledge-workplace,
.document-workplace {
  background: #ffffff;
}

.workplace-toolbar,
.document-status,
.review-history-header,
.knowledge-header,
.portal-knowledge-tabs {
  background: #ffffff;
  border-color: var(--portal-border);
}

.review-history-header,
.knowledge-header {
  min-height: 68px;
  background: #ffffff;
}

.review-history-header span,
.knowledge-header span {
  color: #64748b;
  font-weight: 700;
}

.review-history-header h1,
.knowledge-header h1,
.portal-panel-title h2 {
  color: var(--portal-text);
  font-weight: 800;
  letter-spacing: 0;
}

.review-history-section,
.portal-knowledge-section {
  background: #ffffff;
}

.review-history-table,
.knowledge-table,
.checklist-picker-table {
  overflow: hidden;
  border-color: var(--portal-border);
  border-radius: var(--portal-radius-card);
  background: #fff;
  box-shadow: var(--portal-soft-shadow);
}

.review-history-empty {
  min-height: 220px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 10px;
  color: var(--portal-muted);
}

.review-history-empty .el-icon {
  color: #c3cede;
  font-size: 34px;
}

.review-history-empty strong {
  color: #42526a;
  font-size: 13px;
}

.portal-knowledge-tabs {
  min-height: 58px;
  gap: 8px;
}

.portal-knowledge-tabs button {
  height: 34px;
  border-radius: 8px;
  color: #475569;
}

.portal-knowledge-tabs button:hover {
  color: var(--portal-primary);
  background: #f1f5fb;
}

.portal-knowledge-tabs button.active {
  color: var(--portal-primary);
  background: var(--portal-primary-soft);
  box-shadow: inset 0 0 0 1px rgba(29, 78, 216, 0.12);
}

.portal-rule-library,
.checklist-rule-layout {
  border-color: var(--portal-border);
  border-radius: var(--portal-radius-card);
  background: #fff;
  box-shadow: var(--portal-soft-shadow);
}

.portal-rule-type-panel,
.portal-library-rule-panel,
.portal-library-detail-panel,
.checklist-rule-list,
.checklist-rule-detail {
  background: #ffffff;
}

.portal-rule-type-panel,
.portal-library-rule-panel,
.checklist-rule-list {
  border-color: var(--portal-border);
}

.portal-rule-type-list button,
.portal-library-rule-list button,
.checklist-rule-list button {
  border-radius: 8px;
  transition:
    color 0.18s ease,
    background-color 0.18s ease,
    border-color 0.18s ease,
    transform 0.14s ease;
}

.portal-rule-type-list button:hover,
.portal-library-rule-list button:hover,
.checklist-rule-list button:hover {
  transform: translateY(-1px);
}

.portal-rule-type-list button.active,
.portal-library-rule-list button.active,
.checklist-rule-list button.active {
  color: var(--portal-primary);
  border-color: rgba(29, 78, 216, 0.24);
  background: var(--portal-primary-soft);
}

.portal-rule-detail dl > div {
  border-color: #e1e8f2;
  border-radius: 8px;
  background: #f8fafc;
}

.document-stage {
  background: #ffffff;
}

.document-paper {
  border-color: #dce5ef;
  border-radius: 4px;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.12);
}

.paper-header {
  color: #64748b;
  border-bottom-color: #e2e8f0;
}

.review-panel {
  border-left-color: var(--portal-border);
  background: #ffffff;
}

.panel-scroll {
  padding: 16px;
}

.workflow-card,
.config-card,
.overview-card,
.review-result-card {
  border-color: var(--portal-border);
  border-radius: var(--portal-radius-card);
  background: #ffffff;
  box-shadow: var(--portal-soft-shadow);
}

.workflow-card {
  padding: 15px 12px 13px;
}

.config-card :deep(.el-card__header),
.overview-card :deep(.el-card__header),
.review-result-card :deep(.el-card__header) {
  min-height: 48px;
  background: #fbfcfe;
}

.card-title {
  color: var(--portal-text);
}

.card-title .el-icon {
  color: var(--portal-primary);
}

.checklist-action {
  border-color: var(--portal-border);
  border-radius: var(--portal-radius-card);
  box-shadow: none;
  transition:
    border-color 0.18s ease,
    background-color 0.18s ease,
    transform 0.14s ease;
}

.checklist-action:hover,
.checklist-action.active {
  border-color: rgba(29, 78, 216, 0.28);
  background: #f8fbff;
  transform: translateY(-1px);
  box-shadow: none;
}

.action-icon {
  border-radius: 8px;
  background: var(--portal-primary-soft);
}

.selected-checklist-card,
.overview-copy,
.review-running,
.review-placeholder,
.review-error,
.review-summary div,
.review-page-summary,
.review-page-empty,
.review-issue dl > div {
  border-radius: 8px;
}

.selected-checklist-card {
  border-color: rgba(29, 78, 216, 0.16);
  background: #f8fbff;
}

.overview-copy,
.review-summary div,
.review-page-summary,
.review-page-empty {
  border-color: #e2e8f0;
  background: #f8fafc;
}

.review-issue {
  border-color: #e2e8f0;
  border-radius: 9px;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.035);
}

.review-footer {
  border-top-color: var(--portal-border);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 -10px 26px rgba(15, 23, 42, 0.06);
}

.generate-button,
.upload-button,
.start-review-button {
  border-radius: var(--portal-radius-control);
  box-shadow: 0 8px 18px rgba(29, 78, 216, 0.16);
}

.page-control {
  border-color: var(--portal-border);
  background: #ffffff;
}

.page-action:hover:not(:disabled) {
  color: var(--portal-primary);
  background: var(--portal-primary-soft);
}

.document-upload-dialog {
  border-radius: 12px;
}

.upload-drop-zone {
  background: #f8fafc;
}

.upload-drop-zone:hover,
.upload-drop-zone.is-dragover {
  border-color: rgba(29, 78, 216, 0.34);
  background: #f3f7fc;
}

.upload-icon-bubble {
  border-radius: 10px;
  box-shadow: 0 12px 26px rgba(29, 78, 216, 0.12);
}

@media (prefers-reduced-motion: reduce) {
  .portal-page *,
  .portal-auth-page * {
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }
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
    grid-template-columns: 236px minmax(460px, 1fr) minmax(320px, var(--review-panel-width));
  }

  .portal-page.is-sidebar-collapsed {
    grid-template-columns: 72px minmax(460px, 1fr) minmax(320px, var(--review-panel-width));
  }

  .portal-page.is-knowledge-mode {
    grid-template-columns: 236px minmax(0, 1fr);
  }

  .portal-page.is-knowledge-mode.is-sidebar-collapsed {
    grid-template-columns: 72px minmax(0, 1fr);
  }

  .portal-page.is-review-history-mode {
    grid-template-columns: 236px minmax(0, 1fr);
  }

  .portal-page.is-review-history-mode.is-sidebar-collapsed {
    grid-template-columns: 72px minmax(0, 1fr);
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

  .portal-rule-library {
    grid-template-columns: 220px minmax(340px, 1fr) 320px;
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

  .portal-page.is-knowledge-mode,
  .portal-page.is-knowledge-mode.is-sidebar-collapsed,
  .portal-page.is-review-history-mode,
  .portal-page.is-review-history-mode.is-sidebar-collapsed {
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
  .knowledge-workplace,
  .review-history-workplace,
  .review-panel {
    height: auto;
    min-height: 640px;
  }

  .portal-rule-library {
    grid-template-columns: 220px 1fr;
  }

  .portal-library-rule-panel {
    border-right: 0;
  }

  .portal-library-detail-panel {
    grid-column: 1 / -1;
    border-top: 1px solid #e4e8f0;
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
  .review-history-header,
  .knowledge-header,
  .document-status {
    align-items: stretch;
    flex-direction: column;
    padding: 14px 16px;
  }

  .document-workplace {
    grid-template-rows: auto minmax(0, 1fr) auto;
  }

  .portal-knowledge-tabs {
    flex-wrap: wrap;
    padding: 14px 16px;
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

  .portal-knowledge-section {
    padding: 18px 16px 24px;
  }

  .review-history-section {
    padding: 18px 16px 24px;
  }

  .knowledge-list-toolbar {
    justify-content: stretch;
  }

  .review-history-toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .workplace-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .start-review-button,
  .workplace-actions .el-button {
    width: 100%;
  }

  .knowledge-search,
  .review-history-search {
    width: 100%;
  }

  .portal-rule-library,
  .checklist-rule-layout {
    grid-template-columns: 1fr;
  }

  .portal-rule-type-panel,
  .portal-library-rule-panel,
  .checklist-rule-list {
    border-right: 0;
    border-bottom: 1px solid #e4e8f0;
  }

  .portal-library-detail-panel {
    grid-column: auto;
  }

  .checklist-actions {
    grid-template-columns: 1fr;
  }
}
</style>
