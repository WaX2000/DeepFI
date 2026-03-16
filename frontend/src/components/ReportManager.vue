<template>
  <div class="report-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>📄 报告管理</h3>
          <div class="header-actions">
            <el-button type="primary" @click="openUploadDialog" icon="Upload">
              上传个人指标
            </el-button>
            <el-button type="success" @click="generateReport" :loading="generating"
              :disabled="!currentPatientData" icon="DocumentAdd">
              生成个人报告
            </el-button>
            <el-button @click="previewReport" :disabled="!currentReport" icon="View">
              预览报告
            </el-button>
          </div>
        </div>
      </template>

      <!-- 报告历史表格 -->
      <el-alert v-if="reportHistory.length === 0" title="暂无报告记录，请先上传个人指标并生成报告。" type="info" show-icon />
      <!-- <el-table v-else :data="reportHistory" style="width: 100%">
        <el-table-column prop="timestamp" label="生成时间" width="180">
          <template #default="{ row }">{{ new Date(row.timestamp).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="patientCount" label="分析人数" width="100">
          <template #default>1</template>
        </el-table-column>
        <el-table-column prop="title" label="报告标题" width="200" />
        <el-table-column prop="patientName" label="患者信息" width="200">
          <template #default="{ row }">{{ row.patientInfo?.age }}岁 {{ row.patientInfo?.gender }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button type="text" size="small" @click="previewSpecificReport(row)">查看</el-button>
            <el-button type="text" size="small" @click="downloadReport(row)">下载PDF</el-button>
            <el-button type="text" size="small" @click="deleteReport(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table> -->
    </el-card>

    <!-- 上传个人指标对话框 -->
    <el-dialog v-model="uploadVisible" title="上传个人指标记录" width="70%" :close-on-click-modal="false">
      <div class="csv-upload-container">
        <!-- 上传区域 -->
        <div class="upload-section">
          <el-upload class="upload-demo" drag :http-request="uploadRequest" :before-upload="beforeCSVUpload"
            :show-file-list="false" accept=".csv">
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">拖拽CSV文件到此处或 <em>点击上传</em></div>
            <div class="el-upload__tip">只能上传单条记录，CSV格式，大小不超过5MB</div>
          </el-upload>
        </div>

        <!-- 数据预览 -->
        <div v-if="previewData && previewData.length > 0" class="preview-section">
          <h3>数据预览</h3>
          <div class="data-preview">
            <el-table :data="previewData.slice(0, 1)" border style="width: 100%; margin: 15px 0;" max-height="300">
              <el-table-column v-for="col in previewColumns" :key="col" :prop="col" :label="col" min-width="150" />
            </el-table>
<!-- 
            <div class="record-count-info">
              <p>总记录数: {{ recordCount }} 条</p>
            </div> -->

            <!-- <div class="required-columns-info">
              <el-collapse v-model="activeCollapse">
                <el-collapse-item title="查看必需指标说明" name="1">
                  <div class="columns-list">
                    <el-tag v-for="col in requiredColumns" :key="col" type="success" size="small" class="column-tag">
                      {{ col }}
                    </el-tag>
                  </div>
                  <p class="hint-text">以上指标为必需指标，请确保您的CSV文件包含这些列。</p>
                </el-collapse-item>
              </el-collapse>
            </div> -->

            <div class="action-buttons">
              <el-button type="primary" @click="runPrediction" :loading="isPredicting"
                :disabled="isPredicting">
                {{ isPredicting ? '预测中...' : '预测衰弱指数' }}
              </el-button>
              <el-button @click="clearData">清除数据</el-button>
              <!-- <el-button type="text" @click="downloadTemplate" icon="Download">下载模板</el-button> -->
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="uploadVisible = false">取消</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 报告预览对话框 
              <el-button @click="copyReportContent" icon="CopyDocument">复制内容</el-button> 
    -->
    <el-dialog v-model="previewVisible" title="报告预览" width="80%" fullscreen :close-on-click-modal="false">
      <div v-if="previewContent" class="report-preview">
        <div class="preview-toolbar">
          <el-button type="primary" @click="downloadCurrentReport" icon="Download">下载PDF</el-button>
          <el-button @click="printReport" icon="Printer">打印</el-button>
        </div>
        <div class="report-content" v-html="renderedReport"></div>
      </div>
      <div v-else class="no-preview">暂无报告内容可预览</div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="previewVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElTimePicker } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import axios from 'axios'
