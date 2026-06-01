<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <div class="stats-grid" v-loading="loading">
      <div class="stat-card blue">
        <div class="stat-icon">📋</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.today_registrations }}</div>
          <div class="stat-label">今日挂号数</div>
        </div>
      </div>
      <div class="stat-card green">
        <div class="stat-icon">💰</div>
        <div class="stat-info">
          <div class="stat-value">¥{{ stats.today_revenue }}</div>
          <div class="stat-label">今日收入</div>
        </div>
      </div>
      <div class="stat-card orange">
        <div class="stat-icon">🛏️</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.inpatients }}</div>
          <div class="stat-label">当前住院人数</div>
        </div>
      </div>
      <div class="stat-card teal">
        <div class="stat-icon">🛏</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.available_beds }}</div>
          <div class="stat-label">可用床位</div>
        </div>
      </div>
      <div class="stat-card red">
        <div class="stat-icon">⚠️</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.low_stock_drugs }}</div>
          <div class="stat-label">药品库存预警</div>
        </div>
      </div>
      <div class="stat-card purple">
        <div class="stat-icon">📝</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.pending_orders }}</div>
          <div class="stat-label">待执行医嘱</div>
        </div>
      </div>
    </div>

    <div class="info-bar" v-if="!loading && stats.low_stock_drugs > 0">
      <el-alert :title="`⚠️ 当前有 ${stats.low_stock_drugs} 种药品库存低于预警线，请及时补货！`"
        type="warning" :closable="false" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const loading = ref(false)
const stats = ref({
  today_registrations: 0,
  today_revenue: '0.00',
  inpatients: 0,
  available_beds: 0,
  low_stock_drugs: 0,
  pending_orders: 0,
})

const loadDashboard = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/director/dashboard')
    stats.value = res.data
  } catch (err) {
    // 非管理员无权限时显示友好提示
    if (err.response?.status === 403) {
      ElMessage.info('当前账号无权查看统计数据')
    } else {
      ElMessage.error('获取统计数据失败：' + (err.response?.data?.detail || err.message))
    }
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>

<style scoped>
.dashboard { padding: 4px; }
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
  border-left: 4px solid transparent;
}
.stat-card.blue   { border-color: #1677ff; }
.stat-card.green  { border-color: #22c55e; }
.stat-card.orange { border-color: #f97316; }
.stat-card.teal   { border-color: #14b8a6; }
.stat-card.red    { border-color: #ef4444; }
.stat-card.purple { border-color: #a855f7; }
.stat-icon  { font-size: 32px; }
.stat-value { font-size: 28px; font-weight: 700; color: #1a2332; }
.stat-label { font-size: 13px; color: #667085; margin-top: 4px; }
.info-bar   { margin-top: 8px; }
</style>