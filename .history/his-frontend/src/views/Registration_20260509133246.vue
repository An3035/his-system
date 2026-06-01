<template>
  <div class="page-wrap">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>门诊挂号</span>
          <el-button type="primary" @click="openAdd">新增挂号</el-button>
        </div>
      </template>

      <el-table :data="list" border v-loading="loading" style="width:100%">
        <el-table-column prop="id"             label="挂号ID"  width="80" />
        <el-table-column prop="reg_no"         label="挂号单号" width="160" />
        <el-table-column prop="patient_id"     label="患者ID"  width="80" />
        <el-table-column prop="doctor_id"      label="医生ID"  width="80" />
        <el-table-column prop="reg_type"       label="挂号类型" width="100">
          <template #default="{ row }">
            <el-tag :type="typeColor(row.reg_type)">{{ row.reg_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reg_fee"        label="挂号费"  width="90" />
        <el-table-column prop="visit_date"     label="就诊日期" width="130" />
        <el-table-column prop="payment_status" label="缴费状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.payment_status === 'paid' ? 'success' : 'warning'">
              {{ row.payment_status === 'paid' ? '已缴费' : '待缴费' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="success"
              v-if="row.payment_status !== 'paid'"
              @click="pay(row.id)">缴费</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增挂号弹窗 -->
    <el-dialog v-model="dialogVisible" title="新增挂号" width="520px">
      <el-form :model="form" label-width="90px">

        <!-- 患者搜索 -->
        <el-form-item label="选择患者" required>
          <el-autocomplete
            v-model="patientSearchText"
            :fetch-suggestions="searchPatient"
            placeholder="输入姓名或电话搜索"
            value-key="label"
            style="width:100%"
            @select="onSelectPatient"
          />
          <div v-if="form.patient_id" style="margin-top:4px;color:#667085;font-size:12px">
            已选患者 ID: {{ form.patient_id }}
          </div>
        </el-form-item>

        <el-form-item label="挂号类型" required>
          <el-select v-model="form.reg_type" style="width:100%">
            <el-option label="普通 (¥5)"  value="普通" />
            <el-option label="专家 (¥20)" value="专家" />
            <el-option label="急诊 (¥15)" value="急诊" />
            <el-option label="专科 (¥10)" value="专科" />
          </el-select>
        </el-form-item>

        <el-form-item label="医生ID" required>
          <el-input-number v-model="form.doctor_id" :min="1" style="width:100%" />
          <div style="font-size:12px;color:#999;margin-top:4px">
            种子数据医生：张伟(1) 李芳(2) 王磊(3) 赵敏(4)
          </div>
        </el-form-item>

        <el-form-item label="就诊日期" required>
          <el-date-picker v-model="form.visit_date" type="date"
            value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">确定挂号</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const list    = ref([])
const loading = ref(false)

const dialogVisible    = ref(false)
const patientSearchText = ref('')
const form = ref({ patient_id: null, doctor_id: 1, reg_type: '普通', visit_date: '', remark: '' })

/* ── 列表 ── */
const loadList = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/registrations')
    list.value = res.data
  } catch (err) {
    ElMessage.error('获取挂号列表失败：' + (err.response?.data?.detail || err.message))
  } finally { loading.value = false }
}

/* ── 搜索患者（autocomplete） ── */
const searchPatient = async (query, cb) => {
  if (!query) return cb([])
  try {
    const res = await request.get('/api/patients', { params: { q: query } })
    cb(res.data.map(p => ({ label: `${p.name}（${p.phone || p.patient_no}）`, value: p.id, ...p })))
  } catch { cb([]) }
}
const onSelectPatient = (item) => { form.value.patient_id = item.id }

/* ── 新增 ── */
const openAdd = () => {
  patientSearchText.value = ''
  form.value = { patient_id: null, doctor_id: 1, reg_type: '普通', visit_date: '', remark: '' }
  dialogVisible.value = true
}

/* ── 提交 ── */
const submit = async () => {
  if (!form.value.patient_id || !form.value.visit_date) {
    ElMessage.warning('请填写患者和就诊日期！')
    return
  }
  try {
    await request.post('/api/registrations', form.value)
    ElMessage.success('挂号成功！')
    dialogVisible.value = false
    loadList()
  } catch (err) {
    ElMessage.error('挂号失败：' + (err.response?.data?.detail || err.message))
  }
}

/* ── 缴费 ── */
const pay = async (id) => {
  try {
    await request.patch(`/api/registrations/${id}/pay`)
    ElMessage.success('缴费成功！')
    loadList()
  } catch (err) {
    ElMessage.error('缴费失败：' + (err.response?.data?.detail || err.message))
  }
}

const typeColor = (t) => ({ '普通':'', '专家':'warning', '急诊':'danger', '专科':'success' }[t] || '')

onMounted(loadList)
</script>

<style scoped>
.card-header { display:flex; justify-content:space-between; align-items:center; }
</style>