<template>
  <div class="page-wrap">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>药品管理</span>
          <div style="display:flex;gap:8px">
            <el-input v-model="searchQ" placeholder="搜索药品名/编码" style="width:200px" clearable
              @keyup.enter="loadDrugs" />
            <el-select v-model="filterType" placeholder="全部类型" clearable style="width:120px"
              @change="loadDrugs">
              <el-option label="西药" value="西药" />
              <el-option label="中药" value="中药" />
            </el-select>
            <el-button @click="loadDrugs">搜索</el-button>
            <el-button type="primary" @click="openAdd">新增药品</el-button>
          </div>
        </div>
      </template>

      <el-table :data="list" border v-loading="loading" style="width:100%">
        <el-table-column prop="id"           label="ID"    width="60" />
        <el-table-column prop="drug_code"    label="药品编码" width="110" />
        <el-table-column prop="name"         label="药品名称" width="160" />
        <el-table-column prop="generic_name" label="通用名"  width="130" />
        <el-table-column prop="drug_type"    label="类型"   width="80">
          <template #default="{ row }">
            <el-tag :type="row.drug_type === '西药' ? 'primary' : 'success'">{{ row.drug_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="specification" label="规格"   width="140" />
        <el-table-column prop="unit"          label="单位"   width="70" />
        <el-table-column prop="retail_price"  label="零售价" width="100" />
        <el-table-column prop="manufacturer"  label="生产厂家" min-width="140" />
      </el-table>
    </el-card>

    <!-- 新增药品弹窗 -->
    <el-dialog v-model="dialogVisible" title="新增药品" width="540px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="药品编码" required>
          <el-input v-model="form.drug_code" placeholder="如 W006" />
        </el-form-item>
        <el-form-item label="药品名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="通用名">
          <el-input v-model="form.generic_name" />
        </el-form-item>
        <el-form-item label="药品类型" required>
          <el-select v-model="form.drug_type" style="width:100%">
            <el-option label="西药" value="西药" />
            <el-option label="中药" value="中药" />
          </el-select>
        </el-form-item>
        <el-form-item label="规格">
          <el-input v-model="form.specification" placeholder="如 0.25g×24粒" />
        </el-form-item>
        <el-form-item label="单位">
          <el-input v-model="form.unit" placeholder="如 盒 / 克 / 瓶" />
        </el-form-item>
        <el-form-item label="零售价" required>
          <el-input-number v-model="form.retail_price" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="进货价">
          <el-input-number v-model="form.purchase_price" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="生产厂家">
          <el-input v-model="form.manufacturer" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const list       = ref([])
const loading    = ref(false)
const searchQ    = ref('')
const filterType = ref('')
const dialogVisible = ref(false)
const form = ref({
  drug_code:'', name:'', generic_name:'', drug_type:'西药',
  specification:'', unit:'', retail_price:0, purchase_price:0, manufacturer:''
})

const loadDrugs = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/drugs', {
      params: { q: searchQ.value, drug_type: filterType.value || undefined }
    })
    list.value = res.data
  } catch (err) {
    ElMessage.error('获取药品列表失败：' + (err.response?.data?.detail || err.message))
  } finally { loading.value = false }
}

const openAdd = () => {
  form.value = { drug_code:'', name:'', generic_name:'', drug_type:'西药',
    specification:'', unit:'', retail_price:0, purchase_price:0, manufacturer:'' }
  dialogVisible.value = true
}

const submit = async () => {
  if (!form.value.drug_code || !form.value.name) {
    ElMessage.warning('请填写药品编码和名称！')
    return
  }
  try {
    await request.post('/api/drugs', form.value)
    ElMessage.success('新增药品成功！')
    dialogVisible.value = false
    loadDrugs()
  } catch (err) {
    ElMessage.error('操作失败：' + (err.response?.data?.detail || err.message))
  }
}

onMounted(loadDrugs)
</script>

<style scoped>
.card-header { display:flex; justify-content:space-between; align-items:center; }
</style>