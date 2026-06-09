<template>
  <div class="knowledge-graph">
    <div class="knowledge-tabs">
      <button
        :class="{ active: workspaceMode === 'checklist' }"
        type="button"
        @click="workspaceMode = 'checklist'"
      >
        文件审查清单
      </button>
      <button
        :class="{ active: workspaceMode === 'rules' }"
        type="button"
        @click="workspaceMode = 'rules'"
      >
        审查规则库
      </button>
    </div>

    <div class="knowledge-workspace">
      <aside class="group-panel">
        <div class="panel-title">
          <strong>规则分组</strong>
          <el-button link type="primary">
            <el-icon><Plus /></el-icon>
            新建
          </el-button>
        </div>
        <div class="group-list">
          <button
            v-for="group in ruleGroups"
            :key="group.value"
            :class="{ active: activeGroup === group.value }"
            type="button"
            @click="activeGroup = group.value"
          >
            <span>{{ group.label }}</span>
            <em v-if="group.count">{{ group.count }}</em>
          </button>
        </div>
      </aside>

      <section class="rules-panel">
        <div class="panel-toolbar">
          <h2>{{ workspaceMode === 'rules' ? '审查规则' : '文件审查清单' }}</h2>
          <div class="toolbar-actions">
            <el-button @click="refreshGraph">
              <el-icon><Upload /></el-icon>
              解析规则文档
            </el-button>
            <el-button type="primary">
              <el-icon><Plus /></el-icon>
              新建规则
            </el-button>
          </div>
        </div>

        <el-input
          v-model="searchKeyword"
          class="rule-search"
          clearable
          placeholder="请输入规则名称或描述关键字以搜索"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <div v-if="workspaceMode === 'checklist'" class="graph-container">
          <v-chart :option="graphOption" autoresize v-loading="graphLoading" />
        </div>

        <div v-else class="rule-list" v-loading="loading">
          <button
            v-for="item in filteredWorkspaceItems"
            :key="`${item.kind}-${item.id}`"
            :class="{ active: selectedItemKey === `${item.kind}-${item.id}` }"
            type="button"
            @click="selectedItemKey = `${item.kind}-${item.id}`"
          >
            <span class="rule-icon">
              <el-icon><Notebook /></el-icon>
            </span>
            <span class="rule-main">
              <strong>{{ item.title }}</strong>
              <small>{{ item.description || item.meta }}</small>
            </span>
            <el-tag size="small">{{ item.type }}</el-tag>
          </button>

          <div v-if="!filteredWorkspaceItems.length" class="empty-state">
            <div class="empty-illustration">
              <el-icon><Box /></el-icon>
            </div>
            <strong>暂无数据</strong>
            <span>点击右上方“新建规则”，创建专属文件审查标准</span>
          </div>
        </div>
      </section>

      <aside class="detail-panel">
        <div class="panel-toolbar compact">
          <h2>规则详情</h2>
          <div class="toolbar-actions">
            <el-button class="icon-button">
              <el-icon><MoreFilled /></el-icon>
            </el-button>
            <el-button :disabled="!selectedItem" class="edit-button">
              <el-icon><EditPen /></el-icon>
              编辑
            </el-button>
          </div>
        </div>

        <div v-if="selectedItem" class="detail-content">
          <el-tag>{{ selectedItem.type }}</el-tag>
          <h3>{{ selectedItem.title }}</h3>
          <p>{{ selectedItem.description || '暂无描述' }}</p>
          <dl>
            <div>
              <dt>来源</dt>
              <dd>{{ selectedItem.source }}</dd>
            </div>
            <div>
              <dt>编码</dt>
              <dd>{{ selectedItem.code || '未设置' }}</dd>
            </div>
            <div>
              <dt>更新时间</dt>
              <dd>{{ selectedItem.date || '暂无' }}</dd>
            </div>
          </dl>
        </div>

        <div v-else class="detail-empty">
          <span>点击“新建规则”开始创建审查规则</span>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { GraphChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

use([
  CanvasRenderer,
  GraphChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
])

const loading = ref(false)
const graphLoading = ref(false)
const workspaceMode = ref('rules')
const activeGroup = ref('cooperation')
const searchKeyword = ref('')
const selectedItemKey = ref('')
const entities = ref([])
const regulations = ref([])
const cases = ref([])
const relations = ref([])

const groupLabels = [
  ['cooperation', '合作合同'],
  ['custom', '自定义场景'],
  ['sales', '买卖合同'],
  ['utilities', '供用电、水、气、热力...'],
  ['gift', '赠与合同'],
  ['loan', '借款合同'],
  ['lease', '租赁合同'],
  ['finance', '融资租赁合同'],
  ['contracting', '承揽合同'],
  ['construction', '建设工程合同'],
  ['transport', '运输合同'],
  ['technology', '技术合同'],
  ['custody', '保管合同'],
]

const workspaceItems = computed(() => {
  const entityItems = entities.value.map(item => ({
    id: item.id,
    kind: 'entity',
    group: 'cooperation',
    title: item.entity_name,
    type: item.entity_type || '主体',
    code: item.entity_code,
    source: item.source || '主体库',
    date: item.created_at,
    meta: item.entity_code || item.entity_type || '主体信息',
    description: item.description,
  }))

  const regulationItems = regulations.value.map(item => ({
    id: item.id,
    kind: 'regulation',
    group: 'custom',
    title: item.title,
    type: item.regulation_type || '法规',
    code: item.regulation_no,
    source: item.source_url || '法律法规',
    date: item.publish_date,
    meta: item.regulation_no || item.regulation_type || '法律法规',
    description: item.content,
  }))

  const caseItems = cases.value.map(item => ({
    id: item.id,
    kind: 'case',
    group: 'sales',
    title: item.case_title,
    type: item.case_type || '案例',
    code: item.case_no,
    source: item.court || '案例库',
    date: item.judge_date,
    meta: item.case_no || item.court || '案例',
    description: item.case_summary || item.case_content,
  }))

  return [...entityItems, ...regulationItems, ...caseItems]
})

const ruleGroups = computed(() => {
  return groupLabels.map(([value, label]) => ({
    value,
    label,
    count: workspaceItems.value.filter(item => item.group === value).length,
  }))
})

const filteredWorkspaceItems = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  return workspaceItems.value
    .filter(item => item.group === activeGroup.value)
    .filter(item => {
      if (!keyword) return true
      return [item.title, item.description, item.meta, item.code]
        .filter(Boolean)
        .some(value => String(value).toLowerCase().includes(keyword))
    })
})

