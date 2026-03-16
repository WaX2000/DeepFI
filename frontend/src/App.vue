<template>
  <div id="app">
    <el-container class="main-container">
      <!-- 侧边栏导航 -->
      <el-aside width="260px" class="sidebar">
        <div class="logo">
          <h2>🏥 衰弱指数测评</h2> <!-- 这个icon可以改哎 -->
        </div>
        
        <!-- <el-icon><MagicStick /></el-icon> -->
        
        <el-menu
          :default-active="activeMenu"
          class="nav-menu"
          @select="handleMenuSelect"
        >
          <el-menu-item index="upload">
            <el-icon><Upload /></el-icon> <!-- 这个icon可以改哎 -->
            <span>数据上传</span>
          </el-menu-item>

          <el-menu-item index="results" :disabled="!hasResults">
            <el-icon><DataAnalysis /></el-icon>
            <span>分析结果</span>
          </el-menu-item>

          <el-menu-item index="reports">
            <el-icon><Document /></el-icon>
            <span>报告管理</span>
          </el-menu-item>

        </el-menu>

      </el-aside>

      <!-- 主内容区 
      :survival-curves="survivalCurves" 
      @generate-pdf="handleGeneratePDF"
      -->
      <el-main class="main-content">
        <div v-show="activeMenu === 'upload'">
          <FileUpload 
            @file-uploaded="handleFileUploaded"
            @prediction-complete="handlePredictionComplete"
          />
        </div>
        
        <div v-if="activeMenu === 'results' && hasResults">
          <ResultsDisplay 
            :frailtyResults="frailtyResults"
            
          />
        </div>
        <div v-show="activeMenu === 'reports'">
          <ReportManager 
            />
        </div>
      </el-main>
      
    </el-container>
  </div>
</template>
            <!-- :report-history="reportHistory"  -->
<script setup>
import { ref, computed } from 'vue'
import { Upload, DataAnalysis, Document } from '@element-plus/icons-vue'
import FileUpload from './components/FileUpload.vue'
import ResultsDisplay from './components/ResultsDisplay.vue'
import ReportManager from './components/ReportManager.vue'

// 状态管理
const activeMenu = ref('upload')
// const fileData = ref(null)
const frailtyResults = ref(null)
// const survivalCurves = ref(null)
const reportHistory = ref([])
const hasResults = computed(() => frailtyResults.value !== null)

// 事件处理
const handleMenuSelect = (index) => {
  activeMenu.value = index
}

const handleFileUploaded = (data) => {
  // fileData.value = data
  print("???")
  activeMenu.value = 'results'
}

const handlePredictionComplete = (results) => {
  frailtyResults.value = results.frailty
  console.log("frailtyResults: ",frailtyResults.value)
  console.log("frailtyResults: ",frailtyResults)
  console.log("hasResults: ",hasResults)
  console.log("hasResults: ",hasResults.value)
  // survivalCurves.value = results.survival_curves
}

// const handleGeneratePDF = async () => {
//   try {
//     // 改格地址
//     const response = await fetch('http://localhost:5000/api/generate_pdf', { 
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify({
//         patientData: fileData.value,
//         frailtyResults: frailtyResults.value,
//         survivalCurves: survivalCurves.value
//       })
//     })
    
//     if (response.ok) {
//       const blob = await response.blob()
//       const url = window.URL.createObjectURL(blob)
//       const a = document.createElement('a')
//       a.href = url
//       a.download = `衰弱报告_${new Date().toLocaleDateString()}.pdf`
//       document.body.appendChild(a)
//       a.click()
//       window.URL.revokeObjectURL(url)
      
//       // 记录生成历史
//       reportHistory.value.push({
//         timestamp: new Date().toISOString(),
//         patientCount: frailtyResults.value.frailty_index.length
//       })
//     }
//   } catch (error) {
//     console.error('PDF下载失败:', error)
//   }
// }


</script>

<style scoped>
#app {
  height: 100vh;
  font-family: 'Helvetica Neue', Arial, sans-serif;
}

.main-container {
  height: 100%;
}

.sidebar {
  background: linear-gradient(180deg, #1e3c72 0%, #2a5298 80%);
  color: white;
}

.logo {
  padding: 30px;
  text-align: center;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.nav-menu {
  border-right: none;
  background: transparent;
}

.nav-menu :deep(.el-menu-item) {
  color: rgba(255,255,255,0.8);
  margin: 5px 15px;
  border-radius: 8px;
  /* 同时调整字体大小和图标间距 */
  font-size: 20px;
  height: 66px;
  line-height: 56px;
}

/* 如果需要单独调整图标大小 */
.nav-menu :deep(.el-menu-item .el-icon) {
  font-size: 30px; /* 调整图标本身大小 */
  margin-right: 10px; /* 调整图标与文字的间距 */
} 

.nav-menu :deep(.el-menu-item.is-active) {
  background-color: rgba(255,255,255,0.1);
  color: white;
}

.nav-menu :deep(.el-menu-item:hover) {
  background-color: rgba(255,255,255,0.05);
}

.main-content {
  background-color: #f5f7fa;
  padding: 30px;
}
</style>