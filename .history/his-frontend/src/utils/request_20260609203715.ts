import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '',
  timeout: 60000
})

// 请求拦截器
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器 — 401 自动跳转登录
request.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('role')
      // 避免重复跳转
      if (window.location.pathname !== '/login') {
        ElMessage.warning('登录已过期，请重新登录')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

/**
 * 语音识别：上传 WebM 音频 Blob，返回识别文本。
 */
export async function asrRecognize(audioBlob: Blob) {
  const formData = new FormData()
  formData.append('file', audioBlob, 'recording.webm')

  // 🔥 修复：删除手动设置的 Content-Type！！！
  const res = await request.post('/api/ai/asr', formData, {
    timeout: 30000,
  })
  return res.data
}

export default request