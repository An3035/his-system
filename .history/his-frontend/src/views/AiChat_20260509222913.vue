<template>
  <div class="ai-root">

    <!-- ── 顶栏 ── -->
    <div class="ai-topbar">
      <div class="ai-topbar-left">
        <div class="ai-avatar-sm">🤖</div>
        <div>
          <div class="ai-name">AI 医疗助手</div>
          <div class="ai-model">阿里云百炼 · {{ modelName }}</div>
        </div>
      </div>
      <button class="clear-btn" @click="clearChat">🗑 清空对话</button>
    </div>

    <!-- ── 消息区 ── -->
    <div class="ai-messages" ref="msgRef">

      <!-- 欢迎屏 -->
      <div v-if="messages.length === 0" class="welcome">
        <div class="welcome-orb"></div>
        <div class="welcome-icon">🏥</div>
        <div class="welcome-title">您好，我是 HIS AI 助手</div>
        <div class="welcome-sub">可以询问药物知识、诊断建议、系统使用等问题，也可上传文件让 AI 分析</div>
        <div class="quick-grid">
          <button v-for="q in quickList" :key="q.text" class="quick-card" @click="quickAsk(q.text)">
            <span class="quick-icon">{{ q.icon }}</span>
            <span>{{ q.text }}</span>
          </button>
        </div>
      </div>

      <!-- 消息气泡 -->
      <template v-for="(msg, i) in messages" :key="i">
        <div :class="['msg-row', msg.role === 'user' ? 'row-user' : 'row-ai']">
          <div class="msg-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
          <div class="msg-body">
            <div v-if="msg.files?.length" class="file-tags">
              <span v-for="f in msg.files" :key="f" class="file-tag">📎 {{ f }}</span>
            </div>
            <div :class="['bubble', msg.role === 'user' ? 'bubble-user' : 'bubble-ai']">
              <pre class="bubble-text">{{ msg.content }}</pre>
            </div>
            <div class="msg-time">{{ msg.time }}</div>
          </div>
        </div>
      </template>

      <!-- 打字中 -->
      <div v-if="loading" class="msg-row row-ai">
        <div class="msg-avatar">🤖</div>
        <div class="msg-body">
          <div class="bubble bubble-ai typing">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- ── 文件预览条 ── -->
    <div v-if="pendingFiles.length" class="file-preview-bar">
      <div v-for="(f, i) in pendingFiles" :key="i" class="file-chip">
        <span class="file-chip-icon">{{ fileIcon(f.name) }}</span>
        <span class="file-chip-name">{{ f.name }}</span>
        <span class="file-chip-size">{{ formatSize(f.size) }}</span>
        <button class="file-chip-rm" @click="removeFile(i)">✕</button>
      </div>
    </div>

    <!-- ── 输入区 ── -->
    <div class="ai-input-area">
      <div class="input-box" :class="{ 'input-focused': inputFocused }">
        <textarea
          v-model="inputText"
          class="input-ta"
          placeholder="输入问题…（Enter 换行，Ctrl+Enter 发送）"
          rows="3"
          @focus="inputFocused = true"
          @blur="inputFocused = false"
          @keydown.ctrl.enter.prevent="send"
        />
        <div class="input-actions">
          <label class="action-btn" title="上传文件（txt/csv/json/py 等，最大 2MB）">
            📎
            <input type="file" class="hidden-input"
              accept=".txt,.md,.csv,.json,.pdf,.py,.js,.ts,.vue,.html,.xml"
              multiple
              @change="handleFileSelect" />
          </label>
          <button class="action-btn" title="AI 患者病历摘要（输入患者ID）" @click="showSummaryPrompt">
            🩺
          </button>
          <button
            class="send-btn"
            :disabled="loading || (!inputText.trim() && !pendingFiles.length)"
            @click="send"
          >
            <template v-if="!loading">
              发送
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </template>
            <span v-else class="spinner"></span>
          </button>
        </div>
      </div>
      <div class="input-hint">Ctrl+Enter 发送 · 📎 支持上传 txt / csv / json / py 等文本文件（最大 2MB）</div>
    </div>

  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request'

