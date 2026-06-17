<template>
  <div class="knowledge-review">
    <template v-if="pageMode === 'list'">
      <div class="workspace-tabs">
        <button
          :class="{ active: workspaceMode === 'checklist' }"
          type="button"
          @click="switchWorkspace('checklist')"
        >
          文件审查清单
        </button>
        <button
          :class="{ active: workspaceMode === 'rules' }"
          type="button"
          @click="switchWorkspace('rules')"
        >
          审查规则库
        </button>
      </div>

      <section class="list-section">
        <template v-if="workspaceMode === 'checklist'">
          <div class="list-toolbar">
            <el-input
              v-model="searchKeyword"
              clearable
              class="search-input"
              placeholder="请输入清单名称搜索"
              @clear="handleSearch"
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button type="primary" @click="handleCreateChecklist">
              <el-icon><Plus /></el-icon>
              新建清单
            </el-button>
          </div>

          <el-table
            :data="checklists"
            v-loading="checklistLoading"
            class="review-table"
            row-key="id"
          >
            <el-table-column prop="name" label="审查清单名称" min-width="260" />
            <el-table-column prop="rule_count" label="规则数量" width="180" />
            <el-table-column prop="updated_at" label="最后修改时间" min-width="220">
              <template #default="{ row }">
                {{ formatDateTime(row.updated_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="260" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="handleViewChecklist(row)">查看详情</el-button>
                <el-button link type="primary" @click="handleEditChecklist(row)">编辑</el-button>
                <el-button link type="danger" @click="handleDeleteChecklist(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-row">
            <el-pagination
              v-model:current-page="checklistPagination.page"
              v-model:page-size="checklistPagination.pageSize"
              :total="checklistPagination.total"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="fetchChecklists"
              @current-change="fetchChecklists"
            />
          </div>
        </template>

        <div v-else class="rule-library" v-loading="rulesLoading">
          <aside class="rule-type-panel">
            <div class="rule-type-title">
              <h2>规则类型</h2>
            </div>
            <div class="rule-type-list">
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

          <section class="library-rule-panel">
            <div class="library-panel-header">
              <h2>审查规则</h2>
              <div class="library-actions">
                <el-button type="primary" @click="handleCreateRule">
                  <el-icon><Plus /></el-icon>
                  新建规则
                </el-button>
              </div>
            </div>

            <el-input
              v-model="searchKeyword"
              clearable
              class="library-search"
              placeholder="请输入规则名称或描述关键字以搜索"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>

            <div v-if="filteredLibraryRules.length" class="library-rule-list">
              <button
                v-for="rule in filteredLibraryRules"
                :key="rule.id"
                :class="{ active: librarySelectedRule?.id === rule.id }"
                type="button"
                @click="librarySelectedRuleId = rule.id"
              >
                <span class="library-rule-title">{{ rule.rule_name }}</span>
                <span class="library-rule-meta">
                  <span>{{ rule.description || rule.rule_code || '暂无描述' }}</span>
                  <el-tag size="small" :type="getRiskTagType(rule.risk_level)" effect="plain">
                    {{ getRiskText(rule.risk_level) }}
                  </el-tag>
                </span>
              </button>
            </div>

            <div v-else class="empty-panel library-empty">
              <el-icon><Box /></el-icon>
              <strong>暂无数据</strong>
              <span>点击右上方“新建规则”，创建专属文件审查标准</span>
            </div>
          </section>

          <aside class="library-detail-panel">
            <div class="library-panel-header">
              <h2>规则详情</h2>
              <div class="library-detail-actions">
                <el-button :disabled="!librarySelectedRule" @click="handleEditRule(librarySelectedRule)">
                  <el-icon><Setting /></el-icon>
                  编辑
                </el-button>
                <el-button
                  :disabled="!librarySelectedRule"
                  type="danger"
                  plain
                  @click="handleDeleteRule(librarySelectedRule)"
                >
                  <el-icon><Remove /></el-icon>
                  删除
                </el-button>
              </div>
            </div>

            <div v-if="librarySelectedRule" class="rule-detail">
              <div class="detail-title-row">
                <h3>{{ librarySelectedRule.rule_name }}</h3>
                <el-tag :type="getRiskTagType(librarySelectedRule.risk_level)" effect="plain">
                  {{ getRiskText(librarySelectedRule.risk_level) }}
                </el-tag>
              </div>
              <dl>
                <div>
                  <dt>规则类型</dt>
                  <dd>{{ getRuleTypeText(librarySelectedRule.rule_type) || '-' }}</dd>
                </div>
                <div>
                  <dt>规则编码</dt>
                  <dd>{{ librarySelectedRule.rule_code || '-' }}</dd>
                </div>
                <div>
                  <dt>适用行业</dt>
                  <dd>{{ librarySelectedRule.industry || '-' }}</dd>
                </div>
                <div>
                  <dt>规则分类</dt>
                  <dd>{{ getRuleCategory(librarySelectedRule) }}</dd>
                </div>
                <div>
                  <dt>优先级</dt>
                  <dd>{{ librarySelectedRule.priority ?? 0 }}</dd>
                </div>
                <div>
                  <dt>状态</dt>
                  <dd>{{ librarySelectedRule.is_active ? '启用' : '禁用' }}</dd>
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
                  <dt>规则内容</dt>
                  <dd class="rule-json">{{ formatRuleContent(librarySelectedRule.rule_content) }}</dd>
                </div>
                <div>
                  <dt>最后修改时间</dt>
                  <dd>{{ formatDateTime(librarySelectedRule.updated_at) }}</dd>
                </div>
              </dl>
            </div>

            <div v-else class="empty-panel detail-empty">
              <strong>点击规则查看详情</strong>
            </div>
          </aside>
        </div>
      </section>
    </template>

    <template v-else>
      <div class="editor-header">
        <el-button class="back-button" @click="backToList">
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <h1>{{ editorTitle }}</h1>
        <div class="editor-header-actions" v-if="pageMode === 'detail'">
          <el-button type="primary" @click="handleEditChecklist(currentChecklist)">编辑</el-button>
        </div>
      </div>

      <section class="editor-section" v-loading="detailLoading">
        <el-form
          ref="formRef"
          :model="formData"
          :rules="formRules"
          label-position="top"
          class="checklist-form"
          :disabled="pageMode === 'detail'"
        >
          <el-form-item label="审查清单名称" prop="name" required>
            <el-input
              v-model="formData.name"
              maxlength="100"
              show-word-limit
              placeholder="请输入审查清单名称"
            />
          </el-form-item>
        </el-form>

        <div class="field-title">
          <span>*</span>
          审查规则
        </div>

        <div class="rule-editor">
          <section class="selected-rules-panel">
            <div class="panel-header">
              <h2>规则列表</h2>
              <div class="panel-actions" v-if="pageMode !== 'detail'">
                <el-button link type="primary" @click="showRuleLibrary">
                  <el-icon><Setting /></el-icon>
                  管理规则库
                </el-button>
                <el-button @click="openRuleDialog">
                  <el-icon><Plus /></el-icon>
                  添加规则
                </el-button>
              </div>
            </div>

            <div v-if="selectedRules.length" class="selected-rule-list">
              <button
                v-for="rule in selectedRules"
                :key="rule.id"
                :class="{ active: selectedRuleId === rule.id }"
                type="button"
                @click="selectedRuleId = rule.id"
              >
                <span class="rule-name">{{ rule.rule_name }}</span>
                <span class="rule-meta">
                  {{ getRuleCategory(rule) }}
                  <el-tag size="small" :type="getRiskTagType(rule.risk_level)" effect="plain">
                    {{ getRiskText(rule.risk_level) }}
                  </el-tag>
                </span>
              </button>
            </div>

            <div v-else class="empty-panel">
              <el-icon><Box /></el-icon>
              <strong>暂无数据</strong>
            </div>
          </section>

          <section class="rule-detail-panel">
            <div class="panel-header">
              <h2>规则详情</h2>
              <el-button
                v-if="pageMode !== 'detail'"
                link
                type="danger"
                :disabled="!selectedRule"
                @click="removeSelectedRule(selectedRule?.id)"
              >
                <el-icon><Remove /></el-icon>
                删除规则
              </el-button>
            </div>

            <div v-if="selectedRule" class="rule-detail">
              <div class="detail-title-row">
                <h3>{{ selectedRule.rule_name }}</h3>
                <el-tag :type="getRiskTagType(selectedRule.risk_level)" effect="plain">
                  {{ getRiskText(selectedRule.risk_level) }}
                </el-tag>
              </div>
              <dl>
                <div>
                  <dt>规则编码</dt>
                  <dd>{{ selectedRule.rule_code || '-' }}</dd>
                </div>
                <div>
                  <dt>规则分类</dt>
                  <dd>{{ getRuleCategory(selectedRule) }}</dd>
                </div>
                <div>
                  <dt>规则描述</dt>
                  <dd>{{ selectedRule.description || '-' }}</dd>
                </div>
                <div>
                  <dt>法律依据</dt>
                  <dd>{{ selectedRule.legal_basis || '-' }}</dd>
                </div>
              </dl>
            </div>

            <div v-else class="empty-panel detail-empty">
              <strong>暂无数据</strong>
            </div>
          </section>
        </div>

        <div v-if="pageMode !== 'detail'" class="form-footer">
          <el-button @click="backToList">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="submitChecklist">
            保存清单详情
          </el-button>
        </div>
      </section>
    </template>

    <el-dialog
      v-model="ruleDialogVisible"
      title="添加规则"
      width="900px"
      class="rule-picker-dialog"
    >
      <div class="rule-picker">
        <aside class="category-list">
          <button
            v-for="category in pickerCategories"
            :key="category.name"
            :class="{ active: activeRuleCategory === category.name }"
            type="button"
            @click="activeRuleCategory = category.name"
          >
            <span>{{ category.name }}</span>
            <em>{{ category.count }}</em>
          </button>
        </aside>
        <section class="picker-main">
          <el-input
            v-model="rulePickerKeyword"
            clearable
            class="picker-search"
            placeholder="请输入规则名称搜索"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>

          <el-checkbox-group v-model="ruleSelection" class="picker-rule-list" v-loading="rulesLoading">
            <label
              v-for="rule in pickerRules"
              :key="rule.id"
              class="picker-rule-item"
            >
              <el-checkbox :label="rule.id">
                <span class="picker-rule-name">{{ rule.rule_name }}</span>
              </el-checkbox>
              <span class="picker-rule-desc">{{ rule.description || rule.rule_code || '-' }}</span>
            </label>
          </el-checkbox-group>

          <div v-if="!pickerRules.length && !rulesLoading" class="picker-empty">暂无数据</div>
        </section>
      </div>
      <template #footer>
        <el-button @click="ruleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmRuleSelection">添加规则</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="ruleFormVisible"
      :title="ruleFormTitle"
      width="820px"
      class="rule-form-dialog"
      @close="handleRuleDialogClose"
    >
      <el-form
        ref="ruleFormRef"
        :model="ruleFormData"
        :rules="ruleFormRules"
        label-width="112px"
        class="rule-form"
      >
        <div class="rule-form-grid">
          <el-form-item v-if="isRuleEdit" label="规则编码">
            <el-input v-model="ruleFormData.rule_code" disabled />
          </el-form-item>
          <el-form-item label="规则名称" prop="rule_name">
            <el-input v-model="ruleFormData.rule_name" />
          </el-form-item>
          <el-form-item label="规则类型" prop="rule_type">
            <el-select v-model="ruleFormData.rule_type" placeholder="请选择规则类型" filterable>
              <el-option label="通用规则" value="general" />
              <el-option label="行业规则" value="industry" />
              <el-option label="企业规则" value="enterprise" />
            </el-select>
          </el-form-item>
          <el-form-item label="风险等级" prop="risk_level">
            <el-select v-model="ruleFormData.risk_level" placeholder="请选择风险等级" clearable filterable>
              <el-option label="高风险" value="high" />
              <el-option label="中风险" value="medium" />
              <el-option label="低风险" value="low" />
            </el-select>
          </el-form-item>
          <el-form-item label="适用行业" prop="industry">
            <el-input v-model="ruleFormData.industry" placeholder="如：制造业、金融业等" />
          </el-form-item>
          <el-form-item label="规则分类" prop="category">
            <el-input v-model="ruleFormData.category" placeholder="如：合同条款、风险控制等" />
          </el-form-item>
          <el-form-item label="优先级" prop="priority">
            <el-input-number v-model="ruleFormData.priority" :min="0" :max="100" />
          </el-form-item>
          <el-form-item label="是否启用" prop="is_active">
            <el-switch v-model="ruleFormData.is_active" />
          </el-form-item>
        </div>

        <el-form-item label="规则内容" prop="rule_content">
          <el-input
            v-model="ruleContentText"
            type="textarea"
            :rows="6"
            placeholder='请输入JSON格式的规则内容，例如：{"condition": "...", "action": "..."}'
          />
        </el-form-item>
        <el-form-item label="法律依据" prop="legal_basis">
          <el-input v-model="ruleFormData.legal_basis" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="规则描述" prop="description">
          <el-input v-model="ruleFormData.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="ruleFormVisible = false">取消</el-button>
        <el-button type="primary" :loading="ruleSubmitting" @click="handleSubmitRule">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Box,
  Plus,
  Remove,
  Search,
  Setting,
} from '@element-plus/icons-vue'
import api from '@/utils/api'
import { formatDateTime } from '@/utils/date'

const route = useRoute()

const workspaceMode = ref('checklist')
const pageMode = ref('list')
const checklistLoading = ref(false)
const detailLoading = ref(false)
const rulesLoading = ref(false)
const submitting = ref(false)
const ruleDialogVisible = ref(false)
const ruleFormVisible = ref(false)
const ruleSubmitting = ref(false)
const isRuleEdit = ref(false)
const searchKeyword = ref('')
const rulePickerKeyword = ref('')
const activeRuleCategory = ref('全部')
const activeLibraryCategory = ref('全部')
const selectedRuleId = ref(null)
const librarySelectedRuleId = ref(null)
const formRef = ref(null)
const ruleFormRef = ref(null)
const currentChecklist = ref(null)
const checklists = ref([])
const allRules = ref([])
const selectedRules = ref([])
const ruleSelection = ref([])
const ruleContentText = ref('')

const checklistPagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const formData = reactive({
  id: null,
  name: '',
})

const ruleFormData = reactive({
  id: null,
  rule_code: '',
  rule_name: '',
  rule_type: 'general',
  industry: '',
  category: '',
  priority: 0,
  rule_content: {},
  risk_level: '',
  legal_basis: '',
  description: '',
  is_active: true,
})

const formRules = {
  name: [
    { required: true, message: '请输入审查清单名称', trigger: 'blur' },
    { max: 100, message: '审查清单名称不能超过100个字符', trigger: 'blur' },
  ],
}

const ruleFormRules = {
  rule_name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  rule_type: [{ required: true, message: '请选择规则类型', trigger: 'change' }],
}

const editorTitle = computed(() => {
  if (pageMode.value === 'detail') return '审查清单详情'
  return formData.id ? '编辑审查清单' : '新建审查清单'
})

const ruleFormTitle = computed(() => (isRuleEdit.value ? '编辑规则' : '新建规则'))

const selectedRule = computed(() => {
  if (!selectedRules.value.length) return null
  return selectedRules.value.find(rule => rule.id === selectedRuleId.value) || selectedRules.value[0]
})

const buildRuleCategories = (rules) => {
  const counter = new Map()
  rules.forEach(rule => {
    const category = getRuleCategory(rule)
    counter.set(category, (counter.get(category) || 0) + 1)
  })
  return [
    { name: '全部', count: rules.length },
    ...Array.from(counter.entries()).map(([name, count]) => ({ name, count })),
  ]
}

const activeRules = computed(() => allRules.value.filter(rule => rule.is_active))

const ruleCategories = computed(() => buildRuleCategories(allRules.value))

const pickerCategories = computed(() => buildRuleCategories(activeRules.value))

const filteredLibraryRules = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  return allRules.value
    .filter(rule => activeLibraryCategory.value === '全部' || getRuleCategory(rule) === activeLibraryCategory.value)
    .filter(rule => {
      if (!keyword) return true
      return [rule.rule_name, rule.description, rule.rule_code, rule.category]
        .filter(Boolean)
        .some(value => String(value).toLowerCase().includes(keyword))
    })
})

