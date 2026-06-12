<template>
  <div class="patient-dashboard">
    <h2 class="page-title">欢迎回来，{{ profile.name || '患者' }}</h2>

    <!-- 个人信息卡片 -->
    <el-card class="profile-card" v-loading="loading">
      <template #header>📋 我的信息</template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="患者编号">{{ profile.patient_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ profile.name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="性别">
          <el-tag :type="profile.gender === '男' ? 'primary' : 'danger'" size="small">
            {{ profile.gender || '-' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="出生日期">{{ profile.birth_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ profile.phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="身份证">{{ profile.id_card || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 快捷统计 -->
    <div class="stats-grid">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-value blue">{{ regTotal }}</div>
        <div class="stat-label">挂号记录</div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-value green">{{ presTotal }}</div>
        <div class="stat-label">处方记录</div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-value orange">{{ billTotal }}</div>
        <div class="stat-label">账单记录</div>
      </el-card>
    </div>

    <!-- 最近就诊时间线 -->
    <el-card class="timeline-card">
      <template #header>📅 近期就诊记录</template>
      <el-timeline v-if="timeline.length > 0">
        <el-timeline-item
          v-for="(event, idx) in timeline.slice(0, 8)"
          :key="idx"
          :timestamp="event.time"
          placement="top"
          :color="event.type === '挂号' ? '#409eff' : event.type === '处方' ? '#67c23a' : '#e6a23c'"
        >
          <div class="timeline-title">{{ event.title }}</div>
          <div class="timeline-detail">{{ event.detail }}</div>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-else description="暂无就诊记录" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '../utils/request'

const loading = ref(false)
const profile = ref<any>({})
const regTotal = ref(0)
const presTotal = ref(0)
const billTotal = ref(0)
const timeline = ref<any[]>([])

onMounted(async () => {
  loading.value = true
  try {
    const [pRes, tRes] = await Promise.all([
      request.get('/api/patient-self/profile'),
      request.get('/api/patient-self/timeline'),
    ])
    profile.value = pRes.data
    timeline.value = tRes.data.items || []

    // 统计各类型数量
    regTotal.value = timeline.value.filter((e: any) => e.type === '挂号').length
    presTotal.value = timeline.value.filter((e: any) => e.type === '处方').length
    billTotal.value = timeline.value.filter((e: any) => e.type === '收费').length
  } catch (e) {
    console.error('加载患者信息失败', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.patient-dashboard {
  max-width: 900px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #1f2329;
}

.profile-card {
  margin-bottom: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 6px;
}
.stat-value.blue { color: #409eff; }
.stat-value.green { color: #67c23a; }
.stat-value.orange { color: #e6a23c; }

.stat-label {
  font-size: 14px;
  color: #606266;
}

.timeline-title {
  font-weight: 600;
  color: #1f2329;
}

.timeline-detail {
  font-size: 13px;
  color: #8fa3b8;
  margin-top: 4px;
}
</style>