const messages     = ref([])
const inputText    = ref('')
const loading      = ref(false)
const inputFocused = ref(false)
const msgRef       = ref(null)
const pendingFiles = ref([])
const modelName    = ref('qwen-turbo')

const quickList = [
  { icon: '💊', text: '阿莫西林和布洛芬可以同时服用吗？' },
  { icon: '🩺', text: '高血压患者的用药注意事项有哪些？' },
  { icon: '📋', text: '血常规检查主要指标的正常范围？' },
  { icon: '🏥', text: '如何在系统中为患者办理入院手续？' },
  { icon: '⚗️', text: '头孢类抗生素的主要禁忌症？' },
  { icon: '📊', text: '院长查询模块包含哪些统计报表？' },
]

const now = () => {
  const d = new Date()
  return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

const scrollBottom = async () => {
  await nextTick()
  if (msgRef.value) msgRef.value.scrollTop = msgRef.value.scrollHeight
}

const handleFileSelect = async (e) => {
  const files = Array.from(e.target.files || [])
  for (const f of files) {
    if (f.size > 2 * 1024 * 1024) { ElMessage.warning(`${f.name} 超过 2MB，已跳过`); continue }
    pendingFiles.value.push(f)
  }
  e.target.value = ''
}

const removeFile = (i) => pendingFiles.value.splice(i, 1)

const readFileText = (file) => new Promise((resolve) => {
  const r = new FileReader()
  r.onload = (e) => resolve(e.target.result)
  r.onerror = () => resolve(`[无法读取: ${file.name}]`)
  r.readAsText(file, 'utf-8')
})

const fileIcon = (name) => {
  const m = { pdf:'📄', csv:'📊', json:'🔧', py:'🐍', js:'📜', ts:'📜', vue:'💚', md:'📝' }
  return m[name.split('.').pop()?.toLowerCase()] || '📎'
}
const formatSize = (b) => b < 1024 ? b + ' B' : b < 1048576 ? (b/1024).toFixed(1)+' KB' : (b/1048576).toFixed(1)+' MB'

const send = async () => {
  const text = inputText.value.trim()
  if (!text && !pendingFiles.value.length) return
  if (loading.value) return

  let fullMessage = text
  const fileNames = pendingFiles.value.map(f => f.name)
  if (pendingFiles.value.length > 0) {
    const parts = []
    for (const f of pendingFiles.value) {
      const content = await readFileText(f)
      const truncated = content.length > 6000 ? content.slice(0,6000)+'\n...[已截断]' : content
      parts.push(`=== 文件: ${f.name} ===\n${truncated}`)
    }
    fullMessage = (text ? text + '\n\n' : '请分析以下文件内容：\n\n') + parts.join('\n\n')
  }

  messages.value.push({ role:'user', content: text || '(分析上传文件)', files: fileNames, time: now() })
  inputText.value = ''
  pendingFiles.value = []
  loading.value = true
  await scrollBottom()

  const history = messages.value.slice(-13, -1).map(m => ({ role: m.role, content: m.content }))

  try {
    const res = await request.post('/api/ai/chat', {
      message: fullMessage, history, context_type: 'general', context_id: null
    })
    modelName.value = res.data.model || modelName.value
    messages.value.push({ role: 'assistant', content: res.data.reply, time: now() })
  } catch (err) {
    messages.value.push({ role: 'assistant', content: `⚠️ 请求失败：${err.response?.data?.detail || err.message}`, time: now() })
  } finally {
    loading.value = false
    await scrollBottom()
  }
}

const quickAsk = (q) => { inputText.value = q; send() }
const clearChat = () => { messages.value = [] }

const showSummaryPrompt = async () => {
  try {
    const { value } = await ElMessageBox.prompt('请输入患者ID', 'AI 患者摘要', {
      confirmButtonText: '生成', cancelButtonText: '取消',
      inputPattern: /^\d+$/, inputErrorMessage: '请输入数字ID',
    })
    const res = await request.post(`/api/ai/summarize-patient/${value}`)
    messages.value.push({ role: 'assistant', content: res.data.summary || JSON.stringify(res.data, null, 2), time: now() })
    await scrollBottom()
  } catch { /* cancelled */ }
}
</script>

<style scoped>
.ai-root {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 96px);
  background: #f5f7fb;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,.07);
}

