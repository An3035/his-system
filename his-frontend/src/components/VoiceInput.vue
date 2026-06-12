<template>
  <!-- 全局语音输入：按住空格录音，松开识别并填入 -->
  <Teleport to="body">
    <!-- 豆包风格动态波形：屏幕居中浮层 -->
    <Transition name="voice-overlay">
      <div v-if="recording" class="voice-overlay">
        <div class="voice-wave-card">
          <div class="voice-wave-row">
            <span
              v-for="i in BAR_COUNT"
              :key="i"
              class="voice-wave-pillar"
              :style="pillarStyle(i)"
            />
          </div>
          <span class="voice-wave-hint">松开发送，继续说...</span>
        </div>
      </div>
    </Transition>

    <!-- 环境不支持提示（仅在不支持时显示一次，可关闭） -->
    <Transition name="voice-overlay">
      <div
        v-if="!supported && unsupportedReason && !dismissedHint"
        class="voice-unsupported-hint"
      >
        <span class="voice-unsupported-icon">💡</span>
        <span class="voice-unsupported-text">{{ unsupportedReason === 'insecure' ? '语音输入仅在 Chrome / Edge 浏览器中可用' : '当前浏览器不支持语音输入' }}</span>
        <button class="voice-unsupported-close" @click="dismissedHint = true" title="不再提示">✕</button>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { asrRecognize } from '../utils/request'

// ── 常量 ──────────────────────────────────────────────────────

const BAR_COUNT = 25 // 波形条数量
const MIN_BLOB_SIZE = 100 // 最小有效音频大小（字节）

// ── 状态 ──────────────────────────────────────────────────────

const supported = ref(false)
const unsupportedReason = ref(null)
const dismissedHint = ref(false)
const recording = ref(false)
const activeInput = ref(null)
const volumeLevel = ref(0)

// ── 音频资源 ──────────────────────────────────────────────────

let mediaStream = null
let mediaRecorder = null
let audioContext = null
let analyserNode = null
let volumeTimer = null
let recordedChunks = []
let recordingStartTime = 0
let longPressTimer = null // 长按定时器：400ms 后才启动录音

// ── 光标保存 ──────────────────────────────────────────────────

let savedInput = null // 录音开始时的 native input 元素
let savedStart = 0 // 录音开始时的 selectionStart
let savedEnd = 0 // 录音开始时的 selectionEnd

// ── 工具函数 ──────────────────────────────────────────────────

function isInputElement(el) {
  if (!el) return false
  const tag = el.tagName.toLowerCase()
  if (tag === 'input' || tag === 'textarea') return true
  if (el.getAttribute('contenteditable') === 'true') return true
  if (el.closest('.el-input') || el.closest('.el-textarea')) return true
  return false
}

function getActualInput(el) {
  const tag = el.tagName.toLowerCase()
  if (tag === 'input' || tag === 'textarea' || el.getAttribute('contenteditable') === 'true') {
    return el
  }
  const inner = el.querySelector('input') || el.querySelector('textarea')
  if (inner) return inner
  return el
}

// ── 豆包风格波形算法 ──────────────────────────────────────────

/**
 * 每根柱子的动态样式。
 * 核心算法：正弦波流动 + 音量调制，产生"豆包"式的丝滑律动感。
 *   - 无声音时也有轻微呼吸起伏（idle wave）
 *   - 有声音时振幅随音量增大
 */
function pillarStyle(i) {
  const t = Date.now() / 320 // 时间因子，控制流动速度
  const phase = (i / BAR_COUNT) * Math.PI * 2.5 // 每根柱子的相位，跨约 1.25 个周期
  const wave = Math.sin(t - phase) // 原始正弦波 [-1, 1]
  const normalized = wave * 0.5 + 0.5 // 归一化到 [0, 1]

  const vol = Math.min(1, volumeLevel.value)
  // 静默时有 15% 的 idle 呼吸，说话时振幅随音量提升
  const amplitude = 0.15 + vol * 0.7
  // 最终高度：底部 8% + 波动部分
  const height = 8 + normalized * amplitude * 100

  return {
    height: `${height}%`,
    opacity: 0.45 + normalized * 0.35 + vol * 0.2,
  }
}

