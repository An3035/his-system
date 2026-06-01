<template>
  <div class="ai-root">

    <!-- ════════ 侧边栏：会话列表 ════════ -->
    <div class="ai-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-inner">
        <div class="sidebar-header">
          <div class="sidebar-title-row">
            <span class="sidebar-title">历史对话</span>
            <button class="collapse-btn" @click="toggleSidebar" title="收起侧栏">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                <polyline points="15 6 9 12 15 18"/>
              </svg>
            </button>
          </div>
          <button
            :class="['new-chat-btn', { active: !activeSessionId }]"
            @click="newSession"
          ><span class="new-chat-icon">＋</span> 新对话</button>
        </div>

        <!-- 搜索框 -->
        <div class="sidebar-search">
          <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#b0bece" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input v-model="searchQuery" class="search-input" placeholder="搜索会话…" />
        </div>

        <!-- 会话列表 -->
        <div class="sidebar-sessions" v-loading="sessionLoading">
          <div
            v-for="s in filteredSessions"
            :key="s.id"
            :class="['session-item', { active: s.id === activeSessionId }]"
            @click="selectSession(s.id)"
          >
            <input
              type="checkbox"
              class="session-cb"
              :checked="selection.includes(s.id)"
              @click.stop="toggleSelect(s.id)"
            />
            <div class="session-info">
              <!-- 内联重命名 -->
              <template v-if="renamingId === s.id">
                <input
                  ref="renameInputRef"
                  v-model="renameText"
                  class="rename-input"
                  placeholder="输入标题…"
                  @keydown.enter="saveRename(s.id)"
                  @keydown.esc="cancelRename"
                  @blur="saveRename(s.id)"
                  @click.stop
                  @mousedown.stop
                />
              </template>
              <template v-else>
                <div
                  class="session-title"
                  :class="{ 'no-title': !s.title }"
                  @dblclick.stop="startRename(s)"
                >{{ s.title || '新会话' }}</div>
              </template>
              <div class="session-meta">{{ formatTime(s.updated_at) }}</div>
            </div>
            <button
              class="session-del" title="删除"
              :disabled="deletingIds.has(s.id)"
              @click.stop="confirmDelete(s.id)"
            >
              <span v-if="deletingIds.has(s.id)" class="mini-spinner"></span>
              <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
            </button>
          </div>

          <div v-if="!sessionLoading && filteredSessions.length === 0" class="sidebar-empty">
            <div class="sidebar-empty-icon">💬</div>
            <div>{{ searchQuery ? '未找到匹配会话' : '暂无历史对话' }}</div>
          </div>

          <!-- 加载更多 -->
          <div v-if="sessionHasMore && !searchQuery" class="load-more-wrap">
            <button class="load-more-btn" :disabled="sessionLoadingMore" @click="loadMoreSessions">
              <span v-if="sessionLoadingMore" class="mini-spinner"></span>
              <span v-else>加载更多</span>
            </button>
          </div>
        </div>

        <!-- 批量操作栏 -->
        <transition name="fade">
          <div v-if="selection.length > 0" class="batch-bar">
            <span class="batch-info">已选 {{ selection.length }} 项</span>
            <button class="batch-del-btn" :disabled="batchDeleting" @click="batchDelete">
              <span v-if="batchDeleting" class="mini-spinner"></span>
              <span v-else>删除</span>
            </button>
            <button class="batch-cancel-btn" @click="selection = []">取消</button>
          </div>
        </transition>
      </div>
    </div>

    <!-- 侧栏折叠展开按钮 -->
    <button class="sidebar-toggle" @click="toggleSidebar" :title="sidebarCollapsed ? '展开侧栏' : '收起侧栏'">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <polyline v-if="sidebarCollapsed" points="9 18 15 12 9 6"/>
        <polyline v-else points="15 18 9 12 15 6"/>
      </svg>
    </button>

    <!-- ════════ 主聊天区 ════════ -->
    <div class="ai-chat-area">

      <!-- ── 顶栏 ── -->
      <div class="ai-topbar">
        <div class="ai-topbar-left">
          <div class="ai-avatar-sm">🤖</div>
          <div>
            <div class="ai-name">AI 医疗助手</div>
            <div class="ai-model">
              阿里云百炼 · {{ modelName }}
              <span v-if="activeSessionId && currentSessionTitle" class="topbar-sep">·</span>
              <span v-if="currentSessionTitle" class="topbar-session-title">{{ currentSessionTitle }}</span>
            </div>
          </div>
        </div>
        <div class="ai-topbar-right">
          <button v-if="activeSessionId" class="rename-btn" @click="startRenameActive" title="重命名">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </button>
          <button class="clear-btn" @click="newSession">＋ 新对话</button>
        </div>
      </div>

      <!-- ── 消息区 ── -->
      <div class="ai-messages" ref="msgRef">

        <!-- 欢迎屏 -->
        <div v-if="messages.length === 0 && !activeSessionId" class="welcome">
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
              <div v-if="msg.time" class="msg-time">{{ msg.time }}</div>
            </div>
          </div>
        </template>

        <!-- 文件处理中 -->
        <div v-if="fileLoading" class="msg-row row-ai">
          <div class="msg-avatar">📎</div>
          <div class="msg-body">
            <div class="bubble bubble-ai" style="font-size:13px;color:#667085">
              正在读取文件内容...
            </div>
          </div>
        </div>

        <!-- 打字中 -->
        <div v-if="loading" class="msg-row row-ai">
          <div class="msg-avatar">🤖</div>
          <div class="msg-body">
            <div class="bubble bubble-ai typing"><span></span><span></span><span></span></div>
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
                multiple @change="handleFileSelect" />
            </label>
            <button class="action-btn" title="AI 患者病历摘要（输入患者ID）" @click="showSummaryPrompt">🩺</button>
            <button :class="['action-btn', kbMode ? 'action-active' : '']" title="知识库检索模式" @click="kbMode = !kbMode">📚</button>
            <button
              class="send-btn" :disabled="loading || (!inputText.trim() && !pendingFiles.length)" @click="send"
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as pdfjsLib from 'pdfjs-dist'
import request from '../utils/request'

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL('pdfjs-dist/build/pdf.worker.mjs', import.meta.url).toString()

