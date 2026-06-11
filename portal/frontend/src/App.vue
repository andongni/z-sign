<template>
  <div class="portal-page">
    <aside class="portal-sidebar">
      <div class="portal-brand">
        <div class="brand-mark" aria-hidden="true">
          <el-icon><Connection /></el-icon>
        </div>
        <div class="brand-copy">
          <strong>智审</strong>
          <span>AI Legal Review</span>
        </div>
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
          <el-tag class="file-tag" effect="plain">
            <el-icon><DocumentChecked /></el-icon>
            {{ currentFileName }}
          </el-tag>
          <span>智能审查任务</span>
        </div>
        <el-button type="primary" class="upload-button">
          <el-icon><Plus /></el-icon>
          上传文档
        </el-button>
      </header>

      <section class="document-stage" aria-label="合同文档预览">
        <div class="paper-scale-shell" :style="{ '--preview-scale': previewScale }">
          <article class="document-paper">
            <div class="paper-header">
              <span>合同编号: FR-SALE-2026-0611</span>
              <span>买卖合同</span>
            </div>
            <h1>设备采购及服务合同</h1>
            <p class="paper-intro">
              甲乙双方依据《中华人民共和国民法典》及相关法律法规，就智能检测设备采购、安装调试、售后服务等事项达成本合同。
            </p>
            <section v-for="section in documentSections" :key="section.title" class="contract-section">
              <h2>{{ section.title }}</h2>
              <p v-html="section.content"></p>
            </section>
            <div class="risk-note">
              <el-icon><Warning /></el-icon>
              AI 已识别 4 处核心条款需要重点关注，黄色标记为当前审查上下文。
            </div>
          </article>
        </div>
      </section>

      <footer class="document-status">
        <div class="status-group">
          <div class="page-control" aria-label="文档分页">
            <button
              class="page-action"
              type="button"
              :disabled="currentPage === 1"
              @click="goPrevPage"
            >
              <span>上一页</span>
              <span class="page-chevron" aria-hidden="true">&lt;</span>
            </button>
            <span class="page-counter">
              <strong>{{ currentPage }}</strong><span>/{{ totalPages }}</span>
            </span>
            <button
              class="page-action"
              type="button"
              :disabled="currentPage === totalPages"
              @click="goNextPage"
            >
              <span class="page-chevron" aria-hidden="true">&gt;</span>
              <span>下一页</span>
            </button>
          </div>
          <span>字数 <strong>2334</strong></span>
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

    <aside class="review-panel">
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
            <el-form-item label="合同类型">
              <el-select v-model="contractType" class="full-control">
                <el-option label="买卖合同" value="sale" />
                <el-option label="服务合同" value="service" />
                <el-option label="租赁合同" value="lease" />
                <el-option label="劳动合同" value="labor" />
              </el-select>
            </el-form-item>

            <el-form-item label="审查立场">
              <el-radio-group v-model="standpoint" class="segmented-group">
                <el-radio-button label="partyA">甲方立场</el-radio-button>
                <el-radio-button label="partyB">乙方立场</el-radio-button>
                <el-radio-button label="neutral">中立立场</el-radio-button>
              </el-radio-group>
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
                  <small>基于合同上下文自动构建</small>
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
              <span>合同概览</span>
            </div>
          </template>

          <div class="overview-copy">
            合同概览生成中，您可以直接点击下方按钮直接生成审查清单，稍后返回查看概览内容
          </div>

          <div class="pipeline">
            <div class="pipeline-track">
              <div class="pipeline-fill"></div>
              <div
                v-for="(stage, index) in pipelineStages"
                :key="stage"
                class="pipeline-node"
                :class="{ done: index < 2, active: index === 2 }"
              >
                <span>
                  <el-icon v-if="index < 2"><Check /></el-icon>
                  <el-icon v-else-if="index === 2" class="spin"><Loading /></el-icon>
                  <span v-else>{{ index + 1 }}</span>
                </span>
                <strong>{{ stage }}</strong>
              </div>
            </div>
            <el-progress :percentage="68" :stroke-width="10" :show-text="false" />
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
import { computed, ref, shallowRef } from 'vue'
import {
  Check,
  Collection,
  Connection,
  Document,
  DocumentChecked,
  Grid,
  Loading,
  MagicStick,
  Memo,
  Minus,
  Operation,
  Plus,
  Reading,
  Warning,
} from '@element-plus/icons-vue'