/* 顶栏 */
.ai-topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px; background: #fff;
  border-bottom: 1px solid #e8ecf2; flex-shrink: 0;
}
.ai-topbar-left { display: flex; align-items: center; gap: 12px; }
.ai-avatar-sm {
  width: 40px; height: 40px;
  background: linear-gradient(135deg, #0f2744, #1a7fc4);
  border-radius: 12px; display: flex; align-items: center;
  justify-content: center; font-size: 20px; flex-shrink: 0;
}
.ai-name  { font-size: 15px; font-weight: 600; color: #1a2332; }
.ai-model { font-size: 11px; color: #8fa3b8; margin-top: 1px; }
.clear-btn {
  padding: 6px 14px; border: 1px solid #e0e6ef; border-radius: 8px;
  background: #fff; color: #667085; font-size: 13px; cursor: pointer; transition: all .15s;
}
.clear-btn:hover { border-color: #ef4444; color: #ef4444; background: #fef2f2; }

/* 消息区 */
.ai-messages { flex: 1; overflow-y: auto; padding: 20px 24px 8px; scroll-behavior: smooth; }
.ai-messages::-webkit-scrollbar { width: 5px; }
.ai-messages::-webkit-scrollbar-thumb { background: #d1dae6; border-radius: 3px; }

/* 欢迎屏 */
.welcome { display: flex; flex-direction: column; align-items: center; padding: 30px 20px 20px; text-align: center; position: relative; }
.welcome-orb {
  position: absolute; top: 20px;
  width: 200px; height: 200px;
  background: radial-gradient(circle, rgba(26,127,196,.1), transparent 70%);
  border-radius: 50%; pointer-events: none;
}
.welcome-icon  { font-size: 48px; margin-bottom: 12px; position: relative; }
.welcome-title { font-size: 20px; font-weight: 700; color: #1a2332; margin-bottom: 8px; }
.welcome-sub   { font-size: 13px; color: #8fa3b8; max-width: 460px; margin-bottom: 28px; line-height: 1.6; }
.quick-grid    { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; width: 100%; max-width: 700px; }
.quick-card {
  display: flex; align-items: flex-start; gap: 8px; padding: 12px 14px;
  background: #fff; border: 1.5px solid #e8ecf2; border-radius: 12px;
  font-size: 13px; color: #3a5068; cursor: pointer; text-align: left;
  transition: all .15s; line-height: 1.4;
}
.quick-card:hover { border-color: #1a7fc4; color: #1a7fc4; background: #f0f8ff; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(26,127,196,.12); }
.quick-icon { font-size: 18px; flex-shrink: 0; margin-top: 1px; }

/* 消息行 */
.msg-row { display: flex; gap: 12px; margin-bottom: 20px; align-items: flex-start; }
.row-user { flex-direction: row-reverse; }
.msg-avatar {
  width: 36px; height: 36px; border-radius: 10px; background: #e8f0fa;
  display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0;
}
.row-user .msg-avatar { background: linear-gradient(135deg, #1a7fc4, #0f5fa0); }
.msg-body { max-width: 72%; display: flex; flex-direction: column; gap: 4px; }
.row-user .msg-body { align-items: flex-end; }

.file-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.file-tag  { padding: 2px 8px; background: #e8f0fa; color: #1a7fc4; border-radius: 6px; font-size: 11px; }

.bubble { padding: 12px 16px; border-radius: 16px; max-width: 100%; word-break: break-word; }
.bubble-user { background: linear-gradient(135deg, #1a7fc4, #0f5fa0); color: #fff; border-radius: 16px 4px 16px 16px; }
.bubble-ai   { background: #fff; color: #1a2332; border-radius: 4px 16px 16px 16px; box-shadow: 0 1px 4px rgba(0,0,0,.06); border: 1px solid #e8ecf2; }
.bubble-text { margin: 0; white-space: pre-wrap; font-family: 'PingFang SC','Microsoft YaHei',sans-serif; font-size: 14px; line-height: 1.75; }

.msg-time { font-size: 11px; color: #b0bece; }

.typing { padding: 14px 20px; display: flex; align-items: center; gap: 5px; }
.typing span { width: 8px; height: 8px; background: #1a7fc4; border-radius: 50%; display: inline-block; animation: bounce 1.2s ease-in-out infinite; opacity:.5; }
.typing span:nth-child(2) { animation-delay: .2s; }
.typing span:nth-child(3) { animation-delay: .4s; }
@keyframes bounce { 0%,80%,100%{transform:translateY(0);opacity:.5} 40%{transform:translateY(-6px);opacity:1} }

/* 文件预览条 */
.file-preview-bar { display: flex; flex-wrap: wrap; gap: 8px; padding: 8px 20px; background: #f0f8ff; border-top: 1px solid #d0e8f8; flex-shrink: 0; }
.file-chip { display: flex; align-items: center; gap: 6px; padding: 5px 10px; background: #fff; border: 1px solid #b3d6f0; border-radius: 8px; font-size: 12px; color: #1a5f8f; }
.file-chip-name { font-weight: 500; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-chip-size { color: #7fb3d4; }
.file-chip-rm { background: none; border: none; cursor: pointer; color: #8fa3b8; font-size: 13px; padding: 0 2px; }
.file-chip-rm:hover { color: #ef4444; }

/* 输入区 */
.ai-input-area { padding: 12px 20px 16px; background: #fff; border-top: 1px solid #e8ecf2; flex-shrink: 0; }
.input-box { border: 1.5px solid #dde3ed; border-radius: 14px; background: #f8fafc; transition: border-color .2s, box-shadow .2s; overflow: hidden; }
.input-box.input-focused { border-color: #1a7fc4; box-shadow: 0 0 0 3px rgba(26,127,196,.1); background: #fff; }
.input-ta { width: 100%; border: none; outline: none; background: transparent; padding: 14px 16px 8px; font-size: 14px; font-family: 'PingFang SC','Microsoft YaHei',sans-serif; color: #1a2332; resize: none; line-height: 1.6; box-sizing: border-box; }
.input-ta::placeholder { color: #b0bece; }
.input-actions { display: flex; align-items: center; gap: 8px; padding: 8px 12px 10px; border-top: 1px solid #f0f2f5; }
.action-btn { width: 36px; height: 36px; border: 1px solid #e0e6ef; border-radius: 8px; background: #fff; cursor: pointer; font-size: 17px; display: flex; align-items: center; justify-content: center; transition: all .15s; flex-shrink: 0; }
.action-btn:hover { border-color: #1a7fc4; background: #f0f8ff; }
.hidden-input { display: none; }
.send-btn { margin-left: auto; display: flex; align-items: center; gap: 6px; padding: 0 20px; height: 36px; background: linear-gradient(135deg, #1a7fc4, #0f5fa0); color: #fff; border: none; border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer; transition: opacity .15s, transform .15s; }
.send-btn:hover:not(:disabled) { opacity: .9; transform: translateY(-1px); }
.send-btn:disabled { opacity: .5; cursor: not-allowed; }
.spinner { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,.3); border-top-color: #fff; border-radius: 50%; animation: spin .7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.input-hint { font-size: 11px; color: #b0bece; margin-top: 6px; padding-left: 4px; }
</style>