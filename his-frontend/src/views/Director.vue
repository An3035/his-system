<template>
  <div class="director-container">
    <h2 class="page-title">院长查询系统</h2>

    <!-- 今日数据概览 -->
    <div class="stats-cards">
      <el-card class="stat-card">
        <div class="stat-value">{{ stats.today_registrations }}</div>
        <div class="stat-label">今日挂号数</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-value">¥ {{ stats.today_revenue }}</div>
        <div class="stat-label">今日收入</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-value">{{ stats.inpatients }}</div>
        <div class="stat-label">在院人数</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-value">{{ stats.available_beds }}</div>
        <div class="stat-label">可用床位</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-value" style="color:#e6a23c">{{ stats.low_stock_drugs }}</div>
        <div class="stat-label">库存预警数</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-value" style="color:#a855f7">{{ stats.pending_orders }}</div>
        <div class="stat-label">待执行医嘱</div>
      </el-card>
    </div>

    <!-- 图表区域 -->
    <div class="charts-row">
      <el-card class="chart-card">
        <template #header>近7天收入趋势</template>
        <div ref="revenueChartRef" class="chart-container"></div>
      </el-card>

      <el-card class="chart-card">
        <template #header>科室挂号量统计</template>
        <div ref="departmentChartRef" class="chart-container"></div>
      </el-card>
    </div>

    <!-- 药品销量排行榜 -->
    <el-card class="ranking-card">
      <template #header>药品销量排行榜</template>
      <el-table
        :data="drugRanking"
        border
        stripe
        style="width: 100%"
      >
        <el-table-column prop="rank" label="排名" width="80" align="center" />
        <el-table-column prop="drug_name" label="药品名称" />
        <el-table-column prop="total_qty" label="销量" width="100" align="center" />
        <el-table-column prop="total_amount" label="销售额" width="120" align="center" />
      </el-table>
    </el-card>

    <!-- AI 自然语言问数 -->
    <el-card class="nlq-card" style="margin-top:16px">
      <template #header>
        <span>🧠 AI 智能问数 — 用中文查数据</span>
      </template>
      <div class="nlq-body">
        <div class="nlq-input-row">
          <el-input
            v-model="nlqQuestion"
            type="text"
            placeholder="例如：上周哪个科室收入最高？库存预警的有哪些？今天收入比昨天怎么样？"
            :disabled="nlqLoading"
            @keydown.enter.prevent="askQuestion"
          />
          <el-button type="primary" :loading="nlqLoading" :disabled="!nlqQuestion.trim()" @click="askQuestion">
            提问
          </el-button>
        </div>
        <transition name="fade">
          <div v-if="nlqAnswer" class="nlq-answer">
            <div class="nlq-answer-content">{{ nlqAnswer }}</div>
            <div class="nlq-examples">
              试试问：
              <el-button text size="small" @click="quickNLQ('今天医院整体运营情况怎么样？')">今天运营概况</el-button>
              <el-button text size="small" @click="quickNLQ('哪个科室挂号量最多？')">哪个科室最忙</el-button>
              <el-button text size="small" @click="quickNLQ('近7天收入趋势如何？')">收入趋势</el-button>
              <el-button text size="small" @click="quickNLQ('有哪些药品库存不足？')">库存预警</el-button>
            </div>
          </div>
        </transition>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import request from '../utils/request'
import { showError } from '../utils/message'

const stats = ref({
  today_registrations: 0,
  today_revenue: 0,
  inpatients: 0,
  available_beds: 0,
  low_stock_drugs: 0,
  pending_orders: 0
})

const drugRanking = ref<{ rank: number; drug_name: string; total_qty: number; total_amount: number }[]>([])

const revenueChartRef = ref<HTMLElement | null>(null)
const departmentChartRef = ref<HTMLElement | null>(null)
let revenueChart: echarts.ECharts | null = null
let departmentChart: echarts.ECharts | null = null

const fetchStats = async () => {
  try {
    const res = await request.get('/api/director/dashboard')
    stats.value = res.data
  } catch (err: any) {
    showError('获取统计数据失败：' + (err.response?.data?.detail || err.message))
  }
}

/** 获取近7天收入数据，更新折线图 */
const fetchRevenueData = async () => {
  const end = new Date()
  const start = new Date(end)
  start.setDate(start.getDate() - 6)
  const fmt = (d: Date) => d.toISOString().split('T')[0]
  try {
    const res = await request.get('/api/director/revenue-report', {
      params: { start_date: fmt(start), end_date: fmt(end) }
    })
    const data: { date: string; registrations: number; revenue: number }[] = res.data || []
    // 补全7天，无数据的天填0
    const dateMap = new Map(data.map(d => [d.date, d]))
    const days: string[] = []
    const revenues: number[] = []
    for (let i = 0; i < 7; i++) {
      const d = new Date(start)
      d.setDate(d.getDate() + i)
      const key = fmt(d)
      days.push(key.slice(5)) // MM-DD
      revenues.push(dateMap.has(key) ? Number(dateMap.get(key)!.revenue) : 0)
    }
    if (revenueChart) {
      revenueChart.setOption({
        xAxis: { data: days },
        series: [{ data: revenues }]
      })
    }
  } catch { /* 使用默认空数据 */ }
}

