<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>患者管理</span>
          <el-button type="primary" size="small" @click="openAddDialog">新增患者</el-button>
        </div>
      </template>

      <!-- 患者列表（对接MySQL） -->
      <el-table :data="patientList" border style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="患者ID" width="80" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="gender" label="性别" width="80" />
        <el-table-column prop="age" label="年龄" width="80" />
        <el-table-column prop="phone" label="联系电话" width="150" />
        <el-table-column prop="id_card" label="身份证号" width="180" />
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="openEditDialog(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deletePatient(scope.row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="姓名" required>
          <el-input v-model="form.name" placeholder="请输入患者姓名" />
        </el-form-item>
        <el-form-item label="性别" required>
          <el-select v-model="form.gender" placeholder="请选择性别">
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
          </el-select>
        </el-form-item>
        <el-form-item label="年龄" required>
          <el-input-number v-model="form.age" :min="0" :max="150" placeholder="请输入年龄" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="身份证号">
          <el-input v-model="form.id_card" placeholder="请输入身份证号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
// 复用你已有的 request.ts（关键！）
import request from '../utils/request'

// 核心数据
const patientList = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const form = ref({
  id: '',
  name: '',
  gender: '',
  age: 0,
  phone: '',
  id_card: ''
})

// 1. 获取患者列表（真实读取MySQL）
const getPatientList = async () => {
  loading.value = true
  try {
    // 调用你后端的患者列表接口
    const res = await request.get('/patient')
    patientList.value = res.data
  } catch (err) {
    ElMessage.error('获取患者列表失败：' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

// 2. 打开新增弹窗
const openAddDialog = () => {
  // 重置表单
  form.value = { id: '', name: '', gender: '', age: 0, phone: '', id_card: '' }
  dialogTitle.value = '新增患者'
  dialogVisible.value = true
}

// 3. 打开编辑弹窗
const openEditDialog = (row) => {
  form.value = { ...row }
  dialogTitle.value = '编辑患者'
  dialogVisible.value = true
}

// 4. 提交表单（新增/编辑）
const submitForm = async () => {
  if (!form.value.name) {
    ElMessage.warning('请输入患者姓名！')
    return
  }
  try {
    if (form.value.id) {
      // 编辑：调用后端更新接口
      await request.put(`/patient/${form.value.id}`, form.value)
      ElMessage.success('编辑患者成功！')
    } else {
      // 新增：调用后端创建接口
      await request.post('/patient', form.value)
      ElMessage.success('新增患者成功！')
    }
    dialogVisible.value = false
    getPatientList() // 刷新列表
  } catch (err) {
    ElMessage.error('操作失败：' + (err.response?.data?.detail || err.message))
  }
}

// 5. 删除患者
const deletePatient = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该患者吗？', '提示', {
      type: 'warning'
    })
    // 调用后端删除接口
    await request.delete(`/patient/${id}`)
    ElMessage.success('删除患者成功！')
    getPatientList() // 刷新列表
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除失败：' + (err.response?.data?.detail || err.message))
    }
  }
}

// 页面加载时获取列表
onMounted(() => {
  getPatientList()
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