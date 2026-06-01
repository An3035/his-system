<template>
  <div class="page-wrap">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>患者管理</span>
          <div style="display:flex;gap:8px">
            <el-input v-model="searchQ" placeholder="搜索姓名/电话/病历号"
              style="width:220px" clearable @keyup.enter="loadPatients" />
            <el-button @click="loadPatients">搜索</el-button>
            <el-button type="primary" @click="openAdd">新增患者</el-button>
          </div>
        </div>
      </template>

      <el-table :data="list" border v-loading="loading" style="width:100%">
        <el-table-column prop="id"         label="ID"     width="70" />
        <el-table-column prop="patient_no" label="病历号"  width="130" />
        <el-table-column prop="name"       label="姓名"   width="100" />
        <el-table-column prop="gender"     label="性别"   width="70" />
        <el-table-column prop="birth_date" label="出生日期" width="120" />
        <el-table-column prop="phone"      label="联系电话" width="140" />
        <el-table-column prop="ic_card_no" label="身份证号"  width="180" />
        <el-table-column prop="address"    label="地址"   min-width="160" />
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row)">详情</el-button>
            <el-button size="small" type="success" @click="quickRegister(row)">挂号</el-button>
            <el-button size="small" type="warning" @click="quickAdmit(row)">入院</el-button>
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="del(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="姓名" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="性别" required>
          <el-select v-model="form.gender" style="width:100%">
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
          </el-select>
        </el-form-item>
        <el-form-item label="出生日期">
          <el-date-picker v-model="form.birth_date" type="date" value-format="YYYY-MM-DD"
            placeholder="选择日期" style="width:100%" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="身份证号">
          <el-input v-model="form.ic_card_no" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.address" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 患者详情弹窗 -->
    <el-dialog v-model="detailVisible" title="患者详情" width="800px">
      <div style="margin-bottom:12px" v-if="currentPatient">
        <el-button type="warning" size="small" :loading="aiSummaryLoading" @click="generateAiSummary">
          AI 病历摘要
        </el-button>
        <div v-if="aiSummaryText" style="margin-top:8px;padding:12px;background:#fef8e7;border-radius:8px;white-space:pre-wrap;line-height:1.8;font-size:13px">
          {{ aiSummaryText }}
        </div>
      </div>
      <el-descriptions :column="3" border v-if="currentPatient">
        <el-descriptions-item label="ID">{{ currentPatient.id }}</el-descriptions-item>
        <el-descriptions-item label="病历号">{{ currentPatient.patient_no }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ currentPatient.name }}</el-descriptions-item>
        <el-descriptions-item label="性别">{{ currentPatient.gender }}</el-descriptions-item>
        <el-descriptions-item label="出生日期">{{ currentPatient.birth_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ currentPatient.phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="身份证号" :span="2">{{ currentPatient.ic_card_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="地址" :span="3">{{ currentPatient.address || '-' }}</el-descriptions-item>
      </el-descriptions>

      <div style="margin-top:20px">
        <el-tabs v-model="detailTab" @tab-change="onDetailTabChange">
          <el-tab-pane label="挂号记录" name="registrations">
            <el-table :data="patientRecords.registrations" border size="small" v-loading="recordsLoading">
              <el-table-column prop="reg_no" label="挂号单号" width="150" />
              <el-table-column prop="reg_type" label="挂号类型" width="90" />
              <el-table-column prop="doctor_id" label="医生ID" width="80" />
              <el-table-column prop="visit_date" label="就诊日期" width="120" />
              <el-table-column prop="reg_fee" label="挂号费" width="80" />
              <el-table-column prop="payment_status" label="缴费状态" width="90">
                <template #default="{ row }">
                  <el-tag :type="row.payment_status === '已付' ? 'success' : 'warning'" size="small">
                    {{ row.payment_status === '已付' ? '已缴费' : '待缴费' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!recordsLoading && patientRecords.registrations.length === 0" description="暂无挂号记录" />
          </el-tab-pane>

          <el-tab-pane label="处方记录" name="prescriptions">
            <el-table :data="patientRecords.prescriptions" border size="small" v-loading="recordsLoading">
              <el-table-column prop="pres_no" label="处方单号" width="150" />
              <el-table-column prop="pres_type" label="类型" width="90" />
              <el-table-column prop="total_amount" label="金额" width="90" />
              <el-table-column prop="payment_status" label="缴费状态" width="90">
                <template #default="{ row }">
                  <el-tag :type="row.payment_status === '已付' ? 'success' : 'warning'" size="small">
                    {{ row.payment_status === '已付' ? '已缴费' : '待缴费' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="开立时间" width="160">
                <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!recordsLoading && patientRecords.prescriptions.length === 0" description="暂无处方记录" />
          </el-tab-pane>

          <el-tab-pane label="住院记录" name="admissions">
            <el-table :data="patientRecords.admissions" border size="small" v-loading="recordsLoading">
              <el-table-column prop="admission_no" label="住院号" width="150" />
              <el-table-column prop="bed_id" label="床位ID" width="80" />
              <el-table-column prop="department_id" label="科室ID" width="80" />
              <el-table-column prop="admit_date" label="入院日期" width="140">
                <template #default="{ row }">{{ formatDate(row.admit_date) }}</template>
              </el-table-column>
              <el-table-column prop="discharge_date" label="出院日期" width="140">
                <template #default="{ row }">{{ row.discharge_date ? formatDate(row.discharge_date) : '在院' }}</template>
              </el-table-column>
              <el-table-column prop="deposit" label="押金" width="90" />
              <el-table-column prop="total_fee" label="总费用" width="90" />
              <el-table-column prop="settled" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.settled ? 'success' : 'warning'" size="small">
                    {{ row.settled ? '已出院' : '在院' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!recordsLoading && patientRecords.admissions.length === 0" description="暂无住院记录" />
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>

    <!-- 快速挂号弹窗 -->
    <el-dialog v-model="regDialogVisible" title="快速挂号" width="520px">
      <el-form :model="regForm" label-width="90px">
        <el-form-item label="患者">
          <el-input :model-value="`${currentPatient?.name} (ID:${currentPatient?.id})`" disabled />
        </el-form-item>
        <el-form-item label="挂号类型" required>
          <el-select v-model="regForm.reg_type" style="width:100%">
            <el-option label="普通 (¥5)"  value="普通" />
            <el-option label="专家 (¥20)" value="专家" />
            <el-option label="急诊 (¥15)" value="急诊" />
            <el-option label="专科 (¥10)" value="专科" />
          </el-select>
        </el-form-item>
        <el-form-item label="医生ID" required>
          <el-input-number v-model="regForm.doctor_id" :min="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="就诊日期" required>
          <el-date-picker v-model="regForm.visit_date" type="date"
            value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="regForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="regDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRegister">确定挂号</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import request from '../utils/request'
import { formatDate } from '../utils/date'

const router = useRouter()

const list    = ref([])
const loading = ref(false)
const searchQ = ref('')

const dialogVisible = ref(false)
const dialogTitle   = ref('')
const form = ref({ id:'', name:'', gender:'', birth_date:'', phone:'', ic_card_no:'', address:'' })

const detailVisible = ref(false)
const detailTab = ref('registrations')
const currentPatient = ref(null)
const recordsLoading = ref(false)
const patientRecords = ref({ registrations: [], prescriptions: [], admissions: [] })

const regDialogVisible = ref(false)
const regForm = ref({ patient_id: null, doctor_id: 1, reg_type: '普通', visit_date: '', remark: '' })

/* ── 列表 ── */
const loadPatients = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/patients', { params: { q: searchQ.value } })
    list.value = res.data
  } catch (err) {
    ElMessage.error('获取患者列表失败：' + (err.response?.data?.detail || err.message))
  } finally { loading.value = false }
}

/* ── 新增 ── */
const openAdd = () => {
  form.value = { id:'', name:'', gender:'', birth_date:'', phone:'', ic_card_no:'', address:'' }
  dialogTitle.value = '新增患者'
  dialogVisible.value = true
}

/* ── 编辑 ── */
const openEdit = (row) => {
  form.value = { ...row }
  dialogTitle.value = '编辑患者'
  dialogVisible.value = true
}

/* ── 提交 ── */
const submit = async () => {
  if (!form.value.name || !form.value.gender) {
    ElMessage.warning('请填写姓名和性别！')
    return
  }
  try {
    const payload = { ...form.value }
    delete payload.id
    if (form.value.id) {
      await request.put(`/api/patients/${form.value.id}`, payload)
      ElMessage.success('编辑成功！')
    } else {
      await request.post('/api/patients', payload)
      ElMessage.success('新增患者成功！')
    }
    dialogVisible.value = false
    loadPatients()
  } catch (err) {
    ElMessage.error('操作失败：' + (err.response?.data?.detail || err.message))
  }
}

/* ── 删除 ── */
const del = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除该患者吗？', '提示', { type: 'warning' })
    await request.delete(`/api/patients/${id}`)
    ElMessage.success('删除成功！')
    loadPatients()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败：' + (err.response?.data?.detail || err.message))
  }
}

/* ── 详情 ── */
const viewDetail = (row) => {
  currentPatient.value = row
  detailVisible.value = true
  detailTab.value = 'registrations'
  loadPatientRecords(row.id)
}

const onDetailTabChange = () => {
  if (currentPatient.value) {
    loadPatientRecords(currentPatient.value.id)
  }
}

const loadPatientRecords = async (patientId) => {
  recordsLoading.value = true
  try {
    const [regRes, presRes, admRes] = await Promise.all([
      request.get('/api/registrations', { params: { patient_id: patientId } }).catch(() => ({ data: [] })),
      request.get('/api/prescriptions', { params: { patient_id: patientId } }).catch(() => ({ data: { items: [] } })),
      request.get('/api/admissions', { params: { patient_id: patientId } }).catch(() => ({ data: [] }))
    ])
    patientRecords.value.registrations = Array.isArray(regRes.data) ? regRes.data : []
    patientRecords.value.prescriptions = presRes.data.items || []
    patientRecords.value.admissions = Array.isArray(admRes.data) ? admRes.data : []
  } catch (e) {
    console.error('加载患者记录失败', e)
  } finally {
    recordsLoading.value = false
  }
}

/* ── 快速挂号 ── */
const quickRegister = (row) => {
  currentPatient.value = row
  regForm.value = { patient_id: row.id, doctor_id: 1, reg_type: '普通', visit_date: new Date().toISOString().split('T')[0], remark: '' }
  regDialogVisible.value = true
}

const submitRegister = async () => {
  if (!regForm.value.visit_date) {
    ElMessage.warning('请填写就诊日期！')
    return
  }
  try {
    await request.post('/api/registrations', regForm.value)
    ElMessage.success('挂号成功！')
    regDialogVisible.value = false
  } catch (err) {
    ElMessage.error('挂号失败：' + (err.response?.data?.detail || err.message))
  }
}

/* ── 快速入院 ── */
const aiSummaryLoading = ref(false)
const aiSummaryText = ref('')

const generateAiSummary = async () => {
  if (!currentPatient.value) return
  aiSummaryLoading.value = true
  aiSummaryText.value = ''
  try {
    const res = await request.post(`/api/ai/summarize-patient/${currentPatient.value.id}`)
    aiSummaryText.value = res.data.summary || JSON.stringify(res.data)
  } catch (err) {
    ElMessage.error('AI摘要生成失败：' + (err.response?.data?.detail || err.message))
  } finally {
    aiSummaryLoading.value = false
  }
}

const quickAdmit = (row) => {
  // 携带患者ID跳转至入院管理页面
  router.push({ path: '/index/admission', query: { patient_id: row.id, patient_name: row.name } })
}

onMounted(loadPatients)
</script>

<style scoped>
.card-header { display:flex; justify-content:space-between; align-items:center; }
</style>
