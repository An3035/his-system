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
  available_beds: 0
})

const drugRanking = ref([
  { rank: 1, drug_name: '阿莫西林胶囊', total_qty: 120, total_amount: 1200 },
  { rank: 2, drug_name: '布洛芬缓释片', total_qty: 98, total_amount: 980 },
  { rank: 3, drug_name: '感冒灵颗粒', total_qty: 85, total_amount: 850 },
  { rank: 4, drug_name: '头孢克肟分散片', total_qty: 72, total_amount: 1440 },
  { rank: 5, drug_name: '奥美拉唑肠溶胶囊', total_qty: 65, total_amount: 1300 }
])

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

const initCharts = () => {
  // 收入趋势图
  if (revenueChartRef.value) {
    revenueChart = echarts.init(revenueChartRef.value)
    revenueChart.setOption({
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
      },
      yAxis: {
        type: 'value'
      },
      series: [{
        data: [1200, 1900, 1500, 2200, 1800, 2500, 2100],
        type: 'line',
        smooth: true,
        itemStyle: {
          color: '#409eff'
        },
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
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      xAxis: {
        type: 'category',
        data: ['内科', '外科', '儿科', '妇科', '骨科', '眼科']
      },
      yAxis: {
        type: 'value'
      },
      series: [{
        data: [45, 38, 32, 28, 22, 18],
        type: 'bar',
        itemStyle: {
          color: '#67c23a'
        }
      }]
    })
  }
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
  grid-template-columns: repeat(4, 1fr);
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
</style>