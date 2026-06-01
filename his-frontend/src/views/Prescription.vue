<template>
  <div class="page-wrap">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>处方管理</span>
          <div style="display:flex;gap:8px">
            <el-button type="primary" @click="openAddPrescription">新开处方</el-button>
            <el-button @click="loadPending">刷新</el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="待发药" name="pending">
          <el-table :data="pendingList" border v-loading="loading" style="width:100%">
            <el-table-column prop="id" label="处方ID" width="80" />
            <el-table-column prop="pres_no" label="处方单号" width="160" />
            <el-table-column label="患者信息" min-width="160">
              <template #default="{ row }">
                <div v-if="row.patient">
                  <div style="font-weight:500">{{ row.patient.name }}</div>
                  <div style="font-size:12px;color:#667085">{{ row.patient.phone }}</div>
                </div>
                <div v-else-if="row.registration?.patient">
                  <div style="font-weight:500">{{ row.registration.patient.name }}</div>
                  <div style="font-size:12px;color:#667085">{{ row.registration.patient.phone }}</div>
                </div>
                <div v-else>患者ID: {{ row.registration?.patient_id || '-' }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="pres_type" label="处方类型" width="100" />
            <el-table-column prop="diagnosis" label="诊断" min-width="160" />
            <el-table-column prop="total_amount" label="金额" width="100" />
            <el-table-column label="缴费" width="90">
              <template #default="{ row }">
                <el-tag type="success">{{ row.payment_status === '已付' ? '已缴费' : row.payment_status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="药品明细" min-width="200">
              <template #default="{ row }">
                <div v-for="item in row.items" :key="item.id" style="font-size:12px">
                  {{ item.drug?.name || ('药品#' + item.drug_id) }} × {{ item.quantity }}{{ item.unit }} = ¥{{ item.amount }}
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="110" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="dispense(row.id)">发药</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!loading && pendingList.length === 0" description="暂无待发药处方" />
        </el-tab-pane>

        <el-tab-pane label="全部处方" name="all">
          <el-table :data="allList" border v-loading="allLoading" style="width:100%">
            <el-table-column prop="id" label="处方ID" width="80" />
            <el-table-column prop="pres_no" label="处方单号" width="160" />
            <el-table-column label="患者信息" min-width="160">
              <template #default="{ row }">
                <div v-if="row.patient">
                  <div style="font-weight:500">{{ row.patient.name }}</div>
                </div>
                <div v-else-if="row.registration?.patient">
                  <div style="font-weight:500">{{ row.registration.patient.name }}</div>
                </div>
                <div v-else>患者ID: {{ row.registration?.patient_id || '-' }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="pres_type" label="类型" width="90" />
            <el-table-column prop="diagnosis" label="诊断" min-width="140" />
            <el-table-column prop="total_amount" label="金额" width="90" />
            <el-table-column label="缴费状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.payment_status === '已付' ? 'success' : 'warning'" size="small">
                  {{ row.payment_status === '已付' ? '已缴费' : '待缴费' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="发药状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.dispensed ? 'success' : 'info'" size="small">
                  {{ row.dispensed ? '已发药' : '待发药' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="开立时间" width="160">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
          </el-table>
          <div style="margin-top:16px;display:flex;justify-content:flex-end">
            <el-pagination
              v-model:current-page="allPage"
              v-model:page-size="allPageSize"
              :page-sizes="[10, 20, 50]"
              :total="allTotal"
              layout="total, sizes, prev, pager, next"
              @size-change="loadAll"
              @current-change="loadAll"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 新开处方弹窗 -->
    <el-dialog v-model="addVisible" title="新开处方" width="720px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="选择挂号" required>
          <el-select-v2
            v-model="form.registration_id"
            :options="registrationOptions"
            placeholder="选择已缴费的挂号记录"
            style="width:100%"
          />
          <div style="font-size:12px;color:#999;margin-top:4px">
            仅显示已缴费且未开立处方的挂号记录
          </div>
        </el-form-item>
        <el-form-item label="处方类型" required>
          <el-select v-model="form.pres_type" style="width:100%">
            <el-option label="西药" value="西药" />
            <el-option label="中药" value="中药" />
          </el-select>
        </el-form-item>
        <el-form-item label="诊断">
          <el-input v-model="form.diagnosis" type="textarea" :rows="2" placeholder="请输入诊断结果" />
        </el-form-item>
      </el-form>

      <div style="margin:16px 0 8px;font-weight:600">药品明细</div>
      <el-table :data="form.items" border size="small" style="width:100%">
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
        <el-table-column label="数量" width="110">
          <template #default="{ row, $index }">
            <el-input-number v-model="row.quantity" :min="1" style="width:100%" @change="calcAmount($index)" />
          </template>
        </el-table-column>
        <el-table-column label="单位" width="80">
          <template #default="{ row }">
            <el-input v-model="row.unit" placeholder="盒" />
          </template>
        </el-table-column>
        <el-table-column label="用法" min-width="130">
          <template #default="{ row }">
            <el-input v-model="row.usage_instruction" placeholder="口服 每日3次" />
          </template>
        </el-table-column>
        <el-table-column label="单价" width="90">
          <template #default="{ row }">
            <span>{{ row.unit_price || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="90">
          <template #default="{ row }">
            <span style="font-weight:600">{{ row.amount || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="70">
          <template #default="{ $index }">
            <el-button size="small" type="danger" text @click="removeItem($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top:8px">
        <el-button type="primary" text @click="addItem">+ 添加药品</el-button>
        <el-button
          type="warning"
          text
          size="small"
          :disabled="form.items.length < 2"
          :loading="drugCheckLoading"
          @click="checkDrugInteraction"
        >
          配伍检查
        </el-button>
        <span style="float:right;font-weight:600;font-size:16px">合计：¥{{ totalAmount }}</span>
      </div>
      <div v-if="drugCheckResult" style="margin-top:8px;padding:12px;background:#fef8e7;border-radius:8px;white-space:pre-wrap;font-size:13px;line-height:1.7">
        <strong>配伍分析结果：</strong>
        <div style="margin-top:4px">{{ drugCheckResult }}</div>
      </div>

      <template #footer>
        <el-button @click="addVisible = false">取消</el-button>
        <el-button type="primary" :disabled="form.items.length === 0" @click="submit">确认开立</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request'
import { formatDate } from '../utils/date'

const activeTab = ref('pending')
const loading = ref(false)
const pendingList = ref([])

const allLoading = ref(false)
const allList = ref([])
const allPage = ref(1)
const allPageSize = ref(10)
const allTotal = ref(0)

const addVisible = ref(false)
const form = ref({
  registration_id: null,
  pres_type: '西药',
  diagnosis: '',
  items: []
})

const drugList = ref([])
const registrationList = ref([])

const drugOptions = computed(() => {
  return drugList.value.map(d => ({
    value: d.id,
    label: `${d.name} (${d.specification || '-'}) ¥${d.retail_price}`
  }))
})

const registrationOptions = computed(() => {
  // 仅显示已缴费的挂号
  return registrationList.value
    .filter(r => r.payment_status === '已付')
    .map(r => ({
      value: r.id,
      label: `${r.reg_no} - ${r.patient?.name || ('患者#' + r.patient_id)} / ${r.visit_date}`
    }))
})

const totalAmount = computed(() => {
  return form.value.items.reduce((sum, item) => sum + (Number(item.amount) || 0), 0)
})

const loadPending = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/prescriptions/pending-dispense')
    pendingList.value = res.data || []
  } catch (err) {
    ElMessage.error('获取待发药列表失败：' + (err.response?.data?.detail || err.message))
  } finally { loading.value = false }
}

const loadAll = async () => {
  allLoading.value = true
  try {
    const res = await request.get('/api/prescriptions', {
      params: { page: allPage.value, page_size: allPageSize.value }
    })
    allList.value = res.data.items || []
    allTotal.value = res.data.total || 0
  } catch (err) {
    ElMessage.error('获取处方列表失败：' + (err.response?.data?.detail || err.message))
  } finally { allLoading.value = false }
}

const loadDrugs = async () => {
  try {
    const res = await request.get('/api/drugs')
    drugList.value = res.data || []
  } catch (e) {
    console.error('加载药品失败', e)
  }
}

const loadRegistrations = async () => {
  try {
    const res = await request.get('/api/registrations')
    const regs = Array.isArray(res.data) ? res.data : []
    // 尝试加载患者信息映射到挂号记录
    const patientIds = [...new Set(regs.map(r => r.patient_id).filter(Boolean))]
    if (patientIds.length > 0) {
      try {
        const pRes = await request.get('/api/patients')
        const patients = Array.isArray(pRes.data) ? pRes.data : []
        const pmap = new Map(patients.map(p => [p.id, p]))
        registrationList.value = regs.map(r => ({ ...r, patient: pmap.get(r.patient_id) }))
      } catch {
        registrationList.value = regs
      }
    } else {
      registrationList.value = regs
    }
  } catch (e) {
    console.error('加载挂号记录失败', e)
  }
}

const handleTabChange = (tab) => {
  if (tab === 'pending') loadPending()
  if (tab === 'all') loadAll()
}

const dispense = async (id) => {
  try {
    await ElMessageBox.confirm('确认发药？发药后库存将自动扣减。', '提示', { type: 'warning' })
    await request.patch(`/api/prescriptions/${id}/dispense`)
    ElMessage.success('发药完成！')
    loadPending()
  } catch (err) {
    if (err !== 'cancel')
      ElMessage.error('发药失败：' + (err.response?.data?.detail || err.message))
  }
}

/* ── 新开处方 ── */
const openAddPrescription = () => {
  form.value = {
    registration_id: null,
    pres_type: '西药',
    diagnosis: '',
    items: []
  }
  loadRegistrations()
  addVisible.value = true
}

const addItem = () => {
  form.value.items.push({
    drug_id: null,
    quantity: 1,
    unit: '盒',
    usage_instruction: '',
    unit_price: 0,
    amount: 0
  })
}

const removeItem = (index) => {
  form.value.items.splice(index, 1)
}

const onDrugChange = (index) => {
  const item = form.value.items[index]
  const drug = drugList.value.find(d => d.id === item.drug_id)
  if (drug) {
    item.unit_price = Number(drug.retail_price) || 0
    item.unit = drug.unit || '盒'
    calcAmount(index)
  }
}

const drugCheckLoading = ref(false)
const drugCheckResult = ref('')

const checkDrugInteraction = async () => {
  const drugIds = form.value.items
    .filter(i => i.drug_id)
    .map(i => {
      const d = drugList.value.find(dd => dd.id === i.drug_id)
      return d ? d.name : String(i.drug_id)
    })
  if (drugIds.length < 2) return
  drugCheckLoading.value = true
  drugCheckResult.value = ''
  try {
    const res = await request.post('/api/ai/drug-interaction', drugIds)
    drugCheckResult.value = res.data.analysis || JSON.stringify(res.data)
  } catch (err) {
    ElMessage.error('配伍检查失败：' + (err.response?.data?.detail || err.message))
  } finally {
    drugCheckLoading.value = false
  }
}

const calcAmount = (index) => {
  const item = form.value.items[index]
  item.amount = (item.unit_price || 0) * (item.quantity || 0)
}

const submit = async () => {
  if (!form.value.registration_id) {
    ElMessage.warning('请选择挂号记录！')
    return
  }
  const invalidItems = form.value.items.filter(i => !i.drug_id || !i.quantity)
  if (invalidItems.length > 0) {
    ElMessage.warning('请完善药品信息！')
    return
  }

  // AI 处方审核
  const checkItems = form.value.items
    .filter(i => i.drug_id)
    .map(i => ({ drug_id: i.drug_id, quantity: i.quantity, unit: i.unit }))

  try {
    const checkRes = await request.post('/api/ai/check-prescription', { patient_id: null, items: checkItems })
    const check = checkRes.data
    if (check.warnings?.length > 0 && check.safe === false) {
      // 有风险，弹窗让医生确认
      try {
        const warningText = check.warnings
          .map(w => `【${w.severity === 'high' ? '⚠️ 高危' : w.severity === 'medium' ? '⚡ 中危' : '💡 提示'}】${w.message}`)
          .join('\n')
        await ElMessageBox.confirm(
          `<div style="margin-bottom:12px;font-weight:600;color:#e6a23c">AI 审核发现以下问题：</div>
           <div style="padding:12px;background:#fff7e6;border-radius:8px;white-space:pre-wrap;font-size:13px;line-height:1.7">${warningText}</div>
           <div style="margin-top:8px;color:#667085">${check.summary || ''}</div>
           <div style="margin-top:12px;color:#999;font-size:12px">确认仍将开立处方，请谨慎决定</div>`,
          '处方安全审核',
          {
            confirmButtonText: '仍要开立',
            cancelButtonText: '返回修改',
            type: 'warning',
            dangerouslyUseHTMLString: true,
          }
        )
      } catch {
        return // 医生取消
      }
    } else if (check.warnings?.length > 0) {
      // 低风险，提示但不阻止
      const tips = check.warnings.map(w => w.message).join('；')
      ElMessage.info('处方提示：' + tips)
    }
  } catch {
    // AI 审核服务不可用，继续提交
  }

  try {
    const payload = {
      registration_id: form.value.registration_id,
      pres_type: form.value.pres_type,
      diagnosis: form.value.diagnosis,
      items: form.value.items.map(i => ({
        drug_id: i.drug_id,
        quantity: i.quantity,
        unit: i.unit,
        usage_instruction: i.usage_instruction
      }))
    }
    await request.post('/api/prescriptions', payload)
    ElMessage.success('处方开立成功！')
    addVisible.value = false
    loadPending()
    if (activeTab.value === 'all') loadAll()
  } catch (err) {
    ElMessage.error('开立处方失败：' + (err.response?.data?.detail || err.message))
  }
}

onMounted(() => {
  loadPending()
  loadDrugs()
})
</script>

<style scoped>
.card-header { display:flex; justify-content:space-between; align-items:center; }
</style>
