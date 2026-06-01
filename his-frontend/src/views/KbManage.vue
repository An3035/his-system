<template>
  <div class="kb-container">
    <h2 class="page-title">知识库管理</h2>

    <!-- 上传区 -->
    <el-card class="upload-card">
      <template #header>
        <span>上传医疗文档</span>
      </template>
      <el-upload
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :file-list="uploadFiles"
        accept=".pdf,.txt,.docx,.doc"
        :limit="1"
      >
        <el-icon class="el-icon--upload"><Plus /></el-icon>
        <div class="el-upload__text">拖拽文件到此处或 <em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 PDF / TXT / DOCX 格式，最大 10MB</div>
        </template>
      </el-upload>
      <el-button
        type="primary"
        :disabled="!pendingFile || uploading"
        :loading="uploading"
        @click="uploadFile"
        style="margin-top:12px"
      >
        {{ uploading ? '上传解析中...' : '上传到知识库' }}
      </el-button>
    </el-card>

    <!-- 搜索区 -->
    <el-card class="search-card" style="margin-top:16px">
      <template #header>
        <span>语义检索</span>
      </template>
      <div style="display:flex;gap:8px">
        <el-input
          v-model="searchQuery"
          placeholder="输入医疗问题检索知识库..."
          @keyup.enter="searchKb"
          clearable
        />
        <el-button type="primary" @click="searchKb" :loading="searching">搜索</el-button>
      </div>
      <div v-if="searchResults.length" style="margin-top:16px">
        <el-card
          v-for="(r, i) in searchResults"
          :key="i"
          shadow="hover"
          style="margin-bottom:10px"
        >
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span style="font-weight:600">{{ r.document_title }}</span>
              <el-tag size="small" type="success">相关度 {{ (r.score * 100).toFixed(0) }}%</el-tag>
            </div>
          </template>
          <div style="font-size:13px;color:#555;white-space:pre-wrap;line-height:1.7">{{ r.content }}</div>
        </el-card>
      </div>
      <el-empty v-if="searchDone && !searchResults.length" description="未找到相关知识" />
    </el-card>

    <!-- 文档列表 -->
    <el-card class="doc-list-card" style="margin-top:16px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>已上传文档</span>
          <el-button size="small" text @click="loadDocuments">刷新</el-button>
        </div>
      </template>
      <el-table :data="documents" border v-loading="docLoading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="文档名称" min-width="180" />
        <el-table-column prop="filename" label="文件名" min-width="200" />
        <el-table-column prop="doc_type" label="类型" width="80" />
        <el-table-column prop="chunk_count" label="分块数" width="80" />
        <el-table-column prop="created_at" label="上传时间" width="160">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" type="danger" text @click="deleteDoc(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 清理 -->
    <el-card class="cleanup-card" style="margin-top:16px">
      <template #header>
        <span>维护</span>
      </template>
      <el-button @click="cleanup" :loading="cleaning">
        清理重复/过时内容
      </el-button>
      <div v-if="cleanResult !== null" style="margin-top:8px;color:#67c23a">
        已清理 {{ cleanResult }} 条重复内容
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import request from '../utils/request'
import { formatDate } from '../utils/date'

const pendingFile = ref<File | null>(null)
const uploading = ref(false)
const uploadFiles = ref<any[]>([])

const searchQuery = ref('')
const searching = ref(false)
const searchDone = ref(false)
const searchResults = ref<any[]>([])

const documents = ref<any[]>([])
const docLoading = ref(false)

const cleaning = ref(false)
const cleanResult = ref<number | null>(null)

const handleFileChange = (file: any) => {
  pendingFile.value = file.raw
  uploadFiles.value = [file]
}

const uploadFile = async () => {
  if (!pendingFile.value) return
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', pendingFile.value)
    const res = await request.post('/api/kb/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success(res.data.message || '上传成功')
    pendingFile.value = null
    uploadFiles.value = []
    loadDocuments()
  } catch (err: any) {
    ElMessage.error('上传失败：' + (err.response?.data?.detail || err.message))
  } finally {
    uploading.value = false
  }
}

const searchKb = async () => {
  if (!searchQuery.value.trim()) return
  searching.value = true
  searchDone.value = false
  try {
    const res = await request.get('/api/kb/search', {
      params: { q: searchQuery.value, top_k: 5 }
    })
    searchResults.value = res.data.results || []
    searchDone.value = true
  } catch (err: any) {
    ElMessage.error('搜索失败：' + (err.response?.data?.detail || err.message))
  } finally {
    searching.value = false
  }
}

const loadDocuments = async () => {
  docLoading.value = true
  try {
    const res = await request.get('/api/kb/documents')
    documents.value = res.data || []
  } catch (err: any) {
    console.error('加载文档失败', err)
  } finally {
    docLoading.value = false
  }
}

const deleteDoc = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定删除该文档？', '提示', { type: 'warning' })
    await request.delete(`/api/kb/documents/${id}`)
    ElMessage.success('删除成功')
    loadDocuments()
  } catch (err: any) {
    if (err !== 'cancel')
      ElMessage.error('删除失败：' + (err.response?.data?.detail || err.message))
  }
}

const cleanup = async () => {
  cleaning.value = true
  try {
    const res = await request.post('/api/kb/cleanup')
    cleanResult.value = res.data.removed_count
    ElMessage.success(`清理完成，移除了 ${cleanResult.value} 条重复内容`)
    loadDocuments()
  } catch (err: any) {
    ElMessage.error('清理失败：' + (err.response?.data?.detail || err.message))
  } finally {
    cleaning.value = false
  }
}

onMounted(loadDocuments)
</script>

<style scoped>
.kb-container {
  padding: 16px;
}
.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #303133;
}
</style>
