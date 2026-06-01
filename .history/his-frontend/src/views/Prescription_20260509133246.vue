<template>
  <div class="page-wrap">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>处方管理 — 待发药列表</span>
          <el-button @click="loadList">刷新</el-button>
        </div>
      </template>

      <el-table :data="list" border v-loading="loading" style="width:100%">
        <el-table-column prop="id"             label="处方ID"  width="80" />
        <el-table-column prop="pres_no"        label="处方单号" width="160" />
        <el-table-column prop="pres_type"      label="处方类型" width="100" />
        <el-table-column prop="diagnosis"      label="诊断"   min-width="160" />
        <el-table-column prop="total_amount"   label="金额"   width="100" />
        <el-table-column prop="payment_status" label="缴费"   width="90">
          <template #default="{ row }">
            <el-tag type="success">{{ row.payment_status === 'paid' ? '已缴费' : row.payment_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="药品明细" min-width="200">
          <template #default="{ row }">
            <div v-for="item in row.items" :key="item.id" style="font-size:12px">
              药品#{{ item.drug_id }} × {{ item.quantity }}{{ item.unit }} = ¥{{ item.amount }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="dispense(row.id)">发药</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && list.length === 0" description="暂无待发药处方" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request'

const list    = ref([])
const loading = ref(false)

const loadList = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/prescriptions/pending-dispense')
    list.value = res.data
  } catch (err) {
    ElMessage.error('获取待发药列表失败：' + (err.response?.data?.detail || err.message))
  } finally { loading.value = false }
}

const dispense = async (id) => {
  try {
    await ElMessageBox.confirm('确认发药？发药后库存将自动扣减。', '提示', { type: 'warning' })
    await request.patch(`/api/prescriptions/${id}/dispense`)
    ElMessage.success('发药完成！')
    loadList()
  } catch (err) {
    if (err !== 'cancel')
      ElMessage.error('发药失败：' + (err.response?.data?.detail || err.message))
  }
}

onMounted(loadList)
</script>

<style scoped>
.card-header { display:flex; justify-content:space-between; align-items:center; }
</style>