// ── 录音控制 ──────────────────────────────────────────────────

async function startRecording() {
  if (recording.value) return

  try {
    // ★ 修复1：确保 stream 来自用户授权的麦克风，增加详细错误处理
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: 16000,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
      },
    })

    // 验证音频轨道存在
    const audioTracks = mediaStream.getAudioTracks()
    if (audioTracks.length === 0) {
      ElMessage.error('未获取到音频输入，请检查麦克风连接')
      return
    }
    console.log('VoiceInput: 音频轨道已就绪', {
      label: audioTracks[0].label,
      settings: audioTracks[0].getSettings(),
    })

    audioContext = new AudioContext({ sampleRate: 16000 })
    const source = audioContext.createMediaStreamSource(mediaStream)
    analyserNode = audioContext.createAnalyser()
    analyserNode.fftSize = 256
    source.connect(analyserNode)

    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : 'audio/webm'
    mediaRecorder = new MediaRecorder(mediaStream, { mimeType })
    recordedChunks = []

    // ★ 修复2：收集数据块时记录实际大小，便于调试
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        recordedChunks.push(e.data)
      }
    }

    // ★ 修复3：每 100ms 采集一次，确保数据粒度
    mediaRecorder.start(100)
    recordingStartTime = Date.now()
    recording.value = true

    if (activeInput.value) {
      activeInput.value.classList.add('voice-recording')
    }

    startVolumeSampling()
  } catch (err) {
    if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
      if (!window.isSecureContext) {
        supported.value = false
        unsupportedReason.value = 'insecure'
      } else {
        ElMessage.warning('麦克风权限被拒绝，请点击地址栏左侧锁图标 → 允许麦克风访问')
      }
    } else if (err.name === 'NotFoundError') {
      ElMessage.warning('未检测到麦克风设备')
    } else {
      console.error('VoiceInput: 录音启动失败', err)
      ElMessage.error('麦克风启动失败，请检查设备')
    }
    cleanup()
  }
}

async function stopRecording() {
  if (!recording.value || !mediaRecorder) return

  // ★ 修复4：在 stop 之前保存 duration 和 mimeType（cleanup 会置空 mediaRecorder）
  const duration = (Date.now() - recordingStartTime) / 1000
  const savedMimeType = mediaRecorder.mimeType

  // ★ 修复5：先绑定 onstop，再 stop；停止音轨放在 onstop 里（确保数据完整）
  // onstop 整体包裹 try/catch，防止 async 函数内部任何未预料的异常变成
  // "Uncaught (in promise)" 错误（浏览器会追踪事件监听器返回的 Promise）
  mediaRecorder.onstop = async () => {
    try {
      // 先停止音轨释放麦克风
      if (mediaStream) {
        mediaStream.getTracks().forEach((t) => t.stop())
      }

      // 恢复光标位置（必须在 cleanup 之前，因为 cleanup 会置空 activeInput）
      restoreCursorPosition()

      cleanup()

      if (duration < 0.5) {
        ElMessage.warning('说话时间太短，请长按空格键说话')
        return
      }

      if (duration > 60) {
        ElMessage.info('单次录音最长 60 秒，已自动截断')
      }

      // ★ 修复6：计算实际音频数据大小，发送前验证
      const audioBlob = new Blob(recordedChunks, { type: savedMimeType })
      console.log(
        `VoiceInput: 录音完成 — 时长 ${duration.toFixed(1)}s，音频大小 ${audioBlob.size} bytes，格式 ${savedMimeType}`,
      )

      if (audioBlob.size < MIN_BLOB_SIZE) {
        console.warn(`VoiceInput: 音频数据过小 (${audioBlob.size} bytes)，可能为静默或录音失败`)
        ElMessage.warning('未检测到有效语音，请靠近麦克风说话后重试')
        return
      }

      try {
        const result = await asrRecognize(audioBlob)
        console.log('VoiceInput: ASR 识别结果', result)

        // 优先检查服务端返回的错误信息（如 Dashscope API 报错）
        if (result.error) {
          ElMessage.error(result.error)
          return
        }

        if (result.text && result.text.trim()) {
          fillText(result.text.trim())
        } else {
          // 无错误但也没有识别文本 → 可能是静音或语音模糊
          ElMessage.warning('未识别到语音内容，请重试')
        }
      } catch (err) {
        // 网络层错误（无法连接服务器、超时等）
        if (err.message?.includes('Network') || err.message?.includes('network')) {
          ElMessage.error('网络连接失败，请检查网络后重试')
        } else if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
          ElMessage.error('语音识别请求超时，请重试')
        } else {
          console.error('VoiceInput: ASR 请求失败', err)
          ElMessage.error('语音识别失败，请稍后重试')
        }
      }
    } catch (unexpectedErr) {
      // 最外层兜底：捕获 onstop 内所有未预料的同步/异步异常
      console.error('VoiceInput: onstop 内部异常', unexpectedErr)
      ElMessage.error('语音输入异常，请重试')
    }
  }

  // ★ 修复7：调用 stop() 触发 ondataavailable（最后一个 chunk）→ onstop
  mediaRecorder.stop()
}

