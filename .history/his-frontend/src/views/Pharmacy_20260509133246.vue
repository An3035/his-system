<template>
  <div class="page-wrap">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>药房管理（库存）</span>
          <div style="display:flex;gap:8px">
            <el-checkbox v-model="lowStockOnly" @change="loadInventory">仅显示预警</el-checkbox>
            <el-select v-model="pharmType" placeholder="全部药房" clearable style="width:140px"
              @change="loadInventory">
              <el-option label="中药房" value="中药房" />
              <el-option label="西药房" value="西药房" />
            </el-select>
            <el-button @click="loadInventory">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table :data="list" border v-loading="loading" style="width:100%">
        <el-table-column prop="id"            label="ID"    width="70" />
        <el-table-column label="药品名称" width="180">
          <template #default="{ row }">{{ row.drug?.name || row.drug_id }}</template>
        </el-table-column>
        <el-table-column label="药品类型" width="100">
          <template #default="{ row }">{{ row.drug?.drug_type || '-' }}</template>
        </el-table-column>
        <el-table-column prop="pharmacy_type" label="所属药房"   width="110" />
        <el-table-column prop="stock_qty"     label="当前库存"   width="110">
          <template #default="{ row }">
            <el-tag :type="Number(row.stock_qty) <= Number(row.alert_qty) ? 'danger' : 'success'">
              {{ row.stock_qty }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="alert_qty"     label="预警数量"   width="100" />
        <el-table-column label="规格" min-width="140">
          <template #default="{ row }">{{ row.drug?.specification || '-' }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 退药区域 -->
    <el-card style="margin-top:16px">
      <template #header><span>退药操作</span></template>
      <el-form :model="returnForm" inline label-width="80px">
        <el-form-item label="药品ID">
          <el-input-number v-model="returnForm.drug_id" :min="1" />
        </el-form-item>
        <el-form-item label="处方ID">
          <el-input-number v-model="returnForm.prescription_id" :min="1" />
        </el-form-item>
        <el-form-item label="退药数量">
          <el-input-number v-model="returnForm.quantity" :min="1" />
        </el-form-item>
        <el-form-item>
          <el-button type="warning" @click="submitReturn">确认退药</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const list         = ref([])
const loading      = ref(false)
const lowStockOnly = ref(false)
const pharmType    = ref('')

const returnForm = ref({ drug_id: 1, prescription_id: 1, quantity: 1 })

const loadInventory = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/pharmacy/inventory', {
      params: {
        low_stock: lowStockOnly.value || undefined,
        pharmacy_type: pharmType.value || undefined,
      }
    })
    list.value = res.data
  } catch (err) {
    ElMessage.error('获取库存失败：' + (err.response?.data?.detail || err.message))
  } finally { loading.value = false }
}

const submitReturn = async () => {
  try {
    await request.post('/api/pharmacy/return-drug', null, { params: returnForm.value })
    ElMessage.success('退药成功！')
    loadInventory()
  } catch (err) {
    ElMessage.error('退药失败：' + (err.response?.data?.detail || err.message))
  }
}

onMounted(loadInventory)
</script>

<style scoped>
.card-header { display:flex; justify-content:space-between; align-items:center; }
</style>