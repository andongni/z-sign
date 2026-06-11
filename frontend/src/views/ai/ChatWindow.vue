<template>
  <div class="chat-window">
    <el-card class="chat-card" :body-style="{ padding: 0, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }">
      <template #header>
        <div class="chat-header">
          <div class="header-left">
            <el-icon style="font-size: 20px; color: #409EFF; margin-right: 8px"><ChatDotRound /></el-icon>
            <span style="font-size: 18px; font-weight: 500">AI智能助手</span>
            <el-tag v-if="currentModel" size="small" style="margin-left: 10px" type="info">
              {{ currentModel }}
            </el-tag>
          </div>
          <div class="header-right">
            <el-button
              size="small"
              :icon="Delete"
              @click="clearChat"
              :disabled="messages.length === 0"
            >
              清空对话
            </el-button>
          </div>
        </div>
      </template>

      <!-- 消息列表 -->
      <div class="messages-container" ref="messagesContainer">
        <div v-if="messages.length === 0" class="empty-state">
          <el-icon style="font-size: 64px; color: #C0C4CC; margin-bottom: 16px"><ChatDotRound /></el-icon>
          <p style="color: #909399; font-size: 14px">开始与AI助手对话吧！</p>
          <p style="color: #C0C4CC; font-size: 12px; margin-top: 8px">我可以帮您解答合同审核相关问题</p>
        </div>
        <div
          v-for="(message, index) in messages"
          :key="index"
          :class="['message-item', message.role === 'user' ? 'user-message' : 'ai-message']"
        >
          <div class="message-avatar">
            <el-icon v-if="message.role === 'user'" style="font-size: 20px; color: #409EFF"><User /></el-icon>
            <el-icon v-else style="font-size: 20px; color: #67C23A"><Cpu /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-text" v-html="formatMessage(message.content)"></div>
            <span v-if="message.streaming" class="stream-cursor"></span>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
        </div>
        <div v-if="loading && !hasStreamingMessage" class="message-item ai-message">
          <div class="message-avatar">
            <el-icon class="is-loading" style="font-size: 20px; color: #67C23A"><Loading /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-text">
              <span class="typing-indicator">
                <span></span><span></span><span></span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-container">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          placeholder="输入您的问题..."
          @keydown.ctrl.enter="sendMessage"
          @keydown.meta.enter="sendMessage"
          :disabled="loading"
          resize="none"
        />
        <div class="input-actions">
          <div class="input-tips">
            <span style="color: #909399; font-size: 12px">按 Ctrl+Enter 或 Cmd+Enter 发送</span>
          </div>
          <el-button
            type="primary"
            :icon="Promotion"
            @click="sendMessage"
            :loading="loading"
            :disabled="!inputMessage.trim() || loading"
          >
            发送
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ChatDotRound, User, Cpu, Loading, Delete, Promotion } from '@element-plus/icons-vue'
import api from '@/utils/api'

const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref(null)
const currentModel = ref('')
const hasStreamingMessage = computed(() => messages.value.some(message => message.streaming))

// 获取当前使用的AI模型
const fetchCurrentModel = async () => {
  try {
    const response = await api.get('/reviews/ai-model-configs/')
    const configs = response.data.results || []
    const defaultConfig = configs.find(c => c.is_default && c.is_active)
    if (defaultConfig) {
      currentModel.value = defaultConfig.default_model || '未配置'
    }
  } catch (error) {
    console.error('获取AI模型配置失败:', error)
  }
}

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) {
    return
  }

  const userMessage = {
    role: 'user',
    content: inputMessage.value.trim(),
    timestamp: new Date()
  }

  messages.value.push(userMessage)
  const question = inputMessage.value.trim()
  inputMessage.value = ''
  loading.value = true

  // 滚动到底部
  await nextTick()
  scrollToBottom()

  try {
    const aiMessage = {
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      streaming: true
    }

    messages.value.push(aiMessage)
    const aiMessageIndex = messages.value.length - 1
    await nextTick()
    scrollToBottom()

    await streamChatResponse(question, messages.value.slice(0, -2), aiMessageIndex)

    if (!messages.value[aiMessageIndex].content.trim()) {
      messages.value[aiMessageIndex].content = '抱歉，我无法回答这个问题。'
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    const errorMessage = error.message || error.response?.data?.error || error.response?.data?.detail || '发送消息失败，请稍后重试'
    ElMessage.error(errorMessage)
    
    const errorMsg = {
      role: 'assistant',
      content: `抱歉，发生了错误：${errorMessage}`,
      timestamp: new Date()
    }
    messages.value.push(errorMsg)
  } finally {
    const streamingMessage = messages.value.find(message => message.streaming)
    if (streamingMessage) {
      streamingMessage.streaming = false
    }
    loading.value = false
    await nextTick()
    scrollToBottom()
  }
}

