<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>门诊挂号</span>
          <el-button type="primary" size="small" @click="openAddDialog">新增挂号</el-button>
        </div>
      </template>

      <!-- 挂号列表（对接MySQL） -->
      <el-table :data="registrationList" border style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="挂号ID" width="80" />
        <el-table-column prop="patient_name" label="患者姓名" width="100" />
        <el-table-column prop="department_name" label="就诊科室" width="120" />
        <el-table-column prop="doctor_name" label="接诊医生" width="120" />
        <el-table-column prop="register_time" label="挂号时间" width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === '已就诊' ? 'success' : 'primary'">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" type="success" @click="finishRegistration(scope.row.id)" v-if="scope.row.status === '待就诊'">
              完成就诊
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增挂号弹窗 -->
    <el-dialog v-model="dialogVisible" title="新增挂号" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="患者姓名" required>
          <el-input v-model="form.patient_name" placeholder="请输入患者姓名" />
        </el-form-item>
        <el-form-item label="就诊科室" required>
          <el-select v-model="form.department_name" placeholder="请选择科室">
            <el-option label="内科" value="内科" />
            <el-option label="外科" value="外科" />
            <el-option label="儿科" value="儿科" />
            <el-option label="妇科" value="妇科" />
          </el-select>
        </el-form-item>
        <el-form-item label="接诊医生" required>
          <el-input v-model="form.doctor_name" placeholder="请输入医生姓名" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRegistration">确定挂号</el-button>
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
const registrationList = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const form = ref({
  patient_name: '',
  department_name: '',
  doctor_name: ''
})

// 1. 获取挂号列表
const getRegistrationList = async () => {
  loading.value = true
  try {
    const res = await request.get('/registration')
    registrationList.value = res.data
  } catch (err) {
    ElMessage.error('获取挂号列表失败：' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

// 2. 打开新增挂号弹窗
const openAddDialog = () => {
  form.value = { patient_name: '', department_name: '', doctor_name: '' }
  dialogVisible.value = true
}

// 3. 提交挂号
const submitRegistration = async () => {
  if (!form.value.patient_name || !form.value.department_name) {
    ElMessage.warning('请填写必填项！')
    return
  }
  try {
    // 调用后端挂号创建接口
    await request.post('/registration', {
      ...form.value,
      register_time: new Date().toISOString(),
      status: '待就诊'
    })
    ElMessage.success('挂号成功！')
    dialogVisible.value = false
    getRegistrationList()
  } catch (err) {
    ElMessage.error('挂号失败：' + (err.response?.data?.detail || err.message))
  }
}

// 4. 完成就诊
const finishRegistration = async (id) => {
  try {
    await request.put(`/registration/${id}`, { status: '已就诊' })
    ElMessage.success('标记就诊完成！')
    getRegistrationList()
  } catch (err) {
    ElMessage.error('操作失败：' + (err.response?.data?.detail || err.message))
  }
}

// 页面加载时获取列表
onMounted(() => {
  getRegistrationList()
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