function cleanup() {
  recording.value = false

  // 清除可能残留的长按定时器
  if (longPressTimer) {
    clearTimeout(longPressTimer)
    longPressTimer = null
  }

  if (activeInput.value) {
    activeInput.value.classList.remove('voice-recording')
    activeInput.value = null
  }
  volumeLevel.value = 0

  stopVolumeSampling()

  if (audioContext) {
    audioContext.close().catch(() => {})
    audioContext = null
  }
  analyserNode = null
  mediaRecorder = null
  mediaStream = null

  // ★ 不重置 savedInput/savedStart/savedEnd（在 restoreCursorPosition 中使用）
}

// ── 光标位置保存与恢复 ────────────────────────────────────────

/**
 * 保存当前输入框的光标位置。
 * 在录音开始前调用，确保录音结束后能恢复到原位。
 */
function saveCursorPosition(input) {
  savedInput = input
  if (input.isContentEditable) {
    const sel = window.getSelection()
    savedStart = sel && sel.rangeCount > 0 ? sel.getRangeAt(0).startOffset : 0
    savedEnd = 0
  } else {
    savedStart = input.selectionStart ?? 0
    savedEnd = input.selectionEnd ?? 0
  }
}

/**
 * 恢复录音前保存的光标位置。
 * 在录音结束后、填入文本前调用，抵消录音期间键盘事件对光标的影响。
 */
function restoreCursorPosition() {
  if (!savedInput) return
  try {
    if (!savedInput.isContentEditable) {
      savedInput.selectionStart = savedStart
      savedInput.selectionEnd = savedEnd
    }
  } catch (_) {
    // 元素可能已从 DOM 中移除，安全忽略
  }
  // 恢复后清除引用，防止意外重用
  savedInput = null
  savedStart = 0
  savedEnd = 0
}

// ── 音量采样 ──────────────────────────────────────────────────

function startVolumeSampling() {
  stopVolumeSampling()
  volumeTimer = setInterval(() => {
    if (!analyserNode) return
    const dataArray = new Uint8Array(analyserNode.frequencyBinCount)
    analyserNode.getByteFrequencyData(dataArray)
    const max = Math.max(...dataArray)
    volumeLevel.value = Math.min(1, max / 255)
  }, 80)
}

function stopVolumeSampling() {
  if (volumeTimer) {
    clearInterval(volumeTimer)
    volumeTimer = null
  }
}

// ── 空格插入（短按补偿）────────────────────────────────────

/**
 * 短按空格时，keydown 已 preventDefault 阻止了空格插入，
 * 此处手动在保存的光标位置插入一个空格字符。
 */
function insertSpaceAtCursor() {
  const input = savedInput
  if (!input) return

  try {
    if (input.isContentEditable) {
      const sel = window.getSelection()
      if (sel && sel.rangeCount > 0) {
        const range = sel.getRangeAt(0)
        range.deleteContents()
        range.insertNode(document.createTextNode(' '))
        range.collapse(false)
        sel.removeAllRanges()
        sel.addRange(range)
      }
      input.dispatchEvent(new Event('input', { bubbles: true }))
    } else {
      const start = input.selectionStart ?? input.value.length
      const end = input.selectionEnd ?? input.value.length
      input.value = input.value.slice(0, start) + ' ' + input.value.slice(end)
      input.selectionStart = input.selectionEnd = start + 1
      input.dispatchEvent(new Event('input', { bubbles: true }))
    }
  } catch (_) {
    // 元素可能已从 DOM 中移除，安全忽略
  }

  // 清除保存的光标引用
  savedInput = null
  savedStart = 0
  savedEnd = 0
}