const librarySelectedRule = computed(() => {
  if (!filteredLibraryRules.value.length) return null
  return filteredLibraryRules.value.find(rule => rule.id === librarySelectedRuleId.value) || filteredLibraryRules.value[0]
})

const pickerRules = computed(() => {
  const keyword = rulePickerKeyword.value.trim().toLowerCase()
  return activeRules.value
    .filter(rule => activeRuleCategory.value === '全部' || getRuleCategory(rule) === activeRuleCategory.value)
    .filter(rule => {
      if (!keyword) return true
      return [rule.rule_name, rule.description, rule.rule_code, rule.category]
        .filter(Boolean)
        .some(value => String(value).toLowerCase().includes(keyword))
    })
})

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

const formatRuleContent = (content) => {
  if (!content) return '-'
  if (typeof content === 'string') return content || '-'
  if (typeof content === 'object' && !Object.keys(content).length) return '-'
  return JSON.stringify(content, null, 2)
}

const fetchChecklists = async () => {
  checklistLoading.value = true
  try {
    const response = await api.get('/rules/checklists/', {
      params: {
        page: checklistPagination.page,
        page_size: checklistPagination.pageSize,
        search: searchKeyword.value.trim(),
      },
    })
    checklists.value = response.data.results || []
    checklistPagination.total = response.data.count || 0
  } catch (error) {
    ElMessage.error('获取审查清单失败')
  } finally {
    checklistLoading.value = false
  }
}

