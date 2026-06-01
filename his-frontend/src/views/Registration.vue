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
        <el-table-column label="患者信息" min-width="160">
          <template #default="{ row }">
            <div v-if="row.patient">
              <div style="font-weight:500">{{ row.patient.name }}</div>
              <div style="font-size:12px;color:#667085">{{ row.patient.phone }} / {{ row.patient.patient_no }}</div>
            </div>
            <div v-else>
              <div>{{ getPatientName(row.patient_id) }}</div>
              <div style="font-size:12px;color:#667085">患者ID: {{ row.patient_id }}</div>
            </div>
          </template>
        </el-table-column>
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
            <el-tag :type="row.payment_status === '已付' ? 'success' : 'warning'">
              {{ row.payment_status === '已付' ? '已缴费' : '待缴费' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="success"
              v-if="row.payment_status !== '已付'"
              @click="pay(row.id)">缴费</el-button>
            <el-button size="small" type="primary"
              v-if="row.payment_status === '已付'"
              @click="openPrescription(row)">开处方</el-button>
            <el-button size="small" @click="viewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增挂号弹窗 -->
    <el-dialog v-model="dialogVisible" title="新增挂号" width="560px">
      <el-form :model="form" label-width="90px">

        <!-- AI 智能分诊 -->
        <el-form-item label="AI 智能分诊">
          <div style="display:flex;gap:8px;width:100%">
            <el-input
              v-model="symptoms"
              type="textarea"
              :rows="2"
              placeholder="输入患者症状描述，AI 将推荐科室和医生…"
              :disabled="triageLoading"
            />
            <el-button
              type="primary"
              :loading="triageLoading"
              :disabled="!symptoms.trim()"
              @click="aiTriage"
              style="flex-shrink:0;align-self:flex-start"
            >🤖 分诊</el-button>
          </div>
          <transition name="fade">
            <div v-if="triageResult" class="triage-result">
              <div class="triage-header">
                <span class="triage-badge">AI 推荐</span>
                <el-button text size="small" @click="applyTriage">应用</el-button>
                <el-button text size="small" @click="triageResult = null">✕</el-button>
              </div>
              <div class="triage-body">
                <div><strong>科室：</strong>{{ triageResult.department || '-' }}</div>
                <div><strong>号别：</strong>
                  <el-tag size="small" :type="triageTagType(triageResult.reg_type)">{{ triageResult.reg_type || '-' }}</el-tag>
                </div>
                <div><strong>医生：</strong>{{ triageResult.doctor || '不限' }}</div>
                <div class="triage-reason"><strong>理由：</strong>{{ triageResult.reason }}</div>
              </div>
            </div>
          </transition>
        </el-form-item>

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

    <!-- 开处方弹窗 -->
    <el-dialog v-model="presDialogVisible" title="开立处方" width="700px">
      <el-form :model="presForm" label-width="90px">
        <el-form-item label="挂号信息">
          <el-input
            :model-value="`患者:${currentReg?.patient?.name || getPatientName(currentReg?.patient_id)} / 挂号ID:${currentReg?.id}`"
            disabled
          />
        </el-form-item>
        <el-form-item label="处方类型" required>
          <el-select v-model="presForm.pres_type" style="width:100%">
            <el-option label="西药" value="西药" />
            <el-option label="中药" value="中药" />
          </el-select>
        </el-form-item>
        <el-form-item label="诊断">
          <el-input v-model="presForm.diagnosis" type="textarea" :rows="2" placeholder="请输入诊断结果" />
        </el-form-item>
      </el-form>

      <div style="margin:16px 0 8px;font-weight:600">药品明细</div>
      <el-table :data="presForm.items" border size="small" style="width:100%">
        <el-table-column label="药品" min-width="180">
          <template #default="{ row, $index }">
            <el-select-v2
              v-model="row.drug_id"
              :options="drugOptions"
              placeholder="选择药品"
              style="width:100%"
              @change="onDrugChange($index)"
            />
          </template>
        </el-table-column>
        <el-table-column label="数量" width="120">
          <template #default="{ row, $index }">
            <el-input-number v-model="row.quantity" :min="1" style="width:100%" @change="calcAmount($index)" />
          </template>
        </el-table-column>
        <el-table-column label="单位" width="90">
          <template #default="{ row }">
            <el-input v-model="row.unit" placeholder="盒/克" />
          </template>
        </el-table-column>
        <el-table-column label="用法" min-width="140">
          <template #default="{ row }">
            <el-input v-model="row.usage_instruction" placeholder="口服 每日3次" />
          </template>
        </el-table-column>
        <el-table-column label="单价" width="100">
          <template #default="{ row }">
            <span>{{ row.unit_price || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="100">
          <template #default="{ row }">
            <span style="font-weight:600">{{ row.amount || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="70">
          <template #default="{ $index }">
            <el-button size="small" type="danger" text @click="removeDrugItem($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top:8px">
        <el-button type="primary" text @click="addDrugItem">+ 添加药品</el-button>
        <span style="float:right;font-weight:600;font-size:16px">合计：¥{{ presTotal }}</span>
      </div>

      <template #footer>
        <el-button @click="presDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="presForm.items.length === 0" @click="submitPrescription">确认开立</el-button>
      </template>
    </el-dialog>

    <!-- 挂号详情弹窗 -->
    <el-dialog v-model="detailVisible" title="挂号详情" width="600px">
      <el-descriptions :column="2" border v-if="currentReg">
        <el-descriptions-item label="挂号ID">{{ currentReg.id }}</el-descriptions-item>
        <el-descriptions-item label="挂号单号">{{ currentReg.reg_no }}</el-descriptions-item>
        <el-descriptions-item label="患者姓名">{{ currentReg.patient?.name || getPatientName(currentReg.patient_id) }}</el-descriptions-item>
        <el-descriptions-item label="医生ID">{{ currentReg.doctor_id }}</el-descriptions-item>
        <el-descriptions-item label="挂号类型">{{ currentReg.reg_type }}</el-descriptions-item>
        <el-descriptions-item label="挂号费">{{ currentReg.reg_fee }}</el-descriptions-item>
        <el-descriptions-item label="就诊日期">{{ currentReg.visit_date }}</el-descriptions-item>
        <el-descriptions-item label="缴费状态">
          <el-tag :type="currentReg.payment_status === '已付' ? 'success' : 'warning'">
            {{ currentReg.payment_status === '已付' ? '已缴费' : '待缴费' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <div v-if="currentReg?.prescriptions?.length" style="margin-top:20px">
        <div style="font-weight:600;margin-bottom:12px">关联处方</div>
        <el-table :data="currentReg.prescriptions" border size="small">
          <el-table-column prop="pres_no" label="处方单号" width="140" />
          <el-table-column prop="pres_type" label="类型" width="80" />
          <el-table-column prop="total_amount" label="金额" width="80" />
          <el-table-column prop="payment_status" label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.payment_status === '已付' ? 'success' : 'warning'" size="small">
                {{ row.payment_status === '已付' ? '已缴费' : '待缴费' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-empty v-else-if="detailVisible" description="暂无关联处方" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const list    = ref([])
const loading = ref(false)
const patientMap = ref(new Map())
const drugList = ref([])

const dialogVisible    = ref(false)
const patientSearchText = ref('')
const form = ref({ patient_id: null, doctor_id: 1, reg_type: '普通', visit_date: '', remark: '' })

// AI 智能分诊
const symptoms = ref('')
const triageLoading = ref(false)
const triageResult = ref(null)

const presDialogVisible = ref(false)
const currentReg = ref(null)
const presForm = ref({
  registration_id: null,
  pres_type: '西药',
  diagnosis: '',
  items: []
})

const detailVisible = ref(false)

/* ── 药品选项（用于el-select-v2） -- */
const drugOptions = computed(() => {
  return drugList.value.map(d => ({
    value: d.id,
    label: `${d.name} (${d.specification || '-'}) ¥${d.retail_price}`
  }))
})

const presTotal = computed(() => {
  return presForm.value.items.reduce((sum, item) => sum + (Number(item.amount) || 0), 0)
})

/* ── 列表 ── */
const loadList = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/registrations')
    list.value = res.data
    // 同时加载患者映射
    await loadPatientMap(res.data)
  } catch (err) {
    ElMessage.error('获取挂号列表失败：' + (err.response?.data?.detail || err.message))
  } finally { loading.value = false }
}

const loadPatientMap = async (registrations) => {
  const patientIds = [...new Set(registrations.map(r => r.patient_id).filter(Boolean))]
  if (patientIds.length === 0) return
  try {
    const res = await request.get('/api/patients')
    const patients = Array.isArray(res.data) ? res.data : []
    const map = new Map()
    patients.forEach(p => map.set(p.id, p))
    patientMap.value = map
  } catch (e) {
    console.error('加载患者映射失败', e)
  }
}

const getPatientName = (patientId) => {
  if (!patientId) return '-'
  const p = patientMap.value.get(patientId)
  return p ? p.name : `患者#${patientId}`
}

const loadDrugs = async () => {
  try {
    const res = await request.get('/api/drugs')
    drugList.value = res.data || []
  } catch (e) {
    console.error('加载药品列表失败', e)
  }
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

// ── AI 智能分诊 ──
const aiTriage = async () => {
  if (!symptoms.value.trim()) return
  triageLoading.value = true
  triageResult.value = null
  try {
    const res = await request.post('/api/ai/triage', { symptoms: symptoms.value.trim() })
    triageResult.value = res.data
  } catch (err) {
    ElMessage.error('分诊失败：' + (err.response?.data?.detail || err.message))
  } finally {
    triageLoading.value = false
  }
}

const applyTriage = () => {
  if (!triageResult.value) return
  if (triageResult.value.reg_type) {
    form.value.reg_type = triageResult.value.reg_type
  }
  // 尝试从推荐的医生名匹配 doctor_id
  if (triageResult.value.doctor && triageResult.value.doctor !== 'null') {
    const doctorName = triageResult.value.doctor.replace(/\(.*\)/, '').trim()
    // 种子数据医生：张伟(1) 李芳(2) 王磊(3) 赵敏(4)
    const doctorMap = { '张伟': 1, '李芳': 2, '王磊': 3, '赵敏': 4 }
    if (doctorMap[doctorName]) {
      form.value.doctor_id = doctorMap[doctorName]
    }
  }
  ElMessage.success('已应用 AI 推荐')
}

const triageTagType = (type) => ({ '普通':'', '专家':'warning', '急诊':'danger', '专科':'success' }[type] || '')

/* ── 新增 ── */
const openAdd = () => {
  patientSearchText.value = ''
  symptoms.value = ''
  triageResult.value = null
  form.value = { patient_id: null, doctor_id: 1, reg_type: '普通', visit_date: new Date().toISOString().split('T')[0], remark: '' }
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

/* ── 开处方 ── */
const openPrescription = (row) => {
  currentReg.value = row
  presForm.value = {
    registration_id: row.id,
    pres_type: '西药',
    diagnosis: '',
    items: []
  }
  presDialogVisible.value = true
}

const addDrugItem = () => {
  presForm.value.items.push({
    drug_id: null,
    quantity: 1,
    unit: '盒',
    usage_instruction: '',
    unit_price: 0,
    amount: 0
  })
}

const removeDrugItem = (index) => {
  presForm.value.items.splice(index, 1)
}

const onDrugChange = (index) => {
  const item = presForm.value.items[index]
  const drug = drugList.value.find(d => d.id === item.drug_id)
  if (drug) {
    item.unit_price = Number(drug.retail_price) || 0
    item.unit = drug.unit || '盒'
    calcAmount(index)
  }
}

const calcAmount = (index) => {
  const item = presForm.value.items[index]
  item.amount = (item.unit_price || 0) * (item.quantity || 0)
}

const submitPrescription = async () => {
  if (!presForm.value.diagnosis) {
    ElMessage.warning('请填写诊断！')
    return
  }
  const invalidItems = presForm.value.items.filter(i => !i.drug_id || !i.quantity)
  if (invalidItems.length > 0) {
    ElMessage.warning('请完善药品信息！')
    return
  }
  try {
    const payload = {
      registration_id: presForm.value.registration_id,
      pres_type: presForm.value.pres_type,
      diagnosis: presForm.value.diagnosis,
      items: presForm.value.items.map(i => ({
        drug_id: i.drug_id,
        quantity: i.quantity,
        unit: i.unit,
        usage_instruction: i.usage_instruction
      }))
    }
    await request.post('/api/prescriptions', payload)
    ElMessage.success('处方开立成功！')
    presDialogVisible.value = false
    loadList()
  } catch (err) {
    ElMessage.error('开立处方失败：' + (err.response?.data?.detail || err.message))
  }
}

/* ── 详情 ── */
const viewDetail = async (row) => {
  currentReg.value = row
  detailVisible.value = true
  // 尝试加载该挂号关联的处方
  try {
    const res = await request.get('/api/prescriptions', { params: { registration_id: row.id } })
    currentReg.value = { ...row, prescriptions: res.data.items || [] }
  } catch (e) {
    console.error('加载关联处方失败', e)
  }
}

const typeColor = (t) => ({ '普通':'', '专家':'warning', '急诊':'danger', '专科':'success' }[t] || '')

onMounted(() => {
  loadList()
  loadDrugs()
})
</script>

<style scoped>
.card-header { display:flex; justify-content:space-between; align-items:center; }

/* AI 智能分诊 */
.triage-result {
  margin-top: 8px;
  border: 1px solid #b3d6f0;
  border-radius: 10px;
  background: #f0f8ff;
  overflow: hidden;
  width: 100%;
}
.triage-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #e6f4ff;
  border-bottom: 1px solid #b3d6f0;
}
.triage-badge {
  font-size: 11px;
  font-weight: 600;
  color: #1a7fc4;
  background: #d0e8f8;
  padding: 1px 8px;
  border-radius: 4px;
  margin-right: auto;
}
.triage-body {
  padding: 10px 12px;
  font-size: 13px;
  color: #1a2332;
  line-height: 1.8;
}
.triage-reason {
  margin-top: 4px;
  padding: 6px 8px;
  background: #fff;
  border-radius: 6px;
  font-size: 12px;
  color: #667085;
}

.fade-enter-active, .fade-leave-active { transition: opacity .2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