import { extractFirst } from 'element-plus/es/utils/arrays.mjs'

// ==================== 工具函数 ====================
/**
 * 简单Markdown转HTML转换器
 * @param {string} text - Markdown文本
 * @returns {string} HTML文本
 */
const simpleMarkdownToHtml = (text) => {
  if (!text) return ''
  let html = text

  // 替换标题
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>')
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>')
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>')

  // 替换粗体和斜体
  html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
  html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>')

  // 替换代码和内联代码
  html = html.replace(/`(.*?)`/gim, '<code>$1</code>')

  // 替换列表
  html = html.replace(/^\* (.*$)/gim, '<li>$1</li>')
  html = html.replace(/<li>(.*?)<\/li>/gim, '<ul><li>$1</li></ul>')

  // 表格处理
  const lines = html.split('\n')
  let inTable = false
  let tableHtml = ''

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()

    if (line.includes('|') && line.replace(/\|/g, '').trim()) {
      if (!inTable) {
        tableHtml = '<table class="md-table">'
        inTable = true
      }

      if (line.includes('---')) continue // 跳过表头分割线

      const cells = line.split('|').filter(cell => cell.trim() !== '')
      tableHtml += '<tr>'
      cells.forEach(cell => {
        tableHtml += i === 0 ? `<th>${cell.trim()}</th>` : `<td>${cell.trim()}</td>`
      })
      tableHtml += '</tr>'
    } else {
      if (inTable) {
        tableHtml += '</table>'
        inTable = false
        lines[i] = tableHtml + line
        tableHtml = ''
      }
    }
  }

  html = lines.join('\n')
  html = html.replace(/\n/g, '<br>')
  return html
}

// /**
//  * 根据衰弱指数获取风险等级
//  * @param {number} fiValue - 衰弱指数
//  * @returns {Object} 风险等级信息
//  */
// const getRiskLevel = (fiValue) => {
//   if (fiValue < 0.1) return { label: '低风险', type: 'success' }
//   if (fiValue < 0.2) return { label: '中风险', type: 'warning' }
//   return { label: '高风险', type: 'danger' }
// }

/**
 * 格式化性别信息
 * @param {string} gender - 原始性别数据
 * @returns {string} 格式化后的性别
 */
const formatGender = (gender) => {
  if (gender==1 ) return '男'
  if (gender==0) return '女'
  else return '默认男'
}

// ==================== 响应式数据 ====================
// 患者数据和报告数据
const currentPatientData = ref(null)
const currentReport = ref(null)
const reportHistory = ref([])

// 对话框显示状态
const previewVisible = ref(false)
const uploadVisible = ref(false)
const previewContent = ref('')

// 加载状态
const generating = ref(false)
const isPredicting = ref(false)

// 文件上传相关数据
const previewData = ref([])
const previewColumns = ref([])
// const recordCount = ref(0)
const fileId = ref(null)
const activeCollapse = ref([])

// 必需指标列定义
const requiredColumns = ref([
'sex','age','Snoring', 'Able to confide', 'Sleeplessness', 'Time spent watching TV', 
'Usual walking pace', 'Current tobacco smoking', 'Past tobacco smoking', 
'Time spend outdoors in summer', 'Alcohol intake frequency', 
'Age first had sexual intercourse', 'Chest pain or discomfort', 
'Hearing difficulty/problems', 'Hearing difficulty/problems with background noise', 
'Hand grip strength (left)', 'Waist circumference', 'Chest pain or discomfort walking normally', 
'Forced expiratory volume in 1-second (FEV1)', 'Body mass index (BMI)', 'Whole body fat mass', 
'Hip circumference', 'linoleic acid to total fatty acids', 'docosahexaenoic acid to total fatty acids', 
'free cholesterol in idl', 'triglycerides to total lipids in medium hdl', 'cholesteryl esters in large hdl', 
'cholesteryl esters to total lipids in large hdl', 'cholesterol in large hdl', 'triglycerides in large ldl', 
'vldl cholesterol', 'free cholesterol to total lipids in large vldl', 'I_inteR', 'III_S', 'aVR_T', 'aVR_inteT',
 'aVL_R', 'V6_inteR', 'LV circumferential strain AHA 2', 'RA maximum volume', 'LV mean myocardial wall thickness AHA 10',
'Nitrogen dioxide air pollution; 2010', 'Nitrogen oxides air pollution; 2010', 'Particulate matter air pollution (pm10); 2010', 
'Particulate matter air pollution (pm2.5); 2010',
])

