<template>
  <div class="upload-container">
    <el-card class="upload-card">

      <template #header>
        <div class="card-header">
          <h3>📁 上传生理指标数据</h3>
          <p class="subtitle">支持CSV或Excel格式</p> <!--包含年龄、血压、步速等指标 -->
        </div>
      </template>

      <!-- 文件上传区域 -->
      <el-upload
        class="upload-demo"
        drag
        action="/api/upload"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :before-upload="beforeUpload"
        :show-file-list="false"
        accept=".csv,.xlsx,.xls"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处或 <em>点击上传</em>
        </div>
        <div class="el-upload__tip">
          单次最多处理1000条记录，文件大小不超过100MB
        </div>
       </el-upload>
        
        
        <!-- @click="cleanupDownloadUrl" -->


     


      <!-- 数据预览-->
      <div v-if="previewData" class="preview-section">
        <h3>数据预览</h3>

        <el-table :data="previewData" border style="width: 200%; margin-top: 15px;">
          <el-table-column 
            v-for="col in previewColumns" 
            :key="col"
            :prop="col" 
            :label="col"
            min-width="120"
          />
        </el-table>

        <div v-if="downloadUrl" class="download-section">
          <p>✅ 文件上传成功！</p>
          <el-descriptions :column="2" size="small" border style="margin-top: 10px; margin-bottom: 15px;margin-right: 1000px;">
          <el-descriptions-item label="数据量">{{ rowCount }} 行</el-descriptions-item>
          <!-- <el-row :gutter="20">
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-icon">👥</div>
                <div class="stat-content">
                  <div class="stat-label">总样本数</div>
                  <div class="stat-value">{{ overallStats.totalPatients }}</div>
                </div>
              </div>
            </el-col>
          </el-row> -->
          <!-- <el-descriptions-item label="指标数">{{ .previewColumns.length }} 个</el-descriptions-item>-->
          </el-descriptions>
          <!-- <p>点击链接下载：</p>
            <a 
              :href="downloadUrl" 
              :download="downloadFileName"
              class="download-link"
            >
              下载 {{ downloadFileName}}
            </a> -->
          <div style="margin-top: 10px;">
            <el-button 
              type="text" 
              @click="downloadOriginalFile" 
              :loading="isDownloadingOriginal"
              :disabled="isDownloadingOriginal"
            >
              <el-icon><Download /></el-icon>
              {{ isDownloadingOriginal ? '准备文件中...' : `下载原始文件` }}
            </el-button>
          </div>


            


        </div>
        
        <!-- <div class="upload-stats">
          <el-tag type="success">共 {{ rowCount }} 行，{{ previewColumns.length }} 列</el-tag>
        </div> -->
        
        <div class="action-buttons">
          <el-button type="primary" 
                    @click="runPrediction" 
                    :loading="isPredicting">
            {{ isPredicting ? '预测中...' : '预测衰弱指数' }}
          </el-button>
          <el-button @click="clearData">清除上传文件</el-button>
        </div> 

        <!-- 新增：预测结果下载区域 (仅在预测成功后显示) -->
        <!-- <div v-if="showDownload" style="margin-top: 15px;">
          <el-button type="text" 
                    @click="downloadPredictionCSV" 
                    :loading="isDownloading" 
                    :disabled="isDownloading">
            <el-icon><Download /></el-icon>
            {{ isDownloading ? '正在生成文件...' : '下载预测结果 CSV' }}
          </el-button>
        </div> -->
        <div v-if="showDownload" class="download-prediction-section" style="margin-top: 20px;  border-top: 2px dashed #eaeaea;">
          <p style="margin-bottom: 15px; color: #67c23a;">
            <el-icon><CircleCheck /></el-icon> 预测结果已就绪！
          </p>
          <div>
            <el-button 
              type="success" 
              @click="downloadPredictionCSV" 
              :loading="isDownloading"
              :disabled="isDownloading"
            >
              <el-icon><Download /></el-icon>
              {{ isDownloading ? '准备下载中...' : '下载预测结果 (CSV)' }}
            </el-button>
          </div>
        </div>


      </div> 

    <!-- 上传结果区域 -->
    <!-- <div v-if="showDownloadSection" class="download-section">
      <h3>文件上传成功!</h3>
      
      <div class="file-info">
        <p><strong>文件名:</strong> {{ uploadedFileName }}</p>
        <p><strong>文件大小:</strong> {{ formatFileSize(uploadedFileSize) }}</p>
        <p><strong>上传时间:</strong> {{ uploadTime }}</p>
        <p v-if="rowCount"><strong>记录数:</strong> {{ rowCount }} 条</p>
      </div>
      
      <div class="download-actions">
        <button @click="downloadFile" class="download-btn">
          <i class="download-icon">↓</i> 下载已上传的文件
        </button>
      </div>
      
      <p class="download-hint">
        点击上方按钮下载您刚刚上传的文件。
      </p>
      
      <button @click="resetUpload" class="reset-btn">
        上传新文件
      </button>
    </div>

      <div v-else-if="isUploading" class="uploading-section">
        <p>正在上传文件，请稍候...</p>
        <div class="loading-spinner"></div>
      </div> -->
    </el-card>



    <!-- 示例文件下载 -->
    <el-card class="sample-card">
      <template #header>
        <span>📋 上传格式</span>
      <div style="margin-top: 15px;">
        <el-button type="text" @click="downloadSample">
          <el-icon><Download /></el-icon>下载示例文件
        </el-button>
      </div>

      </template>

      <p><el-icon><InfoFilled /></el-icon> 确保您的数据包含关键指标：</p>
      <!-- <el-tag v-for="item in sampleColumns" :key="item" class="sample-tag">
        {{ item }}
      </el-tag> -->

      <div v-for="(group, groupName) in categorizedColumns" :key="groupName" class="category-group">
        <!-- <h4>{{ groupName }}</h4> -->
        <div class="tags-container">
          <el-tag 
            v-for="item in group" 
            :key="item.original" 
            class="sample-tag"
            :type="getTagType(groupName)"
          >
            {{ item.original }}
          </el-tag>
        </div>
      </div>

    </el-card>

  </div>
