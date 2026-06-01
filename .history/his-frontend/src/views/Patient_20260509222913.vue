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
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request'

const list    = ref([])
const loading = ref(false)
const searchQ = ref('')

const dialogVisible = ref(false)
const dialogTitle   = ref('')
const form = ref({ id:'', name:'', gender:'', birth_date:'', phone:'', ic_card_no:'', address:'' })

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
      // 编辑（后端如有更新接口）
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

onMounted(loadPatients)
</script>

<style scoped>
.card-header { display:flex; justify-content:space-between; align-items:center; }
</style>