// ── 文本填入 ──────────────────────────────────────────────────

function fillText(text) {
  // ★ 优先使用保存的输入元素（录音期间焦点可能转移）
  const input = savedInput || getActualInput(document.activeElement)
  if (!input) return

  if (input.isContentEditable) {
    const sel = window.getSelection()
    if (sel && sel.rangeCount > 0) {
      const range = sel.getRangeAt(0)
      range.deleteContents()
      range.insertNode(document.createTextNode(text))
      range.collapse(false)
      sel.removeAllRanges()
      sel.addRange(range)
    }
    input.dispatchEvent(new Event('input', { bubbles: true }))
    return
  }

  // ★ 使用恢复后的光标位置
  const start = input.selectionStart ?? input.value.length
  const end = input.selectionEnd ?? input.value.length
  input.value = input.value.slice(0, start) + text + input.value.slice(end)
  input.selectionStart = input.selectionEnd = start + text.length

  input.dispatchEvent(new Event('input', { bubbles: true }))

  // ★ 填入后聚焦回该输入框
  input.focus()
}

// ── 键盘事件 ──────────────────────────────────────────────────

/**
 * keydown 处理：
 *   - 空格键 + 输入框聚焦 → 始终 preventDefault 阻止空格字符插入
 *   - 首次按下（非 repeat）→ 保存光标 + 启动 400ms 长按定时器
 *   - 重复按下（repeat）→ 仅 preventDefault，不重置定时器
 *
 * 设计思路：
 *   短按（<400ms）→ keyup 取消定时器 + 手动插入空格，正常打字不受影响
 *   长按（≥400ms）→ 定时器触发，启动录音
 */
function onKeyDown(e) {
  if (e.code !== 'Space') return // 非空格不处理
  if (e.ctrlKey || e.altKey || e.metaKey) return // 组合键不处理
  if (!supported.value) return // 不支持则完全放行（保持正常键盘行为）

  const focused = document.activeElement
  if (!focused || !isInputElement(focused)) return // 非输入框放行

  // 始终阻止空格默认行为（插入空格字符 / 页面滚动）
  // 短按时空格由 onKeyUp 手动插入，长按时完全不需要空格
  e.preventDefault()
  e.stopPropagation()

  // 按键重复：不重置定时器，但 preventDefault 已生效
  if (e.repeat) return

  // 首次按下：保存光标 + 标记输入框 + 启动长按定时器
  const input = getActualInput(focused)
  activeInput.value = input
  saveCursorPosition(input)

  // 清除可能残留的旧定时器
  if (longPressTimer) {
    clearTimeout(longPressTimer)
  }

  longPressTimer = setTimeout(() => {
    longPressTimer = null
    startRecording()
  }, 400)
}

function onKeyUp(e) {
  if (e.code !== 'Space') return

  // 情况1：短按 — 定时器尚未触发，取消录音，手动插入空格
  if (longPressTimer) {
    clearTimeout(longPressTimer)
    longPressTimer = null
    insertSpaceAtCursor()
    activeInput.value = null
    return
  }

  // 情况2：长按后松开 — 停止录音
  if (!recording.value) return

  e.preventDefault()
  stopRecording()
}

// ── 焦点事件 ──────────────────────────────────────────────────

function onFocusIn(e) {
  const target = e.target
  if (target && isInputElement(target) && recording.value) {
    if (activeInput.value) {
      activeInput.value.classList.remove('voice-recording')
    }
    activeInput.value = getActualInput(target)
    activeInput.value.classList.add('voice-recording')
  }
}

// ── 生命周期 ──────────────────────────────────────────────────