</template>


<script setup>
// console.log('FileUpload 组件加载完成！');
// const uploadAction = '/api/upload'; // 或你的完整后端地址
// console.log('上传地址设置为:', uploadAction);
import { ref } from 'vue'
import { UploadFilled, Download,CircleCheck} from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
// import { cloneElement } from 'react'

const emit = defineEmits(['file-uploaded', 'prediction-complete'])

const previewData = ref(null) // 存储从后端返回的文件预览数据（前5行）
const previewColumns = ref([]) // 存储文件的列名
const rowCount = ref(0) // 存储文件的总行数
const isPredicting = ref(false) // 一个“开关”，用于在分析时显示“加载中”
const uploadedFile = ref(null)
const downloadUrl = ref('')
const fileId = ref(null)

// 新增状态：控制下载链接显示，以及下载时可能需要的加载状态
const showDownload = ref(false)
const isDownloading = ref(false)

const sampleColumns = [
'Able to confide',
'Age first had sexual intercourse',
'Alcohol intake frequency',
'BMI',
'Chest pain or discomfort',
'Chest pain or discomfort walking normally',
'Current tobacco smoking',
'DHA_pct',
'Forced expiratory volume in 1-second',
'Hand grip strength (left)',
'Hearing difficulty/problems',
'Hearing difficulty/problems with background noise',
'Hip circumference',
'I_inteR',
'IDL_FC',
'III_S',
'LA_pct',
'L_HDL_C',
'L_HDL_CE',
'L_HDL_CE_pct',
'L_LDL_TG',
'LVCC_AHA_2',
'LVWT_AHA_10',
'L_VLDL_FC_pct',
'M_HDL_TG_pct',
'Nitrogen dioxide air pollution; 2010',
'Nitrogen oxides air pollution; 2010',
'Particulate matter air pollution (pm10); 2010',
'Particulate matter air pollution (pm2.5); 2010',
'Past tobacco smoking',
'RAV_max',
'Sleeplessness',
'Snoring',
'Time spend outdoors in summer',
'Time spent watching television',
'Usual walking pace',
'V6_inteR',
'VLDL_C',
'Waist circumference',
'Whole body fat mass',
'aVL_R',
'aVR_T',
'aVR_inteT',
]