// ==================== 计算属性 ====================
const renderedReport = computed(() => simpleMarkdownToHtml(previewContent.value))

// ==================== 文件上传相关方法 ====================
/**
 * 打开上传对话框
 */
const openUploadDialog = () => {
  uploadVisible.value = true
  clearData()
}



const uploadRequest = async (options) => {
  const { file, onSuccess, onError, onProgress } = options
  
  try {
    console.log('开始上传文件:', file.name)
    
    const formData = new FormData()
    formData.append('file', file)
    
    console.log('FormData内容:')
    for (let [key, value] of formData.entries()) {
      console.log(`${key}:`, value)
    }

    const response = await axios.post(`/api/upload-single-csv`, formData, {
    // const BACKEND_URL = 'http://localhost:5000'
    // const response = await axios.post(`${BACKEND_URL}/api/upload-single-csv`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          console.log(`上传进度: ${percent}%`)
          onProgress({ percent })
        }
      }
    })
    
    console.log('上传成功，响应数据:', response.data)
    
    if (response.data.error) {
      ElMessage.error(`上传失败: ${response.data.error}`)
      onError(new Error(response.data.error))
      return
    }
    
    // 重要：直接处理上传成功的数据，不要调用两次onSuccess
    processUploadedData(response.data)
    
    // Element Plus需要这个回调
    onSuccess(response.data)
    
  } catch (error) {
    console.error('上传失败:', error)
    const errorMessage = error.response?.data?.error || error.message || '网络错误'
    ElMessage.error(`文件上传失败：${errorMessage}`)
    onError(error)
  }
}

const processUploadedData = (response) => {
  console.log('处理上传数据:', response)
  
  if (!response.success) {
    ElMessage.error(response.message || '上传处理失败')
    return
  }
  
  // 根据实际后端返回的数据结构调整
  const data = response.data || []
  const columns = response.columns || []
  const file_id = response.file_id || Date.now().toString()

  if (data.length === 0) {
    ElMessage.warning('CSV文件内容为空或格式不正确')
    return
  }
  console.log("data: ",data)

   const formattedData = data.map(rowArray => {
    const rowObject = {}
    columns.forEach((columnName, index) => {
      rowObject[columnName] = rowArray[index]
    })
    return rowObject
  })

  console.log("转换后的数据： ", formattedData)
  // 更新预览数据
  previewData.value = formattedData
  previewColumns.value = columns
  fileId.value = file_id

  console.log("previewData: ",previewData.value)
  console.log("previewData: ",previewData.value[0])

  console.log('预览数据已更新:', {
    previewData: previewData.value,
    previewColumns: previewColumns.value,
  })
  
  // 检查必需列
  const missingColumns = checkRequiredColumns(columns)
    if (missingColumns.length > 0) {
      ElMessage.error(`缺少必需列: ${missingColumns.join(', ')}，无法进行预测`)
      // 根据函数上下文选择合适的中断方式
      return          // 如果是在普通函数中，直接返回
      // 或 throw new Error('缺少必需列')   // 如果希望抛出异常由上层捕获
}
}

/**
 * 检查必需列
 */
const checkRequiredColumns = (uploadedColumns) => {
  const missing = []
  requiredColumns.value.forEach(col => {
    if (!uploadedColumns.includes(col)) {
      missing.push(col)
    }
  })
  return missing
}

/**
 * CSV文件上传前校验
 */
const beforeCSVUpload = (file) => {
  console.log('文件校验:', file.name, file.type, file.size)
  
  const isValidType = file.name.toLowerCase().endsWith('.csv')
  if (!isValidType) {
    ElMessage.error('仅支持CSV格式文件 (.csv)')
    return false
  }

  const MAX_SIZE = 5 * 1024 * 1024
  if (file.size > MAX_SIZE) {
    const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2)
    ElMessage.error(`文件大小不能超过5MB！当前文件为 ${fileSizeMB} MB。`)
    return false
  }

  return true
}

