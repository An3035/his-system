<template>
  <div class="page-wrap">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>护士工作站</span>
          <div style="display:flex;gap:8px">
            <el-input-number v-model="departmentId" :min="1" placeholder="科室ID" style="width:120px" />
            <el-button @click="handleDeptChange">查询</el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- ── 床位看板 ── -->
        <el-tab-pane label="床位看板" name="beds">
          <div v-loading="bedLoading" class="bed-grid">
            <div
              v-for="bed in bedList"
              :key="bed.id"
              class="bed-card"
              :class="bed.status"
            >
              <div style="font-size:18px;font-weight:bold">{{ bed.bed_no }}</div>
              <div style="color:#667085;font-size:12px">{{ bed.room_no }}</div>
              <el-tag
                :type="bed.status === 'free' ? 'success' : bed.status === 'occupied' ? 'primary' : 'danger'"
                style="margin-top:8px"
              >
                {{ bed.status === 'free' ? '空闲' : bed.status === 'occupied' ? '占用' : '维修' }}
              </el-tag>
              <div v-if="bed.status === 'occupied'" style="margin-top:8px;font-size:13px">
                {{ bed.patient_name }}<br>{{ bed.admission_no }}
              </div>
            </div>
          </div>
          <el-empty v-if="!bedLoading && bedList.length === 0" description="暂无床位数据" />
        </el-tab-pane>

        <!-- ── 在院患者 ── -->
        <el-tab-pane label="在院患者" name="patients">
          <div style="display:flex;gap:8px;margin-bottom:16px">
            <el-input
              v-model="inpatientSearchQ"
              placeholder="搜索姓名/住院号"
              style="width:220px"
              clearable
              @keyup.enter="loadInpatients"
            />
            <el-button @click="loadInpatients">搜索</el-button>
          </div>
          <el-table :data="inpatientList" border v-loading="inpatientLoading" style="width:100%">
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="admission_no" label="住院号" width="150" />
            <el-table-column prop="patient_id" label="患者ID" width="80" />
            <el-table-column prop="name" label="姓名" width="100" />
            <el-table-column prop="gender" label="性别" width="70" />
            <el-table-column prop="age" label="年龄" width="70" />
            <el-table-column prop="bed_no" label="床号" width="90" />
            <el-table-column prop="department_id" label="科室ID" width="80" />
            <el-table-column prop="admit_date" label="入院日期" width="160">
              <template #default="{ row }">{{ formatDate(row.admit_date) }}</template>
            </el-table-column>
            <el-table-column prop="diagnosis" label="诊断" min-width="160" />
          </el-table>
          <div style="margin-top:16px;display:flex;justify-content:flex-end">
            <el-pagination
              v-model:current-page="inpatientPage"
              v-model:page-size="inpatientPageSize"
              :page-sizes="[10, 20, 50]"
              :total="inpatientTotal"
              layout="total, sizes, prev, pager, next"
              @size-change="handleInpatientPageChange"
              @current-change="handleInpatientPageChange"
            />
          </div>
          <el-empty v-if="!inpatientLoading && inpatientList.length === 0" description="暂无在院患者" />
        </el-tab-pane>

        <!-- ── 医嘱管理 ── -->
        <el-tab-pane label="医嘱管理" name="orders">
          <div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap">
            <el-autocomplete
              v-model="orderPatientSearchText"
              :fetch-suggestions="searchPatient"
              placeholder="选择患者"
              value-key="label"
              style="width:260px"
              @select="onSelectOrderPatient"
            />
            <el-select v-model="orderType" placeholder="医嘱类型" clearable style="width:130px">
              <el-option label="长期医嘱" value="long_term" />
              <el-option label="临时医嘱" value="temp" />
            </el-select>
            <el-select v-model="orderStatusFilter" placeholder="医嘱状态" clearable style="width:130px">
              <el-option label="待执行" value="pending" />
              <el-option label="发药中" value="dispensing" />
              <el-option label="已发药" value="dispensed" />
              <el-option label="已完成" value="completed" />
              <el-option label="已取消" value="cancelled" />
            </el-select>
            <el-button @click="loadOrders">查询</el-button>
          </div>

          <el-table :data="orderList" border v-loading="orderLoading" style="width:100%">
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="order_type" label="类型" width="90">
              <template #default="{ row }">
                <el-tag :type="row.order_type === 'long_term' ? 'primary' : 'warning'" size="small">
                  {{ row.order_type === 'long_term' ? '长期' : '临时' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="content" label="医嘱内容" min-width="160" />
            <el-table-column prop="dosage" label="剂量" width="100" />
            <el-table-column prop="frequency" label="频次" width="100" />
            <el-table-column prop="route" label="途径" width="100" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="orderStatusTagType(row.status)" size="small">
                  {{ orderStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="doctor_name" label="医生" width="90" />
            <el-table-column prop="created_at" label="开立时间" width="155">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
            <el-table-column prop="executed_at" label="执行时间" width="155">
              <template #default="{ row }">{{ row.executed_at ? formatDate(row.executed_at) : '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="190" fixed="right">
              <template #default="{ row }">
                <div class="order-actions">
                  <!-- 待执行 → 执行（进入发药流程） -->
                  <el-button
                    v-if="row.status === 'pending'"
                    size="small"
                    type="primary"
                    @click="updateOrderStatus(row, 'execute')"
                  >执行</el-button>

                  <!-- 发药中 → 发药完成 -->
                  <el-button
                    v-if="row.status === 'dispensing'"
                    size="small"
                    type="warning"
                    @click="updateOrderStatus(row, 'dispense')"
                  >确认发药</el-button>

                  <!-- 已发药 → 完成医嘱 -->
                  <el-button
                    v-if="row.status === 'dispensed'"
                    size="small"
                    type="success"
                    @click="updateOrderStatus(row, 'complete')"
                  >完成</el-button>

                  <!-- 可取消：待执行 / 发药中 / 已发药 -->
                  <el-popconfirm
                    v-if="['pending', 'dispensing', 'dispensed'].includes(row.status)"
                    title="确认取消该医嘱？"
                    confirm-button-text="确认"
                    cancel-button-text="取消"
                    @confirm="updateOrderStatus(row, 'cancel')"
                  >
                    <template #reference>
                      <el-button size="small" type="danger" plain>取消</el-button>
                    </template>
                  </el-popconfirm>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <div style="margin-top:16px;display:flex;justify-content:flex-end">
            <el-pagination
              v-model:current-page="orderPage"
              v-model:page-size="orderPageSize"
              :page-sizes="[10, 20, 50]"
              :total="orderTotal"
              layout="total, sizes, prev, pager, next"
              @size-change="handleOrderPageChange"
              @current-change="handleOrderPageChange"
            />
          </div>
          <el-empty v-if="!orderLoading && orderList.length === 0" description="暂无医嘱" />
        </el-tab-pane>

        <!-- ── 生命体征 ── -->
        <el-tab-pane label="生命体征" name="vitals">
          <div style="display:flex;gap:8px;margin-bottom:16px">
            <el-autocomplete
              v-model="vitalPatientSearchText"
              :fetch-suggestions="searchPatient"
              placeholder="选择患者"
              value-key="label"
              style="width:260px"
              @select="onSelectVitalPatient"
            />
            <el-button type="primary" @click="openAddVital">新增体征</el-button>
          </div>
          <el-table :data="vitalList" border v-loading="vitalLoading" style="width:100%">
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="patient_id" label="患者ID" width="80" />
            <el-table-column prop="temperature" label="体温" width="90" />
            <el-table-column prop="pulse" label="脉搏" width="90" />
            <el-table-column prop="respiration" label="呼吸" width="90" />
            <el-table-column prop="systolic_bp" label="收缩压" width="90" />
            <el-table-column prop="diastolic_bp" label="舒张压" width="90" />
            <el-table-column prop="record_time" label="记录时间" width="160">
              <template #default="{ row }">{{ formatDate(row.record_time) }}</template>
            </el-table-column>
            <el-table-column prop="recorder_name" label="记录人" width="100" />
          </el-table>
          <div style="margin-top:16px;display:flex;justify-content:flex-end">
            <el-pagination
              v-model:current-page="vitalPage"
              v-model:page-size="vitalPageSize"
              :page-sizes="[10, 20, 50]"
              :total="vitalTotal"
              layout="total, sizes, prev, pager, next"
              @size-change="handleVitalPageChange"
              @current-change="handleVitalPageChange"
            />
          </div>
          <el-empty v-if="!vitalLoading && vitalList.length === 0" description="暂无体征记录" />
        </el-tab-pane>
      </el-tabs>

      <!-- 录入生命体征弹窗 -->
      <el-dialog v-model="vitalDialogVisible" title="录入生命体征" width="520px">
        <el-form :model="vitalForm" label-width="100px">
          <el-form-item label="患者ID">
            <el-input :model-value="vitalForm.patient_id" disabled />
          </el-form-item>
          <el-form-item label="体温" required>
            <el-input-number v-model="vitalForm.temperature" :min="30" :max="45" :precision="1" style="width:100%" />
          </el-form-item>
          <el-form-item label="脉搏" required>
            <el-input-number v-model="vitalForm.pulse" :min="0" :max="200" style="width:100%" />
          </el-form-item>
          <el-form-item label="呼吸" required>
            <el-input-number v-model="vitalForm.respiration" :min="0" :max="60" style="width:100%" />
          </el-form-item>
          <el-form-item label="收缩压" required>
            <el-input-number v-model="vitalForm.systolic_bp" :min="0" :max="300" style="width:100%" />
          </el-form-item>
          <el-form-item label="舒张压" required>
            <el-input-number v-model="vitalForm.diastolic_bp" :min="0" :max="200" style="width:100%" />
          </el-form-item>
          <el-form-item label="记录时间" required>
            <el-date-picker
              v-model="vitalForm.record_time"
              type="datetime"
              value-format="YYYY-MM-DD HH:mm:ss"
              placeholder="选择时间"
              style="width:100%"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="vitalDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitVital">确定</el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '../utils/request'
import { formatDate } from '../utils/date'
import { showSuccess, showError } from '../utils/message'

// ── 类型定义 ──────────────────────────────────────────────
interface Bed {
  id: number
  bed_no: string
  room_no: string
  department_id: number
  status: 'free' | 'occupied' | 'maintenance'
  patient_name?: string
  admission_no?: string
}

interface Inpatient {
  id: number
  admission_id: number
  admission_no: string
  patient_id: number
  name: string
  gender: string
  age: number
  bed_no: string
  department_id: number
  admit_date: string
  diagnosis: string
}

/** 医嘱状态流转：pending → dispensing → dispensed → completed | cancelled */
type OrderStatus = 'pending' | 'dispensing' | 'dispensed' | 'completed' | 'cancelled'

interface Order {
  id: number
  patient_id: number
  admission_id: number
  order_type: 'long_term' | 'temp'
  content: string
  dosage: string
  frequency: string
  route: string
  status: OrderStatus
  doctor_name: string
  created_at: string
  executed_at?: string
}

interface Vital {
  id: number
  patient_id: number
  temperature: number
  pulse: number
  respiration: number
  systolic_bp: number
  diastolic_bp: number
  record_time: string
  recorder_name: string
}

interface PatientOption {
  id: number
  label: string
  value: number
}

// ── 通用状态辅助函数 ──────────────────────────────────────
const ORDER_STATUS_MAP: Record<OrderStatus, { label: string; type: string }> = {
  pending:    { label: '待执行', type: 'info' },
  dispensing: { label: '发药中', type: 'warning' },
  dispensed:  { label: '已发药', type: 'primary' },
  completed:  { label: '已完成', type: 'success' },
  cancelled:  { label: '已取消', type: 'danger' }
}

const orderStatusLabel = (status: OrderStatus) =>
  ORDER_STATUS_MAP[status]?.label ?? status

const orderStatusTagType = (status: OrderStatus) =>
  ORDER_STATUS_MAP[status]?.type ?? 'info'

/** 操作名 → API 路径段 */
const ACTION_PATH: Record<string, string> = {
  execute:  'execute',   // pending → dispensing
  dispense: 'dispense',  // dispensing → dispensed
  complete: 'complete',  // dispensed → completed
  cancel:   'cancel'     // any → cancelled
}

// ── 响应式数据 ────────────────────────────────────────────
const activeTab = ref('beds')
const departmentId = ref<number | null>(1)

const bedList = ref<Bed[]>([])
const bedLoading = ref(false)

const inpatientList = ref<Inpatient[]>([])
const inpatientLoading = ref(false)
const inpatientSearchQ = ref('')
const inpatientPage = ref(1)
const inpatientPageSize = ref(10)
const inpatientTotal = ref(0)

const orderList = ref<Order[]>([])
const orderLoading = ref(false)
const orderPatientSearchText = ref('')
const selectedOrderPatientId = ref<number | null>(null)
const orderType = ref('')
const orderStatusFilter = ref('')
const orderPage = ref(1)
const orderPageSize = ref(10)
const orderTotal = ref(0)

const vitalList = ref<Vital[]>([])
const vitalLoading = ref(false)
const vitalPatientSearchText = ref('')
const selectedVitalPatientId = ref<number | null>(null)
const vitalPage = ref(1)
const vitalPageSize = ref(10)
const vitalTotal = ref(0)

const vitalDialogVisible = ref(false)
const vitalForm = ref({
  patient_id: null as number | null,
  temperature: 36.5,
  pulse: 70,
  respiration: 18,
  systolic_bp: 120,
  diastolic_bp: 80,
  record_time: ''
})

// ── 床位 ──────────────────────────────────────────────────
const loadBeds = async () => {
  if (!departmentId.value) {
    showError('请选择科室')
    return
  }
  bedLoading.value = true
  try {
    const res = await request.get('/api/nurse/beds', { params: { department_id: departmentId.value } })
    bedList.value = res.data
  } catch (err: any) {
    showError('获取床位失败：' + (err.response?.data?.detail || err.message))
  } finally {
    bedLoading.value = false
  }
}

// ── 在院患者 ──────────────────────────────────────────────
const loadInpatients = async () => {
  if (!departmentId.value) {
    showError('请选择科室')
    return
  }
  inpatientLoading.value = true
  try {
    const res = await request.get('/api/nurse/inpatients', {
      params: {
        department_id: departmentId.value,
        q: inpatientSearchQ.value,
        page: inpatientPage.value,
        page_size: inpatientPageSize.value
      }
    })
    inpatientList.value = res.data.items
    inpatientTotal.value = res.data.total
  } catch (err: any) {
    showError('获取患者列表失败：' + (err.response?.data?.detail || err.message))
  } finally {
    inpatientLoading.value = false
  }
}

const handleInpatientPageChange = () => loadInpatients()

// ── 医嘱 ──────────────────────────────────────────────────
const loadOrders = async () => {
  if (!selectedOrderPatientId.value) {
    showError('请选择患者')
    return
  }
  orderLoading.value = true
  try {
    const params: Record<string, any> = {
      patient_id: selectedOrderPatientId.value,
      page: orderPage.value,
      page_size: orderPageSize.value
    }
    if (orderType.value) params.order_type = orderType.value
    if (orderStatusFilter.value) params.status = orderStatusFilter.value

    const res = await request.get('/api/nurse/orders', { params })
    orderList.value = res.data.items
    orderTotal.value = res.data.total
  } catch (err: any) {
    showError('获取医嘱失败：' + (err.response?.data?.detail || err.message))
  } finally {
    orderLoading.value = false
  }
}

const handleOrderPageChange = () => loadOrders()

const onSelectOrderPatient = (item: PatientOption) => {
  selectedOrderPatientId.value = item.id
  orderPatientSearchText.value = item.label
  orderPage.value = 1
  loadOrders()
}

/**
 * 统一的医嘱状态变更入口
 * action: 'execute' | 'dispense' | 'complete' | 'cancel'
 */
const updateOrderStatus = async (row: Order, action: string) => {
  const path = ACTION_PATH[action]
  if (!path) return
  try {
    await request.patch(`/api/nurse/orders/${row.id}/${path}`)
    const actionLabelMap: Record<string, string> = {
      execute:  '医嘱已执行，进入发药流程',
      dispense: '发药确认成功',
      complete: '医嘱已完成',
      cancel:   '医嘱已取消'
    }
    showSuccess(actionLabelMap[action] || '操作成功')
    loadOrders()
  } catch (err: any) {
    showError('操作失败：' + (err.response?.data?.detail || err.message))
  }
}

// ── 生命体征 ──────────────────────────────────────────────
const loadVitals = async () => {
  if (!selectedVitalPatientId.value) {
    showError('请选择患者')
    return
  }
  vitalLoading.value = true
  try {
    const res = await request.get('/api/nurse/vitals', {
      params: {
        patient_id: selectedVitalPatientId.value,
        page: vitalPage.value,
        page_size: vitalPageSize.value
      }
    })
    vitalList.value = res.data.items
    vitalTotal.value = res.data.total
  } catch (err: any) {
    showError('获取体征记录失败：' + (err.response?.data?.detail || err.message))
  } finally {
    vitalLoading.value = false
  }
}

const handleVitalPageChange = () => loadVitals()

const onSelectVitalPatient = (item: PatientOption) => {
  selectedVitalPatientId.value = item.id
  vitalPatientSearchText.value = item.label
  vitalPage.value = 1
  loadVitals()
}

const searchPatient = async (query: string, cb: (arg: PatientOption[]) => void) => {
  if (!query) return cb([])
  try {
    const res = await request.get('/api/patients', { params: { q: query } })
    cb(res.data.map((p: any) => ({
      label: `${p.name}（${p.phone || p.patient_no}）`,
      value: p.id,
      id: p.id
    })))
  } catch {
    cb([])
  }
}

const openAddVital = () => {
  if (!selectedVitalPatientId.value) {
    showError('请先选择患者')
    return
  }
  vitalForm.value = {
    patient_id: selectedVitalPatientId.value,
    temperature: 36.5,
    pulse: 70,
    respiration: 18,
    systolic_bp: 120,
    diastolic_bp: 80,
    record_time: new Date().toISOString().slice(0, 19).replace('T', ' ')
  }
  vitalDialogVisible.value = true
}

const submitVital = async () => {
  if (!vitalForm.value.patient_id || !vitalForm.value.record_time) {
    showError('请填写完整信息')
    return
  }
  try {
    await request.post('/api/nurse/vitals', vitalForm.value)
    showSuccess('录入成功')
    vitalDialogVisible.value = false
    loadVitals()
  } catch (err: any) {
    showError('录入失败：' + (err.response?.data?.detail || err.message))
  }
}

// ── Tab / 科室切换 ────────────────────────────────────────
const handleDeptChange = () => {
  if (activeTab.value === 'beds') {
    loadBeds()
  } else if (activeTab.value === 'patients') {
    inpatientPage.value = 1
    loadInpatients()
  } else if (activeTab.value === 'orders') {
    orderPage.value = 1
    loadOrders()
  } else if (activeTab.value === 'vitals') {
    vitalPage.value = 1
    loadVitals()
  }
}

const handleTabChange = () => {
  if (activeTab.value === 'beds' && bedList.value.length === 0) {
    loadBeds()
  } else if (activeTab.value === 'patients' && inpatientList.value.length === 0) {
    loadInpatients()
  } else if (activeTab.value === 'orders' && orderList.value.length === 0 && selectedOrderPatientId.value) {
    loadOrders()
  } else if (activeTab.value === 'vitals' && vitalList.value.length === 0 && selectedVitalPatientId.value) {
    loadVitals()
  }
}

onMounted(() => {
  loadBeds()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bed-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.bed-card {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
  text-align: center;
}

.bed-card.occupied {
  background: #ecf5ff;
  border-color: #409eff;
}

.bed-card.maintenance {
  background: #fef0f0;
  border-color: #f56c6c;
}

.order-actions {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  align-items: center;
}
</style>