// ── 侧栏 ────────────────────────────────────────────────
const sidebarCollapsed = ref(localStorage.getItem('aiSidebarCollapsed') === '1')
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('aiSidebarCollapsed', sidebarCollapsed.value ? '1' : '0')
}

// ── 搜索 ────────────────────────────────────────────────
const searchQuery = ref('')

// ── 会话状态 ────────────────────────────────────────────
const sessions = ref([])
const activeSessionId = ref(null)
const selection = ref([])
const sessionLoading = ref(false)
const sessionPage = ref(1)
const sessionHasMore = ref(false)
const sessionLoadingMore = ref(false)
const renamingId = ref(null)
const renameText = ref('')
const renameInputRef = ref(null)
const deletingIds = ref(new Set())
const batchDeleting = ref(false)

// ── 聊天状态 ────────────────────────────────────────────
const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const fileLoading = ref(false)
const inputFocused = ref(false)
const msgRef = ref(null)
const pendingFiles = ref([])
const modelName = ref('qwen-turbo')
const kbMode = ref(false)

const quickList = [
  { icon: '💊', text: '阿莫西林和布洛芬可以同时服用吗？' },
  { icon: '🩺', text: '高血压患者的用药注意事项有哪些？' },
  { icon: '📋', text: '血常规检查主要指标的正常范围？' },
  { icon: '🏥', text: '如何在系统中为患者办理入院手续？' },
  { icon: '⚗️', text: '头孢类抗生素的主要禁忌症？' },
  { icon: '📊', text: '院长查询模块包含哪些统计报表？' },
]

// ── 计算属性 ────────────────────────────────────────────