/**
 * 处理上传成功
 */
// const handleUploadSuccess = (response) => {
//   if (response.error) {
//     ElMessage.error(response.error)
//     return
//   }

//   previewData.value = response.data
//   previewColumns.value = response.columns
//   recordCount.value = response.record_count
//   fileId.value = response.file_id

//   const missingColumns = checkRequiredColumns(response.columns)
//   if (missingColumns.length > 0) {
//     ElMessage.warning(`缺少必需列: ${missingColumns.join(', ')}，可能会影响预测准确性`)
//   }

//   ElMessage.success(`文件上传成功，共 ${response.record_count} 条记录`)
// }


/**
 * 处理上传错误
 */
// const handleUploadError = (error) => {
//   console.error('上传失败:', error)
//   ElMessage.error(`文件上传失败：${error.message || '网络或服务器错误'}`)
// }


const diseaseThresholds = {
      cardiovascular: { 
        name: '心血管疾病', 
        threshold: 0.158, 
        color: '#FF6B6B',
      },
      diabetes: { 
        name:'二型糖尿病',
        threshold: 0.207, 
        color: '#4ECDC4',
      },
      NN: { 
        name: '神经退行性病变', 
        threshold: 0.143, 
        color: '#FFEAA7',
      },
      Auto: { 
        name: '自身免疫性疾病', 
        threshold: 0.222, 
        color: '#DDA0DD',
      },
    }

// {
//         cardiovascular: { 
//           name: '恶性肿瘤病', 
//           threshold: 0.122, 
//           color: '#FF6B6B',
//           description: '包括冠心病、高血压、心力衰竭等'
//         },
//         diabetes: { 
//           name: '慢性阻塞性肺病', 
//           threshold: 0.216, 
//           color: '#4ECDC4',
//           description: '2型糖尿病及其并发症风险'
//         },
//         kidney: { 
//           name: '二型糖尿病', 
//           threshold: 0.199, 
//           color: '#45B7D1',
//           description: '慢性肾功能不全风险'
//         },
//         stroke: { 
//           name: '心脑血管疾病', 
//           threshold: 0.206, 
//           color: '#96CEB4',
//           description: '缺血性和出血性脑卒中'
//         },
//         osteoporosis: { 
//           name: '神经退行性病变', 
//           threshold: 0.149,
//           color: '#FFEAA7',
//           description: '骨折和骨密度下降风险'
//         },
//         autoimmune: { 
//           name: '自身免疫性疾病', 
//           threshold: 0.151, // 注意：您这里加了0.1，应该是0.251
//           color: '#DDA0DD',
//         },
//         depression: { 
//           name: '抑郁症', 
//           threshold: 0.201, 
//           color: '#DDA0DD',
//           description: '多种癌症的总体风险'
//         }
//       }