const streamChatResponse = async (question, historyMessages, aiMessageIndex) => {
  const token = localStorage.getItem('token')
  const response = await fetch('/api/reviews/ai-model-configs/stream-chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify({
      message: question,
      history: historyMessages.map(msg => ({
        role: msg.role,
        content: msg.content
      }))
    })
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(parseStreamError(errorText, response.status))
  }

  if (!response.body) {
    throw new Error('当前浏览器不支持流式响应')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    await appendStreamContent(aiMessageIndex, decoder.decode(value, { stream: true }))
  }

  const rest = decoder.decode()
  if (rest) {
    await appendStreamContent(aiMessageIndex, rest)
  }
}

const appendStreamContent = async (messageIndex, chunk) => {
  if (!chunk || !messages.value[messageIndex]) return
  const batchSize = Math.max(1, Math.ceil(chunk.length / 80))
  for (let index = 0; index < chunk.length; index += batchSize) {
    if (!messages.value[messageIndex]) return
    messages.value[messageIndex].content += chunk.slice(index, index + batchSize)
    await nextTick()
    scrollToBottom()
    await waitNextFrame()
  }
}

const waitNextFrame = () => new Promise(resolve => {
  if (typeof requestAnimationFrame === 'function') {
    requestAnimationFrame(resolve)
  } else {
    setTimeout(resolve, 16)
  }
})

const parseStreamError = (text, status) => {
  try {
    const data = JSON.parse(text)
    if (Array.isArray(data.detail)) {
      return data.detail.map(item => item.msg).join('；') || `请求失败（${status}）`
    }
    return data.detail || data.error || data.message || `请求失败（${status}）`
  } catch (error) {
    return text || `请求失败（${status}）`
  }
}

// 清空对话
const clearChat = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有对话记录吗？', '提示', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    })
    messages.value = []
    ElMessage.success('对话已清空')
  } catch (error) {
    // 用户取消
  }
}

