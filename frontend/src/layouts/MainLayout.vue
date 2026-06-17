<template>
  <el-container class="layout-container" :class="{ 'is-sidebar-collapsed': isSidebarCollapsed }">
    <el-aside :width="isSidebarCollapsed ? '76px' : '264px'" class="sidebar">
      <div class="brand">
        <div v-show="!isSidebarCollapsed" class="brand-left">
          <div class="brand-mark">
            <el-icon><Connection /></el-icon>
          </div>
          <div class="brand-copy">
            <div class="brand-name">智审</div>
            <div class="brand-desc">合同审查工作台</div>
          </div>
        </div>
        <el-button
          class="sidebar-toggle"
          text
          :title="isSidebarCollapsed ? '展开侧边栏' : '收起侧边栏'"
          :aria-label="isSidebarCollapsed ? '展开侧边栏' : '收起侧边栏'"
          :aria-expanded="String(!isSidebarCollapsed)"
          @click="toggleSidebar"
        >
          <el-icon>
            <Expand v-if="isSidebarCollapsed" />
            <Fold v-else />
          </el-icon>
        </el-button>
      </div>

      <el-scrollbar class="sidebar-scroll">
        <el-menu
          :default-active="activeMenu"
          :collapse="isSidebarCollapsed"
          :collapse-transition="false"
          router
          class="sidebar-menu"
        >
          <el-menu-item index="/dashboard">
            <el-icon><Odometer /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          <el-menu-item index="/contracts">
            <el-icon><Document /></el-icon>
            <span>合同管理</span>
          </el-menu-item>
          <el-menu-item index="/templates">
            <el-icon><Files /></el-icon>
            <span>模板库</span>
          </el-menu-item>
          <el-menu-item index="/reviews">
            <el-icon><Search /></el-icon>
            <span>合同审核</span>
          </el-menu-item>
          <el-menu-item index="/review-focus-config" v-if="userStore.user?.role === 'admin'">
            <el-icon><Edit /></el-icon>
            <span>审核重点配置</span>
          </el-menu-item>
          <el-menu-item index="/ai-model-config" v-if="userStore.user?.role === 'admin'">
            <el-icon><Cpu /></el-icon>
            <span>AI模型配置</span>
          </el-menu-item>
          <el-menu-item index="/ai-chat">
            <el-icon><ChatDotRound /></el-icon>
            <span>AI智能助手</span>
          </el-menu-item>
          <el-menu-item index="/rule-matches">
            <el-icon><List /></el-icon>
            <span>规则匹配记录</span>
          </el-menu-item>
          <el-menu-item index="/knowledge">
            <el-icon><Connection /></el-icon>
            <span>知识库</span>
          </el-menu-item>
          <el-menu-item index="/users" v-if="userStore.user?.role === 'admin'">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="/departments" v-if="userStore.user?.role === 'admin'">
            <el-icon><OfficeBuilding /></el-icon>
            <span>部门管理</span>
          </el-menu-item>
          <el-menu-item index="/audit-logs" v-if="userStore.user?.role === 'admin'">
            <el-icon><DocumentCopy /></el-icon>
            <span>操作日志</span>
          </el-menu-item>
          <el-menu-item index="/permission-config" v-if="userStore.user?.role === 'admin'">
            <el-icon><Lock /></el-icon>
            <span>权限配置</span>
          </el-menu-item>
        </el-menu>
      </el-scrollbar>

    </el-aside>
    <el-container class="content-shell">
      <el-header class="header">
        <div class="header-left">
          <div class="page-tabs">
            <strong>{{ pageTitle }}</strong>
            <span class="tab-divider"></span>
            <span>{{ moduleTitle }}</span>
          </div>
        </div>
        <div class="header-right">
          <el-button class="language-button">
            中
          </el-button>
          <el-dropdown @command="handleCommand" trigger="click">
            <span class="user-info">
              <el-icon><User /></el-icon>
              {{ userStore.user?.real_name || userStore.user?.username || '用户' }}
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon style="margin-right: 8px"><User /></el-icon>
                  个人中心
                </el-dropdown-item>
                <!-- 最近登录用户 -->
                <template v-if="recentUsersList && recentUsersList.length > 0">
                  <el-dropdown-item divided disabled>
                    <span style="color: #909399; font-size: 12px">最近登录</span>
                  </el-dropdown-item>
                  <el-dropdown-item
                    v-for="recentUser in recentUsersList"
                    :key="`recent-${recentUser.id}`"
                    :command="`switch:${recentUser.id}`"
                    class="recent-user-item"
                  >
                    <div style="display: flex; align-items: center; justify-content: space-between; width: 100%; min-width: 200px">
                      <div style="display: flex; align-items: center; flex: 1; min-width: 0">
                        <el-icon style="margin-right: 8px; color: #409EFF; flex-shrink: 0"><RefreshRight /></el-icon>
                        <div style="flex: 1; min-width: 0; overflow: hidden">
                          <div style="font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">
                            {{ recentUser.real_name || recentUser.username }}
                          </div>
                          <div style="font-size: 12px; color: #909399; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">
                            {{ recentUser.email || recentUser.username }}
                          </div>
                        </div>
                      </div>
                      <el-icon
                        class="remove-icon"
                        @click.stop="handleRemoveRecentUser(recentUser.id)"
                        style="margin-left: 10px; color: #909399; flex-shrink: 0; cursor: pointer"
                      >
                        <Close />
                      </el-icon>
                    </div>
                  </el-dropdown-item>
                </template>
                <el-dropdown-item command="logout" divided>
                  <el-icon style="margin-right: 8px"><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, OfficeBuilding, DocumentCopy, Edit, Cpu, RefreshRight, Close, SwitchButton, Lock, ChatDotRound, List, Fold, Expand } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const isSidebarCollapsed = ref(localStorage.getItem('sidebar_collapsed') === '1')