const runPrediction = async () => {
  if (!fileId.value) {
    ElMessage.warning('请先上传有效的CSV文件')
    return
  }
  isPredicting.value = true
  try {
    const response = await axios.post('api/predict-single-csv', {
      file_id: fileId.value
    }, {
      timeout: 60000 // 预测可能需要更长时间
    })
    
    if (response.data.success) {
      const predictionResult = response.data.data[0]
      console.log("predictionResult: ",predictionResult)
      const firstRow = previewData.value[0]
      console.log("第一行数据:", firstRow)
      const patientData={...firstRow}
      const DeepFI = predictionResult.DeepFI || 0
      console.log("DeepFI:", DeepFI)

      const highRiskDiseases = []
      for (const [key, disease] of Object.entries(diseaseThresholds)) {
        if (DeepFI >= disease.threshold) {
          highRiskDiseases.push({
            name: disease.name,
            threshold: disease.threshold,
            riskLevel: '高风险',
            description: disease.description
          })
        }
      }
      
      // 按阈值从低到高排序
      highRiskDiseases.sort((a, b) => a.threshold - b.threshold)
      
      // 提取疾病名称列表
      const diseaseNames = highRiskDiseases.map(d => d.name)
      
      console.log('高风险疾病列表:', highRiskDiseases)
      console.log('疾病名称列表:', diseaseNames)


      currentPatientData.value = {
        ...patientData,
        DeepFI: predictionResult.DeepFI || 0,
        // disease_list: predictionResult.disease_list || ['神经退行性疾病', '抑郁症', '心血管疾病', '2型糖尿病'],
        // risk_level: getRiskLevel(predictionResult.fi_value || 0).label,
        disease_list: diseaseNames,
        highRiskDiseases: highRiskDiseases, // 包含完整信息的列表
        gender: formatGender(patientData.sex)
      }
      console.log('患者数据已更新:', patientData)
      console.log('患者数据已更新:', currentPatientData.value)

      if (highRiskDiseases.length > 0) {
        const diseaseCount = highRiskDiseases.length
        const diseaseListStr = diseaseNames.join('、')
        ElMessage.warning(`检测到${diseaseCount}种高风险疾病：${diseaseListStr}`)
      } else {
        ElMessage.success('未检测到高风险疾病')
      }

      
      ElMessage.success('预测完成！')
      uploadVisible.value = false
      
      // 自动生成报告
      // await generateReport()

    } else {
      throw new Error(response.data.message || '预测失败')
    }
  } catch (error) {
    console.error('预测失败:', error)
    ElMessage.error(`分析失败: ${error.response?.data?.message || error.message}`)
  } finally {
    isPredicting.value = false
  }
}


/**
 * 清除上传的数据
 */
const clearData = () => {
  previewData.value = []
  previewColumns.value = []
  // recordCount.value = 0
  fileId.value = null
}

/**
 * 下载CSV模板
 */
const downloadTemplate = () => {
  const headers = requiredColumns.value.join(',')
  const sampleRow = requiredColumns.value.map(col => {
    const samples = {
      age: '65',
      gender: 'male',
      BMI: '28.02',
      current_tobacco_smoking: 'Previous smoker',
      alcohol_intake_frequency: 'Daily or almost daily',
      sleeplessness: 'Never/rarely',
      Snoring: 'Yes',
      Time_spent_watching_TV: '1-2 hours',
      Able_to_confide: 'Quite a bit',
      Chest_pain_or_discomfort: 'No',
      Hearing_difficulty: 'No',
      Usual_walking_pace: 'Average pace'
    }
    return samples[col] || ''
  }).join(',')

  const csvContent = `${headers}\n${sampleRow}`
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = '个人指标模板.csv'
  link.click()
  URL.revokeObjectURL(link.href)
}

// ==================== 报告相关方法 ====================
/**
 * 生成个人报告
 * `你是一个智能医疗报告生成系统。任务是根据提供的患者数据和衰弱指数(FI)生成结构化临床报告。请遵循以下规则：
                        1. 报告需包含【临床解读】【风险预警】【干预模拟和健康建议】三大模块
                        2. 干预模拟要求
                            -创建表格对比行为指标调整前后的FI变化，包含列：调整指标 | 原始状态 | 调整后状态 | FI变化值
                            - 根据FI变化值排序（从小到大）
                            - 对每个调整项给出具体建议，不要给出具体频率
                        3. 使用医学术语但保持可读性
                        4. 重要数值用**加粗**突出
                        5. 生理系统脆弱性分析、主要风险因子关联性、各疾病风险机制说明使用表格的形式表示
                        6. 临床指南的推荐应基于真实、可靠的证据，指南名称完整准确，并确保内容最新。
                        7. 分优先级的干预措施显示60-65岁人群中轻微虚弱的人群FI阈值
                        8. 合规声明：※ 报告题目后必须包含以下声明：「本报告基于算法推导，不作为临床诊断依据。具体诊疗方案需经执业医师确认」`
 */