// 格式化消息内容：先转义HTML，再渲染常用Markdown语法
const formatMessage = (content) => {
  if (!content) return ''
  const lines = String(content).replace(/\r\n/g, '\n').split('\n')
  const html = []

  for (let index = 0; index < lines.length; index++) {
    const line = lines[index]
    const trimmed = line.trim()

    if (!trimmed) {
      continue
    }

    const fenceMatch = trimmed.match(/^```(\w+)?\s*$/)
    if (fenceMatch) {
      const language = fenceMatch[1] || ''
      const codeLines = []
      index++
      while (index < lines.length && !lines[index].trim().startsWith('```')) {
        codeLines.push(lines[index])
        index++
      }
      html.push(
        `<pre class="markdown-code-block"><code data-language="${escapeAttribute(language)}">${escapeHtml(codeLines.join('\n'))}</code></pre>`
      )
      continue
    }

    if (/^---+$|^\*\*\*+$|^___+$/.test(trimmed)) {
      html.push('<hr>')
      continue
    }

    const headingMatch = trimmed.match(/^(#{1,6})\s+(.+)$/)
    if (headingMatch) {
      const level = headingMatch[1].length
      html.push(`<h${level}>${renderInlineMarkdown(headingMatch[2])}</h${level}>`)
      continue
    }

    if (isTableStart(lines, index)) {
      const headers = splitTableRow(lines[index])
      index += 2
      const rows = []
      while (index < lines.length && isTableRow(lines[index])) {
        rows.push(splitTableRow(lines[index]))
        index++
      }
      index--
      html.push(renderMarkdownTable(headers, rows))
      continue
    }

    if (/^>\s?/.test(trimmed)) {
      const quoteLines = []
      while (index < lines.length && /^>\s?/.test(lines[index].trim())) {
        quoteLines.push(lines[index].trim().replace(/^>\s?/, ''))
        index++
      }
      index--
      html.push(`<blockquote>${quoteLines.map(renderInlineMarkdown).join('<br>')}</blockquote>`)
      continue
    }

    if (/^\s*[-*+]\s+/.test(line)) {
      const items = []
      while (index < lines.length && /^\s*[-*+]\s+/.test(lines[index])) {
        items.push(lines[index].replace(/^\s*[-*+]\s+/, ''))
        index++
      }
      index--
      html.push(`<ul>${items.map(item => `<li>${renderInlineMarkdown(item)}</li>`).join('')}</ul>`)
      continue
    }

    if (/^\s*\d+\.\s+/.test(line)) {
      const items = []
      while (index < lines.length && /^\s*\d+\.\s+/.test(lines[index])) {
        items.push(lines[index].replace(/^\s*\d+\.\s+/, ''))
        index++
      }
      index--
      html.push(`<ol>${items.map(item => `<li>${renderInlineMarkdown(item)}</li>`).join('')}</ol>`)
      continue
    }

    const paragraphLines = [line]
    while (
      index + 1 < lines.length &&
      lines[index + 1].trim() &&
      !isMarkdownBlockStart(lines[index + 1], lines[index + 2])
    ) {
      paragraphLines.push(lines[index + 1])
      index++
    }
    html.push(`<p>${paragraphLines.map(renderInlineMarkdown).join('<br>')}</p>`)
  }

  return html.join('')
}

const escapeHtml = (value) => String(value)
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;')

const escapeAttribute = (value) => escapeHtml(value).replace(/`/g, '&#96;')

const renderInlineMarkdown = (text) => {
  const codeSegments = []
  let rendered = escapeHtml(text).replace(/`([^`]+)`/g, (_, code) => {
    codeSegments.push(`<code>${code}</code>`)
    return `@@CODE_${codeSegments.length - 1}@@`
  })

  rendered = rendered
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/__([^_]+)__/g, '<strong>$1</strong>')
    .replace(/~~([^~]+)~~/g, '<del>$1</del>')
    .replace(/\*([^*\n]+)\*/g, '<em>$1</em>')
    .replace(/_([^_\n]+)_/g, '<em>$1</em>')

  return rendered.replace(/@@CODE_(\d+)@@/g, (_, index) => codeSegments[Number(index)] || '')
}

const isMarkdownBlockStart = (line, nextLine = '') => {
  const trimmed = line.trim()
  return (
    !trimmed ||
    /^```/.test(trimmed) ||
    /^(#{1,6})\s+/.test(trimmed) ||
    /^>\s?/.test(trimmed) ||
    /^\s*[-*+]\s+/.test(line) ||
    /^\s*\d+\.\s+/.test(line) ||
    /^---+$|^\*\*\*+$|^___+$/.test(trimmed) ||
    isTableStart([line, nextLine], 0)
  )
}

const isTableStart = (lines, index) => {
  return isTableRow(lines[index] || '') && isTableSeparator(lines[index + 1] || '')
}

const isTableRow = (line) => line.includes('|') && splitTableRow(line).length > 1

const isTableSeparator = (line) => {
  const cells = splitTableRow(line)
  return cells.length > 1 && cells.every(cell => /^:?-{3,}:?$/.test(cell))
}

const splitTableRow = (line) => line
  .trim()
  .replace(/^\|/, '')
  .replace(/\|$/, '')
  .split('|')
  .map(cell => cell.trim())

const renderMarkdownTable = (headers, rows) => {
  const head = headers.map(header => `<th>${renderInlineMarkdown(header)}</th>`).join('')
  const body = rows
    .map(row => `<tr>${headers.map((_, index) => `<td>${renderInlineMarkdown(row[index] || '')}</td>`).join('')}</tr>`)
    .join('')
  return `<div class="markdown-table-wrap"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) {
    return '刚刚'
  } else if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  } else {
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 监听消息变化，自动滚动
watch(() => messages.value.length, () => {
  nextTick(() => {
    scrollToBottom()
  })
})

onMounted(() => {
  fetchCurrentModel()
})
</script>

<style scoped>
.chat-window {
  padding: 20px;
  height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

/* 确保 el-card 的 body 部分也能正确设置高度 */
.chat-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
  padding: 0;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 24px;
  background: #fdfefe;
  min-height: 0;
  max-height: 100%;
  position: relative;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
}

.message-item {
  display: flex;
  margin-bottom: 20px;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-message {
  flex-direction: row-reverse;
}

.user-message .message-content {
  background: linear-gradient(135deg, #4f9bff 0%, #76b4ff 100%);
  color: white;
  margin-right: 12px;
  margin-left: 60px;
  border: 1px solid rgba(79, 155, 255, 0.16);
  box-shadow: 0 8px 20px rgba(79, 155, 255, 0.12);
}

.ai-message .message-content {
  background: #ffffff;
  color: #2b3445;
  margin-left: 12px;
  margin-right: 60px;
  border: 1px solid #e3eaf5;
  box-shadow: 0 10px 28px rgba(31, 43, 77, 0.06);
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid #e3eaf5;
  background-color: #fff;
}

.user-message .message-avatar {
  border-color: #cfe3ff;
  background-color: #edf6ff;
}

.ai-message .message-avatar {
  border-color: #d8eee3;
  background-color: #f0fbf5;
}

.message-content {
  max-width: 70%;
  padding: 14px 18px;
  border-radius: 10px;
  word-wrap: break-word;
}

.message-text {
  line-height: 1.6;
  font-size: 14px;
}

.message-text :deep(p) {
  margin: 0 0 10px;
}

.message-text :deep(p:last-child),
.message-text :deep(ul:last-child),
.message-text :deep(ol:last-child),
.message-text :deep(blockquote:last-child),
.message-text :deep(pre:last-child),
.message-text :deep(.markdown-table-wrap:last-child) {
  margin-bottom: 0;
}

.message-text :deep(h1),
.message-text :deep(h2),
.message-text :deep(h3),
.message-text :deep(h4),
.message-text :deep(h5),
.message-text :deep(h6) {
  margin: 14px 0 8px;
  color: #1f2430;
  font-weight: 700;
  line-height: 1.35;
}

.message-text :deep(h1:first-child),
.message-text :deep(h2:first-child),
.message-text :deep(h3:first-child),
.message-text :deep(h4:first-child),
.message-text :deep(h5:first-child),
.message-text :deep(h6:first-child) {
  margin-top: 0;
}

.message-text :deep(h1) {
  font-size: 22px;
}

.message-text :deep(h2) {
  font-size: 20px;
}

.message-text :deep(h3) {
  font-size: 18px;
}

.message-text :deep(h4),
.message-text :deep(h5),
.message-text :deep(h6) {
  font-size: 16px;
}

.message-text :deep(ul),
.message-text :deep(ol) {
  margin: 0 0 10px;
  padding-left: 22px;
}

.message-text :deep(li) {
  margin: 4px 0;
}

.message-text :deep(blockquote) {
  margin: 0 0 10px;
  padding: 8px 12px;
  color: #586174;
  border-left: 4px solid #9fb6d8;
  border-radius: 0 6px 6px 0;
  background: #f5f8fd;
}

.message-text :deep(a) {
  color: #1677ff;
  font-weight: 600;
  text-decoration: none;
}

.message-text :deep(a:hover) {
  text-decoration: underline;
}

.message-text :deep(strong) {
  color: #1f2430;
  font-weight: 700;
}

.message-text :deep(del) {
  color: #8a93a5;
}

.stream-cursor {
  display: inline-block;
  width: 2px;
  height: 16px;
  margin-left: 2px;
  vertical-align: -2px;
  background: #67c23a;
  animation: cursorBlink 0.9s infinite;
}

@keyframes cursorBlink {
  0%, 45% {
    opacity: 1;
  }
  46%, 100% {
    opacity: 0;
  }
}

.message-text :deep(code) {
  background-color: #edf4ff;
  padding: 2px 6px;
  border-radius: 4px;
  color: #315078;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 13px;
}

.message-text :deep(.markdown-code-block) {
  margin: 0 0 12px;
  padding: 12px;
  overflow-x: auto;
  color: #edf3ff;
  border-radius: 8px;
  background: #1f2937;
}

.message-text :deep(.markdown-code-block code) {
  display: block;
  padding: 0;
  color: inherit;
  white-space: pre;
  background: transparent;
}

.message-text :deep(.markdown-table-wrap) {
  max-width: 100%;
  margin: 0 0 12px;
  overflow-x: auto;
}

.message-text :deep(table) {
  width: 100%;
  min-width: 360px;
  border-collapse: collapse;
  font-size: 13px;
}

.message-text :deep(th),
.message-text :deep(td) {
  padding: 8px 10px;
  text-align: left;
  border: 1px solid #dce3ef;
}

.message-text :deep(th) {
  color: #2b3445;
  font-weight: 700;
  background: #f5f8fd;
}

.message-text :deep(hr) {
  height: 1px;
  margin: 14px 0;
  border: 0;
  background: #dce3ef;
}

.user-message .message-text :deep(code) {
  background-color: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.user-message .message-text :deep(strong),
.user-message .message-text :deep(h1),
.user-message .message-text :deep(h2),
.user-message .message-text :deep(h3),
.user-message .message-text :deep(h4),
.user-message .message-text :deep(h5),
.user-message .message-text :deep(h6),
.user-message .message-text :deep(a) {
  color: #fff;
}

.user-message .message-text :deep(blockquote) {
  color: rgba(255, 255, 255, 0.88);
  border-left-color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.12);
}

.message-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 6px;
}

.ai-message .message-time {
  color: #909399;
}

.typing-indicator {
  display: inline-flex;
  gap: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #409EFF;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.7;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

.input-container {
  padding: 16px;
  background: #ffffff;
  border-top: 1px solid #e3eaf5;
  flex-shrink: 0;
  box-shadow: 0 -8px 22px rgba(31, 43, 77, 0.04);
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.input-tips {
  flex: 1;
}

/* 滚动条样式 */
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-track {
  background: #eef3fa;
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb {
  background: #c8d3e3;
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: #aab8cc;
}
</style>