// const downloadFileName = ref('')

// 处理上传成功

const categorizedColumns = {
  'Demographics & Lifestyle': [
    { original: 'Age first had sexual intercourse' },
    { original: 'Alcohol intake frequency' },
    { original: 'Current tobacco smoking' },
    { original: 'Past tobacco smoking' },
    { original: 'Sleeplessness' },
    { original: 'Snoring' },
    { original: 'Time spent watching TV' },
    { original: 'Time spend outdoors in summer' },
    { original: 'Usual walking pace' },
    { original: 'Able to confide' },
    { original: 'Forced expiratory volume in 1-second' }
  ],
  'Hearing Function': [
    { original: 'Hearing difficulty' },
    { original: 'Hearing difficulty with background noise' }
  ],
  'Anthropometric Measures': [
    { original: 'BMI' },
    { original: 'Hand grip strength (left)' },
    { original: 'Hip circumference' },
    { original: 'Waist circumference' },
    { original: 'Whole body fat mass' }
  ],
  'Cardiovascular Indicators': [
    { original: 'Chest discomfort' },
    { original: 'Chest discomfort walking normally' },

    // { original: 'RAV_max' },
    // { original: 'LVCC_AHA_2' },
    // { original: 'LVWT_AHA_10' }
    
    { original: 'RA maximum volume' },
    { original: 'LV circumferential strain AHA 2' },
    { original: 'LV mean myocardial wall thickness AHA 10' }
  ],
  'Blood Lipid Metabolism': [
    // { original: 'DHA_pct' },
    // { original: 'IDL_FC' },
    // { original: 'LA_pct' },
    // { original: 'L_HDL_C' },
    // { original: 'L_HDL_CE' },
    // { original: 'L_HDL_CE_pct' },
    // { original: 'L_LDL_TG' },
    // { original: 'L_VLDL_FC_pct' },
    // { original: 'M_HDL_TG_pct' },
    // { original: 'VLDL_C' }    
    // 
    { original: 'docosahexaenoic acid to total fatty acids' },
    // { original: 'I_inteR' },
    { original: 'free cholesterol in idl' },
    // { original: 'III_S' },
    { original: 'linoleic acid to total fatty acids' },
    { original: 'cholesterol in large hdl' },
    { original: 'cholesteryl esters in large hdl' },
    { original: 'cholesteryl esters to total lipids in large hdl' },
    { original: 'triglycerides in large ldl' },
    { original: 'free cholesterol to total lipids in large vldl' },
    { original: 'triglycerides to total lipids in medium hdl' },
    { original: 'vldl cholesterol' }
  ],
  'Environmental Exposure': [
    { original: 'Nitrogen dioxide air pollution; 2010' },
    { original: 'Nitrogen oxides air pollution; 2010' },
    { original: 'Particulate matter air pollution (pm10); 2010' },
    { original: 'Particulate matter air pollution (pm2.5); 2010' }
  ],
  'ECG Indicators': [
    { original: 'V6_inteR' },
    { original: 'I_inteR' },
    { original: 'III_S' },
    { original: 'aVL_R' },
    { original: 'aVR_T' },
    { original: 'aVR_inteT' }
  ]
}

const getTagType = (category) => {
  const typeMap = {
    'Demographics & Lifestyle': 'primary',
    'Anthropometric Measures': 'primary',//'success',
    'Cardiovascular Indicators': 'primary',//'danger',
    'Pulmonary Function': 'primary',//'info',
    'Blood Lipid Metabolism': 'primary',//'warning',
    'Hearing Function': 'primary',//'',
    'Environmental Exposure': 'primary',//'',
    'ECG Indicators': 'primary',//'primary'
  }
  return typeMap[category] || ''
}