const generateReport = async () => {
  try {
    if (!currentPatientData.value) {
      ElMessage.warning('请先上传个人指标数据')
      openUploadDialog()
      return
    }

    generating.value = true

    const requestData = {
      model: "deepseek-reasoner",
      messages: [
        {
          "role": "system",
          "content": `你是一个智能医疗报告生成系统。任务是根据提供的患者数据和衰弱指数(FI)生成结构化临床报告。请遵循以下规则：
                        1. 报告需包含【临床解读】【风险预警】【健康建议】三大模块
                        2. 健康建议不要给出具体频率
                        3. 使用医学术语但保持可读性
                        4. 重要数值用**加粗**突出
                        5. 生理系统脆弱性分析、主要风险因子关联性、各疾病风险机制说明使用表格的形式表示
                        6. 临床指南的推荐应基于真实、可靠的证据，指南名称完整准确，并确保内容最新。
                        7. 合规声明：※ 报告题目后必须包含以下声明：「本报告基于算法推导，不作为临床诊断依据。具体诊疗方案需经执业医师确认」`
        },
        {
          "role": "user",
          "content": formatPatientDataForReport(currentPatientData.value)
        }
      ],
      stream: false
    }
    console.log("request: ",requestData)
    const response = await axios.post('/api/generate-report', requestData, {
      headers: { 'Content-Type': 'application/json' }
    })

    if (response.data.success) {
      const reportData = response.data.data
      const newReport = {
        id: reportData.id,
        // timestamp: new Date().toISOString(),
        // patientCount: 1,
        title: `个人衰弱指数报告`+reportData.id,
        content: reportData.markdown,
        // htmlContent: reportData.html,
        // patientInfo: {
        //   age: currentPatientData.value.age,
        //   gender: currentPatientData.value.gender === 'male' ? '男' : '女',
        //   fi_value: currentPatientData.value.fi_value
        // }
      }

      reportHistory.value.unshift(newReport)
      currentReport.value = newReport
      previewContent.value = reportData.markdown
      previewVisible.value = true
      // saveToLocalStorage()
      ElMessage.success('报告生成成功！')
    } else {
      throw new Error(response.data.message || '报告生成失败')
    }
  } catch (error) {
    console.error('生成报告失败:', error)
    ElMessage.error(`生成报告失败: ${error.message}`)
  } finally {
    generating.value = false
  }
}

/**
 * 格式化患者数据用于报告生成
 */

const FIELD_MAPPINGS = {
    "Current tobacco smoking":{
      "1": "Yes, on most or all days",
      "2":	"Only occasionally",
      "0":	"No",
      "3":	"Prefer not to answer",
    },

    "Snoring":{
      "1": 	"Yes",
      "2": 	"No",
      "0": 	"Do not know",
      "3": 	"Prefer not to answer",
      },

    "Past tobacco smoking":{
      "1": 	"Smoked on most or all days",
      "2": 	"Smoked occasionally",
      "3": 	"Just tried once or twice",
      "4": 	"I have never smoked",
      "0": 	"Prefer not to answer",
    },

    "Alcohol intake frequency":{
      "0":	"Daily or almost daily",
      "1":	"Three or four times a week",
      "2":	"Once or twice a week",
      "3":	"One to three times a month",
      "4":	"Special occasions only",
      "5":	"Never",
      "6":	"Prefer not to answer",
      },

    "Chest pain or discomfort walking normally":{
      "2":	"Yes",
      "1":	"No",
      "0":	"Unable to walk on the level",
      },

    "difficulty/problems":{
      "2":	"Yes",
      "1":	"No",
      "0":	"Do not know",
      },

    "Able to confide":{
      "6":	"Almost daily",
      "5":	"2-4 times a week",
      "4":	"About once a week",
      "3":	"About once a month",
      "2":	"Once every few months",
      "1":	"Never or almost never",
      "0":	"Do not know",
      "7":	"Prefer not to answer",
    },

    "Usual walking pace":{
      "0":	"Slow pace",
      "1":	"Steady average pace",
      "2":	"Brisk pace",
      "0":	"None of the above",
      "3":	"Prefer not to answer",
      },

    "Hearing difficulty/problems":{
      "2":	"Yes",
      "1":	"No",
      "4":	"I am completely deaf",
      "0":	"Do not know",
      },

    "Sleeplessness":{
      "0":	"Never/rarely",
      "1":	"Sometimes",
      "2":	"Usually",
      "3":	"Prefer not to answer",
    },

    "Chest pain or discomfort":{
    "2":	"Yes",
    "1":	"No",
    "0":	"Do not know",
    },

    "sex":{
      "0":"女",
      "1":"男",
    }
}
const smartConvertValue = (fieldName, value) => {
  // if (value === null || value === undefined || value === '') {
  //   return '未提供'
  // }
  const strValue = String(value)
  // 特定字段的映射
  if (FIELD_MAPPINGS[fieldName]) {
    const mapped = FIELD_MAPPINGS[fieldName][strValue]
    if (mapped) return mapped
    else return "请上传有效的个人指标"
  }
  

  if (!isNaN(value)) {
    const numValue = Number(value)
    return strValue
  }
  
  // 默认返回原值
  return strValue
}

