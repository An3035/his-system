<template>
  <div class="page-wrap">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>药库库存</span>
          <div style="display:flex;gap:8px">
            <el-select v-model="warehouseType" placeholder="全部仓库" clearable style="width:140px"
              @change="loadInventory">
              <el-option label="西药库" value="西药库" />
              <el-option label="中药库" value="中药库" />
            </el-select>
            <el-button @click="loadInventory">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table :data="list" border v-loading="loading" style="width:100%">
        <el-table-column prop="id"             label="ID"    width="70" />
        <el-table-column prop="drug"           label="药品名称" width="200" />
        <el-table-column prop="stock_qty"      label="库存数量" width="120" />
        <el-table-column prop="warehouse_type" label="仓库类型" width="120" />
      </el-table>
    </el-card>

    <!-- 入库操作 -->
    <el-card style="margin-top:16px">
      <template #header><span>入库操作</span></template>
      <el-form :model="stockForm" inline label-width="80px">
        <el-form-item label="药品ID">
          <el-input-number v-model="stockForm.drug_id" :min="1" />
        </el-form-item>
        <el-form-item label="入库数量">
          <el-input-number v-model="stockForm.quantity" :min="1" />
        </el-form-item>
        <el-form-item label="仓库类型">
          <el-select v-model="stockForm.warehouse_type" style="width:120px">
            <el-option label="西药库" value="西药库" />
            <el-option label="中药库" value="中药库" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="submitStockIn">确认入库</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const list          = ref([])
const loading       = ref(false)
const warehouseType = ref('')
const stockForm     = ref({ drug_id: 1, quantity: 100, warehouse_type: '西药库' })

const loadInventory = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/warehouse/inventory', {
      params: { warehouse_type: warehouseType.value || undefined }
    })
    list.value = res.data
  } catch (err) {
    ElMessage.error('获取药库库存失败：' + (err.response?.data?.detail || err.message))
  } finally { loading.value = false }
}

const submitStockIn = async () => {
  try {
    await request.post('/api/warehouse/stock-in', null, { params: stockForm.value })
    ElMessage.success('入库成功！')
    loadInventory()
  } catch (err) {
    ElMessage.error('入库失败：' + (err.response?.data?.detail || err.message))
  }
}

onMounted(loadInventory)
</script>

<style scoped>
.card-header { display:flex; justify-content:space-between; align-items:center; }
</style>