const activeNav = ref('file-review')
const currentFileName = '设备采购及服务合同.docx'
const contractType = ref('sale')
const standpoint = ref('partyA')
const strictness = ref('strong')
const zoom = ref(75)
const isGenerating = ref(false)
const currentPage = ref(1)
const totalPages = 8
const minZoom = 50
const maxZoom = 125
const zoomStep = 5
const previewScale = computed(() => zoom.value / 100)

const navItems = shallowRef([
  { key: 'file-review', label: '文件审查', icon: Document },
  { key: 'text-reading', label: '文本阅读', icon: Reading },
  { key: 'knowledge-base', label: '知识库', icon: Collection },
])

const documentSections = [
  {
    title: '一、标的与交付',
    content:
      '乙方应于合同生效后 30 日内完成设备交付、安装及验收支持。<mark>如因乙方原因导致交付延迟，每逾期一日按合同总价的 0.3% 支付违约金</mark>，但累计不超过合同总价的 10%。',
  },
  {
    title: '二、付款安排',
    content:
      '甲方在签署合同后支付 30% 预付款，设备到货并经初验合格后支付 50%，最终验收通过后支付尾款。<mark>甲方有权在乙方未完成整改前暂停支付对应款项</mark>。',
  },
  {
    title: '三、质量保证',
    content:
      '乙方保证设备符合技术规格书及国家强制性标准。质保期为最终验收合格之日起 24 个月，质保期内因产品质量导致的维修、更换及运输费用由乙方承担。',
  },
  {
    title: '四、保密与数据安全',
    content:
      '双方应对合作过程中获知的商业秘密、技术资料及业务数据承担保密义务。<mark>未经甲方书面同意，乙方不得向第三方披露、复制或用于本合同以外目的</mark>。',
  },
]

const pipelineStages = ['理解合同', '提取信息', '总结内容', '完成']

const goPrevPage = () => {
  currentPage.value = Math.max(1, currentPage.value - 1)
}

const goNextPage = () => {
  currentPage.value = Math.min(totalPages, currentPage.value + 1)
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
  --portal-primary: #5b52e3;
  --portal-primary-dark: #463fca;
  --portal-primary-soft: #f0efff;
  --portal-purple: #7b61ff;
  --portal-blue: #2563eb;
  --portal-border: #e5e8f2;
  --portal-border-strong: #d9def0;
  --portal-text: #1f2433;
  --portal-muted: #6e778a;
  --portal-faint: #98a1b3;
  --el-font-size-base: 13px;
  --el-font-size-small: 12px;
  --el-component-size: 34px;
  min-height: 100vh;
  display: grid;
  grid-template-columns: 220px minmax(560px, 1fr) 400px;
  background: #f7f8fc;
  color: var(--portal-text);
  font-size: 13px;
  overflow: hidden;
}

.portal-page :deep(.el-button),
.portal-page :deep(.el-input__inner),
.portal-page :deep(.el-select__placeholder),
.portal-page :deep(.el-radio-button__inner),
.portal-page :deep(.el-tag) {
  font-size: 13px;
}

.portal-sidebar {
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 18px 14px;
  border-right: 1px solid var(--portal-border);
  background:
    linear-gradient(180deg, rgba(91, 82, 227, 0.08), rgba(91, 82, 227, 0.02) 34%),
    #f3f4fb;
}

.portal-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 50px;
  margin-bottom: 22px;
}

