<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <div class="login-brand-mark">
            <el-icon><Connection /></el-icon>
          </div>
          <h2>AI智能合同审核系统</h2>
          <p>合同审查工作台</p>
        </div>
      </template>
      <el-form :model="loginForm" :rules="rules" ref="loginFormRef" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="loginForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleLogin" :loading="loading" style="width: 100%">
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { Connection } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const loginFormRef = ref(null)
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await userStore.login(loginForm.username, loginForm.password)
        ElMessage.success('登录成功')
        router.push('/')
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '登录失败，请检查用户名和密码')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100dvh;
  padding: 24px;
  background: var(--app-bg);
}

.login-card {
  width: min(420px, 100%);
}

.card-header {
  text-align: center;
}

.login-brand-mark {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  margin: 0 auto 14px;
  color: #fff;
  font-size: 20px;
  border-radius: var(--app-radius);
  background: var(--app-primary);
  box-shadow: 0 10px 22px rgba(31, 97, 196, 0.18);
}

.card-header h2 {
  margin: 0;
  color: var(--app-text);
  font-size: 20px;
  font-weight: 800;
}

.card-header p {
  margin: 6px 0 0;
  color: var(--app-text-muted);
  font-size: 13px;
}
</style>
