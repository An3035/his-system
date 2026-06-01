<template>
  <div class="page-wrap">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>出入院管理</span>
          <div style="display:flex;gap:8px">
            <el-input v-model="searchQ" placeholder="搜索住院号/患者ID" style="width:220px" clearable @keyup.enter="loadList" />
            <el-button @click="loadList">搜索</el-button>
            <el-button type="primary" @click="openAdd">新增入院</el-button>
          </div>
        </div>
      </template>

      <el-table :data="paginatedList" border v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="admission_no" label="住院号" width="150" />
        <el-table-column prop="patient_id" label="患者ID" width="80" />
        <el-table-column prop="bed_id" label="床位ID" width="80" />
        <el-table-column prop="department_id" label="科室ID" width="80" />
        <el-table-column prop="admit_date" label="入院日期" width="160">
          <template #default="{ row }">
            {{ formatDate(row.admit_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="deposit" label="押金" width="100" />
        <el-table-column prop="total_fee" label="总费用" width="100" />
        <el-table-column prop="settled" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.settled ? 'success' : 'warning'">
              {{ row.settled ? '已出院' : '在院' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="discharge_date" label="出院日期" width="160">
          <template #default="{ row }">
            {{ row.discharge_date ? formatDate(row.discharge_date) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row)">详情</el-button>
            <el-button size="small" type="primary" v-if="!row.settled" @click="viewDailyBill(row.id)">一日清单</el-button>
            <el-button size="small" type="success" v-if="!row.settled" @click="handleDischarge(row.id)">出院</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top:16px;display:flex;justify-content:flex-end">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @size-change="handlePageChange"
          @current-change="handlePageChange"
        />
      </div>

      <el-empty v-if="!loading && list.length === 0" description="暂无入院记录" />
    </el-card>

    <!-- 新增入院弹窗 -->
    <el-dialog v-model="dialogVisible" title="新增入院" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="选择患者" required>
          <el-autocomplete
            v-model="patientSearchText"
            :fetch-suggestions="searchPatient"
            placeholder="输入姓名或电话搜索"
            value-key="label"
            style="width:100%"
            @select="onSelectPatient"
          />
          <div v-if="form.patient_id" style="margin-top:4px;color:#667085;font-size:12px">
            已选患者 ID: {{ form.patient_id }}
          </div>
        </el-form-item>
        <el-form-item label="床位ID" required>
          <el-input-number v-model="form.bed_id" :min="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="科室ID" required>
          <el-input-number v-model="form.department_id" :min="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="押金">
          <el-input-number v-model="form.deposit" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="诊断">
          <el-input v-model="form.diagnosis" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="入院详情" width="520px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="ID">{{ detail.id }}</el-descriptions-item>
        <el-descriptions-item label="住院号">{{ detail.admission_no }}</el-descriptions-item>
        <el-descriptions-item label="患者ID">{{ detail.patient_id }}</el-descriptions-item>
        <el-descriptions-item label="床位ID">{{ detail.bed_id }}</el-descriptions-item>
        <el-descriptions-item label="科室ID">{{ detail.department_id }}</el-descriptions-item>
        <el-descriptions-item label="入院日期">{{ formatDate(detail.admit_date) }}</el-descriptions-item>
        <el-descriptions-item label="押金">{{ detail.deposit }}</el-descriptions-item>
        <el-descriptions-item label="总费用">{{ detail.total_fee }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="detail.settled ? 'success' : 'warning'">
            {{ detail.settled ? '已出院' : '在院' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="出院日期">{{ detail.discharge_date ? formatDate(detail.discharge_date) : '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 一日清单弹窗 -->
    <el-dialog v-model="billVisible" title="住院一日清单" width="640px">
      <div style="display:flex;gap:8px;margin-bottom:16px">
        <el-date-picker v-model="billDate" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width:200px" />
        <el-button @click="loadDailyBill">查询</el-button>
      </div>
      <el-table :data="billItems" border style="width:100%">
        <el-table-column prop="category" label="类别" width="100" />
        <el-table-column prop="item_name" label="项目名称" min-width="160" />
        <el-table-column prop="quantity" label="数量" width="80" />
        <el-table-column prop="amount" label="金额" width="100" />
      </el-table>
      <div style="margin-top:12px;text-align:right;font-weight:bold">
        合计：{{ billTotal }}
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import request from '../utils/request'
import { formatDate } from '../utils/date'
import { showSuccess, showError } from '../utils/message'

interface Admission {
  id: number
  admission_no: string
  patient_id: number
  bed_id: number
  department_id: number
  admit_date: string
  discharge_date?: string
  deposit: number
  total_fee: number
  settled: boolean
}

interface DailyBillItem {
  category: string
  item_name: string
  quantity: number
  amount: number
}

interface PatientOption {
  id: number
  label: string
  value: number
}

const list = ref<Admission[]>([])
const loading = ref(false)
const searchQ = ref('')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const dialogVisible = ref(false)
const patientSearchText = ref('')
const form = ref({
  patient_id: null as number | null,
  bed_id: 1,
  department_id: 1,
  deposit: 0,
  diagnosis: ''
})

const detailVisible = ref(false)
const detail = ref<Partial<Admission>>({})

const billVisible = ref(false)
const currentAdmissionId = ref(0)
const billDate = ref('')
const billItems = ref<DailyBillItem[]>([])
const billTotal = ref(0)

const paginatedList = computed(() => {
  const start = (page.value - 1) * pageSize.value
  const end = start + pageSize.value
  return list.value.slice(start, end)
})

const loadList = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/admissions', { params: { q: searchQ.value } })
    list.value = res.data
    total.value = res.data.length
  } catch (err: any) {
    showError('获取入院列表失败：' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

const handlePageChange = () => {
  // 前端分页，无需重新请求
}

const searchPatient = async (query: string, cb: (arg: PatientOption[]) => void) => {
  if (!query) return cb([])
  try {
    const res = await request.get('/api/patients', { params: { q: query } })
    cb(res.data.map((p: any) => ({ label: `${p.name}（${p.phone || p.patient_no}）`, value: p.id, id: p.id })))
  } catch {
    cb([])
  }
}

const onSelectPatient = (item: PatientOption) => {
  form.value.patient_id = item.id
}

const openAdd = () => {
  patientSearchText.value = ''
  form.value = { patient_id: null, bed_id: 1, department_id: 1, deposit: 0, diagnosis: '' }
  dialogVisible.value = true
}

const submit = async () => {
  if (!form.value.patient_id || !form.value.bed_id || !form.value.department_id) {
    showError('请填写患者、床位和科室信息！')
    return
  }
  try {
    const payload = { ...form.value, deposit: form.value.deposit || 0 }
    await request.post('/api/admissions', payload)
    showSuccess('入院登记成功！')
    dialogVisible.value = false
    loadList()
  } catch (err: any) {
    showError('入院登记失败：' + (err.response?.data?.detail || err.message))
  }
}

const viewDetail = (row: Admission) => {
  detail.value = { ...row }
  detailVisible.value = true
}

const handleDischarge = async (id: number) => {
  try {
    await ElMessageBox.confirm('确认办理出院结算？', '提示', { type: 'warning' })
    await request.patch(`/api/admissions/${id}/discharge`)
    showSuccess('出院结算完成！')
    loadList()
  } catch (err: any) {
    if (err !== 'cancel') {
      showError('出院结算失败：' + (err.response?.data?.detail || err.message))
    }
  }
}

const viewDailyBill = (id: number) => {
  currentAdmissionId.value = id
  billDate.value = new Date().toISOString().split('T')[0]
  billItems.value = []
  billTotal.value = 0
  billVisible.value = true
  loadDailyBill()
}

const loadDailyBill = async () => {
  try {
    const params: Record<string, string> = {}
    if (billDate.value) params.bill_date = billDate.value
    const res = await request.get(`/api/admissions/${currentAdmissionId.value}/daily-bill`, { params })
    billItems.value = res.data.items || []
    billTotal.value = res.data.total || 0
  } catch (err: any) {
    showError('获取一日清单失败：' + (err.response?.data?.detail || err.message))
  }
}

onMounted(loadList)
</script>

<style scoped>
.card-header { display:flex; justify-content:space-between; align-items:center; }
</style>