const selectedItem = computed(() => {
  return filteredWorkspaceItems.value.find(item => `${item.kind}-${item.id}` === selectedItemKey.value)
})

const fetchEntities = async () => {
  try {
    const response = await api.get('/knowledge/entities/')
    entities.value = response.data.results || []
  } catch (error) {
    ElMessage.error('获取实体列表失败')
  }
}

const fetchRegulations = async () => {
  try {
    const response = await api.get('/knowledge/regulations/')
    regulations.value = response.data.results || []
  } catch (error) {
    ElMessage.error('获取法律法规列表失败')
  }
}

const fetchCases = async () => {
  try {
    const response = await api.get('/knowledge/cases/')
    cases.value = response.data.results || []
  } catch (error) {
    ElMessage.error('获取案例列表失败')
  }
}

const fetchRelations = async () => {
  try {
    const response = await api.get('/knowledge/relations/')
    relations.value = response.data.results || []
  } catch (error) {
    console.error('获取关系列表失败', error)
    relations.value = []
  }
}

const graphOption = computed(() => {
  // 构建节点数据
  const nodes = entities.value.map(entity => ({
    id: entity.id,
    name: entity.entity_name,
    category: entity.entity_type || '其他',
    symbolSize: 30,
    value: entity.entity_name,
  }))

  // 构建边数据
  const links = relations.value.map(relation => ({
    source: relation.source_entity_id,
    target: relation.target_entity_id,
    value: relation.relation_type,
    label: {
      show: true,
      formatter: relation.relation_type,
    },
  }))

  // 按类型分组节点
  const categories = [...new Set(entities.value.map(e => e.entity_type || '其他'))].map(type => ({
    name: type,
  }))

  return {
    title: {
      text: '知识图谱',
      top: 'top',
      left: 'center',
    },
    tooltip: {
      formatter: (params) => {
        if (params.dataType === 'node') {
          return `${params.data.name}<br/>类型: ${params.data.category}`
        } else {
          return `${params.data.source} → ${params.data.target}<br/>关系: ${params.data.value}`
        }
      },
    },
    legend: {
      data: categories.map(c => c.name),
      orient: 'vertical',
      left: 'left',
      top: 'middle',
    },
    series: [
      {
        name: '知识图谱',
        type: 'graph',
        layout: 'force',
        data: nodes,
        links: links,
        categories: categories,
        roam: true,
        label: {
          show: true,
          position: 'right',
          formatter: '{b}',
        },
        labelLayout: {
          hideOverlap: true,
        },
        scaleLimit: {
          min: 0.4,
          max: 2,
        },
        lineStyle: {
          color: 'source',
          curveness: 0.3,
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 10,
          },
        },
        force: {
          repulsion: 1000,
          gravity: 0.1,
          edgeLength: 200,
          layoutAnimation: true,
        },
      },
    ],
  }
})

const refreshGraph = async () => {
  graphLoading.value = true
  loading.value = true
  try {
    await Promise.all([fetchEntities(), fetchRegulations(), fetchCases(), fetchRelations()])
    ElMessage.success('知识库已刷新')
  } catch (error) {
    ElMessage.error('刷新失败')
  } finally {
    graphLoading.value = false
    loading.value = false
  }
}

