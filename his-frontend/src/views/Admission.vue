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
        <el-table-column label="患者信息" min-width="160">
          <template #default="{ row }">
            <div v-if="row.patient">
              <div style="font-weight:500">{{ row.patient.name }}</div>
              <div style="font-size:12px;color:#667085">{{ row.patient.phone }} / {{ row.patient.patient_no }}</div>
            </div>
            <div v-else>患者ID: {{ row.patient_id }}</div>
          </template>
        </el-table-column>
        <el-table-column label="床位信息" width="140">
          <template #default="{ row }">
            <div v-if="row.bed">
              <div>{{ row.bed.bed_no }}</div>
              <div style="font-size:12px;color:#667085">{{ row.bed.ward }}</div>
            </div>
            <div v-else>床位ID: {{ row.bed_id }}</div>
          </template>
        </el-table-column>
        <el-table-column label="科室" width="120">
          <template #default="{ row }">
            {{ getDepartmentName(row.department_id) }}
          </template>
        </el-table-column>
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
        <el-table-column label="操作" width="260" fixed="right">
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

        <el-form-item label="选择科室" required>
          <el-select v-model="form.department_id" placeholder="请选择科室" style="width:100%" @change="onDepartmentChange">
            <el-option
              v-for="dept in departmentList"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="选择床位" required>
          <el-select v-model="form.bed_id" placeholder="请先选择科室" style="width:100%" :disabled="!form.department_id || bedLoading">
            <el-option
              v-for="bed in availableBeds"
              :key="bed.id"
              :label="`${bed.bed_no} (${bed.ward})`"
              :value="bed.id"
            />
          </el-select>
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
    <el-dialog v-model="detailVisible" title="入院详情" width="600px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="ID">{{ detail.id }}</el-descriptions-item>
        <el-descriptions-item label="住院号">{{ detail.admission_no }}</el-descriptions-item>
        <el-descriptions-item label="患者姓名">{{ detail.patient?.name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="患者电话">{{ detail.patient?.phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="床位">{{ detail.bed?.bed_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="病房">{{ detail.bed?.ward || '-' }}</el-descriptions-item>
        <el-descriptions-item label="科室">{{ getDepartmentName(detail.department_id) }}</el-descriptions-item>
        <el-descriptions-item label="入院日期">{{ formatDate(detail.admit_date) }}</el-descriptions-item>
        <el-descriptions-item label="押金">{{ detail.deposit }}</el-descriptions-item>
        <el-descriptions-item label="总费用">{{ detail.total_fee }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="detail.settled ? 'success' : 'warning'">
            {{ detail.settled ? '已出院' : '在院' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="出院日期">{{ detail.discharge_date ? formatDate(detail.discharge_date) : '-' }}</el-descriptions-item>
        <el-descriptions-item label="诊断" :span="2">{{ detail.diagnosis || '-' }}</el-descriptions-item>
      </el-descriptions>

      <!-- 患者在本院的历史记录 -->
      <div style="margin-top:20px">
        <div style="font-weight:600;margin-bottom:12px">患者在本院的历史</div>
        <el-tabs v-model="historyTab">
          <el-tab-pane label="挂号记录" name="registrations">
            <el-table :data="patientHistory.registrations" border size="small" v-loading="historyLoading">
              <el-table-column prop="reg_no" label="挂号单号" width="140" />
              <el-table-column prop="reg_type" label="挂号类型" width="90" />
              <el-table-column prop="visit_date" label="就诊日期" width="120" />
              <el-table-column prop="payment_status" label="缴费状态" width="90" />
            </el-table>
            <el-empty v-if="!historyLoading && patientHistory.registrations.length === 0" description="暂无挂号记录" />
          </el-tab-pane>
          <el-tab-pane label="处方记录" name="prescriptions">
            <el-table :data="patientHistory.prescriptions" border size="small" v-loading="historyLoading">
              <el-table-column prop="pres_no" label="处方单号" width="140" />
              <el-table-column prop="pres_type" label="类型" width="80" />
              <el-table-column prop="total_amount" label="金额" width="80" />
              <el-table-column prop="payment_status" label="缴费状态" width="90" />
            </el-table>
            <el-empty v-if="!historyLoading && patientHistory.prescriptions.length === 0" description="暂无处方记录" />
          </el-tab-pane>
        </el-tabs>
      </div>
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
import { useRoute } from 'vue-router'
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
  diagnosis?: string
  patient?: any
  bed?: any
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

interface Department {
  id: number
  name: string
}

interface Bed {
  id: number
  bed_no: string
  ward: string
  department_id: number
  status: string
}

// 添加挂号记录和处方记录的接口定义
interface Registration {
  id: number
  reg_no: string
  patient_id: number
  doctor_id: number
  reg_type: string
  visit_date: string
  payment_status: string
  created_at: string
}

interface Prescription {
  id: number
  pres_no: string
  patient_id: number
  doctor_id: number
  pres_type: string
  total_amount: number
  payment_status: string
  created_at: string
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
  bed_id: null as number | null,
  department_id: null as number | null,
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

const departmentList = ref<Department[]>([])
const availableBeds = ref<Bed[]>([])
const bedLoading = ref(false)

const historyTab = ref('registrations')
const historyLoading = ref(false)
const patientHistory = ref<{ registrations: Registration[], prescriptions: Prescription[] }>({ registrations: [], prescriptions: [] })

// 直接展示后端分页返回的 list，不再需要前端分片
const paginatedList = computed(() => list.value)

const loadList = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/admissions', { params: { q: searchQ.value, page: page.value, page_size: pageSize.value } })
    list.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (err: any) {
    showError('获取入院列表失败：' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

const handlePageChange = () => {
  loadList()
}

/* ── 科室与床位 ── */
const loadDepartments = async () => {
  try {
    const res = await request.get('/api/kiosk/departments')
    // 后端返回可能是数组或包含 doctors 的对象数组
    const data = Array.isArray(res.data) ? res.data : res.data.departments || []
    departmentList.value = data.map((d: any) => ({ id: d.id, name: d.name }))
  } catch (err: any) {
    console.error('获取科室失败', err)
  }
}

const getDepartmentName = (deptId?: number) => {
  if (!deptId) return '-'
  const dept = departmentList.value.find(d => d.id === deptId)
  return dept?.name || `科室${deptId}`
}

const onDepartmentChange = async () => {
  form.value.bed_id = null
  if (!form.value.department_id) {
    availableBeds.value = []
    return
  }
  bedLoading.value = true
  try {
    const res = await request.get('/api/nurse/beds', {
      params: { department_id: form.value.department_id, status: '空闲' }
    })
    availableBeds.value = res.data || []
  } catch (err: any) {
    showError('获取空闲床位失败：' + (err.response?.data?.detail || err.message))
  } finally {
    bedLoading.value = false
  }
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
  form.value = { patient_id: null, bed_id: null, department_id: null, deposit: 0, diagnosis: '' }
  availableBeds.value = []
  dialogVisible.value = true
}

const submit = async () => {
  if (!form.value.patient_id || !form.value.bed_id || !form.value.department_id) {
    showError('请填写患者、科室和床位信息！')
    return
  }
  try {
    const payload = {
      patient_id: form.value.patient_id,
      bed_id: form.value.bed_id,
      department_id: form.value.department_id,
      deposit: form.value.deposit || 0,
      diagnosis: form.value.diagnosis || null
    }
    await request.post('/api/admissions', payload)
    showSuccess('入院登记成功！')
    dialogVisible.value = false
    loadList()
  } catch (err: any) {
    showError('入院登记失败：' + (err.response?.data?.detail || err.message))
  }
}

const viewDetail = async (row: Admission) => {
  detail.value = { ...row }
  detailVisible.value = true
  // 加载患者历史
  if (row.patient_id) {
    loadPatientHistory(row.patient_id)
  }
}

const loadPatientHistory = async (patientId: number) => {
  historyLoading.value = true
  try {
    const [regRes, presRes] = await Promise.all([
      request.get('/api/registrations', { params: { patient_id: patientId } }).catch(() => ({ data: [] })),
      request.get('/api/prescriptions', { params: { patient_id: patientId } }).catch(() => ({ data: { items: [] } }))
    ])
    patientHistory.value.registrations = Array.isArray(regRes.data) ? regRes.data : []
    patientHistory.value.prescriptions = presRes.data.items || []
  } catch {
    patientHistory.value = { registrations: [], prescriptions: [] }
  } finally {
    historyLoading.value = false
  }
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

const route = useRoute()

onMounted(() => {
  loadList()
  loadDepartments()
  // 如果从患者管理页面跳转过来，自动打开新增入院弹窗
  if (route.query.patient_id) {
    const pid = Number(route.query.patient_id)
    if (pid) {
      form.value.patient_id = pid
      patientSearchText.value = route.query.patient_name as string || `患者#${pid}`
      openAdd()
    }
  }
})
</script>

<style scoped>
.card-header { display:flex; justify-content:space-between; align-items:center; }
</style>
