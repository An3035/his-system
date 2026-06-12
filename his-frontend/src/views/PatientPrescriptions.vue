<template>
  <div class="patient-pres">
    <h2 class="page-title">📝 我的处方记录</h2>

    <el-card v-for="pres in items" :key="pres.id" class="pres-card">
      <template #header>
        <div class="pres-header">
          <span>处方单号：{{ pres.pres_no }}</span>
          <span>
            <el-tag :type="pres.pres_type === '中药' ? 'warning' : 'primary'" size="small">
              {{ pres.pres_type }}
            </el-tag>
            <el-tag :type="pres.payment_status === '已付' ? 'success' : 'warning'" size="small" style="margin-left:8px">
              {{ pres.payment_status }}
            </el-tag>
            <el-tag v-if="pres.dispensed" type="success" size="small" style="margin-left:8px">已发药</el-tag>
            <el-tag v-else type="info" size="small" style="margin-left:8px">未发药</el-tag>
          </span>
        </div>
      </template>

      <div v-if="pres.diagnosis" class="diagnosis">诊断：{{ pres.diagnosis }}</div>

      <el-table :data="pres.items" border size="small" style="margin-top:8px">
        <el-table-column prop="drug_name" label="药品名称" />
        <el-table-column prop="quantity" label="数量" width="80" />
        <el-table-column prop="unit" label="单位" width="60" />
        <el-table-column label="金额" width="100">
          <template #default="{ row }">¥{{ row.amount }}</template>
        </el-table-column>
      </el-table>

      <div class="pres-footer">
        <span>总金额：<strong>¥{{ pres.total_amount }}</strong></span>
        <span class="pres-date">{{ formatDate(pres.created_at) }}</span>
      </div>
    </el-card>

    <el-empty v-if="!loading && items.length === 0" description="暂无处方记录" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '../utils/request'
import { formatDate } from '../utils/date'

const loading = ref(false)
const items = ref<any[]>([])

onMounted(async () => {
  loading.value = true
  try {
    const res = await request.get('/api/patient-self/prescriptions')
    items.value = res.data.items || []
  } catch (e) {
    console.error('加载处方记录失败', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.patient-pres { max-width: 900px; }
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 20px; color: #1f2329; }
.pres-card { margin-bottom: 16px; }
.pres-header { display: flex; justify-content: space-between; align-items: center; }
.diagnosis { font-size: 14px; color: #606266; margin-bottom: 8px; }
.pres-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 12px; font-size: 14px; }
.pres-date { color: #909399; font-size: 13px; }
</style>