/** 获取科室统计，更新柱状图 */
const fetchDeptStats = async () => {
  try {
    const res = await request.get('/api/director/department-stats')
    const data: { dept_name: string; reg_count: number; total_fee: number }[] = res.data || []
    const names = data.map(d => d.dept_name)
    const counts = data.map(d => d.reg_count)
    if (departmentChart) {
      departmentChart.setOption({
        xAxis: { data: names },
        series: [{ data: counts }]
      })
    }
  } catch { /* 使用默认空数据 */ }
}

/** 获取药品销量排行 */
const fetchDrugRanking = async () => {
  const end = new Date()
  const start = new Date(end)
  start.setDate(start.getDate() - 30)
  const fmt = (d: Date) => d.toISOString().split('T')[0]
  try {
    const res = await request.get('/api/pharmacy/sales-stats', {
      params: { start_date: fmt(start), end_date: fmt(end) }
    })
    const data: { drug_name: string; total_qty: number; total_amount: number }[] = res.data || []
    drugRanking.value = data.map((d, i) => ({
      rank: i + 1,
      drug_name: d.drug_name,
      total_qty: Number(d.total_qty) || 0,
      total_amount: Number(d.total_amount) || 0
    }))
  } catch { /* 使用空列表 */ }
}

const initCharts = () => {
  const defaultDays = (() => {
    const arr: string[] = []
    for (let i = 6; i >= 0; i--) {
      const d = new Date()
      d.setDate(d.getDate() - i)
      arr.push(d.toISOString().split('T')[0].slice(5))
    }
    return arr
  })()

  // 收入趋势图
  if (revenueChartRef.value) {
    revenueChart = echarts.init(revenueChartRef.value)
    revenueChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: defaultDays },
      yAxis: { type: 'value' },
      series: [{
        data: [], type: 'line', smooth: true,
        itemStyle: { color: '#409eff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
          ])
        }
      }]
    })
  }

  // 科室挂号量统计图
  if (departmentChartRef.value) {
    departmentChart = echarts.init(departmentChartRef.value)
    departmentChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: [] },
      yAxis: { type: 'value' },
      series: [{
        data: [], type: 'bar',
        itemStyle: { color: '#67c23a' }
      }]
    })
  }

  // 加载真实数据
  fetchRevenueData()
  fetchDeptStats()
  fetchDrugRanking()
}

// ── AI 自然语言问数 ──
const nlqQuestion = ref('')
const nlqLoading = ref(false)
const nlqAnswer = ref('')

const askQuestion = async () => {
  if (!nlqQuestion.value.trim()) return
  nlqLoading.value = true
  nlqAnswer.value = ''
  try {
    const res = await request.post('/api/ai/director-query', { question: nlqQuestion.value.trim() })
    nlqAnswer.value = res.data.answer || '暂无回答'
  } catch (err: any) {
    nlqAnswer.value = '查询失败：' + (err.response?.data?.detail || err.message)
  } finally {
    nlqLoading.value = false
  }
}

const quickNLQ = (q: string) => {
  nlqQuestion.value = q
  askQuestion()
}

const handleResize = () => {
  if (revenueChart) revenueChart.resize()
  if (departmentChart) departmentChart.resize()
}

onMounted(() => {
  fetchStats()
  initCharts()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (revenueChart) revenueChart.dispose()
  if (departmentChart) departmentChart.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.director-container {
  padding: 16px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #303133;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.chart-card {
  height: 350px;
}

.chart-container {
  width: 100%;
  height: 280px;
}

.ranking-card {
  margin-bottom: 20px;
}

/* AI 自然语言问数 */
.nlq-body { padding: 4px 0; }
.nlq-input-row { display: flex; gap: 10px; }
.nlq-answer {
  margin-top: 14px;
  padding: 16px;
  background: #f0f8ff;
  border: 1px solid #b3d6f0;
  border-radius: 10px;
}
.nlq-answer-content {
  white-space: pre-wrap;
  line-height: 1.8;
  font-size: 14px;
  color: #1a2332;
}
.nlq-examples {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid #d0e8f8;
  font-size: 12px;
  color: #8fa3b8;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.fade-enter-active, .fade-leave-active { transition: opacity .25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>