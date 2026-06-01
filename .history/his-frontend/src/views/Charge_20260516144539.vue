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
            <el-table-column prop="type" label="类型" width="80">
              <template #default="{ row }">
                <el-tag :type="row.type === 'prescription' ? 'primary' : 'success'">
                  {{ row.type === 'prescription' ? '门诊处方' : '住院结算' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="no" label="单号" width="150" />
            <el-table-column prop="patient_name" label="患者姓名" width="100" />
            <el-table-column prop="total_amount" label="总金额" width="100" />
            <el-table-column prop="deposit" label="押金" width="100" v-if="activeTab === 'pending'" />
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
            <el-table-column prop="type" label="类型" width="80">
              <template #default="{ row }">
                <el-tag :type="row.type === 'prescription' ? 'primary' : 'success'">
                  {{ row.type === 'prescription' ? '门诊处方' : '住院结算' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="no" label="单号" width="150" />
            <el-table-column prop="patient_name" label="患者姓名" width="100" />
            <el-table-column prop="total_amount" label="总金额" width="100" />
            <el-table-column prop="paid_amount" label="实付金额" width="100" />
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

    <el-dialog
      v-model="chargeVisible"
      title="收费结算"
      width="500px"
      :close-on-click-modal="false"
    >
      <div v-if="currentCharge" class="charge-info">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="单号">{{ currentCharge.no }}</el-descriptions-item>
          <el-descriptions-item label="患者姓名">{{ currentCharge.patient_name }}</el-descriptions-item>
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
import { ref, reactive, onMounted } from 'vue'
import request from '../utils/request'
import { formatDate } from '../utils/date'
import { showSuccess, showError } from '../utils/message'

interface ChargeItem {
  id: number
  type: 'prescription' | 'admission'
  no: string
  patient_name: string
  total_amount: number
  deposit?: number
  pay_amount: number
  created_at: string
  charge_time?: string
}

const activeTab = ref('pending')

const pendingLoading = ref(false)
const pendingList = ref<ChargeItem[]>([])
const pendingTotal = ref(0)
const pendingQuery = reactive({
  patient_name: '',
  page: 1,
  page_size: 10
})

const historyLoading = ref(false)
const historyList = ref<ChargeItem[]>([])
const historyTotal = ref(0)
const historyQuery = reactive({
  patient_name: '',
  charge_date: '',
  page: 1,
  page_size: 10
})

const chargeVisible = ref(false)
const currentCharge = ref<ChargeItem | null>(null)
const chargeLoading = ref(false)

const fetchPendingList = async () => {
  pendingLoading.value = true
  try {
    // 获取待收费处方
    const presRes = await request.get('/api/prescriptions', {
      params: { payment_status: 'PENDING' }
    })
    
    // 获取待结算住院患者
    const admRes = await request.get('/api/admissions', {
      params: { settled: false }
    })

    // 合并数据
    const presList = presRes.data.items.map((item: any) => ({
      id: item.id,
      type: 'prescription' as const,
      no: item.pres_no,
      patient_name: item.patient?.name || '未知',
      total_amount: item.total_amount,
      pay_amount: item.total_amount,
      created_at: item.created_at
    }))

    const admList = admRes.data.items.map((item: any) => ({
      id: item.id,
      type: 'admission' as const,
      no: item.admission_no,
      patient_name: item.patient?.name || '未知',
      total_amount: item.total_fee || 0,
      deposit: item.deposit,
      pay_amount: Math.max(0, (item.total_fee || 0) - item.deposit),
      created_at: item.admission_date
    }))

    pendingList.value = [...presList, ...admList]
    pendingTotal.value = presRes.data.total + admRes.data.total
  } catch (err: any) {
    showError('获取待收费列表失败：' + (err.response?.data?.detail || err.message))
  } finally {
    pendingLoading.value = false
  }
}

const fetchHistoryList = async () => {
  historyLoading.value = true
  try {
    // 获取已收费处方
    const presRes = await request.get('/api/prescriptions', {
      params: { payment_status: 'PAID' }
    })
    
    // 获取已结算住院患者
    const admRes = await request.get('/api/admissions', {
      params: { settled: true }
    })

    // 合并数据
    const presList = presRes.data.items.map((item: any) => ({
      id: item.id,
      type: 'prescription' as const,
      no: item.pres_no,
      patient_name: item.patient?.name || '未知',
      total_amount: item.total_amount,
      paid_amount: item.total_amount,
      charge_time: item.paid_at || item.updated_at
    }))

    const admList = admRes.data.items.map((item: any) => ({
      id: item.id,
      type: 'admission' as const,
      no: item.admission_no,
      patient_name: item.patient?.name || '未知',
      total_amount: item.total_fee || 0,
      paid_amount: item.total_fee || 0,
      charge_time: item.discharge_date
    }))

    historyList.value = [...presList, ...admList]
    historyTotal.value = presRes.data.total + admRes.data.total
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
  pendingQuery.page = 1
  fetchPendingList()
}

const handleHistorySearch = () => {
  historyQuery.page = 1
  fetchHistoryList()
}

const handleHistoryReset = () => {
  historyQuery.patient_name = ''
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
      // 处方收费
      await request.patch(`/api/prescriptions/${currentCharge.value.id}/pay`)
    } else {
      // 住院出院结算
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