const currentSessionTitle = computed(() => {
  if (!activeSessionId.value) return ''
  const s = sessions.value.find(s => s.id === activeSessionId.value)
  return s ? (s.title || '新会话') : ''
})

const filteredSessions = computed(() => {
  if (!searchQuery.value.trim()) return sessions.value
  const q = searchQuery.value.trim().toLowerCase()
  return sessions.value.filter(s => (s.title || '').toLowerCase().includes(q))
})

// ── 时间工具 ────────────────────────────────────────────

const now = () => {
  const d = new Date()
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const formatTime = (isoStr) => {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  const now = new Date()
  const diffMs = now - d
  const diffMin = Math.floor(diffMs / 60000)
  const diffHour = Math.floor(diffMs / 3600000)
  const diffDay = Math.floor(diffMs / 86400000)

  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin} 分钟前`
  if (diffHour < 6) return `${diffHour} 小时前`
  if (diffDay < 1) return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  if (diffDay < 2) return `昨天 ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  if (d.getFullYear() === now.getFullYear()) return `${d.getMonth() + 1}月${d.getDate()}日`
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
}

const formatMsgTime = (timeStr) => {
  if (!timeStr) return now()
  const d = new Date(timeStr)
  if (isNaN(d.getTime())) return timeStr
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const scrollBottom = async () => {
  await nextTick()
  if (msgRef.value) msgRef.value.scrollTop = msgRef.value.scrollHeight
}

// ── 会话管理 ────────────────────────────────────────────

const PAGE_SIZE = 30

const fetchSessions = async () => {
  sessionLoading.value = true
  sessionPage.value = 1
  try {
    const res = await request.get('/api/ai/sessions', {
      params: { page: 1, page_size: PAGE_SIZE },
    })
    sessions.value = res.data || []
    sessionHasMore.value = (res.data || []).length >= PAGE_SIZE
  } catch { /* silent */ } finally {
    sessionLoading.value = false
  }
}

const loadMoreSessions = async () => {
  if (sessionLoadingMore.value || !sessionHasMore.value) return
  sessionLoadingMore.value = true
  try {
    const nextPage = sessionPage.value + 1
    const res = await request.get('/api/ai/sessions', {
      params: { page: nextPage, page_size: PAGE_SIZE },
    })
    const items = res.data || []
    sessions.value = [...sessions.value, ...items]
    sessionPage.value = nextPage
    sessionHasMore.value = items.length >= PAGE_SIZE
  } catch { /* silent */ } finally {
    sessionLoadingMore.value = false
  }
}

const selectSession = async (id) => {
  if (loading.value) return
  try {
    const res = await request.get(`/api/ai/sessions/${id}`)
    const data = res.data
    messages.value = (data.messages || []).map(m => ({
      role: m.role,
      content: m.content,
      time: m.time ? formatMsgTime(m.time) : '',
      files: m.files || [],
    }))
    activeSessionId.value = id
    localStorage.setItem('lastAiSessionId', String(id))
    await scrollBottom()
  } catch {
    ElMessage.error('加载会话失败')
  }
}

const newSession = () => {
  if (loading.value) return
  messages.value = []
  activeSessionId.value = null
  pendingFiles.value = []
  selection.value = []
  searchQuery.value = ''
}

// ── 删除 ────────────────────────────────────────────────

const confirmDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该对话吗？', '删除确认', {
      confirmButtonText: '删除', cancelButtonText: '取消',
      confirmButtonClass: 'el-button--danger', type: 'warning',
    })
    deletingIds.value = new Set([...deletingIds.value, id])
    await request.delete(`/api/ai/sessions/${id}`)
    ElMessage.success('已删除')
    if (activeSessionId.value === id) newSession()
    await fetchSessions()
  } catch { /* cancelled */ } finally {
    const next = new Set(deletingIds.value)
    next.delete(id)
    deletingIds.value = next
  }
}