const handleUploadSuccess = (response) => {
  console.log("handleUploadSuccess begin")

  if (response.error) {
    ElMessage.error(response.error) // 现实的error代码
    return
  }
  console.log("文件上传成功，后端返回:")
  console.log(response)

  previewData.value = response.preview
  previewColumns.value = response.columns
  rowCount.value = response.rows
  fileId.value=response.file_id

  if (uploadedFile.value) {
    const url = URL.createObjectURL(uploadedFile.value)
    downloadUrl.value = url
    downloadFileName.value = uploadedFile.value.name
  }


  ElMessage.success(`成功上传 ${response.rows} 条记录`)
  emit('file-uploaded', response.preview)
  console.log("handleUploadSuccess end")

}

// 新增状态和方法
const isDownloadingOriginal = ref(false)

const downloadOriginalFile = async () => {
  // 确保有文件对象且不在下载中
  if (!uploadedFile.value || !isDownloadingOriginal.value) return
  
  isDownloadingOriginal.value = true
  try {
    // 1. 直接从 uploadedFile.value（File对象）创建下载链接
    const url = URL.createObjectURL(uploadedFile.value)
    
    // 2. 创建隐藏的 <a> 标签并触发点击
    const link = document.createElement('a')
    link.href = url
    link.download = uploadedFile.value.name // 使用文件原始名称
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    // 3. 立即释放 URL 对象（重要！）
    URL.revokeObjectURL(url)
    
    ElMessage.success('原始文件下载开始')
    
  } catch (error) {
    console.error('原始文件下载失败:', error)
    ElMessage.error(`下载失败: ${error.message}`)
  } finally {
    isDownloadingOriginal.value = false
  }
}

const handleUploadError = (error, rawFile) => {
  console.error('上传失败：', error)
  // 显示更友好的错误信息
  ElMessage.error(`文件上传失败：${error.message || '网络或服务器错误'}`)
}

const cleanupDownloadUrl = () => {
  if (downloadUrl.value && downloadUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(downloadUrl.value)
    downloadUrl.value = ''
  }
}

const beforeUpload = (file) => {
  console.log('🔍 [beforeUpload] 开始校验，文件详情:', {
    name: file.name,
    size: file.size,
    type: file.type
  });
  
  // 1. 校验文件类型
  const isValidType = file.name.match(/\.(csv|xlsx|xls)$/i); // 注意：加了 i 标志忽略大小写
  console.log('📄 文件类型校验结果:', isValidType ? '通过' : '失败', '匹配结果:', isValidType);
  
  if (!isValidType) {
    ElMessage.error('仅支持CSV或Excel文件（.csv, .xlsx, .xls）');
    return false; // 这里返回了 false，请求被拦截！
  }
  
  // 2. 校验文件大小 (100MB限制)
  const MAX_SIZE = 100 * 1024 * 1024; // 100MB
  const isValidSize = file.size <= MAX_SIZE;
  const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
  console.log('⚖️ 文件大小校验结果:', isValidSize ? '通过' : '失败', `文件大小: ${fileSizeMB} MB`, `限制: 100 MB`);
  
  if (!isValidSize) {
    ElMessage.error(`文件大小不能超过100MB！当前文件为 ${fileSizeMB} MB。`);
    return false; // 这里返回了 false，请求被拦截！
  }
  
  // 3. 如果所有校验都通过
  console.log('✅ 所有校验通过，准备上传...');
  console.log(file)
  uploadedFile.value = file
  return true; // 必须返回 true 才能继续上传！
}

// 运行预测
const runPrediction = async () => {
  // if (!previewData.value) return
  if (!fileId.value) return
  
  isPredicting.value = true
  try {
    const response = await axios.post('/api/predict', {
      file_id:fileId.value
    })
    // console.log(response)
    ElMessage.success('预测完成！')
    emit('prediction-complete', response.data)
    showDownload.value = true

  } catch (error) {
    ElMessage.error(`分析失败: ${error.response?.data?.error || error.message}`)
  } finally {
    isPredicting.value = false
  }
}