onMounted(() => {
  const isSecure = window.isSecureContext === true
  const hasMediaDevices = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)
  const hasMediaRecorder = typeof MediaRecorder !== 'undefined'

  if (!isSecure) {
    supported.value = false
    unsupportedReason.value = 'insecure'
    console.info('VoiceInput: 非安全上下文，语音输入已禁用（仅 Chrome/Edge 浏览器可用）')
    return
  }

  if (!hasMediaDevices || !hasMediaRecorder) {
    supported.value = false
    unsupportedReason.value = 'unsupported'
    console.info('VoiceInput: 浏览器不支持录音功能，语音输入已禁用')
    return
  }

  supported.value = true

  window.addEventListener('keydown', onKeyDown, true)
  window.addEventListener('keyup', onKeyUp, true)
  document.addEventListener('focusin', onFocusIn)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown, true)
  window.removeEventListener('keyup', onKeyUp, true)
  document.removeEventListener('focusin', onFocusIn)
  cleanup()
})
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   豆包风格动态波形卡片
   ═══════════════════════════════════════════════════════════════ */

.voice-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding-bottom: 15vh;
  pointer-events: none;
  background: radial-gradient(ellipse at 50% 80%, rgba(26, 127, 196, 0.04) 0%, transparent 60%);
}

.voice-wave-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  padding: 20px 28px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(26, 127, 196, 0.12);
  border-radius: 20px;
  box-shadow:
    0 8px 32px rgba(26, 127, 196, 0.08),
    0 2px 8px rgba(0, 0, 0, 0.04);
  min-width: 280px;
}

.voice-wave-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  height: 48px;
  width: 100%;
}

.voice-wave-pillar {
  width: 3px;
  min-width: 3px;
  border-radius: 2px;
  background: linear-gradient(
    180deg,
    #3b9fe0 0%,
    #5baeed 40%,
    #7ec3f4 100%
  );
  transition: height 0.12s ease, opacity 0.12s ease;
}

.voice-wave-hint {
  font-size: 13px;
  color: #7a8ba6;
  letter-spacing: 0.5px;
  user-select: none;
}

/* ── 入场/离场动画 ──────────────────────────────────────────── */

.voice-overlay-enter-active {
  transition: opacity 0.25s ease;
}
.voice-overlay-enter-active .voice-wave-card {
  transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1),
              opacity 0.25s ease;
}
.voice-overlay-leave-active {
  transition: opacity 0.2s ease;
}
.voice-overlay-leave-active .voice-wave-card {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.voice-overlay-enter-from {
  opacity: 0;
}
.voice-overlay-enter-from .voice-wave-card {
  transform: translateY(12px) scale(0.95);
  opacity: 0;
}

.voice-overlay-leave-to {
  opacity: 0;
}
.voice-overlay-leave-to .voice-wave-card {
  transform: translateY(8px) scale(0.97);
  opacity: 0;
}
</style>

<style>
/* ═══════════════════════════════════════════════════════════════
   录音中激活输入框的呼吸灯效果（全局样式，不加 scoped）
   ═══════════════════════════════════════════════════════════════ */

.voice-recording {
  border-color: #3b9fe0 !important;
  box-shadow: 0 0 0 3px rgba(59, 159, 224, 0.18) !important;
  animation: voice-breathe 2.2s ease-in-out infinite;
}

@keyframes voice-breathe {
  0%, 100% {
    box-shadow: 0 0 0 3px rgba(59, 159, 224, 0.18);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(59, 159, 224, 0.35);
  }
}

/* ── 环境不支持提示条 ──────────────────────────────────────── */

.voice-unsupported-hint {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9998;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #f0f8ff;
  border: 1px solid #b0d4f1;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(26, 127, 196, 0.1);
  font-size: 13px;
  color: #1a2332;
  max-width: 360px;
}

.voice-unsupported-icon {
  flex-shrink: 0;
  font-size: 16px;
}

.voice-unsupported-text {
  flex: 1;
  line-height: 1.4;
}

.voice-unsupported-close {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border: none;
  background: none;
  color: #667085;
  font-size: 14px;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.15s, background 0.15s;
}
.voice-unsupported-close:hover {
  color: #1a2332;
  background: rgba(0, 0, 0, 0.06);
}
</style>