const toggleSelect = (id) => {
  const idx = selection.value.indexOf(id)
  if (idx === -1) selection.value.push(id)
  else selection.value.splice(idx, 1)
}

const batchDelete = async () => {
  if (selection.value.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selection.value.length} 个对话吗？`,
      '批量删除确认',
      {
        confirmButtonText: '删除', cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger', type: 'warning',
      }
    )
    batchDeleting.value = true
    await request.post('/api/ai/sessions/batch-delete', { ids: selection.value })
    ElMessage.success(`已删除 ${selection.value.length} 个会话`)
    if (activeSessionId.value && selection.value.includes(activeSessionId.value)) {
      newSession()
    }
    selection.value = []
    await fetchSessions()
  } catch { /* cancelled */ } finally {
    batchDeleting.value = false
  }
}

// ── 内联重命名 ──────────────────────────────────────────

const startRename = (s) => {
  renamingId.value = s.id
  renameText.value = s.title || ''
  nextTick(() => {
    // 使用 querySelector 因为 ref 在 v-for 中不直接可用
    const el = document.querySelector('.rename-input')
    if (el) el.focus()
  })
}

const startRenameActive = () => {
  if (activeSessionId.value) {
    const s = sessions.value.find(x => x.id === activeSessionId.value)
    if (s) startRename(s)
  }
}

const saveRename = async (id) => {
  const text = renameText.value.trim()
  const prevId = renamingId.value
  renamingId.value = null
  if (!text || !prevId) return
  try {
    await request.put(`/api/ai/sessions/${id}`, { title: text })
    await fetchSessions()
  } catch {
    ElMessage.error('重命名失败')
  }
}

const cancelRename = () => {
  renamingId.value = null
}

// ── 文件处理 ────────────────────────────────────────────

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
  const isPdf = file.name.toLowerCase().endsWith('.pdf')
  if (isPdf) {
    const reader = new FileReader()
    reader.onload = async (e) => {
      try {
        const arrayBuf = e.target.result
        const pdf = await pdfjsLib.getDocument({ data: arrayBuf }).promise
        const texts = []
        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i)
          const content = await page.getTextContent()
          texts.push(content.items.map(item => item.str).join(' '))
        }
        resolve(texts.join('\n--- 分页 ---\n'))
      } catch { resolve(`[PDF 解析失败: ${file.name}]`) }
    }
    reader.onerror = () => resolve(`[无法读取: ${file.name}]`)
    reader.readAsArrayBuffer(file)
  } else {
    const r = new FileReader()
    r.onload = (e) => resolve(e.target.result)
    r.onerror = () => resolve(`[无法读取: ${file.name}]`)
    r.readAsText(file, 'utf-8')
  }
})

const fileIcon = (name) => {
  const m = { pdf:'📄', csv:'📊', json:'🔧', py:'🐍', js:'📜', ts:'📜', vue:'💚', md:'📝' }
  return m[name.split('.').pop()?.toLowerCase()] || '📎'
}
const formatSize = (b) => b < 1024 ? `${b} B` : b < 1048576 ? `${(b/1024).toFixed(1)} KB` : `${(b/1048576).toFixed(1)} MB`

// ── 发送消息 ────────────────────────────────────────────

const send = async () => {
  const text = inputText.value.trim()
  if (!text && !pendingFiles.value.length) return
  if (loading.value) return

  let fullMessage = text
  const fileNames = pendingFiles.value.map(f => f.name)

  if (pendingFiles.value.length > 0) {
    fileLoading.value = true
    await scrollBottom()
    const parts = []
    for (const f of pendingFiles.value) {
      const content = await readFileText(f)
      parts.push(`=== 文件: ${f.name} ===\n${content.length > 6000 ? content.slice(0, 6000) + '\n...[已截断]' : content}`)
    }
    fullMessage = (text ? text + '\n\n' : '请分析以下文件内容：\n\n') + parts.join('\n\n')
    fileLoading.value = false
  }

  if (kbMode.value && text) {
    try {
      const kbRes = await request.get('/api/kb/search', { params: { q: text, top_k: 3 } })
      const kbResults = kbRes.data.results || []
      if (kbResults.length) {
        const kbCtx = kbResults.map((r, i) => `[知识库 ${i+1}: ${r.document_title}]\n${r.content}`).join('\n\n')
        fullMessage = `【系统提示：以下是知识库中与用户问题相关的内容，请基于这些内容回答用户问题。如果知识库内容不足以回答问题，请如实说明。】\n\n知识库内容：\n${kbCtx}\n\n用户问题：${text}`
      }
    } catch { /* KB不可用时降级为普通对话 */ }
  }

  messages.value.push({ role: 'user', content: text || '(分析上传文件)', files: fileNames, time: now() })
  inputText.value = ''
  pendingFiles.value = []
  loading.value = true
  await scrollBottom()

  const payload = {
    message: fullMessage,
    context_type: kbMode.value ? 'knowledge_base' : 'general',
    context_id: null,
    history: [],
  }
  if (activeSessionId.value) payload.session_id = activeSessionId.value

  try {
    const res = await request.post('/api/ai/chat', payload)
    const data = res.data
    modelName.value = data.model || modelName.value

    if (data.session_id && data.session_id !== activeSessionId.value) {
      activeSessionId.value = data.session_id
      localStorage.setItem('lastAiSessionId', String(data.session_id))
    }

    messages.value.push({ role: 'assistant', content: data.reply, time: now() })
    await fetchSessions()
  } catch (err) {
    messages.value.push({ role: 'assistant', content: `⚠️ 请求失败：${err.response?.data?.detail || err.message}`, time: now() })
  } finally {
    loading.value = false
    await scrollBottom()
  }
}

const quickAsk = (q) => { inputText.value = q; send() }

// ── 患者摘要 ────────────────────────────────────────────

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

// ── 初始化 ──────────────────────────────────────────────

onMounted(async () => {
  await fetchSessions()
  const lastId = localStorage.getItem('lastAiSessionId')
  if (lastId) {
    const id = parseInt(lastId, 10)
    if (sessions.value.some(s => s.id === id)) {
      await selectSession(id)
    } else {
      localStorage.removeItem('lastAiSessionId')
    }
  }
})
</script>

<style scoped>
.ai-root {
  display: flex;
  height: calc(100vh - 96px);
  background: #f5f7fb;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,.07);
}

/* ═══════════════ 侧边栏 ═══════════════ */

.ai-sidebar {
  width: 280px;
  flex-shrink: 0;
  transition: width .25s ease;
  overflow: hidden;
}
.ai-sidebar.collapsed { width: 0; }

.sidebar-inner {
  width: 280px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fafbfd;
  border-right: 1px solid #e8ecf2;
}

.sidebar-header {
  padding: 16px 14px 12px;
  border-bottom: 1px solid #e8ecf2;
  flex-shrink: 0;
}

.sidebar-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  padding-left: 2px;
}

.sidebar-title {
  font-size: 13px;
  font-weight: 600;
  color: #667085;
}

.collapse-btn {
  width: 24px; height: 24px;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  color: #b0bece;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .15s;
}
.collapse-btn:hover { border-color: #d0d8e4; color: #667085; }

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 9px 14px;
  border: 1.5px dashed #d0d8e4;
  border-radius: 10px;
  background: #fff;
  color: #3a5068;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all .15s;
}
.new-chat-btn:hover,
.new-chat-btn.active { border-color: #1a7fc4; color: #1a7fc4; background: #f0f8ff; }
.new-chat-icon { font-size: 16px; font-weight: 700; }

/* 侧栏搜索 */
.sidebar-search {
  position: relative;
  padding: 8px 10px 4px;
  flex-shrink: 0;
}
.search-icon {
  position: absolute;
  left: 20px;
  top: 16px;
  pointer-events: none;
}
.search-input {
  width: 100%;
  padding: 7px 10px 7px 30px;
  border: 1px solid #e0e6ef;
  border-radius: 8px;
  background: #fff;
  font-size: 13px;
  color: #1a2332;
  outline: none;
  box-sizing: border-box;
  transition: border-color .15s;
}
.search-input:focus { border-color: #1a7fc4; }
.search-input::placeholder { color: #b0bece; }

/* 会话列表 */
.sidebar-sessions {
  flex: 1;
  overflow-y: auto;
  padding: 4px 10px 8px;
}
.sidebar-sessions::-webkit-scrollbar { width: 4px; }
.sidebar-sessions::-webkit-scrollbar-thumb { background: #d1dae6; border-radius: 2px; }

.session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 10px 10px 6px;
  border-radius: 10px;
  cursor: pointer;
  transition: all .12s;
  margin-bottom: 2px;
}
.session-item:hover { background: #eef2f8; }
.session-item.active {
  background: #e6f0fa;
  border-left: 3px solid #1a7fc4;
  padding-left: 10px;
}

/* 复选框 — 常显半透明，hover/active 全透明 */
.session-cb {
  width: 14px;
  height: 14px;
  accent-color: #1a7fc4;
  flex-shrink: 0;
  opacity: .45;
  transition: opacity .12s;
}
.session-item:hover .session-cb,
.session-item.active .session-cb { opacity: 1; }

.session-info { flex: 1; min-width: 0; }

.session-title {
  font-size: 13px;
  font-weight: 500;
  color: #1a2332;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}
.session-title.no-title { color: #8fa3b8; font-style: italic; }

.session-meta {
  font-size: 11px;
  color: #b0bece;
  margin-top: 2px;
}

/* 内联重命名输入框 */
.rename-input {
  width: 100%;
  padding: 2px 6px;
  border: 1.5px solid #1a7fc4;
  border-radius: 4px;
  font-size: 13px;
  font-family: inherit;
  color: #1a2332;
  outline: none;
  background: #fff;
  box-sizing: border-box;
}

.session-del {
  width: 26px; height: 26px;
  border: none; border-radius: 6px;
  background: transparent;
  color: #b0bece;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all .15s;
  opacity: 0;
}
.session-item:hover .session-del { opacity: 1; }
.session-del:hover:not(:disabled) { background: #fee2e2; color: #ef4444; }
.session-del:disabled { cursor: not-allowed; opacity: .3; }

.sidebar-empty {
  text-align: center;
  padding: 40px 20px;
  color: #b0bece;
  font-size: 13px;
}
.sidebar-empty-icon { font-size: 32px; margin-bottom: 8px; }

/* 批量操作栏 */
.batch-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-top: 1px solid #e8ecf2;
  background: #f0f8ff;
  flex-shrink: 0;
}
.batch-info { font-size: 12px; color: #1a5f8f; flex: 1; }
.batch-del-btn {
  padding: 5px 14px;
  border: 1px solid #ef4444; border-radius: 6px;
  background: #fff; color: #ef4444; font-size: 12px; cursor: pointer;
  transition: all .12s;
  display: flex; align-items: center; gap: 4px;
}
.batch-del-btn:hover:not(:disabled) { background: #fef2f2; }
.batch-del-btn:disabled { opacity: .5; cursor: not-allowed; }
.batch-cancel-btn {
  padding: 5px 10px; border: 1px solid #d0d8e4; border-radius: 6px;
  background: #fff; color: #667085; font-size: 12px; cursor: pointer;
}
.batch-cancel-btn:hover { border-color: #1a7fc4; color: #1a7fc4; }

/* 侧栏折叠/展开按钮 */
.sidebar-toggle {
  width: 18px;
  flex-shrink: 0;
  background: #f5f6f8;
  border: none;
  border-left: 1px solid #e8ecf2;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #b0bece;
  transition: background .12s, color .12s;
}
.sidebar-toggle:hover { background: #e6f0fa; color: #1a7fc4; }

/* 迷你 spinner */
.mini-spinner {
  display: inline-block;
  width: 12px; height: 12px;
  border: 2px solid rgba(239,68,68,.25);
  border-top-color: #ef4444;
  border-radius: 50%;
  animation: spin .6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ═══════════════ 主聊天区 ═══════════════ */

.ai-chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* 顶栏 */
.ai-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: #fff;
  border-bottom: 1px solid #e8ecf2;
  flex-shrink: 0;
}
.ai-topbar-left { display: flex; align-items: center; gap: 12px; }
.ai-topbar-right { display: flex; align-items: center; gap: 6px; }
.ai-avatar-sm {
  width: 40px; height: 40px;
  background: linear-gradient(135deg, #0f2744, #1a7fc4);
  border-radius: 12px; display: flex; align-items: center;
  justify-content: center; font-size: 20px; flex-shrink: 0;
}
.ai-name  { font-size: 15px; font-weight: 600; color: #1a2332; }
.ai-model { font-size: 11px; color: #8fa3b8; margin-top: 1px; }
.topbar-sep { margin: 0 4px; }
.topbar-session-title { color: #1a7fc4; font-weight: 500; }

.rename-btn {
  width: 32px; height: 32px;
  border: 1px solid #e0e6ef; border-radius: 8px;
  background: #fff; color: #8fa3b8; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all .15s;
}
.rename-btn:hover { border-color: #1a7fc4; color: #1a7fc4; background: #f0f8ff; }

.clear-btn {
  padding: 6px 14px; border: 1px solid #e0e6ef; border-radius: 8px;
  background: #fff; color: #667085; font-size: 13px; cursor: pointer; transition: all .15s;
}
.clear-btn:hover { border-color: #1a7fc4; color: #1a7fc4; }

/* 消息区 */
.ai-messages { flex: 1; overflow-y: auto; padding: 20px 24px 8px; scroll-behavior: smooth; }
.ai-messages::-webkit-scrollbar { width: 5px; }
.ai-messages::-webkit-scrollbar-thumb { background: #d1dae6; border-radius: 3px; }

/* 欢迎屏 */
.welcome { display: flex; flex-direction: column; align-items: center; padding: 30px 20px 20px; text-align: center; position: relative; }
.welcome-orb { position: absolute; top: 20px; width: 200px; height: 200px; background: radial-gradient(circle, rgba(26,127,196,.1), transparent 70%); border-radius: 50%; pointer-events: none; }
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
.msg-avatar { width: 36px; height: 36px; border-radius: 10px; background: #e8f0fa; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
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
.action-active { border-color: #1a7fc4; background: #e6f4ff; }
.hidden-input { display: none; }
.send-btn { margin-left: auto; display: flex; align-items: center; gap: 6px; padding: 0 20px; height: 36px; background: linear-gradient(135deg, #1a7fc4, #0f5fa0); color: #fff; border: none; border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer; transition: opacity .15s, transform .15s; }
.send-btn:hover:not(:disabled) { opacity: .9; transform: translateY(-1px); }
.send-btn:disabled { opacity: .5; cursor: not-allowed; }
.spinner { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,.3); border-top-color: #fff; border-radius: 50%; animation: spin .7s linear infinite; }
.input-hint { font-size: 11px; color: #b0bece; margin-top: 6px; padding-left: 4px; }

/* 加载更多 */
.load-more-wrap { text-align: center; padding: 8px 0 4px; }
.load-more-btn {
  padding: 5px 16px;
  border: 1px solid #d0d8e4; border-radius: 14px;
  background: #fff; color: #667085; font-size: 12px;
  cursor: pointer; transition: all .15s;
  display: inline-flex; align-items: center; gap: 4px;
}
.load-more-btn:hover:not(:disabled) { border-color: #1a7fc4; color: #1a7fc4; }
.load-more-btn:disabled { opacity: .5; cursor: not-allowed; }

/* 过渡动画 */
.fade-enter-active, .fade-leave-active { transition: opacity .2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
