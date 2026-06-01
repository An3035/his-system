<template>
  <div class="charge-container">
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="待收费" name="pending">
        <el-card class="search-card">
          <el-form :inline="true" :model="pendingQuery" class="search-form">
            <el-form-item label="患者姓名">
              <el-input
                v-model="pendingQuery.patient_name"
                placeholder="请输入患者姓名"
                clearable
              />
            </el-form-item>
            <el-form-item label="患者编号">
              <el-input
                v-model="pendingQuery.patient_no"
                placeholder="请输入患者编号"
                clearable
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handlePendingSearch">查询</el-button>
              <el-button @click="handlePendingReset">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="table-card">
          <el-table
            v-loading="pendingLoading"
            :data="pendingList"
            border
            stripe
            style="width: 100%"
          >
            <el-table-column prop="type" label="类型" width="90">
              <template #default="{ row }">
                <el-tag :type="row.type === 'prescription' ? 'primary' : 'success'">
                  {{ row.type === 'prescription' ? '门诊处方' : '住院结算' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="no" label="单号" width="150" />
            <el-table-column prop="patient_no" label="患者编号" width="120" />
            <el-table-column label="患者姓名" width="100">
              <template #default="{ row }">
                {{ row.patient_name || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="性别" width="70">
              <template #default="{ row }">
                <el-tag
                  v-if="row.gender"
                  :type="row.gender === '男' ? 'primary' : 'danger'"
                  size="small"
                >
                  {{ row.gender }}
                </el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="年龄" width="70">
              <template #default="{ row }">
                {{ row.age != null ? row.age + '岁' : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="total_amount" label="总金额(元)" width="110" />
            <el-table-column label="押金(元)" width="90" v-if="hasAdmissionType">
              <template #default="{ row }">
                {{ row.type === 'admission' ? row.deposit : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="160">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link @click="handleCharge(row)">收费结算</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination
            v-model:current-page="pendingQuery.page"
            v-model:page-size="pendingQuery.page_size"
            :total="pendingTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next, jumper"
            class="pagination"
            @size-change="fetchPendingList"
            @current-change="fetchPendingList"
          />
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="收费历史" name="history">
        <el-card class="search-card">
          <el-form :inline="true" :model="historyQuery" class="search-form">
            <el-form-item label="患者姓名">
              <el-input
                v-model="historyQuery.patient_name"
                placeholder="请输入患者姓名"
                clearable
              />
            </el-form-item>
            <el-form-item label="患者编号">
              <el-input
                v-model="historyQuery.patient_no"
                placeholder="请输入患者编号"
                clearable
              />
            </el-form-item>
            <el-form-item label="收费日期">
              <el-date-picker
                v-model="historyQuery.charge_date"
                type="date"
                placeholder="请选择日期"
                value-format="YYYY-MM-DD"
                clearable
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleHistorySearch">查询</el-button>
              <el-button @click="handleHistoryReset">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="table-card">
          <el-table
            v-loading="historyLoading"
            :data="historyList"
            border
            stripe
            style="width: 100%"
          >
            <el-table-column prop="type" label="类型" width="90">
              <template #default="{ row }">
                <el-tag :type="row.type === 'prescription' ? 'primary' : 'success'">
                  {{ row.type === 'prescription' ? '门诊处方' : '住院结算' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="no" label="单号" width="150" />
            <el-table-column prop="patient_no" label="患者编号" width="120" />
            <el-table-column label="患者姓名" width="100">
              <template #default="{ row }">
                {{ row.patient_name || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="性别" width="70">
              <template #default="{ row }">
                <el-tag
                  v-if="row.gender"
                  :type="row.gender === '男' ? 'primary' : 'danger'"
                  size="small"
                >
                  {{ row.gender }}
                </el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="年龄" width="70">
              <template #default="{ row }">
                {{ row.age != null ? row.age + '岁' : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="total_amount" label="总金额(元)" width="110" />
            <el-table-column prop="paid_amount" label="实付金额(元)" width="110" />
            <el-table-column prop="charge_time" label="收费时间" width="160">
              <template #default="{ row }">
                {{ formatDate(row.charge_time) }}
              </template>
            </el-table-column>
          </el-table>
          <el-pagination
            v-model:current-page="historyQuery.page"
            v-model:page-size="historyQuery.page_size"
            :total="historyTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next, jumper"
            class="pagination"
            @size-change="fetchHistoryList"
            @current-change="fetchHistoryList"
          />
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 收费结算弹窗 -->
    <el-dialog
      v-model="chargeVisible"
      title="收费结算"
      width="520px"
      :close-on-click-modal="false"
    >
      <div v-if="currentCharge" class="charge-info">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="类型">
            <el-tag :type="currentCharge.type === 'prescription' ? 'primary' : 'success'">
              {{ currentCharge.type === 'prescription' ? '门诊处方' : '住院结算' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="单号">{{ currentCharge.no }}</el-descriptions-item>
          <el-descriptions-item label="患者编号">{{ currentCharge.patient_no || '-' }}</el-descriptions-item>
          <el-descriptions-item label="患者姓名">{{ currentCharge.patient_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="性别">
            <el-tag
              v-if="currentCharge.gender"
              :type="currentCharge.gender === '男' ? 'primary' : 'danger'"
              size="small"
            >
              {{ currentCharge.gender }}
            </el-tag>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="年龄">
            {{ currentCharge.age != null ? currentCharge.age + '岁' : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="总金额">{{ currentCharge.total_amount }} 元</el-descriptions-item>
          <el-descriptions-item label="押金" v-if="currentCharge.type === 'admission'">
            {{ currentCharge.deposit }} 元
          </el-descriptions-item>
          <el-descriptions-item label="应支付" :span="2" class="total-pay">
            <span class="amount">{{ currentCharge.pay_amount }} 元</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="chargeVisible = false">取消</el-button>
        <el-button type="success" :loading="chargeLoading" @click="confirmCharge">确认收费</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import request from '../utils/request'
import { formatDate } from '../utils/date'
import { showSuccess, showError } from '../utils/message'

interface ChargeItem {
  id: number
  type: 'prescription' | 'admission'
  no: string
  patient_no: string
  patient_name: string
  gender?: string
  age?: number
  total_amount: number
  deposit?: number
  pay_amount: number
  paid_amount?: number
  created_at: string
  charge_time?: string
}

const activeTab = ref('pending')

const pendingLoading = ref(false)
const pendingList = ref<ChargeItem[]>([])
const pendingTotal = ref(0)
const pendingQuery = reactive({
  patient_name: '',
  patient_no: '',
  page: 1,
  page_size: 10
})

const historyLoading = ref(false)
const historyList = ref<ChargeItem[]>([])
const historyTotal = ref(0)
const historyQuery = reactive({
  patient_name: '',
  patient_no: '',
  charge_date: '',
  page: 1,
  page_size: 10
})

const chargeVisible = ref(false)
const currentCharge = ref<ChargeItem | null>(null)
const chargeLoading = ref(false)

const patientMap = ref(new Map<number, any>())

// 是否有住院类型的待收费项目
const hasAdmissionType = computed(() => {
  return pendingList.value.some(item => item.type === 'admission')
})

const loadPatientMap = async () => {
  try {
    const res = await request.get('/api/patients')
    const patients = Array.isArray(res.data) ? res.data : []
    const map = new Map<number, any>()
    patients.forEach((p: any) => map.set(p.id, p))
    patientMap.value = map
  } catch (e) {
    console.error('加载患者映射失败', e)
  }
}

/**
 * 从 patientMap 中补充患者字段（当后端未 JOIN 返回时的兜底）
 */
const enrichFromPatientMap = (patientId?: number) => {
  if (!patientId) return { patient_name: '-', patient_no: '-', gender: undefined, age: undefined }
  const p = patientMap.value.get(patientId)
  if (!p) return { patient_name: `患者#${patientId}`, patient_no: '-', gender: undefined, age: undefined }
  return {
    patient_name: p.name,
    patient_no: p.patient_no || p.no || '-',
    gender: p.gender,
    age: p.age
  }
}

const fetchPendingList = async () => {
  pendingLoading.value = true
  try {
    // 获取待缴费处方
    const presRes = await request.get('/api/prescriptions', {
      params: {
        payment_status: 'pending',
        patient_name: pendingQuery.patient_name || undefined,
        patient_no: pendingQuery.patient_no || undefined,
        page: pendingQuery.page,
        page_size: pendingQuery.page_size
      }
    })
    const prescriptions = presRes.data.items || []

    // 获取在院未结算患者（住院结算）
    let admissions: any[] = []
    try {
      const admRes = await request.get('/api/admissions', {
        params: {
          settled: false,
          patient_name: pendingQuery.patient_name || undefined,
          patient_no: pendingQuery.patient_no || undefined,
          page: pendingQuery.page,
          page_size: pendingQuery.page_size
        }
      })
      admissions = Array.isArray(admRes.data) ? admRes.data : (admRes.data.items || [])
    } catch {
      admissions = []
    }

    // 合并列表，优先使用后端 JOIN 返回的 patient 对象，兜底使用 patientMap
    const presItems: ChargeItem[] = prescriptions.map((item: any) => {
      const fallback = enrichFromPatientMap(item.registration?.patient_id ?? item.patient_id)
      const p = item.patient || {}
      return {
        id: item.id,
        type: 'prescription' as const,
        no: item.pres_no,
        patient_no: p.patient_no || p.no || fallback.patient_no,
        patient_name: p.name || fallback.patient_name,
        gender: p.gender || fallback.gender,
        age: p.age ?? fallback.age,
        total_amount: Number(item.total_amount) || 0,
        pay_amount: Number(item.total_amount) || 0,
        created_at: item.created_at
      }
    })

    const admItems: ChargeItem[] = admissions.map((item: any) => {
      const fallback = enrichFromPatientMap(item.patient_id)
      const p = item.patient || {}
      return {
        id: item.id,
        type: 'admission' as const,
        no: item.admission_no,
        patient_no: p.patient_no || p.no || fallback.patient_no,
        patient_name: p.name || fallback.patient_name,
        gender: p.gender || fallback.gender,
        age: p.age ?? fallback.age,
        total_amount: Number(item.total_fee) || 0,
        deposit: Number(item.deposit) || 0,
        pay_amount: Math.max(0, (Number(item.total_fee) || 0) - (Number(item.deposit) || 0)),
        created_at: item.admit_date
      }
    })

    // 前端二次筛选（后端已支持参数时可省略，保留作兜底）
    let allItems = [...presItems, ...admItems]
    if (pendingQuery.patient_name) {
      const q = pendingQuery.patient_name.toLowerCase()
      allItems = allItems.filter(item => item.patient_name.toLowerCase().includes(q))
    }
    if (pendingQuery.patient_no) {
      const q = pendingQuery.patient_no.toLowerCase()
      allItems = allItems.filter(item => (item.patient_no || '').toLowerCase().includes(q))
    }

    pendingList.value = allItems
    pendingTotal.value = allItems.length
  } catch (err: any) {
    showError('获取待收费列表失败：' + (err.response?.data?.detail || err.message))
  } finally {
    pendingLoading.value = false
  }
}

const fetchHistoryList = async () => {
  historyLoading.value = true
  try {
    // 获取已缴费处方
    const presRes = await request.get('/api/prescriptions', {
      params: {
        payment_status: 'paid',
        patient_name: historyQuery.patient_name || undefined,
        patient_no: historyQuery.patient_no || undefined,
        page: historyQuery.page,
        page_size: historyQuery.page_size
      }
    })
    const prescriptions = presRes.data.items || []

    // 获取已出院结算记录
    let admissions: any[] = []
    try {
      const admRes = await request.get('/api/admissions', {
        params: {
          settled: true,
          patient_name: historyQuery.patient_name || undefined,
          patient_no: historyQuery.patient_no || undefined,
          page: historyQuery.page,
          page_size: historyQuery.page_size
        }
      })
      admissions = Array.isArray(admRes.data) ? admRes.data : (admRes.data.items || [])
    } catch {
      admissions = []
    }

    const presItems: ChargeItem[] = prescriptions.map((item: any) => {
      const fallback = enrichFromPatientMap(item.registration?.patient_id ?? item.patient_id)
      const p = item.patient || {}
      return {
        id: item.id,
        type: 'prescription' as const,
        no: item.pres_no,
        patient_no: p.patient_no || p.no || fallback.patient_no,
        patient_name: p.name || fallback.patient_name,
        gender: p.gender || fallback.gender,
        age: p.age ?? fallback.age,
        total_amount: Number(item.total_amount) || 0,
        paid_amount: Number(item.total_amount) || 0,
        pay_amount: Number(item.total_amount) || 0,
        charge_time: item.paid_at || item.updated_at,
        created_at: item.created_at
      }
    })

    const admItems: ChargeItem[] = admissions.map((item: any) => {
      const fallback = enrichFromPatientMap(item.patient_id)
      const p = item.patient || {}
      return {
        id: item.id,
        type: 'admission' as const,
        no: item.admission_no,
        patient_no: p.patient_no || p.no || fallback.patient_no,
        patient_name: p.name || fallback.patient_name,
        gender: p.gender || fallback.gender,
        age: p.age ?? fallback.age,
        total_amount: Number(item.total_fee) || 0,
        paid_amount: Number(item.total_fee) || 0,
        pay_amount: Number(item.total_fee) || 0,
        charge_time: item.discharge_date,
        created_at: item.admit_date
      }
    })

    let allItems = [...presItems, ...admItems]
    if (historyQuery.patient_name) {
      const q = historyQuery.patient_name.toLowerCase()
      allItems = allItems.filter(item => item.patient_name.toLowerCase().includes(q))
    }
    if (historyQuery.patient_no) {
      const q = historyQuery.patient_no.toLowerCase()
      allItems = allItems.filter(item => (item.patient_no || '').toLowerCase().includes(q))
    }
    if (historyQuery.charge_date) {
      allItems = allItems.filter(item => {
        const t = item.charge_time || ''
        return t.startsWith(historyQuery.charge_date)
      })
    }

    historyList.value = allItems
    historyTotal.value = allItems.length
  } catch (err: any) {
    showError('获取收费历史失败：' + (err.response?.data?.detail || err.message))
  } finally {
    historyLoading.value = false
  }
}

const handlePendingSearch = () => {
  pendingQuery.page = 1
  fetchPendingList()
}

const handlePendingReset = () => {
  pendingQuery.patient_name = ''
  pendingQuery.patient_no = ''
  pendingQuery.page = 1
  fetchPendingList()
}

const handleHistorySearch = () => {
  historyQuery.page = 1
  fetchHistoryList()
}

const handleHistoryReset = () => {
  historyQuery.patient_name = ''
  historyQuery.patient_no = ''
  historyQuery.charge_date = ''
  historyQuery.page = 1
  fetchHistoryList()
}

const handleTabChange = (tab: string) => {
  if (tab === 'pending') {
    fetchPendingList()
  } else if (tab === 'history') {
    fetchHistoryList()
  }
}

const handleCharge = (row: ChargeItem) => {
  currentCharge.value = row
  chargeVisible.value = true
}

const confirmCharge = async () => {
  if (!currentCharge.value) return
  chargeLoading.value = true
  try {
    if (currentCharge.value.type === 'prescription') {
      await request.patch(`/api/prescriptions/${currentCharge.value.id}/pay`)
    } else {
      await request.patch(`/api/admissions/${currentCharge.value.id}/discharge`)
    }
    showSuccess('收费结算成功')
    chargeVisible.value = false
    fetchPendingList()
  } catch (err: any) {
    showError('收费结算失败：' + (err.response?.data?.detail || err.message))
  } finally {
    chargeLoading.value = false
  }
}

onMounted(() => {
  loadPatientMap().then(() => {
    fetchPendingList()
  })
})
</script>

<style scoped>
.charge-container {
  padding: 16px;
}

.search-card {
  margin-bottom: 16px;
}

.search-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}

.table-card {
  margin-bottom: 16px;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.charge-info {
  padding: 0 8px;
}

.total-pay {
  text-align: center;
  font-size: 18px;
  font-weight: 600;
}

.amount {
  color: #f56c6c;
  font-size: 24px;
}
</style>