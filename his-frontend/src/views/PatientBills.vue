<template>
  <div class="patient-bills">
    <h2 class="page-title">💰 我的账单</h2>

    <el-card>
      <!-- 汇总 -->
      <div class="bill-summary" v-if="items.length > 0">
        <span class="summary-label">合计已付：</span>
        <span class="summary-amount">¥{{ totalPaid.toFixed(2) }}</span>
        <span class="summary-count">（共 {{ items.length }} 笔）</span>
      </div>

      <el-table :data="items" border stripe v-loading="loading" style="width: 100%">
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.charge_type === '挂号收费' ? 'warning' : row.charge_type === '门诊处方' ? 'primary' : 'success'"
              size="small"
            >
              {{ row.charge_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ref_no" label="业务单号" width="160" />
        <el-table-column label="金额" width="100">
          <template #default="{ row }">¥{{ row.paid_amount }}</template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === '已收' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="收费时间" width="170">
          <template #default="{ row }">{{ formatDate(row.charge_time) }}</template>
        </el-table-column>
        <el-table-column prop="bill_no" label="账单号" min-width="180" />
      </el-table>
      <el-empty v-if="!loading && items.length === 0" description="暂无账单记录" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import request from '../utils/request'
import { formatDate } from '../utils/date'

const loading = ref(false)
const items = ref<any[]>([])

const totalPaid = computed(() => {
  return items.value.reduce((sum, b) => sum + (parseFloat(b.paid_amount) || 0), 0)
})

onMounted(async () => {
  loading.value = true
  try {
    const res = await request.get('/api/patient-self/bills')
    items.value = res.data.items || []
  } catch (e) {
    console.error('加载账单失败', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.patient-bills { max-width: 1000px; }
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 20px; color: #1f2329; }
.bill-summary { padding: 12px 16px; background: #f0fdf4; border-radius: 8px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
.summary-label { font-weight: 600; color: #606266; }
.summary-amount { font-size: 22px; font-weight: 700; color: #059669; }
.summary-count { font-size: 13px; color: #909399; }
</style>
