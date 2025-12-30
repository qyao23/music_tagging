<template>
  <div class="tagging-container">
    <div v-if="currentTask" class="tagging-content">
      <div class="music-info">
        <h2>{{ currentTask.music.filepath }}</h2>
        <p v-if="duration > 0">时长: {{ formatDuration(duration) }}</p>
      </div>

      <div class="audio-player">
        <audio
          ref="audioRef"
          :src="audioUrl"
          controls
          @ended="handleAudioEnded"
          @error="handleAudioError"
          @loadedmetadata="handleLoadedMetadata"
        >
          您的浏览器不支持音频播放
        </audio>
        <div v-if="audioError" class="audio-error">
          <el-alert
            :title="audioError"
            type="warning"
            :closable="false"
            show-icon
          >
            <template #default>
              <p>无法加载音频文件: {{ currentTask.music.filepath }}</p>
              <p>请确保文件路径正确且文件可访问</p>
            </template>
          </el-alert>
        </div>
      </div>

      <div class="questions-section">
        <div
          v-for="(record, index) in currentTask.records"
          :key="record.id"
          class="question-item"
          :class="{ active: currentQuestionIndex === index }"
        >
          <div class="question-header">
            <h3>题目 {{ index + 1 }}: {{ record.question.title }}</h3>
            <el-tag :type="record.question.is_multiple_choice ? 'success' : 'info'">
              {{ record.question.is_multiple_choice ? '多选题' : '单选题' }}
            </el-tag>
          </div>
          <p v-if="record.question.description" class="question-description">
            {{ record.question.description }}
          </p>
          <div class="options">
            <el-checkbox-group
              v-if="record.question.is_multiple_choice"
              v-model="record.selected_options"
            >
              <el-checkbox
                v-for="(option, optIndex) in record.question.options"
                :key="optIndex"
                :label="option"
                class="option-checkbox"
              >
                {{ option }}
              </el-checkbox>
            </el-checkbox-group>
            <el-radio-group
              v-else
              v-model="record.selected_options[0]"
              @change="handleRadioChange(record)"
            >
              <el-radio
                v-for="(option, optIndex) in record.question.options"
                :key="optIndex"
                :value="option"
                class="option-radio"
              >
                {{ option }}
              </el-radio>
            </el-radio-group>
          </div>
        </div>
      </div>

      <div class="actions">
        <el-button
          type="primary"
          size="large"
          @click="handleSave"
          :loading="saving"
        >
          保存当前题目
        </el-button>
        <el-button
          type="success"
          size="large"
          @click="handleFinish"
          :loading="finishing"
          :disabled="!canFinish"
        >
          完成打标
        </el-button>
      </div>
    </div>

    <div v-else class="no-task">
      <el-empty description="暂无待打标任务">
        <el-button type="primary" @click="loadNextTask">刷新</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import {
  getTaggingTaskList,
  tagMusic,
  operateTaggingTask
} from '../api/tagging'
import { API_BASE_URL } from '../api/index'
import type { TaggingTaskResponse, TaggingRecordUpdate } from '../types/interfaces'
import { TaggingStatusEnum, OperationEnum } from '../types/enums'

const userStore = useUserStore()
const taskList = ref<TaggingTaskResponse[]>([])
const currentTask = ref<TaggingTaskResponse | null>(null)
const currentQuestionIndex = ref(0)
const saving = ref(false)
const finishing = ref(false)
const audioRef = ref<HTMLAudioElement | null>(null)
const audioError = ref<string | null>(null)
const duration = ref(0)
const audioUrl = ref<string>('')
let currentBlobUrl: string | null = null

