<template>
  <div class="pharmacy-order-container">
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <!-- ── 待发药（处方+医嘱合并） ── -->
      <el-tab-pane label="待发药" name="pending">
        <el-card class="search-card">
          <el-form :inline="true" class="search-form">
            <el-form-item label="患者姓名">
              <el-input v-model="searchName" placeholder="请输入" clearable style="width:160px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSearch">查询</el-button>
              <el-button @click="searchName = ''; handleSearch()">重置</el-button>
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
            <el-table-column label="来源" width="80">
              <template #default="{ row }">
                <el-tag :type="row._type === 'prescription' ? 'primary' : 'warning'" size="small">
                  {{ row._type === 'prescription' ? '处方' : '医嘱' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="id_display" label="编号" width="150" />
            <el-table-column prop="patient_name" label="患者姓名" width="110" />
            <el-table-column prop="patient_no" label="患者编号" width="120" />
            <el-table-column label="性别" width="70">
              <template #default="{ row }">{{ row.gender || '-' }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row._type === 'prescription' ? 'success' : 'warning'">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at_label" label="时间" width="155">
              <template #default="{ row }">{{ row.created_at_label }}</template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link @click="handleViewDetail(row)">查看详情</el-button>
                <el-button
                  v-if="row._type === 'prescription'"
                  type="success"
                  link
                  @click="handleDispensePrescription(row)"
                >发药</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!pendingLoading && pendingList.length === 0" description="暂无待发药项目" />
        </el-card>
      </el-tab-pane>

      <!-- ── 发药历史 ── -->
      <el-tab-pane label="发药历史" name="history">
        <el-card class="table-card">
          <el-table
            v-loading="historyLoading"
            :data="historyList"
            border
            stripe
            style="width: 100%"
          >
            <el-table-column label="来源" width="80">
              <template #default="{ row }">
                <el-tag :type="row._type === 'prescription' ? 'primary' : 'warning'" size="small">
                  {{ row._type === 'prescription' ? '处方' : '医嘱' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="id_display" label="编号" width="150" />
            <el-table-column prop="patient_name" label="患者姓名" width="110" />
            <el-table-column prop="patient_no" label="患者编号" width="120" />
            <el-table-column label="性别" width="70">
              <template #default="{ row }">{{ row.gender || '-' }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" />
            <el-table-column prop="created_at_label" label="时间" width="155" />
          </el-table>
          <el-empty v-if="!historyLoading && historyList.length === 0" description="暂无发药历史" />
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="详情" width="700px" :close-on-click-modal="false">
      <div v-if="currentItem" class="detail-info">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="类型">
            <el-tag :type="currentItem._type === 'prescription' ? 'primary' : 'warning'" size="small">
              {{ currentItem._type === 'prescription' ? '门诊处方' : '住院医嘱' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="编号">{{ currentItem.id_display }}</el-descriptions-item>
          <el-descriptions-item label="患者姓名">{{ currentItem.patient_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="患者编号">{{ currentItem.patient_no || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ currentItem.status }}</el-descriptions-item>
          <el-descriptions-item label="时间">{{ currentItem.created_at_label }}</el-descriptions-item>
        </el-descriptions>

        <div class="drug-detail-title" v-if="currentItem.drug_items && currentItem.drug_items.length">
          药品明细
        </div>
        <el-table v-if="currentItem.drug_items && currentItem.drug_items.length" :data="currentItem.drug_items" border stripe style="width: 100%">
          <el-table-column prop="drug_name" label="药品名称" min-width="140" />
          <el-table-column prop="specification" label="规格" width="110" />
          <el-table-column prop="quantity" label="数量" width="80" />
          <el-table-column prop="unit" label="单位" width="60" />
          <el-table-column prop="unit_price" label="单价" width="80" />
          <el-table-column prop="amount" label="金额" width="80" />
        </el-table>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button
          v-if="currentItem && currentItem._type === 'prescription'"
          type="success"
          @click="handleDispensePrescription(currentItem)"
        >执行发药</el-button>
      </template>
    </el-dialog>

    <!-- 确认发药弹窗 -->
    <el-dialog v-model="dispenseVisible" title="确认发药" width="400px" :close-on-click-modal="false">
      <div v-if="dispenseItem" class="dispense-confirm">
        <p>确认执行发药操作？</p>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="类型">
            <el-tag :type="dispenseItem._type === 'prescription' ? 'primary' : 'warning'" size="small">
              {{ dispenseItem._type === 'prescription' ? '门诊处方' : '住院医嘱' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="编号">{{ dispenseItem.id_display }}</el-descriptions-item>
          <el-descriptions-item label="患者姓名">{{ dispenseItem.patient_name }}</el-descriptions-item>
          <el-descriptions-item label="药品数">{{ dispenseItem.drug_items?.length || 0 }} 种</el-descriptions-item>
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
  specification?: string
  quantity: number
  unit: string
  unit_price?: number
  amount?: number
  dosage?: string
  dosage_unit?: string
  usage?: string
  frequency?: string
}

interface DispenseItem {
  _type: 'prescription' | 'order'
  id: number
  id_display: string
  patient_name: string
  patient_no?: string
  gender?: string
  status: string
  created_at_label: string
  created_at?: string
  drug_items: DrugItem[]
  // 处方发药用
  pres_no?: string
  // 医嘱发药用
  order_id?: string
}

const activeTab = ref('pending')
const searchName = ref('')

const pendingLoading = ref(false)
const pendingList = ref<DispenseItem[]>([])

const historyLoading = ref(false)
const historyList = ref<DispenseItem[]>([])

const detailVisible = ref(false)
const currentItem = ref<DispenseItem | null>(null)

const dispenseVisible = ref(false)
const dispenseItem = ref<DispenseItem | null>(null)
const dispenseLoading = ref(false)

/** 格式化时间显示 */
function fmtTime(t?: string): string {
  if (!t) return '-'
  try {
    return new Date(t).toLocaleString('zh-CN')
  } catch { return t }
}

/** 加载待发药列表（处方 + 医嘱） */
const fetchPendingList = async () => {
  pendingLoading.value = true
  try {
    // 1) 取已付款待发药处方
    const presRes = await request.get('/api/prescriptions/pending-dispense').catch(() => ({ data: [] }))
    const prescriptions: any[] = Array.isArray(presRes.data) ? presRes.data : []

    // 2) 取待发药医嘱
    const orderRes = await request.get('/api/orders', {
      params: { status: '待发药', page: 1, page_size: 100 }
    }).catch(() => ({ data: { items: [] } }))
    const orders: any[] = orderRes.data.items || []

    // 3) 合并
    const nameFilter = (name: string) => {
      if (!searchName.value) return true
      return (name || '').toLowerCase().includes(searchName.value.toLowerCase())
    }

    const presItems: DispenseItem[] = prescriptions
      .filter(p => nameFilter(p.patient_name))
      .map(p => ({
        _type: 'prescription' as const,
        id: p.id,
        id_display: p.pres_no || `处方#${p.id}`,
        patient_name: p.patient_name || '-',
        patient_no: p.patient_no,
        gender: p.gender,
        status: '已付费·待发药',
        created_at_label: fmtTime(p.created_at),
        created_at: p.created_at,
        drug_items: (p.drug_items || []).map((d: any) => ({
          drug_name: d.drug_name,
          specification: d.specification,
          quantity: d.quantity,
          unit: d.unit,
          unit_price: d.unit_price,
          amount: d.amount,
        })),
        pres_no: p.pres_no,
      }))

    const orderItems: DispenseItem[] = orders
      .filter((o: any) => nameFilter(o.patient_name))
      .map((o: any) => ({
        _type: 'order' as const,
        id: parseInt(o.order_id) || 0,
        id_display: o.admission_no ? `医嘱(${o.admission_no})` : `医嘱#${o.order_id}`,
        patient_name: o.patient_name || '-',
        patient_no: '',
        status: o.status || '待发药',
        created_at_label: fmtTime(o.order_time),
        created_at: o.order_time,
        drug_items: (o.drug_items || []).map((d: any) => ({
          drug_name: d.drug_name,
          specification: d.drug_spec,
          quantity: d.quantity,
          unit: d.dosage_unit,
          dosage: d.dosage,
          usage: d.usage,
          frequency: d.frequency,
        })),
        order_id: o.order_id,
      }))

    // 按时间倒序合并
    const all = [...presItems, ...orderItems]
    all.sort((a, b) => {
      if (!a.created_at) return 1
      if (!b.created_at) return -1
      return b.created_at.localeCompare(a.created_at)
    })
    pendingList.value = all
  } catch (err: any) {
    const detail = err.response?.data?.detail
    const msg = typeof detail === 'string' ? detail : err.message
    showError('获取待发药列表失败：' + msg)
  } finally {
    pendingLoading.value = false
  }
}

/** 加载发药历史 */
const fetchHistoryList = async () => {
  historyLoading.value = true
  try {
    // 已发药处方（dispensed = true）
    const presRes = await request.get('/api/prescriptions', {
      params: { page: 1, page_size: 100 }
    }).catch(() => ({ data: { items: [] } }))
    const allPres: any[] = presRes.data.items || []
    const dispensedPres = allPres.filter((p: any) => p.dispensed)

    // 已发药医嘱
    const orderRes = await request.get('/api/orders', {
      params: { status: '已发药', page: 1, page_size: 100 }
    }).catch(() => ({ data: { items: [] } }))
    const orders: any[] = orderRes.data.items || []

    const presItems: DispenseItem[] = dispensedPres.map((p: any) => ({
      _type: 'prescription' as const,
      id: p.id,
      id_display: p.pres_no || `处方#${p.id}`,
      patient_name: p.patient_name || p.patient?.name || '-',
      patient_no: p.patient_no || p.patient?.patient_no,
      gender: p.gender || p.patient?.gender,
      status: '已发药',
      created_at_label: fmtTime(p.updated_at || p.created_at),
      drug_items: (p.items || []).map((d: any) => ({
        drug_name: d.drug?.name || `药品#${d.drug_id}`,
        quantity: d.quantity,
        unit: d.unit,
      })),
    }))

    const orderItems: DispenseItem[] = orders.map((o: any) => ({
      _type: 'order' as const,
      id: parseInt(o.order_id) || 0,
      id_display: o.admission_no ? `医嘱(${o.admission_no})` : `医嘱#${o.order_id}`,
      patient_name: o.patient_name || '-',
      patient_no: '',
      status: o.status || '已发药',
      created_at_label: fmtTime(o.dispense_time || o.order_time),
      drug_items: (o.drug_items || []).map((d: any) => ({
        drug_name: d.drug_name,
        quantity: d.quantity,
        unit: d.dosage_unit,
      })),
    }))

    const all = [...presItems, ...orderItems]
    all.sort((a, b) => {
      if (!a.created_at) return 1; if (!b.created_at) return -1
      return b.created_at.localeCompare(a.created_at)
    })
    historyList.value = all
  } catch (err: any) {
    const detail = err.response?.data?.detail
    const msg = typeof detail === 'string' ? detail : err.message
    showError('获取发药历史失败：' + msg)
  } finally {
    historyLoading.value = false
  }
}

const handleSearch = () => { fetchPendingList() }

const handleTabChange = (tab: string) => {
  if (tab === 'pending') fetchPendingList()
  else if (tab === 'history') fetchHistoryList()
}

/** 查看详情 */
const handleViewDetail = (row: DispenseItem) => {
  currentItem.value = row
  detailVisible.value = true
}

/** 处方发药 */
const handleDispensePrescription = (row: DispenseItem) => {
  dispenseItem.value = row
  dispenseVisible.value = true
}

const confirmDispense = async () => {
  if (!dispenseItem.value) return
  dispenseLoading.value = true
  try {
    if (dispenseItem.value._type === 'prescription') {
      await request.patch(`/api/prescriptions/${dispenseItem.value.id}/dispense`)
    } else {
      await request.patch(`/api/orders/${dispenseItem.value.id}/execute`)
    }
    showSuccess('发药成功！')
    dispenseVisible.value = false
    detailVisible.value = false
    fetchPendingList()
  } catch (err: any) {
    const detail = err.response?.data?.detail
    const msg = typeof detail === 'string' ? detail : err.message
    showError('发药失败：' + msg)
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