watch(filteredWorkspaceItems, (items) => {
  if (!items.length) {
    selectedItemKey.value = ''
    return
  }
  if (!items.some(item => `${item.kind}-${item.id}` === selectedItemKey.value)) {
    const first = items[0]
    selectedItemKey.value = `${first.kind}-${first.id}`
  }
})

onMounted(() => {
  refreshGraph()
})
</script>

<style scoped>
.knowledge-graph {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 92px);
  background: #fff;
}

.knowledge-tabs {
  height: 88px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 0 44px;
  border-bottom: 1px solid #e5e9f2;
}

.knowledge-tabs button {
  height: 44px;
  padding: 0 18px;
  color: #2d3443;
  font-size: 18px;
  font-weight: 700;
  border: 0;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
}

.knowledge-tabs button.active {
  color: #1677ff;
  background: #eef6ff;
}

.knowledge-workspace {
  display: grid;
  grid-template-columns: 300px minmax(520px, 1fr) 420px;
  flex: 1;
  min-height: 0;
}

.group-panel,
.rules-panel,
.detail-panel {
  min-width: 0;
  min-height: 0;
  border-right: 1px solid #e5e9f2;
}

.detail-panel {
  border-right: 0;
}

.group-panel {
  padding: 32px 32px 24px 44px;
}

.rules-panel {
  padding: 32px 44px;
}

.detail-panel {
  display: flex;
  flex-direction: column;
  padding: 32px 40px;
}

.panel-title,
.panel-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.panel-title {
  margin-bottom: 20px;
}

.panel-title strong,
.panel-toolbar h2 {
  margin: 0;
  color: #20242e;
  font-size: 21px;
  font-weight: 800;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.panel-toolbar.compact {
  min-height: 42px;
}

.group-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.group-list button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 50px;
  padding: 0 18px;
  color: #687285;
  font-size: 17px;
  font-weight: 650;
  text-align: left;
  border: 0;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
}

.group-list button.active {
  color: #1677ff;
  background: #eef4fb;
}

.group-list em {
  min-width: 24px;
  height: 24px;
  padding: 0 8px;
  color: #1677ff;
  font-size: 12px;
  font-style: normal;
  line-height: 24px;
  text-align: center;
  border-radius: 999px;
  background: #fff;
}

.rule-search {
  margin: 24px 0;
}

.rule-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 460px;
}

.rule-list > button {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  min-height: 74px;
  padding: 14px 16px;
  text-align: left;
  border: 1px solid #e7ebf3;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.rule-list > button:hover,
.rule-list > button.active {
  border-color: #bfdbff;
  background: #f7fbff;
}

.rule-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  color: #1677ff;
  border-radius: 8px;
  background: #eef6ff;
}

.rule-main {
  display: flex;
  flex: 1;
  min-width: 0;
  flex-direction: column;
  gap: 6px;
}

.rule-main strong,
.detail-content h3 {
  color: #20242e;
  font-weight: 800;
}

.rule-main strong {
  overflow: hidden;
  font-size: 16px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.rule-main small {
  overflow: hidden;
  color: #7c8799;
  font-size: 13px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.graph-container {
  width: 100%;
  height: 520px;
  padding: 16px;
  border: 1px solid #e7ebf3;
  border-radius: 8px;
}

.graph-container > div {
  width: 100%;
  height: 100%;
}

.empty-state,
.detail-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  min-height: 440px;
  color: #697386;
  text-align: center;
}

.empty-state strong {
  margin-top: 16px;
  color: #20242e;
  font-size: 20px;
}

.empty-state span,
.detail-empty span {
  margin-top: 14px;
  color: #626b80;
  font-size: 16px;
}

.empty-illustration {
  width: 76px;
  height: 76px;
  display: grid;
  place-items: center;
  color: #9bbdf4;
  font-size: 52px;
  border-radius: 18px;
  background: linear-gradient(180deg, #f7f8fb 0%, #e8ebf0 100%);
}

.icon-button {
  width: 42px;
  padding: 0;
}

.edit-button.is-disabled {
  color: #b5bdcc;
  background: #fbfcff;
}

.detail-content {
  padding-top: 64px;
}

.detail-content h3 {
  margin: 18px 0 12px;
  font-size: 24px;
}

.detail-content p {
  color: #5f6878;
  font-size: 16px;
  line-height: 1.7;
}

.detail-content dl {
  display: grid;
  gap: 14px;
  margin-top: 28px;
}

.detail-content dl > div {
  padding: 16px;
  border: 1px solid #e7ebf3;
  border-radius: 8px;
  background: #fbfcff;
}

.detail-content dt {
  color: #8a93a5;
  font-size: 13px;
  font-weight: 700;
}

.detail-content dd {
  margin-top: 8px;
  color: #252b38;
  font-size: 15px;
  line-height: 1.5;
  word-break: break-word;
}

@media (max-width: 1280px) {
  .knowledge-workspace {
    grid-template-columns: 240px minmax(420px, 1fr) 340px;
  }

  .group-panel,
  .rules-panel,
  .detail-panel {
    padding-inline: 24px;
  }
}
</style>
