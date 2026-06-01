<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>药房管理</span>
          <el-button type="primary" size="small" @click="openAddDialog">新增药品</el-button>
        </div>
      </template>

      <!-- 药品列表（对接MySQL） -->
      <el-table :data="drugList" border style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="药品ID" width="80" />
        <el-table-column prop="name" label="药品名称" width="150" />
        <el-table-column prop="specification" label="规格" width="150" />
        <el-table-column prop="manufacturer" label="生产厂家" width="200" />
        <el-table-column prop="stock" label="库存数量" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.stock < 10 ? 'danger' : 'success'">
              {{ scope.row.stock }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="retail_price" label="零售价格" width="100" />
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="openEditDialog(scope.row)">编辑</el-button>
            <el-button size="small" type="primary" @click="dispenseDrug(scope.row.id)">发药</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑药品弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="药品名称" required>
          <el-input v-model="form.name" placeholder="请输入药品名称" />
        </el-form-item>
        <el-form-item label="规格" required>
          <el-input v-model="form.specification" placeholder="请输入药品规格" />
        </el-form-item>
        <el-form-item label="生产厂家" required>
          <el-input v-model="form.manufacturer" placeholder="请输入生产厂家" />
        </el-form-item>
        <el-form-item label="库存数量" required>
          <el-input-number v-model="form.stock" :min="0" placeholder="请输入库存数量" />
        </el-form-item>
        <el-form-item label="零售价格" required>
          <el-input-number v-model="form.retail_price" :min="0" :precision="2" placeholder="请输入零售价格" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitDrugForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
// 复用你已有的 request.ts
import request from '../utils/request'

// 核心数据
const drugList = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const form = ref({
  id: '',
  name: '',
  specification: '',
  manufacturer: '',
  stock: 0,
  retail_price: 0
})

// 1. 获取药品列表
const getDrugList = async () => {
  loading.value = true
  try {
    const res = await request.get('/drug')
    drugList.value = res.data
  } catch (err) {
    ElMessage.error('获取药品列表失败：' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

// 2. 打开新增药品弹窗
const openAddDialog = () => {
  form.value = { id: '', name: '', specification: '', manufacturer: '', stock: 0, retail_price: 0 }
  dialogTitle.value = '新增药品'
  dialogVisible.value = true
}

// 3. 打开编辑药品弹窗
const openEditDialog = (row) => {
  form.value = { ...row }
  dialogTitle.value = '编辑药品'
  dialogVisible.value = true
}

// 4. 提交药品表单（新增/编辑）
const submitDrugForm = async () => {
  if (!form.value.name || !form.value.specification) {
    ElMessage.warning('请填写必填项！')
    return
  }
  try {
    if (form.value.id) {
      // 编辑药品
      await request.put(`/drug/${form.value.id}`, form.value)
      ElMessage.success('编辑药品成功！')
    } else {
      // 新增药品
      await request.post('/drug', form.value)
      ElMessage.success('新增药品成功！')
    }
    dialogVisible.value = false
    getDrugList()
  } catch (err) {
    ElMessage.error('操作失败：' + (err.response?.data?.detail || err.message))
  }
}

// 5. 发药（库存减1）
const dispenseDrug = async (id) => {
  try {
    await ElMessageBox.confirm('确定发药吗？库存将减少1', '提示')
    // 调用后端发药接口
    await request.put(`/drug/${id}/dispense`)
    ElMessage.success('发药成功！')
    getDrugList()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('发药失败：' + (err.response?.data?.detail || err.message))
    }
  }
}

// 页面加载时获取列表
onMounted(() => {
  getDrugList()
})
</script>

<style scoped>
.page-container {
  padding: 20px;
  background: #f3f3f4;
  min-height: calc(100vh - 80px);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>