const prepareFormattedPatientData = (patientData) => {
  const result = {}
  
  // 复制所有数据
  Object.keys(patientData).forEach(key => {
    result[key] = smartConvertValue(key, patientData[key])
  })
  
  // 添加计算字段
  if (patientData.DeepFI) {
    result.DeepFI_formatted = patientData.DeepFI.toFixed(4)
  }
  
  // 添加高风险疾病
  if (patientData.disease_list && Array.isArray(patientData.disease_list)) {
    result.disease_list_str = patientData.disease_list.join('、')
    result.disease_count = patientData.disease_list.length
    console.log("disease list :",result.disease_list_str,result.disease_count)
  }
  
  return result
}

const formatPatientDataForReport = (patientData) => {
  console.log("formatPatient: ",patientData)

  const formatted = prepareFormattedPatientData(patientData)
  console.log("格式化患者数据: ", formatted)
  console.log("格式化患者数据 sex: ", formatted.sex)
  console.log("格式化患者数据 DeepFI: ", formatted.DeepFI_formatted)
  
  // 提取关键信息
  const genderText = formatted.sex || '未知'
  const ageText = formatted.age || '未提供'
  const bcdfiText = formatted.DeepFI_formatted || '0.0000'
  // const riskLevelText = formatted.risk_level || '未知'
  const diseaseListText = formatted.disease_list_str || '未检测到高风险疾病'
  const diseaseCount = formatted.disease_count || 0

  return `患者数据：
            - 基本信息：${genderText}性｜${ageText}岁
            - 行为指标：吸烟：${formatted["Current tobacco smoking"] || '未提供'},
                        饮酒：${formatted["Alcohol intake frequency"] || '未提供'},
                        睡眠：${formatted["Sleeplessness"] || '未提供'},
                        BMI：${formatted["Body mass index (BMI)"] || '未提供'},
                        打鼾：${formatted["Snoring"] || '未提供'},
                        胸痛：${formatted["Chest pain or discomfort"] || '未提供'},
                        听力：${formatted["Hearing difficulty/problems"] || '未提供'},
                        步速：${formatted["Usual walking pace"] || '未提供'},
                        倾诉：${formatted["Able to confide"] || '未提供'},
                        电视观看时长：${formatted["Time spent watching TV"]+"hours" || '未提供'}
            - 衰弱指数(DeepFI)：${bcdfiText}，
            - 预警疾病数量：${diseaseCount}种，
            - 具体疾病：${diseaseListText} 

            请生成包含以下结构的报告：
            # 衰弱指数临床报告

            ## 患者概况
            - 人口学特征
            - 关键行为指标

            ## 临床解读
            1. 生理系统脆弱性分析
            2. 主要风险因子关联性

            ## 风险预警
            疾病风险预测列表
            疾病风险预测说明

            ## 健康建议
            ✚ 分优先级的干预措施  
            ✚ 监测建议
            ✚ 最新的临床参考指南
            ✚ 推荐专科门诊`
}

/**
 * 预览当前报告
 */
const previewReport = () => {
  if (currentReport.value) {
    previewContent.value = currentReport.value.content
    previewVisible.value = true
  }
}

/**
 * 预览特定报告
 */
const previewSpecificReport = (report) => {
  previewContent.value = report.content
  currentReport.value = report
  previewVisible.value = true
}

/**
 * 下载报告为PDF
 */
