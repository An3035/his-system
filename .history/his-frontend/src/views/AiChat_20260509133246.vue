<template>
  <div class="ai-page">
    <el-card class="chat-card">
      <template #header>
        <div class="card-header">
          <span>🤖 AI 医疗助手（阿里云百炼）</span>
          <el-button size="small" @click="clearChat">清空对话</el-button>
        </div>
      </template>

      <!-- 消息列表 -->
      <div class="message-list" ref="msgListRef">
        <div v-if="messages.length === 0" class="empty-hint">
          <div class="hint-title">您好，我是 HIS AI 助手</div>
          <div class="hint-desc">您可以询问：药物相互作用、诊断建议、系统操作指引等</div>
          <div class="quick-btns">
            <el-button v-for="q in quickQuestions" :key="q" size="small" @click="quickAsk(q)">
              {{ q }}
            </el-button>
          </div>
        </div>

        <div v-for="(msg, i) in messages" :key="i"
          :class="['message-row', msg.role === 'user' ? 'user-row' : 'ai-row']">
          <div class="avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
          <div :class="['bubble', msg.role === 'user' ? 'user-bubble' : 'ai-bubble']">
            <pre class="bubble-text">{{ msg.content }}</pre>
          </div>
        </div>

        <div v-if="loading" class="message-row ai-row">
          <div class="avatar">🤖</div>
          <div class="bubble ai-bubble">
            <el-icon class="is-loading"><Loading /></el-icon> AI 正在思考...
          </div>
        </div>
      </div>

      <!-- 输入框 -->
      <div class="input-area">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="3"
          placeholder="请输入您的问题，按 Ctrl+Enter 发送..."
          @keydown.ctrl.enter="send"
        />
        <el-button type="primary" :loading="loading" @click="send" style="margin-top:8px;width:100%">
          发送 (Ctrl+Enter)
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import request from '../utils/request'

const messages  = ref([])
const inputText = ref('')
const loading   = ref(false)
const msgListRef = ref(null)

const quickQuestions = [
  '阿莫西林和布洛芬能一起服用吗？',
  '头孢类药物有哪些注意事项？',
  '如何为患者办理入院手续？',
  '血常规检查的正常参考值是多少？',
]

const scrollToBottom = async () => {
  await nextTick()
  if (msgListRef.value) {
    msgListRef.value.scrollTop = msgListRef.value.scrollHeight
  }
}

const send = async () => {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  loading.value = true
  await scrollToBottom()

  // 构建历史记录（最多取最近10条）
  const history = messages.value.slice(-11, -1).map(m => ({
    role: m.role, content: m.content
  }))

  try {
    const res = await request.post('/api/ai/chat', {
      message: text,
      history,
      context_type: 'general',
      context_id: null,
    })
    messages.value.push({ role: 'assistant', content: res.data.reply })
  } catch (err) {
    messages.value.push({ role: 'assistant', content: '⚠️ AI 服务暂时不可用：' + (err.response?.data?.detail || err.message) })
    ElMessage.error('AI 请求失败')
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

const quickAsk = (q) => {
  inputText.value = q
  send()
}

const clearChat = () => { messages.value = [] }
</script>

<style scoped>
.ai-page { height: 100%; }
.chat-card { display:flex; flex-direction:column; height: calc(100vh - 120px); }
.chat-card :deep(.el-card__body) { flex:1; display:flex; flex-direction:column; overflow:hidden; padding:16px; }
.card-header { display:flex; justify-content:space-between; align-items:center; }

/* 消息列表 */
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
  margin-bottom: 12px;
}
.empty-hint {
  text-align:center;
  padding:40px 20px;
  color:#667085;
}
.hint-title { font-size:18px; font-weight:600; margin-bottom:8px; color:#1a2332; }
.hint-desc  { font-size:14px; margin-bottom:16px; }
.quick-btns { display:flex; flex-wrap:wrap; gap:8px; justify-content:center; }

/* 消息行 */
.message-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 16px;
}
.user-row { flex-direction: row-reverse; }
.avatar { font-size: 24px; flex-shrink:0; }

.bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
}
.user-bubble { background:#1677ff; color:#fff; border-radius:12px 0 12px 12px; }
.ai-bubble   { background:#f0f2f5; color:#1a2332; border-radius:0 12px 12px 12px; }
.bubble-text { margin:0; white-space:pre-wrap; word-break:break-word; font-family:inherit; }

/* 输入区 */
.input-area { flex-shrink:0; }
</style>