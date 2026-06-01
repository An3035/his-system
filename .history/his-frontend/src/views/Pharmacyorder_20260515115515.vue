<template>
  <div class="pharmacy-order-container">
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="待发药医嘱" name="pending">
        <el-card class="search-card">
          <el-form :inline="true" :model="pendingQuery" class="search-form">
            <el-form-item label="住院号">
              <el-input
                v-model="pendingQuery.admission_no"
                placeholder="请输入住院号"
                clearable
              />
            </el-form-item>
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
            <el-table-column prop="order_id" label="医嘱编号" width="120" />
            <el-table-column prop="admission_no" label="住院号" width="120" />
            <el-table-column prop="patient_name" label="患者姓名" width="100" />
            <el-table-column prop="ward_name" label="病区" width="100" />
            <el-table-column prop="bed_no" label="床号" width="80" />
            <el-table-column prop="doctor_name" label="开单医生" width="100" />
            <el-table-column prop="order_time" label="开单时间" width="160">
              <template #default="{ row }">
                {{ formatDate(row.order_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="drug_count" label="药品数量" width="90" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag type="warning">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link @click="handleViewDetail(row)">查看详情</el-button>
                <el-button type="success" link @click="handleDispense(row)">执行发药</el-button>
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

      <el-tab-pane label="发药历史" name="history">
        <el-card class="search-card">
          <el-form :inline="true" :model="historyQuery" class="search-form">
            <el-form-item label="住院号">
              <el-input
                v-model="historyQuery.admission_no"
                placeholder="请输入住院号"
                clearable
              />
            </el-form-item>
            <el-form-item label="患者姓名">
              <el-input
                v-model="historyQuery.patient_name"
                placeholder="请输入患者姓名"
                clearable
              />
            </el-form-item>
            <el-form-item label="发药日期">
              <el-date-picker
                v-model="historyQuery.dispense_date"
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
            <el-table-column prop="order_id" label="医嘱编号" width="120" />
            <el-table-column prop="admission_no" label="住院号" width="120" />
            <el-table-column prop="patient_name" label="患者姓名" width="100" />
            <el-table-column prop="ward_name" label="病区" width="100" />
            <el-table-column prop="bed_no" label="床号" width="80" />
            <el-table-column prop="doctor_name" label="开单医生" width="100" />
            <el-table-column prop="order_time" label="开单时间" width="160">
              <template #default="{ row }">
                {{ formatDate(row.order_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="dispense_time" label="发药时间" width="160">
              <template #default="{ row }">
                {{ formatDate(row.dispense_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="dispenser_name" label="发药人" width="100" />
            <el-table-column prop="drug_count" label="药品数量" width="90" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag type="success">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link @click="handleViewDetail(row)">查看详情</el-button>
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
      v-model="detailVisible"
      title="医嘱详情"
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="currentOrder" class="detail-info">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="医嘱编号">{{ currentOrder.order_id }}</el-descriptions-item>
          <el-descriptions-item label="住院号">{{ currentOrder.admission_no }}</el-descriptions-item>
          <el-descriptions-item label="患者姓名">{{ currentOrder.patient_name }}</el-descriptions-item>
          <el-descriptions-item label="病区">{{ currentOrder.ward_name }}</el-descriptions-item>
          <el-descriptions-item label="床号">{{ currentOrder.bed_no }}</el-descriptions-item>
          <el-descriptions-item label="开单医生">{{ currentOrder.doctor_name }}</el-descriptions-item>
          <el-descriptions-item label="开单时间" :span="2">{{ formatDate(currentOrder.order_time) }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ currentOrder.status }}</el-descriptions-item>
        </el-descriptions>

        <div class="drug-detail-title">药品明细</div>
        <el-table
          :data="currentOrder.drug_items"
          border
          stripe
          style="width: 100%"
        >
          <el-table-column prop="drug_name" label="药品名称" />
          <el-table-column prop="drug_spec" label="规格" width="120" />
          <el-table-column prop="dosage" label="用量" width="100" />
          <el-table-column prop="dosage_unit" label="单位" width="80" />
          <el-table-column prop="usage" label="用法" width="100" />
          <el-table-column prop="frequency" label="频次" width="100" />
          <el-table-column prop="quantity" label="数量" width="80" />
        </el-table>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button
          v-if="currentOrder && currentOrder.status === '待发药'"
          type="success"
          @click="handleDispense(currentOrder)"
        >
          执行发药
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="dispenseVisible"
      title="确认发药"
      width="400px"
      :close-on-click-modal="false"
    >
      <div v-if="dispenseOrder" class="dispense-confirm">
        <p>确认对以下医嘱执行发药操作？</p>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="医嘱编号">{{ dispenseOrder.order_id }}</el-descriptions-item>
          <el-descriptions-item label="患者姓名">{{ dispenseOrder.patient_name }}</el-descriptions-item>
          <el-descriptions-item label="住院号">{{ dispenseOrder.admission_no }}</el-descriptions-item>
          <el-descriptions-item label="药品数量">{{ dispenseOrder.drug_count }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="dispenseVisible = false">取消</el-button>
        <el-button type="success" :loading="dispenseLoading" @click="confirmDispense">确认发药</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import request from '../utils/request'
import { formatDate } from '../utils/date'
import { showSuccess, showError } from '../utils/message'

interface DrugItem {
  drug_name: string
  drug_spec: string
  dosage: string
  dosage_unit: string
  usage: string
  frequency: string
  quantity: number
}

interface OrderItem {
  order_id: string
  admission_no: string
  patient_name: string
  ward_name: string
  bed_no: string
  doctor_name: string
  order_time: string
  dispense_time: string
  dispenser_name: string
  drug_count: number
  status: string
  drug_items: DrugItem[]
}

const activeTab = ref('pending')

const pendingLoading = ref(false)
const pendingList = ref<OrderItem[]>([])
const pendingTotal = ref(0)
const pendingQuery = reactive({
  admission_no: '',
  patient_name: '',
  page: 1,
  page_size: 10
})

const historyLoading = ref(false)
const historyList = ref<OrderItem[]>([])
const historyTotal = ref(0)
const historyQuery = reactive({
  admission_no: '',
  patient_name: '',
  dispense_date: '',
  page: 1,
  page_size: 10
})

const detailVisible = ref(false)
const currentOrder = ref<OrderItem | null>(null)

const dispenseVisible = ref(false)
const dispenseOrder = ref<OrderItem | null>(null)
const dispenseLoading = ref(false)

const fetchPendingList = async () => {
  pendingLoading.value = true
  try {
    const res = await request.get('/api/orders/pending', { params: pendingQuery })
    pendingList.value = res.data.items
    pendingTotal.value = res.data.total
  } catch {
    showError('获取待发药医嘱列表失败')
  } finally {
    pendingLoading.value = false
  }
}

const fetchHistoryList = async () => {
  historyLoading.value = true
  try {
    const res = await request.get('/api/orders/history', { params: historyQuery })
    historyList.value = res.data.items
    historyTotal.value = res.data.total
  } catch {
    showError('获取发药历史列表失败')
  } finally {
    historyLoading.value = false
  }
}

const handlePendingSearch = () => {
  pendingQuery.page = 1
  fetchPendingList()
}

const handlePendingReset = () => {
  pendingQuery.admission_no = ''
  pendingQuery.patient_name = ''
  pendingQuery.page = 1
  fetchPendingList()
}

const handleHistorySearch = () => {
  historyQuery.page = 1
  fetchHistoryList()
}

const handleHistoryReset = () => {
  historyQuery.admission_no = ''
  historyQuery.patient_name = ''
  historyQuery.dispense_date = ''
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

const handleViewDetail = async (row: OrderItem) => {
  try {
    const res = await request.get(`/api/orders/${row.order_id}`)
    currentOrder.value = res.data
    detailVisible.value = true
  } catch {
    showError('获取医嘱详情失败')
  }
}

const handleDispense = (row: OrderItem) => {
  dispenseOrder.value = row
  dispenseVisible.value = true
}

const confirmDispense = async () => {
  if (!dispenseOrder.value) return
  dispenseLoading.value = true
  try {
    await request.patch(`/api/orders/${dispenseOrder.value.order_id}/dispense`)
    showSuccess('发药成功')
    dispenseVisible.value = false
    if (detailVisible.value && currentOrder.value) {
      const res = await request.get(`/api/orders/${currentOrder.value.order_id}`)
      currentOrder.value = res.data
    }
    fetchPendingList()
  } catch {
    showError('发药操作失败')
  } finally {
    dispenseLoading.value = false
  }
}

onMounted(() => {
  fetchPendingList()
})
</script>

<style scoped>
.pharmacy-order-container {
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

.detail-info {
  padding: 0 8px;
}

.drug-detail-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 16px 0 8px;
}

.dispense-confirm p {
  margin-bottom: 12px;
  color: #606266;
  font-size: 14px;
}
</style>