const downloadPredictionCSV = async () => {
  if (!fileId.value || isDownloading.value) return
  isDownloading.value = true
  try {
    const downloadUrlPrediction = `/api/download?file_id=${encodeURIComponent(fileId.value)}`
    
    // 1. 使用 fetch API 获取文件数据（responseType 为 blob）
    const response = await fetch(downloadUrlPrediction)
    
    // 检查请求是否成功
    if (!response.ok) {
      throw new Error(`下载失败: ${response.status} ${response.statusText}`)
    }
    
    // 2. 将响应转换为 Blob 对象
    const blob = await response.blob()
    
    // 3. 创建一个指向该 Blob 的临时 URL
    const blobUrl = window.URL.createObjectURL(blob)
    
    // 4. 动态创建隐藏的 <a> 标签并触发点击
    const link = document.createElement('a')
    link.href = blobUrl
    // 从响应头中提取文件名，或使用默认文件名
    const contentDisposition = response.headers.get('content-disposition')
    let filename = `衰弱预测结果_${fileId.value}.csv`
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/i)
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1]
      }
    }
    link.download = filename // 设置下载的文件名
    
    // 5. 触发下载
    document.body.appendChild(link) // 临时添加到DOM
    link.click() // 模拟点击
    document.body.removeChild(link) // 移除
    
    // 6. 释放 URL 对象占用的内存
    window.URL.revokeObjectURL(blobUrl)
    
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error(`下载失败: ${error.response?.data?.error || error.message}`)
  } finally {
    isDownloading.value = false
  }
}

const clearData = () => {
  previewData.value = null
  previewColumns.value = []
  rowCount.value = 0
  URL.revokeObjectURL(downloadUrl.value)
  downloadUrl.value = ''
  URL.revokeObjectURL(downloadUrlPrediction.value)
  downloadUrlPrediction.value = ''
  downloadFileName.value = ''
  isPredicting.value = false 
  uploadedFile.value = null
  fileId.value=null
  showDownload.value=false

}

const downloadSample = () => {
  // 这里可以生成示例CSV文件
//   const sampleData = `patient_id,age,gender,systolic_bp,diastolic_bp,gait_speed,grip_strength,bmi,comorbidities,medication_count
// P001,72,M,145,88,0.8,28,24.5,2,3
// P002,68,F,130,85,1.0,22,26.1,1,2
// P003,81,M,160,95,0.6,18,22.8,3,5`
  
//   const blob = new Blob([sampleData], { type: 'text/csv' })
//   const url = window.URL.createObjectURL(blob)
//   const a = document.createElement('a')
//   a.href = url
//   a.download = 'frailty_sample_data.csv'
//   a.click()
  const link = document.createElement('a');
  link.href = '../../data/SampleFile.csv'; // 假设文件在服务器的根目录下的data文件夹
  link.download = 'frailty_sample_data.csv'; // 可选，指定下载的文件名
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
</script>

<style scoped>
.upload-container {
  display: flex;
  gap: 30px;
  flex-wrap: wrap;
  
}

.upload-card {
  flex: 1;
  min-width: 500px;
  font-size:18px
}

.sample-card {
  width: 300px;
}

.card-header .subtitle {
  color: #666;
  font-size: 16px;
  margin-top: 5px;
}

.upload-demo {
  margin: 20px 0;
}

.preview-section {
  margin-top: 30px;
}

.upload-stats {
  margin: 15px 0;
}

.action-buttons {
  margin-top: 20px;
}

.sample-tag {
  margin: 5px 8px 5px 0;
}
.download-section {
  margin-top: 15px;
  padding: 10px;
  background-color: #f0f9ff;
  border-radius: 6px;
  border-left: 4px solid #409eff;
}

.download-section p {
  margin: 0 0 10px 0;
  color: #333;
  font-weight: 500;
}
.download-link {
  display: inline-block;
  margin-top: 8px;
  padding: 8px 16px;
  background-color: #409eff;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-weight: 500;
}

.download-link:hover {
  background-color: #337ecc;
}
</style>