// 加载音频文件
const loadAudio = async (filepath: string) => {
  // 清除之前的错误和 blob URL
  audioError.value = null
  if (currentBlobUrl) {
    URL.revokeObjectURL(currentBlobUrl)
    currentBlobUrl = null
  }
  audioUrl.value = ''
  
  // 如果路径已经是完整的URL（http/https），直接使用
  if (filepath.startsWith('http://') || filepath.startsWith('https://')) {
    audioUrl.value = filepath
    return
  }
  
  try {
    // 使用 fetch 获取音频文件，携带认证头
    const token = localStorage.getItem('token')
    const response = await fetch(`${API_BASE_URL}/music/file?path=${encodeURIComponent(filepath)}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    // 创建 blob URL
    const blob = await response.blob()
    currentBlobUrl = URL.createObjectURL(blob)
    audioUrl.value = currentBlobUrl
    
    // 等待音频元素加载，检查是否真的可以播放
    if (audioRef.value) {
      audioRef.value.load()
      // 监听 canplay 事件，如果能播放就清除错误
      const onCanPlay = () => {
        audioError.value = null
        audioRef.value?.removeEventListener('canplay', onCanPlay)
      }
      // 监听 loadedmetadata 事件，清除可能的错误
      const onLoadedMetadata = () => {
        audioError.value = null
        audioRef.value?.removeEventListener('loadedmetadata', onLoadedMetadata)
      }
      audioRef.value.addEventListener('canplay', onCanPlay)
      audioRef.value.addEventListener('loadedmetadata', onLoadedMetadata)
    }
  } catch (error) {
    console.error('Failed to load audio:', error)
    audioError.value = '无法加载音频文件，请检查文件路径和权限'
    audioUrl.value = ''
  }
}

// 格式化时长（只显示到秒，不显示小数）
const formatDuration = (seconds: number) => {
  const totalSeconds = Math.floor(seconds) // 向下取整，只保留整数秒
  const mins = Math.floor(totalSeconds / 60)
  const secs = totalSeconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 检查是否可以完成打标
const canFinish = computed(() => {
  if (!currentTask.value) return false
  return currentTask.value.records.every(
    record => record.selected_options && record.selected_options.length > 0
  )
})

// 加载待打标任务列表
const loadTaskList = async () => {
  try {
    const response = await getTaggingTaskList({ page: 1, page_size: 100 })
    if (response.data) {
      // 适配新的分页返回格式
      const items = response.data.items || []
      // 过滤出当前用户的待打标任务（管理员可以看到所有任务）
      const pendingTasks = items.filter(
        task => (task.status === TaggingStatusEnum.PENDING || task.status === TaggingStatusEnum.REJECTED) &&
                (task.tagger.id === userStore.user?.id || userStore.isAdmin)
      )
      taskList.value = pendingTasks
      
      // 如果有任务，加载第一个
      if (pendingTasks.length > 0 && !currentTask.value) {
        const firstTask = pendingTasks[0]
        if (firstTask) {
          currentTask.value = firstTask
          currentQuestionIndex.value = 0
          duration.value = 0 // 重置时长，等待音频加载
          // 加载音频文件
          await loadAudio(firstTask.music.filepath)
        }
      } else if (pendingTasks.length === 0) {
        currentTask.value = null
        duration.value = 0
        audioUrl.value = ''
      }
    }
  } catch (error) {
    // 错误已在拦截器中处理
  }
}

// 加载下一个任务
const loadNextTask = async () => {
  await loadTaskList()
}

// 处理单选变化
const handleRadioChange = (record: any) => {
  // 单选时，确保selected_options是数组且只有一个元素
  if (record.selected_options && record.selected_options.length > 0) {
    record.selected_options = [record.selected_options[0]]
  }
}

// 保存当前题目
const handleSave = async () => {
  if (!currentTask.value) return
  
  const record = currentTask.value.records[currentQuestionIndex.value]
  if (!record) {
    ElMessage.warning('记录不存在')
    return
  }
  if (!record.selected_options || record.selected_options.length === 0) {
    ElMessage.warning('请先选择答案')
    return
  }

  saving.value = true
  try {
    await tagMusic({
      id: record.id,
      selected_options: record.selected_options
    })
    ElMessage.success('保存成功')
    
    // 自动跳转到下一个题目
    if (currentQuestionIndex.value < currentTask.value.records.length - 1) {
      currentQuestionIndex.value++
    }
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    saving.value = false
  }
}

// 完成打标
const handleFinish = async () => {
  if (!currentTask.value) return
  
  // 先保存所有未保存的题目
  for (let i = 0; i < currentTask.value.records.length; i++) {
    const record = currentTask.value.records[i]
    if (!record) continue
    if (record.selected_options && record.selected_options.length > 0) {
      try {
        await tagMusic({
          id: record.id,
          selected_options: record.selected_options
        })
      } catch (error) {
        ElMessage.error(`保存题目 ${i + 1} 失败`)
        return
      }
    }
  }

  finishing.value = true
  try {
    await operateTaggingTask({
      operation: OperationEnum.FINISH,
      id: currentTask.value.id
    })
    ElMessage.success('打标完成')
    
    // 加载下一个任务
    await loadNextTask()
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    finishing.value = false
  }
}

// 处理音频播放结束
const handleAudioEnded = () => {
  // 音频播放结束后可以自动播放下一首或提示
}

// 处理音频元数据加载
const handleLoadedMetadata = () => {
  if (audioRef.value) {
    duration.value = audioRef.value.duration || 0
  }
}

// 处理音频加载错误
const handleAudioError = (event: Event) => {
  const audio = event.target as HTMLAudioElement
  if (!audio || !audio.error) {
    return
  }
  
  // 延迟检查，给音频一些时间加载
  setTimeout(() => {
    // 如果音频已经可以播放，清除错误
    if (audio.readyState >= 2 || !audio.error) {
      audioError.value = null
      return
    }
    
    // 检查错误类型
    const error = audio.error
    let errorMessage = '音频加载失败'
    
    switch (error.code) {
      case MediaError.MEDIA_ERR_ABORTED:
        // 加载被中止通常不是真正的错误，可能是用户操作或切换任务
        return
      case MediaError.MEDIA_ERR_NETWORK:
        errorMessage = '网络错误，无法加载音频'
        break
      case MediaError.MEDIA_ERR_DECODE:
        errorMessage = '音频解码失败'
        break
      case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
        errorMessage = '不支持的音频格式或文件路径无法访问'
        break
    }
    
    // 只有在确实无法播放时才显示错误
    if (audio.readyState === 0 && audio.error) {
      audioError.value = errorMessage
      console.error('Audio error:', errorMessage, currentTask.value?.music.filepath)
    }
  }, 5000) // 延迟5秒检查，给音频足够时间加载
}

// 监听任务变化，自动加载音频
watch(() => currentTask.value?.music.filepath, (newFilepath) => {
  if (newFilepath) {
    loadAudio(newFilepath)
  }
})

onMounted(() => {
  loadTaskList()
})
</script>

<style scoped>
.tagging-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.tagging-content {
  background: white;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.music-info {
  margin-bottom: 20px;
  text-align: center;
}

.music-info h2 {
  margin: 0 0 10px 0;
  color: #409eff;
}

.audio-player {
  margin: 30px 0;
  display: flex;
  justify-content: center;
}

.audio-player {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.audio-player audio {
  width: 100%;
  max-width: 600px;
}

.audio-error {
  margin-top: 15px;
  width: 100%;
  max-width: 600px;
}

.questions-section {
  margin: 30px 0;
}

.question-item {
  margin-bottom: 30px;
  padding: 20px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  transition: all 0.3s;
}

.question-item.active {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.question-header h3 {
  margin: 0;
  color: #303133;
}

.question-description {
  color: #606266;
  margin-bottom: 15px;
}

.options {
  margin-top: 15px;
}

.option-checkbox,
.option-radio {
  display: block;
  margin-bottom: 10px;
  padding: 10px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.option-checkbox:hover,
.option-radio:hover {
  background-color: #f5f7fa;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 30px;
}

.no-task {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}
</style>