.brand-mark {
  width: 40px;
  height: 46px;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  color: #fff;
  font-size: 20px;
  clip-path: polygon(50% 0, 90% 15%, 82% 68%, 50% 100%, 18% 68%, 10% 15%);
  background: linear-gradient(150deg, var(--portal-primary), var(--portal-purple));
  box-shadow: 0 14px 30px rgba(91, 82, 227, 0.28);
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

.nav-item:hover {
  color: var(--portal-primary);
  background: rgba(255, 255, 255, 0.72);
}

.nav-item.active {
  color: var(--portal-primary);
  border-color: rgba(91, 82, 227, 0.16);
  background: #fff;
  box-shadow: 0 10px 26px rgba(49, 55, 87, 0.07);
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
  --el-avatar-bg-color: var(--portal-primary);
  flex: 0 0 auto;
  font-size: 11px;
  font-weight: 700;
  opacity: 0.82;
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

.document-workplace {
  min-width: 0;
  height: 100vh;
  display: grid;
  grid-template-rows: 64px minmax(0, 1fr) 52px;
  background:
    linear-gradient(180deg, #ffffff 0, #ffffff 64px, #f8f9fc 64px),
    #f8f9fc;
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
  border-color: rgba(91, 82, 227, 0.2);
  background: var(--portal-primary-soft);
}

.upload-button {
  min-width: 124px;
  height: 36px;
  border-color: var(--portal-primary);
  background: var(--portal-primary);
  box-shadow: 0 12px 24px rgba(91, 82, 227, 0.2);
}

.upload-button:hover,
.upload-button:focus {
  border-color: var(--portal-primary-dark);
  background: var(--portal-primary-dark);
}

.document-stage {
  --paper-base-width: 880px;
  --paper-base-height: 1106px;
  --paper-pad-y: 64px;
  --paper-pad-x: 72px;
  min-height: 0;
  overflow: auto;
  padding: 26px 28px 34px;
  background:
    linear-gradient(90deg, rgba(214, 219, 234, 0.48) 1px, transparent 1px) 0 0 / 22px 22px,
    linear-gradient(0deg, rgba(214, 219, 234, 0.48) 1px, transparent 1px) 0 0 / 22px 22px,
    #f8f9fc;
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
  border: 1px solid #edf0f7;
  background: #fff;
  box-shadow: 0 20px 46px rgba(35, 45, 80, 0.14);
  transform: scale(var(--preview-scale));
  transform-origin: top left;
  transition: transform 0.18s ease;
}

.paper-header {
  display: flex;
  justify-content: space-between;
  color: #8a93a5;
  font-size: 14.6px;
  border-bottom: 1px solid #edf0f5;
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
  background: linear-gradient(180deg, transparent 18%, rgba(255, 220, 81, 0.68) 18%);
}

.risk-note {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-top: 32px;
  padding: 13px 16px;
  color: #705111;
  font-size: 16px;
  border: 1px solid #f5d66f;
  border-radius: 8px;
  background: #fff8da;
}

.document-status {
  min-width: 0;
  color: var(--portal-muted);
  border-top: 1px solid var(--portal-border);
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
  border: 1px solid #edf0f7;
  border-radius: 8px;
  background: #f8faff;
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
  height: 100vh;
  display: flex;
  flex-direction: column;
  border-left: 1px solid var(--portal-border);
  background: #fbfcff;
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
  cursor: pointer;
}

.checklist-action.active {
  border-color: rgba(91, 82, 227, 0.72);
  background: linear-gradient(180deg, #fff, #f6f5ff);
  box-shadow: 0 12px 26px rgba(91, 82, 227, 0.14);
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
  color: #7a7f8c;
  font-size: 10px;
  font-style: normal;
  border-radius: 5px;
  background: #eef0f5;
}

.overview-copy {
  color: var(--portal-muted);
  font-size: 12px;
  line-height: 1.65;
  padding: 10px 12px;
  border: 1px solid #edf0f7;
  border-radius: 8px;
  background: #f8faff;
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
  background: #e4e8f3;
}

.pipeline-fill {
  right: 37%;
  z-index: 1;
  background: linear-gradient(90deg, var(--portal-primary), #8b7cff);
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
  border-color: var(--portal-primary);
  background: var(--portal-primary);
}

.pipeline-node.done,
.pipeline-node.active {
  color: #3c4354;
}

.spin {
  animation: portal-spin 1s linear infinite;
}

.review-footer {
  padding: 14px 18px 16px;
  border-top: 1px solid var(--portal-border);
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(10px);
}

.generate-button {
  width: 100%;
  height: 44px;
  border-color: var(--portal-primary);
  background: var(--portal-primary);
  box-shadow: 0 14px 28px rgba(91, 82, 227, 0.24);
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
    grid-template-columns: 88px minmax(460px, 1fr) 390px;
  }

  .portal-sidebar {
    padding: 18px 12px;
  }

  .portal-brand {
    justify-content: center;
  }

  .brand-copy,
  .nav-item span,
  .profile-copy {
    display: none;
  }

  .nav-item {
    justify-content: center;
    padding: 0;
  }

  .profile-card {
    justify-content: center;
    padding: 10px 0;
  }
}

@media (max-width: 980px) {
  .portal-page {
    height: auto;
    min-height: 100vh;
    grid-template-columns: 1fr;
    overflow: auto;
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

  .brand-copy,
  .nav-item span,
  .profile-copy {
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

  .profile-card {
    margin: 0;
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