const downloadReport = async (report) => {
  console.log("downreport: ", report)
  try {
    const response = await axios.post('api/convert-to-pdf', {
      markdown: report.content,
      filename: `个人衰弱指数报告_${report.id}`,
      id:report.id,
    }, { responseType: 'blob' })

    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `衰弱指数报告_${report.id}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()

    ElMessage.success('报告下载成功！')
  } catch (error) {
    console.error('下载报告失败:', error)
    ElMessage.error('下载报告失败')
  }
}

/**
 * 下载当前报告
 */
const downloadCurrentReport = () => {
  if (currentReport.value) downloadReport(currentReport.value)
}

/**
 * 复制报告内容到剪贴板
 */
const copyReportContent = async () => {
  try {
    await navigator.clipboard.writeText(previewContent.value)
    ElMessage.success('报告内容已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
}

/**
 * 打印报告
 */
const printReport = () => {
  const printWindow = window.open('', '_blank')
  printWindow.document.write(`
    <html>
      <head>
        <title>衰弱指数临床报告</title>
        <style>
          body { font-family: 'Microsoft YaHei', sans-serif; padding: 20px; }
          h1 { color: #333; border-bottom: 2px solid #409EFF; padding-bottom: 10px; }
          h2 { color: #555; margin-top: 20px; }
          table { border-collapse: collapse; width: 100%; margin: 10px 0; }
          th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
          th { background-color: #f5f7fa; }
          .disclaimer { color: #f56c6c; font-style: italic; margin: 20px 0; }
        </style>
      </head>
      <body>
        ${renderedReport.value}
      </body>
    </html>
  `)
  printWindow.document.close()
  printWindow.print()
}

/**
 * 删除报告
 */
const deleteReport = (report) => {
  ElMessageBox.confirm('确定要删除这份报告吗？此操作不可撤销。', '删除确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    const index = reportHistory.value.findIndex(r => r.id === report.id)
    if (index !== -1) {
      reportHistory.value.splice(index, 1)
      ElMessage.success('报告已删除')

      if (currentReport.value && currentReport.value.id === report.id) {
        currentReport.value = null
        previewContent.value = ''
      }

      saveToLocalStorage()
    }
  }).catch(() => { })
}

// ==================== 辅助方法 ====================
/**
 * 保存数据到本地存储
 */
// const saveToLocalStorage = () => {
//   try {
//     localStorage.setItem('reportHistory', JSON.stringify(reportHistory.value))
//     localStorage.setItem('currentPatientData', JSON.stringify(currentPatientData.value))
//   } catch (error) {
//     console.error('保存到本地存储失败:', error)
//   }
// }

/**
 * 从本地存储加载数据
 */
const loadFromLocalStorage = () => {
  try {
    const savedHistory = localStorage.getItem('reportHistory')
    if (savedHistory) {
      reportHistory.value = JSON.parse(savedHistory)
      if (reportHistory.value.length > 0) {
        currentReport.value = reportHistory.value[0]
      }
    }

    const savedPatientData = localStorage.getItem('currentPatientData')
    if (savedPatientData) {
      currentPatientData.value = JSON.parse(savedPatientData)
    }
  } catch (error) {
    console.error('加载本地存储数据失败:', error)
  }
}

// ==================== 生命周期钩子 ====================
// onMounted(() => {
//   loadFromLocalStorage()
// })
</script>

<style scoped>
.report-manager {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.csv-upload-container {
  max-height: 70vh;
  overflow-y: auto;
  padding: 10px;
}

.upload-section {
  margin: 20px 0;
}

.upload-demo {
  width: 100%;
}

.preview-section {
  margin-top: 30px;
}

.data-preview {
  margin-top: 20px;
}

.record-count-info {
  margin: 15px 0;
}

.record-count-info p {
  margin: 10px 0;
  color: #666;
  font-size: 14px;
}

.required-columns-info {
  margin: 20px 0;
}

.columns-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 10px 0;
}

.column-tag {
  margin: 2px;
}

.hint-text {
  margin-top: 10px;
  color: #f56c6c;
  font-size: 14px;
}

.action-buttons {
  margin-top: 25px;
  display: flex;
  gap: 15px;
  justify-content: center;
}

/* 报告预览样式 */
.report-preview {
  height: 70vh;
  display: flex;
  flex-direction: column;
}

.preview-toolbar {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  gap: 10px;
}

.report-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: #f9fafc;
}

.no-preview {
  text-align: center;
  padding: 40px;
  color: #909399;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: wrap;
  }

  .action-buttons {
    flex-direction: column;
  }

  .action-buttons .el-button {
    width: 100%;
  }
}
</style>