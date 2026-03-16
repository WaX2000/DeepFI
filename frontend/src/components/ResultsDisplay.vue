

<template>
  <div class="results-container">

    <!-- 新增：衰弱指数分布直方图 -->
    <el-card class="chart-card">
      <template #header>
        <h3>📊 衰弱指数分布</h3>
        <p class="chart-subtitle">展示所有样本预测值的分布情况</p>
      </template>
      <!-- 图表容器，必须指定高度和宽度 -->
      <div ref="distributionChartRef" class="distribution-chart"></div>
      <!-- <div class="chart-note">
        <el-icon><InfoFilled /></el-icon>
        提示：将鼠标悬停在柱子上可查看该区间的具体数值范围与样本数量。
      </div> -->`
    </el-card>

    
    <!-- 环形图仪表盘 -->
    <el-card class="chart-card" style="margin-top: 20px;">
      <template #header>
        <div class="chart-header">
          <h3>🏥 疾病风险分析</h3>
          <!-- <p class="chart-subtitle">基于衰弱指数的各疾病风险分类分析</p> -->
        </div>
      </template>
      
      <!-- 统计摘要 -->
      <div v-if="overallStats" class="stats-summary">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon">👥</div>
              <div class="stat-content">
                <div class="stat-label">总样本数</div>
                <div class="stat-value">{{ overallStats.totalPatients }}</div>
              </div>
            </div>
          </el-col>

          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon">⚠️</div>
              <div class="stat-content">
                <div class="stat-label">平均高风险率</div>
                <div class="stat-value">{{ overallStats.avgHighRiskPercent }}%</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon">📈</div>
              <div class="stat-content">
                <div class="stat-label">最高风险疾病</div>
                <!-- <div class="stat-value">{{ overallStats.maxRiskDisease }}</div>
                <div class="stat-subvalue">{{ overallStats.maxRiskPercent }}%</div> -->
                <div class="stat-value">{{ overallStats.maxRiskDisease }} : {{ overallStats.maxRiskPercent }}%</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon">📉</div>
              <div class="stat-content">
                <div class="stat-label">最低风险疾病</div>
                <!-- <div class="stat-value">{{ overallStats.minRiskDisease }}</div>
                <div class="stat-subvalue">{{ overallStats.minRiskPercent }}%</div> -->
                <div class="stat-value">{{ overallStats.minRiskDisease }} : {{ overallStats.minRiskPercent }}%</div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
      
      <!-- 环形图容器 -->
      <!-- <div class="donut-chart-container">
        <div ref="donutChartRef" class="donut-chart"></div>
      </div> -->
      
      <!-- 图例和阈值信息 -->
      <div class="legend-section">
        <!-- <div class="legend">
          <div class="legend-item">
            <span class="legend-color low-risk"></span>
            <span>低风险 (≤ 阈值)</span>
          </div>
          <div class="legend-item">
            <span class="legend-color high-risk"></span>
            <span>高风险 (> 阈值)</span>
          </div>
        </div> -->
        
        <!-- <div class="threshold-info">
          <el-tag type="info" size="small">疾病阈值</el-tag>
          <div class="threshold-list">
            <span v-for="disease in diseaseRiskDistribution" 
                  :key="disease.id" 
                  class="threshold-item">
              {{ " "+disease.name }}:<strong>{{ disease.threshold.toFixed(3) }}</strong>
            </span>
          </div>
        </div> -->
      </div>
      
      <!-- 详细数据表格 -->
      <div class="detailed-table">
        <el-table :data="diseaseRiskDistribution" size="small" style="width:100%; height:100%;font-size: 19px" stripe  height="500px" max-height="500px">
          <el-table-column prop="name" label="疾病名称" width="300">
            <template #default="scope">
              <div class="disease-name">
                <span class="color-dot" :style="{ backgroundColor: scope.row.color }"></span>
                {{ scope.row.name }}
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="threshold" label="风险阈值" width="200">
            <template #default="scope">
              {{ scope.row.threshold.toFixed(3) }}
            </template>
          </el-table-column>
          <el-table-column label="低风险" width="250">
            <template #default="scope">
              <div class="risk-cell low">
                {{ scope.row.lowRisk }}人 ({{ scope.row.lowRiskPercent.toFixed(1) }}%)
              </div>
            </template>
          </el-table-column>
          <el-table-column label="高风险" width="250">
            <template #default="scope">
              <div class="risk-cell high">
                {{ scope.row.highRisk }}人 ({{ scope.row.highRiskPercent.toFixed(1) }}%)
              </div>
            </template>
          </el-table-column>
          <el-table-column label="平均衰弱指数" width="250">
            <template #default="scope">
              <div class="avg-index">
                <div>低风险: {{ scope.row.lowRiskAvg.toFixed(3) }}</div>
                <div>高风险: {{ scope.row.highRiskAvg.toFixed(3) }}</div>
              </div>
            </template>
          </el-table-column>
          <!-- <el-table-column prop="description" label="说明"></el-table-column> -->
        </el-table>
      </div>
    </el-card>
  </div>
</template>



<script setup>
import { ref, computed, onUnmounted,onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { 
  TrendCharts, InfoFilled, CircleCheck, Document, Download 
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// 接收来自父组件（App.vue）的预测结果
const props = defineProps({
  frailtyResults: Object,
  diseaseThresholds: {
    type: Object,
    default: () => ({
      cardiovascular: { 
        name: '心血管疾病', 
        threshold: 0.158, 
        color: '#FF6B6B',
        // description: '包括冠心病、高血压、心力衰竭等'
      },
      diabetes: { 
        name:'二型糖尿病',
        threshold: 0.207, 
        color: '#4ECDC4',
        // description: '2型糖尿病及其并发症风险'
      },
      // kidney: { 
      //   name: '二型糖尿病', 
      //   threshold: 0.199+0.1, 
      //   color: '#45B7D1',
      //   description: '慢性肾功能不全风险'
      // },
      // stroke: { 
      //   name: '心脑血管疾病', 
      //   threshold: 0.206+0.1, 
      //   color: '#96CEB4',
      //   description: '缺血性和出血性脑卒中'
      // },
      NN: { 
        name: '神经退行性病变', 
        threshold: 0.143, 
        color: '#FFEAA7',
        // description: '骨折和骨密度下降风险'
      },
      Auto: { 
        name: '自身免疫性疾病', 
        threshold: 0.222, 
        color: '#DDA0DD',
        // description: '多种癌症的总体风险'
      },
      // cancer: { 
      //   name: '抑郁症', 
      //   threshold: 0.201+0.1, 
      //   color: '#DDA0DD',
      //   description: '多种癌症的总体风险'
      // },
      
    })
  }
})

console.log('=== Props 调试信息 ===')
console.log('frailtyResults:', props.frailtyResults)
console.log('完整对象:', props.frailtyResults)
console.log('=== 分析 frailtyResults 数据结构 ===')
console.log('类型:', typeof props.frailtyResults)
console.log('是数组吗?', Array.isArray(props.frailtyResults))
console.log('数组长度:', props.frailtyResults?.length || 0)

if (Array.isArray(props.frailtyResults) && props.frailtyResults.length > 0) {
  console.log('第一个元素:', props.frailtyResults[0])
  console.log('第一个元素的键:', Object.keys(props.frailtyResults[0]))
  console.log('前3个元素:')
  props.frailtyResults.slice(0, 3).forEach((item, index) => {
    console.log(`元素 ${index}:`, item)
  })
}


const bcdfiData = computed(() => {
  if (!props.frailtyResults || !Array.isArray(props.frailtyResults)) {
    console.warn('frailtyResults 不是数组或为空')
    return []
  }

  const data = []
  props.frailtyResults.forEach((item, index) => {
    if (item && typeof item === 'object' && 'DeepFI' in item) {
      data.push(item.DeepFI)
    } else {
      console.warn(`第 ${index} 个元素缺少 DeepFI 属性`, item)
    }
  })
  
  console.log('提取的 DeepFI 数据:', data)
  return data
})

const isDataValid = computed(() => {
  return bcdfiData.length > 0
})

// 计算每种疾病的风险分布
const diseaseRiskDistribution = computed(() => {
  const data = bcdfiData.value
  if (data.length === 0) return []
  
  return Object.entries(props.diseaseThresholds).map(([key, disease]) => {
    const threshold = disease.threshold
    
    // 统计风险人数
    let lowRiskCount = 0
    let highRiskCount = 0
    let lowRiskValues = []
    let highRiskValues = []
    
    data.forEach(value => {
      if (value <= threshold) {
        lowRiskCount++
        lowRiskValues.push(value)
      } else {
        highRiskCount++
        highRiskValues.push(value)
      }
    })
    
    const total = lowRiskCount + highRiskCount
    const lowRiskPercent = total > 0 ? (lowRiskCount / total * 100) : 0
    const highRiskPercent = total > 0 ? (highRiskCount / total * 100) : 0
    
    // 计算平均指数
    const lowRiskAvg = lowRiskValues.length > 0 
      ? lowRiskValues.reduce((a, b) => a + b, 0) / lowRiskValues.length 
      : 0
    
    const highRiskAvg = highRiskValues.length > 0 
      ? highRiskValues.reduce((a, b) => a + b, 0) / highRiskValues.length 
      : 0
    
    return {
      id: key,
      name: disease.name,
      threshold: threshold,
      color: disease.color,
      description: disease.description,
      lowRisk: lowRiskCount,
      highRisk: highRiskCount,
      total: total,
      lowRiskPercent: lowRiskPercent,
      highRiskPercent: highRiskPercent,
      lowRiskAvg: lowRiskAvg,
      highRiskAvg: highRiskAvg
    }
  })
})

// 计算总体统计
const overallStats = computed(() => {
  const distribution = diseaseRiskDistribution.value
  if (distribution.length === 0) return null
  
  let totalHighRisk = 0
  let maxHighRiskDisease = { name: '', percent: 0 }
  let minHighRiskDisease = { name: '', percent: 100 }
  
  distribution.forEach(disease => {
    totalHighRisk += disease.highRisk
    
    if (disease.highRiskPercent > maxHighRiskDisease.percent) {
      maxHighRiskDisease = { name: disease.name, percent: disease.highRiskPercent }
    }
    
    if (disease.highRiskPercent < minHighRiskDisease.percent) {
      minHighRiskDisease = { name: disease.name, percent: disease.highRiskPercent }
    }
  })
  
  const avgHighRiskPercent = distribution.reduce((sum, d) => sum + d.highRiskPercent, 0) / distribution.length
  
  return {
    totalPatients: distribution[0]?.total || 0,
    totalHighRisk: totalHighRisk,
    avgHighRiskPercent: avgHighRiskPercent.toFixed(1),
    maxRiskDisease: maxHighRiskDisease.name,
    maxRiskPercent: maxHighRiskDisease.percent.toFixed(1),
    minRiskDisease: minHighRiskDisease.name,
    minRiskPercent: minHighRiskDisease.percent.toFixed(1)
  }
})


const emit = defineEmits(['generate-pdf'])

// 图表引用
// const chartRef = ref(null)
// let chartInstance = null

// 状态
// const selectedDisease = ref('心血管疾病')
// const isGeneratingPDF = ref(false)

const distributionChartRef = ref(null)
let distributionChart = null

const donutChartRef = ref(null)
let donutChart = null

const initDistributionChart = () => {
  console.log("initDistributionChart")
  if (!distributionChartRef.value) {
    console.error('图表容器不存在')
    return
  }
  distributionChart = echarts.init(distributionChartRef.value)
  if (bcdfiData.value.length > 0) {
    console.log("updateDistributionChart")
    updateDistributionChart()
    
  } else {
    showNoDataChart()
  }
  
}
const updateDistributionChart = () => {
  if (!distributionChart) {
    console.warn('图为空')
    return
  }
  
  const data = bcdfiData.value
  console.log('更新图表，数据长度:', data.length)
  
  if (data.length === 0) {
    showNoDataChart()
    return
  }


  
  try {
    const min = Math.min(...data)
    const max = Math.max(...data)
    const binCount = Math.min(15, Math.ceil(Math.sqrt(data.length)))
    const binWidth = (max - min) / binCount
    
    // 统计每个区间的数量
    const bins = []
    const labels = []
    const chartData = []
    
    for (let i = 0; i < binCount; i++) {
      const binStart = min + i * binWidth
      const binEnd = binStart + binWidth
      const count = data.filter(val => val >= binStart && val < binEnd).length
      
      bins.push(count)
      labels.push(`${binStart.toFixed(2)}-${binEnd.toFixed(2)}`)
      chartData.push({
        name: `${binStart.toFixed(2)}-${binEnd.toFixed(2)}`,
        value: count,
        range: [binStart, binEnd]
      })
    }

    const option = {
        title: {
          text: '衰弱指数分布直方图',
          left: 'center',
          top: 10,
          textStyle: {
            color: '#333',
            fontSize: 20,
            fontWeight: 'bold'
          }
        },
        tooltip: {
          trigger: 'item',
          formatter: function(params) {
            const range = params.data.range
            return `
              <div style="font-weight: bold; margin-bottom: 12px;">衰弱指数区间</div>
              <div>${range[0].toFixed(3)} - ${range[1].toFixed(3)}</div>
              <div style="margin-top: 10px;">样本数量：<span style="color: #409EFF; font-weight: bold;">${params.value}人</span></div>
            `
          }
        },

    grid: {
      left: '10%',
      right: '8%',
      bottom: '10%',
      top: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: labels,
      name: '衰弱指数区间',
      nameLocation: 'middle',
      nameGap: 70,
      nameTextStyle: { // 坐标轴名称的文本样式
        // color: '#333',
        fontSize: 18,
        fontWeight: 'bold',
        // 更多文本样式...
      },
      axisLabel: {
        // rotate: 45,
        // margin: 12, // 标签与轴线之间的距离
        // interval:0,
        // fontSize: 17
        rotate: 45,        // 如果仍想显示所有刻度，可旋转45度
      fontSize: 14,      // 适当减小字体
      fontWeight: 'normal', // 取消加粗
      },
      axisLine: {
        show: true, // 是否显示坐标轴轴线
        lineStyle: {
          color: '#333', // 轴线颜色
          width: 1, // 轴线宽度
          type: 'solid' // 轴线类型，可选：'solid' | 'dashed' | 'dotted'
        },
        onZero: true, // 是否在零刻度线上
        symbol: ['none', 'none'], // 轴线两边的箭头，可选：['none', 'none'] | ['arrow', 'arrow'] 等
        symbolSize: [10, 15] // 箭头大小
      },
      axisTick: {
        // show: true, // 是否显示坐标轴刻度
        // inside: false, // 刻度是否朝内，默认朝外
        // length: 5, // 刻度的长度
        // lineStyle: {
        //   color: '#333', // 刻度颜色
        //   width: 1 // 刻度宽度
        // },
        alignWithLabel: true // 刻度与标签对齐
      },
    },
    yAxis: {
      type: 'value',
      name: '样本数量',
      nameLocation: 'middle',
      nameGap: 60,
      min: 0,
      nameTextStyle: { // 坐标轴名称的文本样式
        color: '#333',
        fontSize: 17,
        fontWeight: 'bold',
        // 更多文本样式...
      },
      splitLine: {
        show: true, // 是否显示网格线。在x轴上，通常不显示，因为网格线是从y轴延伸的
        lineStyle: {
          // color: '#eee',
          width: 2,
          type: 'solid'
        }
      },
      // interval: 1,
      axisLabel: {
        formatter: function(value) {
          // 确保是整数
          const intValue = Math.round(value);
          
          // 如果有需要，可以添加千分位分隔符
          if (intValue >= 1000) {
            return intValue.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
          }
          return intValue;
        },
        margin: 12, // 标签与轴线之间的距离
        // interval:0,
        fontSize: 16,
        // color: '#333',
        fontWeight: 'bold',
        rotate: 45,        // 如果仍想显示所有刻度，可旋转45度
        fontSize: 14,      // 适当减小字体
        // fontWeight: 'normal', // 取消加粗
        
      }
      },
     series: [{
      name: '分布',
      type: 'bar',
      data: chartData,
      barWidth: '80%',
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#83bff6' },
          { offset: 0.5, color: '#188df0' },
          { offset: 1, color: '#188df0' }
        ]),
        borderRadius: [10, 10, 0, 0]
      },
      emphasis: {
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#2378f7' },
            { offset: 0.7, color: '#2378f7' },
            { offset: 1, color: '#83bff6' }
          ])
        },
      //   legend: {
      //   show: true,
      //   data: ['衰弱指数分布'],
      //   top: 'bottom'  // 图例放在底部
      // }
      },
      
    }]
  }
  
  distributionChart.setOption(option, true)



  } catch (error) {
    console.error('绘制直方图时出错:', error)
  }
}

const showNoDataChart = () => {
  if (!distributionChart) return
  
  distributionChart.setOption({
    title: {
      text: '暂无数据',
      subtext: '请先进行计算或上传数据',
      left: 'center',
      top: 'center',
      textStyle: {
        fontSize: 18,
        color: '#909399'
      },
      subtextStyle: {
        fontSize: 14,
        color: '#C0C4CC'
      }
    }
  })
}

watch(() => props.frailtyResults, (newVal) => {
  console.log('数据变化:', newVal)
  
  if (isDataValid.value) {
    console.log('数据有效，开始渲染图表')
    nextTick(() => {
      if (!distributionChart) {
        initDistributionChart()
      } else {
        updateDistributionChart()
      }
    })
  }
}, { deep: true, immediate: true })

onMounted(() => {
  console.log('ResultsDisplay 组件挂载完成')
  
  nextTick(() => {
    initDistributionChart()
    
  })
  
  // 窗口大小变化时重绘图表
  const handleResize = () => {
    if (distributionChart) {
      distributionChart.resize()
    }
  }
  window.addEventListener('resize', handleResize)
  
  onUnmounted(() => {
    if (distributionChart) {
      distributionChart.dispose()
      distributionChart = null
    }
    window.removeEventListener('resize', handleResize)
  })
})
onMounted(() => {
  console.log('ResultsDisplay !!!组件挂载完成')
  nextTick(() => {
    initDonutChart()
  })
  
  window.addEventListener('resize', () => {
    if (donutChart) donutChart.resize()
  })
})

// 初始化环形图
const initDonutChart = () => {
  if (!donutChartRef.value) {
    console.log("No donutChartRef!")
    return
  }
  console.log("donutChartRef!")
  donutChart = echarts.init(donutChartRef.value)
  updateDonutChart()
}

// 更新环形图
const updateDonutChart = () => {
  if (!donutChart || diseaseRiskDistribution.value.length === 0) {
    showNoDataDonutChart()
    return
  }
  
  const distribution = diseaseRiskDistribution.value
  
  // 准备环形图数据
  const seriesData = []
  const legendData = []
  
  // 为每种疾病添加低风险和高风险数据
  distribution.forEach(disease => {
    // 低风险数据
    seriesData.push({
      name: `${disease.name} - 低风险`,
      value: disease.lowRisk,
      itemStyle: {
        color: `${disease.color}80` // 添加透明度
      },
      disease: disease.name,
      riskType: 'low',
      percent: disease.lowRiskPercent,
      threshold: disease.threshold,
      avgIndex: disease.lowRiskAvg
    })
    
    // 高风险数据
    seriesData.push({
      name: `${disease.name} - 高风险`,
      value: disease.highRisk,
      itemStyle: {
        color: disease.color
      },
      disease: disease.name,
      riskType: 'high',
      percent: disease.highRiskPercent,
      threshold: disease.threshold,
      avgIndex: disease.highRiskAvg
    })
    
    // 添加到图例
    if (!legendData.includes(disease.name)) {
      legendData.push(disease.name)
    }
  })
  
  const option = {
    title: {
      text: '各疾病风险比例分布',
      subtext: `环形图大小代表样本数量`,
      left: 'center',
      top: 10,
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#333'
      },
      subtextStyle: {
        fontSize: 13,
        color: '#666'
      }
    },
    
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#ddd',
      borderWidth: 1,
      textStyle: {
        color: '#333',
        fontSize: 13
      },
      formatter: function(params) {
        const data = params.data
        const riskText = data.riskType === 'high' ? '高风险' : '低风险'
        const riskColor = data.riskType === 'high' ? '#F56C6C' : '#67C23A'
        
        return `
          <div style="font-weight: bold; color: ${data.itemStyle.color}; margin-bottom: 5px;">
            ${data.disease}
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
            <span>风险类型:</span>
            <span style="color: ${riskColor}; font-weight: bold;">${riskText}</span>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
            <span>样本数量:</span>
            <span style="font-weight: bold;">${data.value}人</span>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
            <span>所占比例:</span>
            <span style="font-weight: bold;">${data.percent.toFixed(1)}%</span>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
            <span>疾病阈值:</span>
            <span style="font-weight: bold;">${data.threshold.toFixed(3)}</span>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span>平均指数:</span>
            <span style="font-weight: bold;">${data.avgIndex.toFixed(3)}</span>
          </div>
        `
      }
    },
    
    legend: {
      type: 'scroll',
      orient: 'vertical',
      right: 20,
      top: 'center',
      bottom: 20,
      textStyle: {
        fontSize: 12,
        color: '#606266'
      },
      pageTextStyle: {
        color: '#606266'
      },
      pageIconColor: '#409EFF',
      pageIconInactiveColor: '#C0C4CC',
      pageButtonItemGap: 5,
      data: legendData,
      formatter: function(name) {
        const disease = distribution.find(d => d.name === name)
        if (!disease) return name
        
        const highRiskPercent = disease.highRiskPercent.toFixed(1)
        return `${name} (${highRiskPercent}%高风险)`
      }
    },
    
    series: [
      {
        name: '疾病风险分布',
        type: 'pie',
        radius: ['40%', '70%'], // 内半径40%，外半径70%，形成环形
        center: ['40%', '50%'], // 位置偏左，为图例留空间
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2,
          borderJoin: 'round'
        },
        
        label: {
          show: true,
          position: 'outside',
          formatter: function(params) {
            // 只显示高风险部分的外部标签
            if (params.data.riskType === 'high') {
              return `{b|${params.data.disease}}\n{c|${params.data.value}}人 (${params.data.percent.toFixed(1)}%)`
            }
            return ''
          },
          rich: {
            b: {
              fontSize: 12,
              color: '#333',
              fontWeight: 'bold',
              lineHeight: 18
            },
            c: {
              fontSize: 11,
              color: '#666',
              lineHeight: 16
            }
          },
          padding: [2, 5],
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          borderColor: '#ddd',
          borderWidth: 1,
          borderRadius: 4
        },
        
        labelLine: {
          show: true,
          length: 15,
          length2: 10,
          smooth: true,
          lineStyle: {
            width: 1,
            type: 'solid',
            color: '#ccc'
          }
        },
        
        emphasis: {
          scale: true,
          scaleSize: 5,
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.3)'
          }
        },
        
        data: seriesData,
        
        // 自定义每个扇区的样式
        itemStyle: function(params) {
          const data = seriesData[params.dataIndex]
          if (data.riskType === 'high') {
            return {
              color: data.itemStyle.color,
              borderColor: '#fff',
              borderWidth: 2
            }
          } else {
            // 低风险部分添加图案
            return {
              color: {
                type: 'pattern',
                image: createStripePattern(data.itemStyle.color),
                repeat: 'repeat'
              },
              borderColor: '#fff',
              borderWidth: 2
            }
          }
        }
      },
      
      // 内环：显示总样本数
      {
        type: 'pie',
        radius: ['30%', '35%'],
        center: ['40%', '50%'],
        label: {
          show: true,
          position: 'center',
          fontSize: 20,
          fontWeight: 'bold',
          color: '#409EFF',
          formatter: `{total|${distribution[0]?.total || 0}}\n{label|总样本数}`,
          rich: {
            total: {
              fontSize: 28,
              fontWeight: 'bold',
              color: '#409EFF',
              lineHeight: 30
            },
            label: {
              fontSize: 14,
              color: '#666',
              lineHeight: 20
            }
          }
        },
        data: [{ value: 1, name: '内环' }],
        itemStyle: {
          color: 'rgba(240, 242, 245, 0.8)'
        },
        silent: true
      }
    ]
  }
  
  donutChart.setOption(option, true)
}

// 创建条纹图案（用于低风险部分）
const createStripePattern = (color) => {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  canvas.width = 10
  canvas.height = 10
  
  ctx.fillStyle = color
  ctx.fillRect(0, 0, 10, 10)
  
  ctx.fillStyle = 'rgba(255, 255, 255, 0.3)'
  ctx.fillRect(0, 0, 5, 1)
  ctx.fillRect(5, 2, 5, 1)
  ctx.fillRect(0, 4, 5, 1)
  ctx.fillRect(5, 6, 5, 1)
  ctx.fillRect(0, 8, 5, 1)
  
  return canvas
}

// 显示无数据状态
const showNoDataDonutChart = () => {
  if (!donutChart) return
  
  donutChart.setOption({
    title: {
      text: '暂无数据',
      subtext: '请先进行计算或上传数据',
      left: 'center',
      top: 'center',
      textStyle: {
        fontSize: 18,
        color: '#909399'
      },
      subtextStyle: {
        fontSize: 14,
        color: '#C0C4CC'
      }
    }
  })
}

// 监听数据变化
watch([() => bcdfiData.value, () => props.diseaseThresholds], () => {
  nextTick(() => {
    if (!donutChart) {
      initDonutChart()
    } else {
      updateDonutChart()
    }
  })
}, { deep: true })

// 生成PDF
const generatePDF = async () => {
  isGeneratingPDF.value = true
  try {
    await emit('generate-pdf')
    ElMessage.success('PDF报告生成成功，开始下载')
  } catch (error) {
    ElMessage.error('报告生成失败')
  } finally {
    isGeneratingPDF.value = false
  }
}

// 导出数据
const exportData = () => {
  const csvContent = frailtyTableData.value.map(row => 
    `${row.id},${row.frailty_index},${row.risk_level}`
  ).join('\n')
  
  const blob = new Blob(['ID,衰弱指数,风险等级\n' + csvContent], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `frailty_results_${new Date().toISOString().slice(0,10)}.csv`
  a.click()
}

</script>

<style scoped>
.results-container {
  padding: 20px;
  /* background-color: #f5f7fa; */
}

.summary-row {
  margin-bottom: 30px;
}


.chart-card {
  margin-bottom: 20px;
  font-size: 18px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 400px;
  width: 100%;
}

.chart-note {
  margin-top: 15px;
  color: #888;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.detail-row {
  margin-bottom: 30px;
}

.warning-card, .detail-card {
  height: 100%;
}

.no-warnings {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100px;
  color: #67c23a;
  gap: 10px;
}

.report-actions {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}
.distribution-chart {
  width: 100%;
  height: 400px; /* 给图表一个固定高度 */
  margin-top: 10px;
}
.chart-subtitle {
  color: #666;
  font-size: 16px;
  margin-top: 5px;
}
.chart-note {
  margin-top: 15px;
  color: #888;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 5px;
}
.stats-summary {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
  font-size:20px
}
.detailed-table {
  margin-top: 20px;
  /* border-top: 1px solid #ebeef5; */
  padding-top: 20px;
}
.custom-table-font {
  font-size: 14px !important;
}

/* 如果需要调整特定部分的字号 */
.custom-table-font .el-table__cell {
  font-size: 14px;
}

/* 如果需要调整表头字号 */
.custom-table-font .el-table__header th {
  font-size: 14px;
}

/* 如果需要调整内容字号 */
.custom-table-font .el-table__body td {
  font-size: 14px;
}
</style>