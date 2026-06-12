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
            <el-table-column prop="charge_type_label" label="类型" width="100">
              <template #default="{ row }">
                <el-tag
                  :type="row.type === 'registration' ? 'warning' : row.type === 'prescription' ? 'primary' : 'success'"
                >
                  {{ row.charge_type_label }}
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
            <el-table-column label="总金额(元)" width="110">
              <template #default="{ row }">
                {{ row.total_amount }}
              </template>
            </el-table-column>
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
            <el-form-item label="收费类型">
              <el-select
                v-model="historyQuery.charge_type"
                placeholder="全部类型"
                clearable
                style="width: 140px"
              >
                <el-option label="全部" value="" />
                <el-option label="挂号收费" value="挂号收费" />
                <el-option label="门诊处方" value="门诊处方" />
                <el-option label="住院结算" value="住院结算" />
              </el-select>
            </el-form-item>
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

        <!-- 汇总栏 -->
        <el-card class="summary-card" v-if="historySummary">
          <div class="summary-row">
            <span class="summary-label">当前筛选汇总：</span>
            <span class="summary-total">共 {{ historySummary.count }} 条，合计 ¥{{ historySummary.total_amount.toFixed(2) }}</span>
            <span class="summary-breakdown" v-if="historySummary.by_type">
              <template v-for="(amount, type) in historySummary.by_type" :key="type">
                <el-tag size="small" style="margin-left: 8px">
                  {{ type }}: ¥{{ Number(amount).toFixed(2) }}
                </el-tag>
              </template>
            </span>
          </div>
        </el-card>

        <el-card class="table-card">
          <el-table
            v-loading="historyLoading"
            :data="historyList"
            border
            stripe
            style="width: 100%"
          >
            <el-table-column prop="charge_type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag
                  :type="row.charge_type === '挂号收费' ? 'warning' : row.charge_type === '门诊处方' ? 'primary' : 'success'"
                >
                  {{ row.charge_type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="ref_no" label="单号" width="150" />
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
            <el-table-column label="总金额(元)" width="110">
              <template #default="{ row }">
                <span :class="{ 'anomaly-amount': row.paid_amount >= 5000 }">
                  {{ row.total_amount }}
                  <el-tag v-if="row.paid_amount >= 5000" type="danger" size="small" style="margin-left: 4px">大额</el-tag>
                </span>
              </template>
            </el-table-column>
            <el-table-column label="实付金额(元)" width="110">
              <template #default="{ row }">
                {{ row.paid_amount }}
              </template>
            </el-table-column>
            <el-table-column label="收费员" width="100">
              <template #default="{ row }">
                {{ row.operator_name || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="收费时间" width="160">
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
            <el-tag
              :type="currentCharge.type === 'registration' ? 'warning' : currentCharge.type === 'prescription' ? 'primary' : 'success'"
            >
              {{ currentCharge.charge_type_label }}
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

interface PendingItem {
  id: number
  type: string
  charge_type_label: string
  no: string
  patient_id: number
  patient_no: string
  patient_name: string
  gender?: string
  age?: number
  total_amount: number
  pay_amount: number
  deposit: number
  created_at: string
}

interface HistoryItem {
  id: number
  bill_no: string
  charge_type: string
  source_id: number
  patient_id: number
  patient_name: string
  patient_no: string
  gender?: string
  age?: number
  total_amount: number
  paid_amount: number
  operator_name?: string
  charge_time: string
  status: string
  ref_no?: string
}

const activeTab = ref('pending')

// ── 待收费 ──
const pendingLoading = ref(false)
const pendingList = ref<PendingItem[]>([])
const pendingTotal = ref(0)
const pendingQuery = reactive({
  patient_name: '',
  patient_no: '',
  page: 1,
  page_size: 10
})

// ── 收费历史 ──
const historyLoading = ref(false)
const historyList = ref<HistoryItem[]>([])
const historyTotal = ref(0)
const historySummary = ref<{ total_amount: number; count: number; by_type: Record<string, number> } | null>(null)
const historyQuery = reactive({
  charge_type: '',
  patient_name: '',
  patient_no: '',
  charge_date: '',
  page: 1,
  page_size: 10
})

// ── 收费弹窗 ──
const chargeVisible = ref(false)
const currentCharge = ref<PendingItem | null>(null)
const chargeLoading = ref(false)

const hasAdmissionType = computed(() => {
  return pendingList.value.some(item => item.type === 'admission')
})

// ── 待收费列表 ──
const fetchPendingList = async () => {
  pendingLoading.value = true
  try {
    const res = await request.get('/api/billing/pending', {
      params: {
        patient_name: pendingQuery.patient_name || undefined,
        patient_no: pendingQuery.patient_no || undefined,
        page: pendingQuery.page,
        page_size: pendingQuery.page_size
      }
    })
    const data = res.data
    pendingList.value = data.items || []
    pendingTotal.value = data.total || 0
  } catch (err: any) {
    const detail = err.response?.data?.detail
    const msg = typeof detail === 'string' ? detail : (Array.isArray(detail) ? detail[0]?.msg || JSON.stringify(detail) : err.message)
    showError('获取待收费列表失败：' + msg)
  } finally {
    pendingLoading.value = false
  }
}

// ── 收费历史列表 ──
const fetchHistoryList = async () => {
  historyLoading.value = true
  try {
    const params: any = {
      page: historyQuery.page,
      page_size: historyQuery.page_size
    }
    if (historyQuery.charge_type) params.charge_type = historyQuery.charge_type
    if (historyQuery.patient_name) params.patient_name = historyQuery.patient_name
    if (historyQuery.patient_no) params.patient_no = historyQuery.patient_no
    if (historyQuery.charge_date) {
      params.start_date = historyQuery.charge_date
      params.end_date = historyQuery.charge_date
    }

    const res = await request.get('/api/billing/history', { params })
    const data = res.data
    historyList.value = data.items || []
    historyTotal.value = data.total || 0
    historySummary.value = data.summary || null
  } catch (err: any) {
    const detail = err.response?.data?.detail
    const msg = typeof detail === 'string' ? detail : (Array.isArray(detail) ? detail[0]?.msg || JSON.stringify(detail) : err.message)
    showError('获取收费历史失败：' + msg)
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
  historyQuery.charge_type = ''
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

const handleCharge = (row: PendingItem) => {
  currentCharge.value = row
  chargeVisible.value = true
}

const confirmCharge = async () => {
  if (!currentCharge.value) return
  chargeLoading.value = true
  try {
    if (currentCharge.value.type === 'registration') {
      await request.patch(`/api/registrations/${currentCharge.value.id}/pay`)
    } else if (currentCharge.value.type === 'prescription') {
      await request.patch(`/api/prescriptions/${currentCharge.value.id}/pay`)
    } else {
      await request.patch(`/api/admissions/${currentCharge.value.id}/discharge`)
    }
    showSuccess('收费结算成功')
    chargeVisible.value = false
    fetchPendingList()
  } catch (err: any) {
    const status = err.response?.status
    const detail = err.response?.data?.detail
    if (status === 409) {
      showError(detail || '该记录已收费，不可重复收费')
    } else {
      showError('收费结算失败：' + (detail || err.message))
    }
  } finally {
    chargeLoading.value = false
  }
}

onMounted(() => {
  fetchPendingList()
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

.summary-card {
  margin-bottom: 16px;
  background: #f0f9eb;
  border-color: #b3e19d;
}

.summary-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.summary-label {
  font-weight: 600;
  color: #606266;
}

.summary-total {
  font-size: 16px;
  font-weight: 700;
  color: #67c23a;
}

.summary-breakdown {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
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

.anomaly-amount {
  color: #f56c6c;
  font-weight: 600;
}
</style>
