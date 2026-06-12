<template>
  <div class="patient-regs">
    <h2 class="page-title">📋 我的挂号记录</h2>

    <el-card>
      <el-table :data="items" border stripe v-loading="loading" style="width: 100%">
        <el-table-column prop="reg_no" label="挂号单号" width="160" />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <el-tag
              :type="row.reg_type === '急诊' ? 'danger' : row.reg_type === '专家' ? 'warning' : 'primary'"
              size="small"
            >
              {{ row.reg_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="department_name" label="科室" width="120" />
        <el-table-column prop="doctor_name" label="医生" width="100" />
        <el-table-column label="挂号费" width="100">
          <template #default="{ row }">¥{{ row.reg_fee }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.payment_status === '已付' ? 'success' : 'warning'" size="small">
              {{ row.payment_status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="挂号时间" width="160">
          <template #default="{ row }">{{ formatDate(row.reg_date) }}</template>
        </el-table-column>
        <el-table-column label="就诊日期" width="120">
          <template #default="{ row }">{{ row.visit_date || '-' }}</template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && items.length === 0" description="暂无挂号记录" />
    </el-card>
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
    const res = await request.get('/api/patient-self/registrations')
    items.value = res.data.items || []
  } catch (e) {
    console.error('加载挂号记录失败', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.patient-regs { max-width: 1000px; }
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 20px; color: #1f2329; }
</style>
