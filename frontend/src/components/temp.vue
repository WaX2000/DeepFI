<template>
  <div class="report-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>📄 报告管理</h3>
          <div class="header-actions">
            <el-button 
              type="primary" 
              @click="openUploadDialog" 
              icon="Upload"
            >
              上传个人指标
            </el-button>
            <el-button 
              type="success" 
              @click="generateReport" 
              :loading="generating"
              :disabled="!currentPatientData"
              icon="DocumentAdd"
            >
              生成个人报告
            </el-button>
            <el-button 
              @click="previewReport" 
              :disabled="!currentReport"
              icon="View"
            >
              预览报告
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 个人信息卡片 -->
      <div v-if="currentPatientData" class="patient-info-card">
        <el-card shadow="hover">
          <template #header>
            <div class="patient-header">
              <span>👤 当前患者信息</span>
              <el-button type="text" @click="openUploadDialog">重新上传</el-button>
            </div>
          </template>
          <el-descriptions :column="3" border>
            <el-descriptions-item label="年龄">{{ currentPatientData.age || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="性别">{{ currentPatientData.gender || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="BMI">{{ currentPatientData.BMI || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="吸烟史">{{ currentPatientData.current_tobacco_smoking || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="饮酒习惯">{{ currentPatientData.alcohol_intake_frequency || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="睡眠质量">{{ currentPatientData.sleeplessness || '未填写' }}</el-descriptions-item>
          </el-descriptions>
          <div class="fi-display" v-if="currentPatientData.fi_value">
            <span class="fi-label">预测衰弱指数：</span>
            <span class="fi-value">{{ currentPatientData.fi_value }}</span>
            <el-tag :type="getRiskLevel(currentPatientData.fi_value).type" size="small">
              {{ getRiskLevel(currentPatientData.fi_value).label }}
            </el-tag>
          </div>
        </el-card>
      </div>
      
      <p>此处将展示已生成的报告历史记录。</p>
      
      <el-alert v-if="reportHistory.length === 0" title="暂无报告记录，请先上传个人指标并生成报告。" type="info" show-icon />
      
      <el-table v-else :data="reportHistory" style="width: 100%">
        <el-table-column prop="timestamp" label="生成时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.timestamp).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="patientCount" label="分析人数" width="100">
          <template #default>1</template>
        </el-table-column>
        <el-table-column prop="title" label="报告标题" width="200" />
        <el-table-column prop="patientName" label="患者信息" width="200">
          <template #default="{ row }">
            {{ row.patientInfo?.age }}岁 {{ row.patientInfo?.gender }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button type="text" size="small" @click="previewSpecificReport(row)">
              查看
            </el-button>
            <el-button type="text" size="small" @click="downloadReport(row)">
              下载PDF
            </el-button>
            <el-button type="text" size="small" @click="deleteReport(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 上传个人指标对话框 -->
    <el-dialog 
      v-model="uploadVisible" 
      title="上传个人指标记录" 
      width="80%"
      :close-on-click-modal="false"
    >
      <div class="single-upload-container">
        <div class="upload-methods">
          <el-radio-group v-model="uploadMethod" @change="changeUploadMethod">
            <el-radio label="form">表单填写</el-radio>
            <el-radio label="file">文件上传</el-radio>
          </el-radio-group>
        </div>

        <!-- 表单填写方式 -->
        <div v-if="uploadMethod === 'form'" class="form-upload">
          <el-form :model="patientForm" label-width="150px" :rules="patientRules" ref="patientFormRef" class="patient-form">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="年龄" prop="age">
                  <el-input-number v-model="patientForm.age" :min="20" :max="120" placeholder="请输入年龄" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="性别" prop="gender">
                  <el-select v-model="patientForm.gender" placeholder="请选择性别">
                    <el-option label="男" value="male" />
                    <el-option label="女" value="female" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="BMI" prop="BMI">
                  <el-input-number v-model="patientForm.BMI" :min="15" :max="50" :step="0.1" placeholder="请输入BMI" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-divider>生活习惯</el-divider>
            
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="吸烟情况" prop="current_tobacco_smoking">
                  <el-select v-model="patientForm.current_tobacco_smoking" placeholder="请选择">
                    <el-option label="从不吸烟" value="Never smoked" />
                    <el-option label="过去吸烟" value="Previous smoker" />
                    <el-option label="现在偶尔吸烟" value="Current occasional smoker" />
                    <el-option label="现在每天吸烟" value="Current daily smoker" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="饮酒频率" prop="alcohol_intake_frequency">
                  <el-select v-model="patientForm.alcohol_intake_frequency" placeholder="请选择">
                    <el-option label="从不喝酒" value="Never" />
                    <el-option label="特殊场合" value="Special occasions only" />
                    <el-option label="每月1-3次" value="One to three times a month" />
                    <el-option label="每周1-2次" value="Once or twice a week" />
                    <el-option label="每周3-4次" value="Three or four times a week" />
                    <el-option label="几乎每天" value="Daily or almost daily" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="睡眠质量" prop="sleeplessness">
                  <el-select v-model="patientForm.sleeplessness" placeholder="请选择">
                    <el-option label="从不/很少" value="Never/rarely" />
                    <el-option label="有时" value="Sometimes" />
                    <el-option label="经常" value="Usually" />
                    <el-option label="总是" value="Always" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="打鼾" prop="Snoring">
                  <el-select v-model="patientForm.Snoring" placeholder="请选择">
                    <el-option label="是" value="Yes" />
                    <el-option label="否" value="No" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="看电视时长" prop="Time_spent_watching_TV">
                  <el-select v-model="patientForm.Time_spent_watching_TV" placeholder="请选择">
                    <el-option label="少于1小时" value="Less than 1 hour" />
                    <el-option label="1-2小时" value="1-2 hours" />
                    <el-option label="3-4小时" value="3-4 hours" />
                    <el-option label="4小时以上" value="More than 4 hours" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="倾诉能力" prop="Able_to_confide">
                  <el-select v-model="patientForm.Able_to_confide" placeholder="请选择">
                    <el-option label="完全不能" value="Not at all" />
                    <el-option label="有一点" value="A little" />
                    <el-option label="相当能" value="Quite a bit" />
                    <el-option label="完全能" value="Completely" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-divider>健康状况</el-divider>
            
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="胸痛不适" prop="Chest_pain_or_discomfort">
                  <el-select v-model="patientForm.Chest_pain_or_discomfort" placeholder="请选择">
                    <el-option label="无" value="No" />
                    <el-option label="有" value="Yes" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="听力问题" prop="Hearing_difficulty">
                  <el-select v-model="patientForm.Hearing_difficulty" placeholder="请选择">
                    <el-option label="无" value="No" />
                    <el-option label="有" value="Yes" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="步速" prop="Usual_walking_pace">
                  <el-select v-model="patientForm.Usual_walking_pace" placeholder="请选择">
                    <el-option label="慢" value="Slow pace" />
                    <el-option label="中等" value="Average pace" />
                    <el-option label="快" value="Brisk pace" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
          
          <div class="form-actions">
            <el-button @click="resetForm">重置</el-button>
            <el-button type="primary" @click="submitForm" :loading="isUploading">
              提交并预测
            </el-button>
          </div>
        </div>

        <!-- 文件上传方式 -->
        <div v-else class="file-upload">
          <div class="upload-section">
            <el-upload
              class="upload-demo"
              drag
              action="/api/upload-single"
              :on-success="handleUploadSuccess"
              :on-error="handleUploadError"
              :before-upload="beforeSingleUpload"
              :show-file-list="false"
              accept=".csv,.xlsx,.xls"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                拖拽文件到此处或 <em>点击上传</em>
              </div>
              <div class="el-upload__tip">
                只能上传单条记录（1行数据），支持CSV或Excel格式
              </div>
            </el-upload>
          </div>

          <!-- 数据预览 -->
          <div v-if="previewData" class="preview-section">
            <h3>数据预览</h3>
            <el-table :data="previewData" border style="width: 100%; margin-top: 15px;">
              <el-table-column 
                v-for="col in previewColumns" 
                :key="col"
                :prop="col" 
                :label="col"
                min-width="120"
              />
            </el-table>
            
            <div class="action-buttons">
              <el-button type="primary" 
                        @click="runSinglePrediction" 
                        :loading="isPredicting">
                {{ isPredicting ? '预测中...' : '预测衰弱指数' }}
              </el-button>
              <el-button @click="clearData">清除</el-button>
            </div> 
          </div>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="uploadVisible = false">取消</el-button>
          <el-button v-if="uploadMethod === 'form'" type="primary" @click="submitForm" :loading="isUploading">
            提交
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 报告预览对话框 -->
    <el-dialog 
      v-model="previewVisible" 
      title="报告预览" 
      width="80%" 
      fullscreen
      :close-on-click-modal="false"
    >
      <div v-if="previewContent" class="report-preview">
        <div class="preview-toolbar">
          <el-button type="primary" @click="downloadCurrentReport" icon="Download">
            下载PDF
          </el-button>
          <el-button @click="copyReportContent" icon="CopyDocument">
            复制内容
          </el-button>
          <el-button @click="printReport" icon="Printer">
            打印
          </el-button>
        </div>
        
        <div class="report-content" v-html="renderedReport"></div>
      </div>
      <div v-else class="no-preview">
        暂无报告内容可预览
      </div>
      
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import axios from 'axios'

// 使用简单的markdown转换函数
const simpleMarkdownToHtml = (text) => {
  if (!text) return ''
  
  let html = text
  
  // 替换标题
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>')
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>')
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>')
  
  // 替换粗体
  html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
  
  // 替换斜体
  html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>')
  
  // 替换代码
  html = html.replace(/`(.*?)`/gim, '<code>$1</code>')
  
  // 替换列表
  html = html.replace(/^\* (.*$)/gim, '<li>$1</li>')
  html = html.replace(/<li>(.*?)<\/li>/gim, '<ul><li>$1</li></ul>')
  
  // 简单表格处理
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
      
      // 处理表头分割线
      if (line.includes('---')) {
        continue
      }
      
      const cells = line.split('|').filter(cell => cell.trim() !== '')
      tableHtml += '<tr>'
      
      for (const cell of cells) {
        if (i === 0) {
          tableHtml += `<th>${cell.trim()}</th>`
        } else {
          tableHtml += `<td>${cell.trim()}</td>`
        }
      }
      
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
  
  // 替换换行符
  html = html.replace(/\n/g, '<br>')
  
  return html
}

// 状态管理
const currentPatientData = ref(null)
const currentReport = ref(null)
const reportHistory = ref([])
const previewVisible = ref(false)
const previewContent = ref('')
const generating = ref(false)
const uploadVisible = ref(false)
const uploadMethod = ref('form')
const isUploading = ref(false)

// 表单填写相关
const patientFormRef = ref(null)
const patientForm = ref({
  age: '',
  gender: '',
  BMI: '',
  current_tobacco_smoking: '',
  alcohol_intake_frequency: '',
  sleeplessness: '',
  Snoring: '',
  Time_spent_watching_TV: '',
  Able_to_confide: '',
  Chest_pain_or_discomfort: '',
  Hearing_difficulty: '',
  Usual_walking_pace: ''
})

const patientRules = {
  age: [{ required: true, message: '请输入年龄', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  BMI: [{ required: true, message: '请输入BMI', trigger: 'blur' }]
}

// 文件上传相关
const previewData = ref(null)
const previewColumns = ref([])
const isPredicting = ref(false)
const uploadedFile = ref(null)
const fileId = ref(null)

const renderedReport = computed(() => {
  return simpleMarkdownToHtml(previewContent.value)
})

// 风险评估函数
const getRiskLevel = (fiValue) => {
  if (!fiValue) return { type: 'info', label: '未评估' }
  if (fiValue < 0.1) return { type: 'success', label: '低风险' }
  if (fiValue < 0.2) return { type: 'warning', label: '中风险' }
  return { type: 'danger', label: '高风险' }
}

// 打开上传对话框
const openUploadDialog = () => {
  uploadVisible.value = true
}

// 切换上传方式
const changeUploadMethod = () => {
  if (uploadMethod.value === 'form') {
    resetForm()
  } else {
    clearData()
  }
}

// 重置表单
const resetForm = () => {
  if (patientFormRef.value) {
    patientFormRef.value.resetFields()
  }
}

// 提交表单数据
const submitForm = async () => {
  if (!patientFormRef.value) return
  
  try {
    await patientFormRef.value.validate()
    isUploading.value = true
    
    // 构建患者数据
    const patientData = {
      ...patientForm.value,
      // 添加一些默认值
      Past_tobacco_smoking: patientForm.value.current_tobacco_smoking === 'Previous smoker' ? 'Previous smoker' : 'Never smoked',
      Chest_pain_or_discomfort_walking_normally: patientForm.value.Chest_pain_or_discomfort,
      Hearing_difficulty_with_background_noise: patientForm.value.Hearing_difficulty,
      Time_spend_outdoors_in_summer: '8 hours or more',
      Hand_grip_strength_left: 30, // 默认值
      Forced_expiratory_volume_in_1_second: 3.0, // 默认值
      Waist_circumference: 90, // 默认值
      Hip_circumference: 100, // 默认值
      Whole_body_fat_mass: 25, // 默认值
    }
    
    // 调用后端预测接口
    const response = await axios.post('/api/predict-single', patientData)
    
    if (response.data.success) {
      const predictionResult = response.data.data
      currentPatientData.value = {
        ...patientData,
        fi_value: predictionResult.fi_value,
        disease_list: predictionResult.disease_list,
        risk_level: getRiskLevel(predictionResult.fi_value).label
      }
      
      ElMessage.success('数据提交成功！')
      uploadVisible.value = false
      
      // 自动生成报告
      await generateReport()
    } else {
      throw new Error(response.data.message || '预测失败')
    }
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error(`提交失败: ${error.message}`)
  } finally {
    isUploading.value = false
  }
}

// 文件上传相关函数
const beforeSingleUpload = (file) => {
  console.log('🔍 [beforeSingleUpload] 开始校验单条记录上传')
  
  // 校验文件类型
  const isValidType = file.name.match(/\.(csv|xlsx|xls)$/i)
  if (!isValidType) {
    ElMessage.error('仅支持CSV或Excel文件（.csv, .xlsx, .xls）')
    return false
  }
  
  // 校验文件大小
  const MAX_SIZE = 10 * 1024 * 1024 // 10MB限制，因为是单条记录
  if (file.size > MAX_SIZE) {
    const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2)
    ElMessage.error(`文件大小不能超过10MB！当前文件为 ${fileSizeMB} MB。`)
    return false
  }
  
  uploadedFile.value = file
  return true
}

const handleUploadSuccess = (response) => {
  console.log('文件上传成功:', response)
  
  if (response.error) {
    ElMessage.error(response.error)
    return
  }
  
  // 检查是否是单条记录
  if (response.rows > 1) {
    ElMessage.warning('检测到多条记录，将只使用第一条记录进行分析')
  }
  
  previewData.value = response.preview
  previewColumns.value = response.columns
  fileId.value = response.file_id
  
  ElMessage.success(`文件上传成功，共 ${response.rows} 条记录`)
}

const handleUploadError = (error) => {
  console.error('上传失败:', error)
  ElMessage.error(`文件上传失败：${error.message || '网络或服务器错误'}`)
}

// 单条记录预测
const runSinglePrediction = async () => {
  if (!fileId.value) return
  
  isPredicting.value = true
  try {
    const response = await axios.post('/api/predict-single', {
      file_id: fileId.value
    })
    
    if (response.data.success) {
      const predictionResult = response.data.data
      
      // 从预览数据中获取第一条记录
      const firstRow = previewData.value[0]
      const patientData = {}
      previewColumns.value.forEach((col, index) => {
        patientData[col] = firstRow[index]
      })
      
      currentPatientData.value = {
        ...patientData,
        fi_value: predictionResult.fi_value,
        disease_list: predictionResult.disease_list,
        risk_level: getRiskLevel(predictionResult.fi_value).label
      }
      
      ElMessage.success('预测完成！')
      uploadVisible.value = false
      
      // 自动生成报告
      await generateReport()
    } else {
      throw new Error(response.data.message || '预测失败')
    }
  } catch (error) {
    console.error('预测失败:', error)
    ElMessage.error(`分析失败: ${error.message}`)
  } finally {
    isPredicting.value = false
  }
}

const clearData = () => {
  previewData.value = null
  previewColumns.value = []
  fileId.value = null
  uploadedFile.value = null
}

// 生成报告函数
const generateReport = async () => {
  try {
    if (!currentPatientData.value) {
      ElMessage.warning('请先上传个人指标数据')
      openUploadDialog()
      return
    }
    
    generating.value = true
    
    // 构建请求数据
    const requestData = {
      model: "deepseek-reasoner",
      messages: [
        {
          "role": "system",
          "content": `你是一个智能医疗报告生成系统。任务是根据提供的患者数据和衰弱指数(FI)生成结构化临床报告。请遵循以下规则：
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
        },
        {
          "role": "user",
          "content": formatPatientDataForReport(currentPatientData.value)
        }
      ],
      stream: false
    }

    // 调用后端API
    const response = await axios.post('http://localhost:5002/api/generate-report', requestData, {
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (response.data.success) {
      const reportData = response.data.data
      
      // 创建新的报告对象
      const newReport = {
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        patientCount: 1,
        title: `个人衰弱指数报告 - ${currentPatientData.value.age}岁${currentPatientData.value.gender === 'male' ? '男' : '女'}`,
        content: reportData.markdown,
        htmlContent: reportData.html,
        patientInfo: {
          age: currentPatientData.value.age,
          gender: currentPatientData.value.gender === 'male' ? '男' : '女',
          fi_value: currentPatientData.value.fi_value
        }
      }
      
      // 添加到历史记录
      reportHistory.value.unshift(newReport)
      currentReport.value = newReport
      
      // 自动预览
      previewContent.value = reportData.markdown
      previewVisible.value = true
      
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

// 格式化患者数据用于报告生成
const formatPatientDataForReport = (patientData) => {
  // 这里需要根据你的实际数据结构进行格式化
  // 以下是一个示例格式
  return `患者数据：
            - 基本信息：${patientData.gender === 'male' ? '男' : '女'}性｜${patientData.age}岁
            - 行为指标： 吸烟：${patientData.current_tobacco_smoking || '未提供'},
                        饮酒：${patientData.alcohol_intake_frequency || '未提供'},
                        睡眠：${patientData.sleeplessness || '未提供'},
                        BMI：${patientData.BMI || '未提供'},
                        打鼾：${patientData.Snoring || '未提供'},
                        胸痛：${patientData.Chest_pain_or_discomfort || '未提供'},
                        听力：${patientData.Hearing_difficulty || '未提供'},
                        步速：${patientData.Usual_walking_pace || '未提供'},
                        倾诉：${patientData.Able_to_confide || '未提供'},
                        电视：${patientData.Time_spent_watching_TV || '未提供'}
            - 衰弱指数：${patientData.fi_value || 0}，
            - 预警疾病：${(patientData.disease_list || ['神经退行性疾病', '抑郁症', '心血管疾病', '2型糖尿病']).join('、')}

            请生成包含以下结构的报告：
            # 衰弱指数临床报告

            ## 患者概况
            - 人口学特征
            - 关键行为指标
            - FI在人群中的位置

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

// 其他函数保持不变
const previewReport = () => {
  if (currentReport.value) {
    previewContent.value = currentReport.value.content
    previewVisible.value = true
  }
}

const previewSpecificReport = (report) => {
  previewContent.value = report.content
  currentReport.value = report
  previewVisible.value = true
}

const downloadReport = async (report) => {
  try {
    const response = await axios.post('http://localhost:5002/api/convert-to-pdf', {
      markdown: report.content,
      filename: `个人衰弱指数报告_${report.id}`
    }, {
      responseType: 'blob'
    })
    
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

const downloadCurrentReport = () => {
  if (currentReport.value) {
    downloadReport(currentReport.value)
  }
}

const copyReportContent = async () => {
  try {
    await navigator.clipboard.writeText(previewContent.value)
    ElMessage.success('报告内容已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
}

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

const deleteReport = (report) => {
  ElMessageBox.confirm(
    '确定要删除这份报告吗？此操作不可撤销。',
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    const index = reportHistory.value.findIndex(r => r.id === report.id)
    if (index !== -1) {
      reportHistory.value.splice(index, 1)
      ElMessage.success('报告已删除')
      
      if (currentReport.value && currentReport.value.id === report.id) {
        currentReport.value = null
        previewContent.value = ''
      }
    }
  }).catch(() => {
    // 用户取消
  })
}

onMounted(() => {
  const savedHistory = localStorage.getItem('reportHistory')
  if (savedHistory) {
    try {
      reportHistory.value = JSON.parse(savedHistory)
      if (reportHistory.value.length > 0) {
        currentReport.value = reportHistory.value[0]
      }
    } catch (error) {
      console.error('加载报告历史失败:', error)
    }
  }
})
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

.patient-info-card {
  margin-bottom: 20px;
}

.patient-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.fi-display {
  margin-top: 15px;
  padding: 10px;
  background: #f0f9ff;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.fi-label {
  font-weight: 500;
  color: #606266;
}

.fi-value {
  font-size: 18px;
  font-weight: 600;
  color: #409eff;
}

.single-upload-container {
  max-height: 70vh;
  overflow-y: auto;
  padding: 10px;
}

.upload-methods {
  margin-bottom: 20px;
}

.form-upload {
  padding: 10px;
}

.patient-form {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 10px;
}

.form-actions {
  margin-top: 20px;
  text-align: right;
}

.file-upload {
  padding: 10px;
}

.upload-section {
  margin: 20px 0;
}

.preview-section {
  margin-top: 20px;
}

.action-buttons {
  margin-top: 20px;
  text-align: right;
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

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
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
    justify-content: flex-end;
  }
}
</style>