const fetchRules = async () => {
  rulesLoading.value = true
  try {
    const response = await api.get('/rules/rules/', {
      params: {
        page: 1,
        page_size: 1000,
        ordering: '-priority',
        include_inactive: true,
      },
    })
    allRules.value = response.data.results || []
    if (selectedRules.value.length) {
      const ruleById = new Map(allRules.value.map(rule => [rule.id, rule]))
      selectedRules.value = selectedRules.value
        .map(rule => ruleById.get(rule.id) || rule)
        .filter(rule => ruleById.has(rule.id))
      ruleSelection.value = selectedRules.value.map(rule => rule.id)
    }
    if (!pickerCategories.value.some(category => category.name === activeRuleCategory.value)) {
      activeRuleCategory.value = '全部'
    }
    if (!ruleCategories.value.some(category => category.name === activeLibraryCategory.value)) {
      activeLibraryCategory.value = '全部'
    }
  } catch (error) {
    ElMessage.error('获取审查规则失败')
  } finally {
    rulesLoading.value = false
  }
}

const handleSearch = () => {
  if (workspaceMode.value === 'checklist') {
    checklistPagination.page = 1
    fetchChecklists()
  }
}

const switchWorkspace = (mode) => {
  workspaceMode.value = mode
  searchKeyword.value = ''
  if (mode === 'checklist') {
    fetchChecklists()
  } else {
    fetchRules()
  }
}

