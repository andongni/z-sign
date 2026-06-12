<template>
  <el-container class="layout-container" :class="{ 'is-sidebar-collapsed': isSidebarCollapsed }">
    <el-aside :width="isSidebarCollapsed ? '88px' : '300px'" class="sidebar">
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
          <el-menu-item index="/rules">
            <el-icon><Setting /></el-icon>
            <span>规则引擎</span>
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
    '/rules': '规则引擎',
    '/review-focus-config': '审核重点配置',
    '/ai-model-config': 'AI模型配置',
    '/rule-matches': '规则匹配记录',
    '/knowledge': '知识图谱',
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
  if (route.path.startsWith('/knowledge')) return '主体库'
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
  height: 100vh;
  color: #1f2430;
  background: #f7f9fc;
}

.sidebar {
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #f7f8fe 0%, #f2f5fb 100%);
  color: #252a36;
  border-right: 1px solid #e2e7f0;
  overflow: hidden;
  transition: width 0.18s ease;
}

.brand {
  height: 92px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px 0 16px;
}

.is-sidebar-collapsed .brand {
  justify-content: center;
  padding: 0;
}

.brand-left {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.brand-mark {
  width: 44px;
  height: 44px;
  aspect-ratio: 1 / 1;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  color: #fff;
  font-size: 22px;
  overflow: hidden;
  border-radius: 12px;
  background: linear-gradient(135deg, #5d5df8 0%, #7775ff 100%);
  box-shadow: 0 12px 28px rgba(80, 91, 238, 0.24);
}

.brand-copy {
  min-width: 0;
}

.brand-name {
  color: #605cff;
  font-size: 24px;
  font-weight: 700;
  line-height: 1.1;
}

.brand-desc {
  margin-top: 4px;
  color: #8a93a5;
  font-size: 12px;
}

.sidebar-toggle {
  width: 40px;
  height: 40px;
  min-height: 40px;
  padding: 0;
  color: #8d96a8;
  border: 1px solid #d9dfeb;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.72);
}

.sidebar-toggle:hover {
  color: #1677ff;
  border-color: #c8d6ec;
  background: #fff;
}

.sidebar-scroll {
  flex: 1;
  min-height: 0;
}

.sidebar-menu {
  border: none;
  padding: 0 16px;
  background: transparent;
  transition: width 0.18s ease;
}

.sidebar-menu :deep(.el-menu-item) {
  height: 56px;
  margin: 3px 0;
  padding: 0 16px !important;
  color: #232733;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
}

.is-sidebar-collapsed .sidebar-menu {
  width: 88px;
  padding: 0 12px;
}

.is-sidebar-collapsed .sidebar-menu :deep(.el-menu-item) {
  justify-content: center;
  width: 64px;
  padding: 0 !important;
}

.sidebar-menu :deep(.el-menu-item .el-icon) {
  margin-right: 14px;
  color: #202734;
  font-size: 22px;
}

.is-sidebar-collapsed .sidebar-menu :deep(.el-menu-item .el-icon) {
  margin-right: 0;
}

.is-sidebar-collapsed .sidebar-menu :deep(.el-menu-tooltip__trigger) {
  justify-content: center;
  width: 64px;
  padding: 0 !important;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  color: #1677ff;
  background: rgba(233, 240, 251, 0.9);
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  color: #252a36;
  background: #e7e8f1;
}

.sidebar-menu :deep(.el-menu-item.is-active .el-icon) {
  color: #1677ff;
}

.content-shell {
  min-width: 0;
  background: #fff;
}

.header {
  height: 92px;
  background: linear-gradient(180deg, #f9fbff 0%, #fff 100%);
  border-bottom: 1px solid #e5e9f2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px 0 64px;
}

.page-tabs {
  display: flex;
  align-items: center;
  gap: 22px;
  color: #667086;
  font-size: 21px;
  line-height: 1;
}

.page-tabs strong {
  color: #20242e;
  font-size: 22px;
  font-weight: 700;
}

.tab-divider {
  width: 1px;
  height: 44px;
  background: #dde3ef;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.language-button {
  width: 54px;
  height: 54px;
  padding: 0;
  color: #1f2530;
  font-size: 20px;
  font-weight: 700;
  border-color: #e3e8f2;
  border-radius: 10px;
  background: #fbfdff;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  height: 42px;
  padding: 0 12px;
  color: #4e596c;
  border-radius: 8px;
}

.user-info .el-icon {
  margin-right: 5px;
}

.main-content {
  --main-inline-padding: 44px;
  background: #fff;
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