// 计算最近登录用户列表（排除当前用户）
const recentUsersList = computed(() => {
  if (!userStore.recentUsers) return []
  return userStore.recentUsers.filter(u => u.id !== userStore.user?.id)
})

const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/contracts')) return '/contracts'
  if (path.startsWith('/reviews')) return '/reviews'
  return path
})
const pageTitle = computed(() => {
  const titles = {
    '/dashboard': '仪表盘',
    '/contracts': '合同管理',
    '/templates': '模板库',
    '/reviews': '合同审核',
    '/rules': '审核规则库',
    '/review-focus-config': '审核重点配置',
    '/ai-model-config': 'AI模型配置',
    '/rule-matches': '规则匹配记录',
    '/knowledge': '知识库',
    '/users': '用户管理',
    '/departments': '部门管理',
    '/audit-logs': '操作日志',
    '/permission-config': '权限配置',
    '/ai-chat': 'AI智能助手',
  }
  if (titles[route.path]) return titles[route.path]
  if (route.path.startsWith('/contracts')) return '合同管理'
  if (route.path.startsWith('/reviews')) return '合同审核'
  return 'AI智能合同审核系统'
})

const moduleTitle = computed(() => {
  if (route.path.startsWith('/contracts')) return '文件库'
  if (route.path.startsWith('/reviews')) return '审查中心'
  if (route.path.startsWith('/rules') || route.path === '/rule-matches') return '审查规则库'
  if (route.path.startsWith('/knowledge')) return '知识库'
  if (route.path.startsWith('/users') || route.path.startsWith('/departments') || route.path.startsWith('/audit-logs') || route.path.startsWith('/permission-config')) return '组织权限'
  if (route.path.startsWith('/ai')) return '智能咨询'
  return '工作台'
})

const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
  localStorage.setItem('sidebar_collapsed', isSidebarCollapsed.value ? '1' : '0')
}

const handleCommand = async (command) => {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        type: 'warning',
      })
      userStore.logout()
      router.push('/login')
      ElMessage.success('已退出登录')
    } catch (error) {
      // 用户取消
    }
  } else if (command === 'profile') {
    ElMessage.info('个人中心功能开发中')
  } else if (command.startsWith('switch:')) {
    const userId = parseInt(command.split(':')[1])
    const recentUser = userStore.recentUsers.find(u => u.id === userId)
    if (recentUser) {
      try {
        await userStore.switchUser(recentUser)
        ElMessage.success(`已切换到 ${recentUser.real_name || recentUser.username}`)
        // 刷新页面以更新权限相关的内容
        window.location.reload()
      } catch (error) {
        ElMessage.error('切换用户失败，请重新登录')
        router.push('/login')
      }
    }
  }
}

const handleRemoveRecentUser = (userId) => {
  userStore.removeRecentUserFromList(userId)
  ElMessage.success('已移除')
}

// 页面加载时，如果有token但没有用户信息，则获取用户信息
onMounted(async () => {
  if (userStore.token && !userStore.user) {
    await userStore.fetchUserInfo()
  }
})
</script>

<style scoped>
.layout-container {
  height: 100dvh;
  color: #1f2430;
  background: var(--app-bg);
}