const resetForm = () => {
  formData.id = null
  formData.name = ''
  currentChecklist.value = null
  selectedRules.value = []
  selectedRuleId.value = null
  ruleSelection.value = []
  formRef.value?.clearValidate()
}

const copyChecklistToForm = (checklist) => {
  formData.id = checklist.id
  formData.name = checklist.name || ''
  currentChecklist.value = checklist
  selectedRules.value = [...(checklist.rules || [])]
  selectedRuleId.value = selectedRules.value[0]?.id || null
  ruleSelection.value = selectedRules.value.map(rule => rule.id)
}

const loadChecklistDetail = async (row) => {
  detailLoading.value = true
  try {
    const response = await api.get(`/rules/checklists/${row.id}/`)
    return response.data
  } finally {
    detailLoading.value = false
  }
}

const handleCreateChecklist = () => {
  resetForm()
  pageMode.value = 'form'
}

const handleViewChecklist = async (row) => {
  try {
    const detail = await loadChecklistDetail(row)
    copyChecklistToForm(detail)
    pageMode.value = 'detail'
  } catch (error) {
    ElMessage.error('获取清单详情失败')
  }
}

const handleEditChecklist = async (row) => {
  if (!row?.id) return
  try {
    const detail = await loadChecklistDetail(row)
    copyChecklistToForm(detail)
    pageMode.value = 'form'
  } catch (error) {
    ElMessage.error('获取清单详情失败')
  }
}