.sidebar {
  display: flex;
  flex-direction: column;
  background: var(--app-sidebar);
  color: #252a36;
  border-right: 1px solid var(--app-border);
  overflow: hidden;
  transition: width 0.18s ease;
}

.brand {
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px 0 18px;
  border-bottom: 1px solid var(--app-border);
}

.is-sidebar-collapsed .brand {
  justify-content: center;
  padding: 0;
}

.brand-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.brand-mark {
  width: 36px;
  height: 36px;
  aspect-ratio: 1 / 1;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  color: #fff;
  font-size: 17px;
  overflow: hidden;
  border-radius: var(--app-radius);
  background: var(--app-primary);
  box-shadow: 0 10px 22px rgba(31, 97, 196, 0.18);
}

.brand-copy {
  min-width: 0;
}

.brand-name {
  color: var(--app-text);
  font-size: 18px;
  font-weight: 800;
  line-height: 1.1;
}

.brand-desc {
  margin-top: 3px;
  color: var(--app-text-muted);
  font-size: 12px;
}

.sidebar-toggle {
  width: 34px;
  height: 34px;
  min-height: 34px;
  padding: 0;
  color: var(--app-text-muted);
  border: 1px solid transparent;
  border-radius: var(--app-radius);
  background: transparent;
}

.sidebar-toggle:hover {
  color: var(--app-primary);
  border-color: var(--app-border);
  background: #fff;
}

.sidebar-scroll {
  flex: 1;
  min-height: 0;
}

.sidebar-menu {
  border: none;
  padding: 10px 12px 16px;
  background: transparent;
  transition: width 0.18s ease;
}

.sidebar-menu :deep(.el-menu-item) {
  height: 42px;
  margin: 2px 0;
  padding: 0 12px !important;
  color: var(--app-text-secondary);
  font-size: 13px;
  font-weight: 650;
  border-radius: var(--app-radius);
}

.is-sidebar-collapsed .sidebar-menu {
  width: 76px;
  padding: 10px 8px 16px;
}

.is-sidebar-collapsed .sidebar-menu :deep(.el-menu-item) {
  justify-content: center;
  width: 60px;
  padding: 0 !important;
}

.sidebar-menu :deep(.el-menu-item .el-icon) {
  margin-right: 10px;
  color: #5f6b7c;
  font-size: 17px;
}

.is-sidebar-collapsed .sidebar-menu :deep(.el-menu-item .el-icon) {
  margin-right: 0;
}

.is-sidebar-collapsed .sidebar-menu :deep(.el-menu-tooltip__trigger) {
  justify-content: center;
  width: 60px;
  padding: 0 !important;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  color: var(--app-primary);
  background: #edf4ff;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  color: var(--app-primary);
  background: var(--app-primary-soft);
  box-shadow: inset 3px 0 0 var(--app-primary);
}

.sidebar-menu :deep(.el-menu-item.is-active .el-icon) {
  color: var(--app-primary);
}

.content-shell {
  min-width: 0;
  background: var(--app-bg);
}

.header {
  height: 72px;
  background: rgba(255, 255, 255, 0.92);
  border-bottom: 1px solid var(--app-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px 0 32px;
  backdrop-filter: blur(10px);
}

.page-tabs {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--app-text-muted);
  font-size: 13px;
  line-height: 1;
}

.page-tabs strong {
  color: var(--app-text);
  font-size: 18px;
  font-weight: 800;
}

.tab-divider {
  width: 1px;
  height: 18px;
  background: var(--app-border-strong);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.language-button {
  width: 38px;
  height: 38px;
  min-height: 38px;
  padding: 0;
  color: var(--app-text-secondary);
  font-size: 14px;
  font-weight: 700;
  border-color: var(--app-border);
  border-radius: var(--app-radius);
  background: #fff;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  height: 38px;
  padding: 0 10px;
  color: var(--app-text-secondary);
  border: 1px solid transparent;
  border-radius: var(--app-radius);
}

.user-info:hover {
  border-color: var(--app-border);
  background: #fff;
}

.user-info .el-icon {
  margin-right: 5px;
}

.main-content {
  --main-inline-padding: 32px;
  background: var(--app-bg);
  padding: 0;
  overflow-y: auto;
}

.recent-user-item {
  padding: 8px 20px;
  min-width: 200px;
}

.recent-user-item:hover {
  background-color: #f5f7fa;
}

.remove-icon {
  opacity: 0;
  transition: opacity 0.2s;
}

.recent-user-item:hover .remove-icon {
  opacity: 1;
}

.remove-icon:hover {
  color: #f56c6c !important;
}
</style>