const handleDeleteChecklist = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除“${row.name}”吗？`, '删除审查清单', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await api.delete(`/rules/checklists/${row.id}/`)
    ElMessage.success('删除成功')
    fetchChecklists()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const resetRuleForm = () => {
  Object.assign(ruleFormData, {
    id: null,
    rule_code: '',
    rule_name: '',
    rule_type: 'general',
    industry: '',
    category: '',
    priority: 0,
    rule_content: {},
    risk_level: '',
    legal_basis: '',
    description: '',
    is_active: true,
  })
  ruleContentText.value = ''
  ruleFormRef.value?.clearValidate()
}

const handleCreateRule = () => {
  isRuleEdit.value = false
  resetRuleForm()
  ruleFormVisible.value = true
}

const handleEditRule = (rule) => {
  if (!rule) return
  isRuleEdit.value = true
  Object.assign(ruleFormData, {
    id: rule.id,
    rule_code: rule.rule_code || '',
    rule_name: rule.rule_name || '',
    rule_type: rule.rule_type || 'general',
    industry: rule.industry || '',
    category: rule.category || '',
    priority: rule.priority ?? 0,
    rule_content: rule.rule_content || {},
    risk_level: rule.risk_level || '',
    legal_basis: rule.legal_basis || '',
    description: rule.description || '',
    is_active: rule.is_active ?? true,
  })
  ruleContentText.value = typeof rule.rule_content === 'string'
    ? rule.rule_content
    : JSON.stringify(rule.rule_content || {}, null, 2)
  ruleFormVisible.value = true
}

const handleDeleteRule = async (rule) => {
  if (!rule) return
  try {
    await ElMessageBox.confirm(`确定要删除“${rule.rule_name}”吗？`, '删除规则', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await api.delete(`/rules/rules/${rule.id}/`)
    ElMessage.success('删除成功')
    if (librarySelectedRuleId.value === rule.id) {
      librarySelectedRuleId.value = null
    }
    selectedRules.value = selectedRules.value.filter(item => item.id !== rule.id)
    ruleSelection.value = selectedRules.value.map(item => item.id)
    await fetchRules()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleSubmitRule = async () => {
  if (!ruleFormRef.value) return
  const valid = await ruleFormRef.value.validate().catch(() => false)
  if (!valid) return

  let ruleContent = {}
  const contentText = ruleContentText.value.trim()
  if (contentText) {
    try {
      ruleContent = JSON.parse(contentText)
    } catch (error) {
      ElMessage.error('规则内容必须是有效的JSON格式')
      return
    }
  }

  ruleSubmitting.value = true
  try {
    const payload = {
      rule_name: ruleFormData.rule_name.trim(),
      rule_type: ruleFormData.rule_type,
      industry: ruleFormData.industry.trim(),
      category: ruleFormData.category.trim(),
      priority: ruleFormData.priority ?? 0,
      rule_content: ruleContent,
      risk_level: ruleFormData.risk_level,
      legal_basis: ruleFormData.legal_basis.trim(),
      description: ruleFormData.description.trim(),
      is_active: ruleFormData.is_active,
    }

    const response = isRuleEdit.value
      ? await api.patch(`/rules/rules/${ruleFormData.id}/`, payload)
      : await api.post('/rules/rules/', payload)

    ElMessage.success(isRuleEdit.value ? '更新成功' : '创建成功')
    librarySelectedRuleId.value = response.data?.id || ruleFormData.id
    ruleFormVisible.value = false
    await fetchRules()
  } catch (error) {
    ElMessage.error(isRuleEdit.value ? '更新失败' : '创建失败')
  } finally {
    ruleSubmitting.value = false
  }
}

const handleRuleDialogClose = () => {
  resetRuleForm()
}

const openRuleDialog = async () => {
  if (!allRules.value.length) {
    await fetchRules()
  }
  ruleSelection.value = selectedRules.value.map(rule => rule.id)
  rulePickerKeyword.value = ''
  activeRuleCategory.value = '全部'
  ruleDialogVisible.value = true
}

const confirmRuleSelection = () => {
  const selectedIds = new Set(ruleSelection.value)
  selectedRules.value = allRules.value.filter(rule => selectedIds.has(rule.id))
  selectedRuleId.value = selectedRules.value[0]?.id || null
  ruleDialogVisible.value = false
}

const removeSelectedRule = (ruleId) => {
  if (!ruleId) return
  selectedRules.value = selectedRules.value.filter(rule => rule.id !== ruleId)
  ruleSelection.value = selectedRules.value.map(rule => rule.id)
  selectedRuleId.value = selectedRules.value[0]?.id || null
}

const submitChecklist = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  if (!selectedRules.value.length) {
    ElMessage.error('请至少添加一条审查规则')
    return
  }

  submitting.value = true
  try {
    const payload = {
      name: formData.name.trim(),
      rule_ids: selectedRules.value.map(rule => rule.id),
    }
    if (formData.id) {
      await api.patch(`/rules/checklists/${formData.id}/`, payload)
      ElMessage.success('更新成功')
    } else {
      await api.post('/rules/checklists/', payload)
      ElMessage.success('创建成功')
    }
    pageMode.value = 'list'
    resetForm()
    fetchChecklists()
  } catch (error) {
    ElMessage.error(formData.id ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

const backToList = () => {
  pageMode.value = 'list'
  resetForm()
  fetchChecklists()
}

const showRuleLibrary = () => {
  pageMode.value = 'list'
  workspaceMode.value = 'rules'
  searchKeyword.value = ''
  resetForm()
  fetchRules()
}

watch(selectedRules, (rules) => {
  if (!rules.length) {
    selectedRuleId.value = null
    return
  }
  if (!rules.some(rule => rule.id === selectedRuleId.value)) {
    selectedRuleId.value = rules[0].id
  }
})

watch(filteredLibraryRules, (rules) => {
  if (!rules.length) {
    librarySelectedRuleId.value = null
    return
  }
  if (!rules.some(rule => rule.id === librarySelectedRuleId.value)) {
    librarySelectedRuleId.value = rules[0].id
  }
})

onMounted(() => {
  if (route.query.tab === 'rules' || route.query.mode === 'rules') {
    workspaceMode.value = 'rules'
  }
  fetchChecklists()
  fetchRules()
})
</script>

<style scoped>
.knowledge-review {
  min-height: calc(100dvh - 72px);
  background: var(--app-bg);
}

.workspace-tabs {
  height: 72px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 32px;
  border-bottom: 1px solid var(--app-border);
  background: #fff;
}

.workspace-tabs button {
  height: 36px;
  padding: 0 14px;
  color: var(--app-text-secondary);
  font-size: 13px;
  font-weight: 700;
  border: 0;
  border-radius: var(--app-radius);
  background: transparent;
  cursor: pointer;
}

.workspace-tabs button.active {
  color: var(--app-primary);
  background: var(--app-primary-soft);
}

.list-section {
  padding: 24px 32px 32px;
}

.list-toolbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 14px;
  margin-bottom: 24px;
}

.search-input {
  width: min(520px, 45vw);
}

.review-table {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
}

.pagination-row {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
}

.rule-library {
  display: grid;
  grid-template-columns: 260px minmax(420px, 1fr) 360px;
  min-height: calc(100dvh - 182px);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  background: #fff;
  overflow: hidden;
}

.rule-type-panel,
.library-rule-panel,
.library-detail-panel {
  min-width: 0;
  padding: 24px;
}

.rule-type-panel,
.library-rule-panel {
  border-right: 1px solid var(--app-border);
}

.rule-type-title h2,
.library-panel-header h2 {
  margin: 0;
  color: var(--app-text);
  font-size: 16px;
  font-weight: 800;
}

.rule-type-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 20px;
}

.rule-type-list button {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  color: var(--app-text-secondary);
  font-size: 13px;
  font-weight: 700;
  border: 0;
  border-radius: var(--app-radius);
  background: transparent;
  cursor: pointer;
}

.rule-type-list button.active {
  color: var(--app-primary);
  background: var(--app-primary-soft);
}

.rule-type-list em {
  color: inherit;
  font-style: normal;
  font-size: 11px;
}

.library-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 40px;
}

.library-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.library-detail-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.library-search {
  margin: 22px 0;
}

.library-rule-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.library-rule-list button {
  width: 100%;
  padding: 12px 14px;
  text-align: left;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  background: #fff;
  cursor: pointer;
}

.library-rule-list button.active,
.library-rule-list button:hover {
  border-color: #9ec5ff;
  background: #f7fbff;
}

.library-rule-title {
  display: block;
  overflow: hidden;
  color: var(--app-text);
  font-size: 13px;
  font-weight: 800;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.library-rule-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 8px;
  color: var(--app-text-muted);
  font-size: 12px;
}

.library-rule-meta > span {
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.library-empty {
  min-height: 420px;
}

.editor-header {
  height: 72px;
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 0 32px;
  border-bottom: 1px solid var(--app-border);
  background: #fff;
}

.editor-header h1 {
  margin: 0;
  color: var(--app-text);
  font-size: 16px;
  font-weight: 800;
}

.editor-header-actions {
  margin-left: auto;
}

.back-button {
  width: 36px;
  padding: 0;
}

.editor-section {
  padding: 24px 32px 32px;
}

.checklist-form {
  width: min(760px, 58vw);
}

.field-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 30px 0 14px;
  color: var(--app-text);
  font-size: 15px;
  font-weight: 800;
}

.field-title span {
  color: #f56c6c;
}

.rule-editor {
  display: grid;
  grid-template-columns: minmax(420px, 1fr) minmax(420px, 1fr);
  min-height: 520px;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  background: #fff;
  overflow: hidden;
}

.selected-rules-panel,
.rule-detail-panel {
  min-width: 0;
  padding: 30px 34px;
}

.selected-rules-panel {
  border-right: 1px solid var(--app-border);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  min-height: 40px;
  margin-bottom: 24px;
}

.panel-header h2 {
  margin: 0;
  color: var(--app-text);
  font-size: 16px;
  font-weight: 800;
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.selected-rule-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.selected-rule-list button {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  padding: 14px 16px;
  text-align: left;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  background: #fff;
  cursor: pointer;
}

.selected-rule-list button.active,
.selected-rule-list button:hover {
  border-color: #9ec5ff;
  background: #f7fbff;
}

.rule-name {
  overflow: hidden;
  color: var(--app-text);
  font-size: 14px;
  font-weight: 800;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.rule-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--app-text-muted);
  font-size: 12px;
}

.empty-panel {
  min-height: 360px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 14px;
  color: var(--app-text-muted);
}

.empty-panel .el-icon {
  color: #c6ccd6;
  font-size: 56px;
}

.empty-panel strong {
  color: var(--app-text);
  font-size: 16px;
}

.detail-empty {
  min-height: 430px;
}

.rule-detail {
  padding-top: 8px;
}

.detail-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 22px;
}

.detail-title-row h3 {
  margin: 0;
  color: var(--app-text);
  font-size: 17px;
  font-weight: 800;
}

.rule-detail dl {
  display: grid;
  gap: 14px;
  margin: 0;
}

.rule-detail dl > div {
  padding: 14px 16px;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  background: var(--app-panel-soft);
}

.rule-detail dt {
  color: var(--app-text-muted);
  font-size: 12px;
  font-weight: 700;
}

.rule-detail dd {
  margin: 8px 0 0;
  color: var(--app-text);
  font-size: 13px;
  line-height: 1.6;
  word-break: break-word;
}

.rule-detail .rule-json {
  white-space: pre-wrap;
  font-family: SFMono-Regular, Consolas, 'Liberation Mono', monospace;
  font-size: 12px;
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.rule-picker {
  display: grid;
  grid-template-columns: 220px 1fr;
  min-height: 500px;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  overflow: hidden;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px;
  border-right: 1px solid var(--app-border);
  background: var(--app-panel-soft);
}

.category-list button {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  color: var(--app-text-secondary);
  border: 0;
  border-radius: var(--app-radius);
  background: transparent;
  cursor: pointer;
}

.category-list button.active {
  color: var(--app-primary);
  background: var(--app-primary-soft);
}

.category-list em {
  color: inherit;
  font-style: normal;
  font-size: 11px;
}

.picker-main {
  min-width: 0;
  padding: 16px;
}

.picker-search {
  margin-bottom: 14px;
}

.picker-rule-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 410px;
  overflow: auto;
}

.picker-rule-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 14px;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
}

.picker-rule-name {
  color: var(--app-text);
  font-weight: 700;
}

.picker-rule-desc {
  padding-left: 24px;
  color: var(--app-text-muted);
  font-size: 12px;
  line-height: 1.5;
}

.picker-empty {
  display: grid;
  place-items: center;
  height: 320px;
  color: var(--app-text-muted);
}

.rule-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 18px;
}

.rule-form :deep(.el-select) {
  width: 100%;
}

@media (max-width: 1180px) {
  .rule-library {
    grid-template-columns: 220px 1fr;
  }

  .library-detail-panel {
    grid-column: 1 / -1;
    border-top: 1px solid var(--app-border);
  }

  .rule-editor {
    grid-template-columns: 1fr;
  }

  .selected-rules-panel {
    border-right: 0;
    border-bottom: 1px solid var(--app-border);
  }

  .checklist-form,
  .search-input {
    width: 100%;
  }

  .library-panel-header,
  .library-actions,
  .library-detail-actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .rule-form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
