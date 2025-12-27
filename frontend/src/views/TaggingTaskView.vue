<template>
  <div class="tagging-task-container">
    <!-- 打标任务列表视图 -->
    <div v-if="!currentTask" class="task-list-view">
      <div class="header">
        <h2>打标任务管理</h2>
        <div class="header-right">
          <el-radio-group v-if="userStore.isAdmin" v-model="viewMode" @change="handleViewModeChange" style="margin-right: 10px">
            <el-radio-button label="all">全部任务</el-radio-button>
            <el-radio-button label="myTagging">我的打标</el-radio-button>
            <el-radio-button label="myReview">我的审核</el-radio-button>
          </el-radio-group>
          <el-button
            v-if="userStore.isAdmin"
            type="primary"
            @click="handleCreate"
          >
            创建打标任务
          </el-button>
        </div>
      </div>

      <div class="search-bar">
        <el-input
          v-model="filters.keyword"
          placeholder="搜索音乐文件名、打标员、审核员"
          clearable
          style="width: 300px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select
          v-model="filters.status"
          placeholder="状态"
          clearable
          style="width: 150px"
        >
          <el-option label="待打标" :value="TaggingStatusEnum.PENDING" />
          <el-option label="已打标" :value="TaggingStatusEnum.TAGGED" />
          <el-option label="已审核通过" :value="TaggingStatusEnum.REVIEWED" />
          <el-option label="审核未通过" :value="TaggingStatusEnum.REJECTED" />
        </el-select>
      </div>

      <el-table
        :data="taskList"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="music.filename" label="音乐文件名" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="tagger.username" label="打标员" width="120" />
        <el-table-column prop="reviewer?.username" label="审核员" width="120" />
        <el-table-column label="题目数量" width="100">
          <template #default="{ row }">
            {{ row.records.length }}
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" width="180" />
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="(userStore.isTagger || userStore.isAdmin) && (row.status === TaggingStatusEnum.PENDING || row.status === TaggingStatusEnum.REJECTED) && (row.tagger.id === userStore.user?.id || userStore.isAdmin)"
              type="primary"
              size="small"
              @click="handleStartTagging(row)"
            >
              打标
            </el-button>
            <el-button
              v-if="(userStore.isReviewer || userStore.isAdmin) && row.status === TaggingStatusEnum.TAGGED"
              type="success"
              size="small"
              @click="handleReview(row)"
            >
              审核
            </el-button>
            <el-button
              v-if="userStore.isAdmin"
              type="danger"
              size="small"
              @click="handleDelete(row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 打标界面 -->
    <div v-else class="tagging-view">
      <div class="tagging-header">
        <el-button @click="handleBackToList" type="info" size="small">
          ← 返回任务列表
        </el-button>
        <h2>打标任务</h2>
        <el-button
          v-if="hasNextTask"
          type="primary"
          size="small"
          @click="handleNextTask"
        >
          下一个任务 →
        </el-button>
      </div>

      <div class="tagging-content">
        <div class="music-info">
          <h3>{{ currentTask.music.filename }}</h3>
          <p>时长: {{ formatDuration(currentTask.music.duration) }}</p>
        </div>

        <div class="audio-player">
          <audio
            ref="audioRef"
            :src="audioUrl"
            @ended="handleAudioEnded"
            @error="handleAudioError"
            @timeupdate="handleTimeUpdate"
            @loadedmetadata="handleLoadedMetadata"
            v-loading="audioLoading"
          >
            您的浏览器不支持音频播放
          </audio>
          <div class="custom-audio-controls">
            <el-button
              :icon="isPlaying ? 'VideoPause' : 'VideoPlay'"
              @click="togglePlayPause"
              circle
              size="large"
            />
            <div class="progress-container">
              <el-slider
                v-model="currentTime"
                :max="duration"
                :format-tooltip="formatTime"
                @change="(value: number) => handleSeek(value)"
                class="progress-slider"
              />
              <div class="time-display">
                <span>{{ formatTime(currentTime) }}</span>
                <span>/</span>
                <span>{{ formatTime(duration) }}</span>
              </div>
            </div>
            <div class="volume-control">
              <el-button
                :icon="volume > 0 ? 'Microphone' : 'Mute'"
                @click="toggleMute"
                circle
                size="small"
              />
              <el-slider
                v-model="volume"
                :max="100"
                :format-tooltip="(val: number) => `${val}%`"
                @input="handleVolumeChange"
                vertical
                height="80px"
                class="volume-slider"
              />
            </div>
          </div>
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

        <div class="questions-section" v-if="currentTask.records && currentTask.records.length > 0">
          <div
            v-for="(record, index) in currentTask.records"
            :key="record.id"
            class="question-item"
            :class="{ active: currentQuestionIndex === index }"
          >
            <div class="question-header" v-if="record.question">
              <h4>题目 {{ index + 1 }}: {{ record.question.title }}</h4>
              <el-tag :type="record.question.is_multiple_choice ? 'success' : 'info'">
                {{ record.question.is_multiple_choice ? '多选题' : '单选题' }}
              </el-tag>
            </div>
            <p v-if="record.question && record.question.description" class="question-description">
              {{ record.question.description }}
            </p>
            <div class="options" v-if="record.question && record.question.options">
              <el-checkbox-group
                v-if="record.question.is_multiple_choice"
                v-model="record.selected_options"
                @change="() => handleAutoSave(record)"
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
                :model-value="record.selected_options && record.selected_options.length > 0 ? record.selected_options[0] : ''"
                @change="(value: string) => handleRadioChange(record, value)"
              >
                <el-radio
                  v-for="(option, optIndex) in record.question.options"
                  :key="optIndex"
                  :label="option"
                  class="option-radio"
                >
                  {{ option }}
                </el-radio>
              </el-radio-group>
            </div>
          </div>
        </div>
        <div v-else class="no-questions">
          <el-alert
            title="暂无题目"
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              <p>该打标任务没有配置题目，请联系管理员添加题目。</p>
            </template>
          </el-alert>
        </div>

        <div class="actions">
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
    </div>

    <!-- 创建打标任务对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="创建打标任务"
      width="700px"
    >
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="100px">
        <el-form-item label="音乐" prop="music_ids">
          <el-select
            v-model="createForm.music_ids"
            placeholder="请选择音乐（可多选，批量创建）"
            multiple
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="music in musicList"
              :key="music.id"
              :label="music.filename"
              :value="music.id"
            />
          </el-select>
          <div style="margin-top: 5px; color: #909399; font-size: 12px;">
            选择多个音乐将批量创建任务，每个音乐都会创建对应的任务
          </div>
        </el-form-item>
        <el-form-item label="打标员" prop="tagger_ids">
          <el-select
            v-model="createForm.tagger_ids"
            placeholder="请选择打标员（可多选，批量创建）"
            multiple
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="user in taggerList"
              :key="user.id"
              :label="user.username"
              :value="user.id"
            />
          </el-select>
          <div style="margin-top: 5px; color: #909399; font-size: 12px;">
            选择多个打标员将批量创建任务，每个打标员都会收到相同的题目和审核员
          </div>
        </el-form-item>
        <el-form-item label="题目" prop="question_ids">
          <el-select
            v-model="createForm.question_ids"
            placeholder="请选择题目（可多选）"
            multiple
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="question in questionList"
              :key="question.id"
              :label="question.title"
              :value="question.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="审核员" prop="reviewer_id">
          <el-select v-model="createForm.reviewer_id" placeholder="请选择审核员" filterable style="width: 100%">
            <el-option
              v-for="user in reviewerList"
              :key="user.id"
              :label="user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 审核对话框 -->
    <el-dialog
      v-model="reviewDialogVisible"
      title="审核打标任务"
      width="900px"
      :close-on-click-modal="false"
    >
      <div v-if="reviewTask" class="review-content">
        <!-- 音乐信息 -->
        <div class="review-music-info">
          <h3>{{ reviewTask.music.filename }}</h3>
          <p>时长: {{ formatDuration(reviewTask.music.duration) }}</p>
          <p>打标员: {{ reviewTask.tagger.username }}</p>
          <p>打标时间: {{ reviewTask.tagging_time || '未完成' }}</p>
        </div>

        <!-- 音乐播放器 -->
        <div class="review-audio-player">
          <audio
            ref="reviewAudioRef"
            :src="reviewAudioUrl"
            @error="handleReviewAudioError"
            @timeupdate="handleReviewTimeUpdate"
            @loadedmetadata="handleReviewLoadedMetadata"
            v-loading="reviewAudioLoading"
          >
            您的浏览器不支持音频播放
          </audio>
          <div class="custom-audio-controls">
            <el-button
              :icon="reviewIsPlaying ? 'VideoPause' : 'VideoPlay'"
              @click="toggleReviewPlayPause"
              circle
              size="large"
            />
            <div class="progress-container">
              <el-slider
                v-model="reviewCurrentTime"
                :max="reviewDuration"
                :format-tooltip="formatTime"
                @change="(value: number) => handleReviewSeek(value)"
                class="progress-slider"
              />
              <div class="time-display">
                <span>{{ formatTime(reviewCurrentTime) }}</span>
                <span>/</span>
                <span>{{ formatTime(reviewDuration) }}</span>
              </div>
            </div>
            <div class="volume-control">
              <el-button
                :icon="reviewVolume > 0 ? 'Microphone' : 'Mute'"
                @click="toggleReviewMute"
                circle
                size="small"
              />
              <el-slider
                v-model="reviewVolume"
                :max="100"
                :format-tooltip="(val: number) => `${val}%`"
                @input="handleReviewVolumeChange"
                vertical
                height="80px"
                class="volume-slider"
              />
            </div>
          </div>
          <div v-if="reviewAudioError" class="audio-error">
            <el-alert
              :title="reviewAudioError"
              type="warning"
              :closable="false"
              show-icon
            />
          </div>
        </div>

        <!-- 题目和打标结果 -->
        <div class="review-questions" v-if="reviewTask.records && reviewTask.records.length > 0">
          <h3>打标结果</h3>
          <div
            v-for="(record, index) in reviewTask.records"
            :key="record.id"
            class="review-question-item"
          >
            <div class="review-question-header" v-if="record.question">
              <h4>题目 {{ index + 1 }}: {{ record.question.title }}</h4>
              <el-tag :type="record.question.is_multiple_choice ? 'success' : 'info'">
                {{ record.question.is_multiple_choice ? '多选题' : '单选题' }}
              </el-tag>
            </div>
            <p v-if="record.question && record.question.description" class="review-question-description">
              {{ record.question.description }}
            </p>
            
            <!-- 显示选项和打标员的选择 -->
            <div class="review-options" v-if="record.question && record.question.options">
              <div
                v-for="(option, optIndex) in record.question.options"
                :key="optIndex"
                class="review-option-item"
                :class="{
                  'selected': record.selected_options && record.selected_options.includes(option),
                  'not-selected': !record.selected_options || !record.selected_options.includes(option)
                }"
              >
                <el-icon v-if="record.selected_options && record.selected_options.includes(option)">
                  <Check />
                </el-icon>
                <span>{{ option }}</span>
                <el-tag
                  v-if="record.selected_options && record.selected_options.includes(option)"
                  type="success"
                  size="small"
                  style="margin-left: 10px"
                >
                  已选择
                </el-tag>
              </div>
            </div>
            
            <div v-if="!record.selected_options || record.selected_options.length === 0" class="no-answer">
              <el-tag type="warning">未作答</el-tag>
            </div>
          </div>
        </div>
        <div v-else class="no-questions">
          <el-alert
            title="暂无题目"
            type="info"
            description="当前任务没有配置任何题目"
            :closable="false"
            show-icon
          />
        </div>

        <!-- 审核表单 -->
        <div class="review-form-section">
          <el-form :model="reviewForm" :rules="reviewRules" ref="reviewFormRef" label-width="100px">
            <el-form-item label="审核结果" prop="result">
              <el-radio-group v-model="reviewForm.result">
                <el-radio :value="ReviewResultEnum.AGREED">通过</el-radio>
                <el-radio :value="ReviewResultEnum.DISAGREED">不通过</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="备注">
              <el-input
                v-model="reviewForm.comment"
                type="textarea"
                :rows="3"
                placeholder="请输入备注（可选）"
              />
            </el-form-item>
          </el-form>
        </div>
      </div>
      <template #footer>
        <el-button @click="reviewDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleReviewSubmit" :loading="loading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Search, Check, VideoPlay, VideoPause, Microphone, Mute } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import {
  getTaggingTaskList,
  operateTaggingTask,
  tagMusic
} from '../api/tagging'
import { getMusicList } from '../api/music'
import { getTaggingQuestionList } from '../api/tagging'
import { getUserList } from '../api/user'
import type {
  TaggingTaskResponse,
  TaggingTaskOperate,
  TaggingRecordUpdate,
  MusicResponse,
  TaggingQuestionResponse,
  UserResponse
} from '../types/interfaces'
import { TaggingStatusEnum, OperationEnum, ReviewResultEnum, UserRoleEnum } from '../types/enums'

const userStore = useUserStore()
const taskList = ref<TaggingTaskResponse[]>([])
const currentTask = ref<TaggingTaskResponse | null>(null)
const currentQuestionIndex = ref(0)
const loading = ref(false)
const saving = ref(false)
const finishing = ref(false)
const audioRef = ref<HTMLAudioElement | null>(null)
const audioError = ref<string | null>(null)
const audioUrl = ref<string>('')
const audioLoading = ref(false)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(100)
let currentBlobUrl: string | null = null

// 视图模式：all-全部任务, myTagging-我的打标, myReview-我的审核
const viewMode = ref<'all' | 'myTagging' | 'myReview'>('all')

// 筛选条件
const filters = reactive({
  keyword: '',
  status: '' as TaggingStatusEnum | ''
})

// 加载音频文件（使用 fetch 携带认证头）
const loadAudioFile = async (filepath: string) => {
  audioError.value = null
  audioLoading.value = true
  
  // 清理旧的 blob URL
  if (currentBlobUrl) {
    URL.revokeObjectURL(currentBlobUrl)
    currentBlobUrl = null
  }
  
  // 如果路径已经是完整的URL（http/https），直接使用
  if (filepath.startsWith('http://') || filepath.startsWith('https://')) {
    audioUrl.value = filepath
    audioLoading.value = false
    return
  }
  
  try {
    // 使用 fetch 获取音频文件，携带认证头
    const token = localStorage.getItem('token')
    const response = await fetch(`http://127.0.0.1:8000/music/file?path=${encodeURIComponent(filepath)}`, {
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
      audioRef.value.addEventListener('canplay', onCanPlay)
      // 监听播放状态变化
      audioRef.value.addEventListener('play', () => {
        isPlaying.value = true
      })
      audioRef.value.addEventListener('pause', () => {
        isPlaying.value = false
      })
      // 设置初始音量
      audioRef.value.volume = volume.value / 100
    }
  } catch (error) {
    console.error('Failed to load audio:', error)
    audioError.value = '无法加载音频文件，请检查文件路径和权限'
    audioUrl.value = ''
  } finally {
    audioLoading.value = false
  }
}

// 格式化时长
const formatDuration = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 格式化时间（用于进度条）
const formatTime = (seconds: number) => {
  if (isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 播放/暂停切换
const togglePlayPause = () => {
  if (!audioRef.value) return
  if (isPlaying.value) {
    audioRef.value.pause()
  } else {
    audioRef.value.play()
  }
  isPlaying.value = !isPlaying.value
}

// 处理时间更新
const handleTimeUpdate = () => {
  if (audioRef.value) {
    currentTime.value = audioRef.value.currentTime
  }
}

// 处理元数据加载
const handleLoadedMetadata = () => {
  if (audioRef.value) {
    duration.value = audioRef.value.duration
    volume.value = audioRef.value.volume * 100
  }
}

// 处理进度条拖拽
const handleSeek = (value: number) => {
  if (audioRef.value) {
    audioRef.value.currentTime = value
    currentTime.value = value
  }
}

// 处理音量变化
const handleVolumeChange = (value: number) => {
  if (audioRef.value) {
    audioRef.value.volume = value / 100
    volume.value = value
  }
}

// 静音/取消静音
const toggleMute = () => {
  if (!audioRef.value) return
  if (volume.value > 0) {
    audioRef.value.volume = 0
    volume.value = 0
  } else {
    audioRef.value.volume = 1
    volume.value = 100
  }
}

// 检查是否可以完成打标
const canFinish = computed(() => {
  if (!currentTask.value) return false
  return currentTask.value.records.every(
    record => record.selected_options && record.selected_options.length > 0
  )
})

// 是否有下一个任务
const hasNextTask = computed(() => {
  if (!currentTask.value) return false
  const currentIndex = taskList.value.findIndex(t => t.id === currentTask.value!.id)
  return currentIndex >= 0 && currentIndex < taskList.value.length - 1
})

// 创建打标任务相关
const createDialogVisible = ref(false)
const createFormRef = ref<FormInstance>()
const musicList = ref<MusicResponse[]>([])
const questionList = ref<TaggingQuestionResponse[]>([])
const taggerList = ref<UserResponse[]>([])
const reviewerList = ref<UserResponse[]>([])

const createForm = reactive({
  music_ids: [] as number[],
  question_ids: [] as number[],
  tagger_ids: [] as number[],
  reviewer_id: undefined as number | undefined
})

const createRules: FormRules = {
  music_ids: [
    { required: true, message: '请至少选择一首音乐', trigger: 'change' }
  ],
  question_ids: [
    { required: true, message: '请至少选择一个题目', trigger: 'change' }
  ],
  tagger_ids: [
    { required: true, message: '请至少选择一个打标员', trigger: 'change' }
  ],
  reviewer_id: [
    { required: true, message: '请选择审核员', trigger: 'change' }
  ]
}

// 审核相关
const reviewDialogVisible = ref(false)
const reviewFormRef = ref<FormInstance>()
const currentTaskId = ref<number | null>(null)
const reviewTask = ref<TaggingTaskResponse | null>(null)
const reviewAudioRef = ref<HTMLAudioElement | null>(null)
const reviewAudioUrl = ref<string>('')
const reviewAudioLoading = ref(false)
const reviewAudioError = ref<string | null>(null)
const reviewIsPlaying = ref(false)
const reviewCurrentTime = ref(0)
const reviewDuration = ref(0)
const reviewVolume = ref(100)
let reviewBlobUrl: string | null = null

const reviewForm = reactive({
  result: '' as ReviewResultEnum | '',
  comment: ''
})

const reviewRules: FormRules = {
  result: [
    { required: true, message: '请选择审核结果', trigger: 'change' }
  ]
}

// 加载打标任务列表
const loadTaskList = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.status) params.status = filters.status as TaggingStatusEnum
    
    // 根据视图模式和用户角色设置筛选条件
    if (userStore.isAdmin) {
      // 管理员：根据视图模式筛选
      if (viewMode.value === 'myTagging') {
        params.tagger_id = userStore.user?.id
      } else if (viewMode.value === 'myReview') {
        params.reviewer_id = userStore.user?.id
      }
      // viewMode === 'all' 时不添加筛选，显示所有任务
    } else if (userStore.isReviewer) {
      // 审核员：只显示分配给自己的审核任务
      params.reviewer_id = userStore.user?.id
    } else {
      // 打标员：只显示分配给自己的打标任务
      params.tagger_id = userStore.user?.id
    }
    
    const response = await getTaggingTaskList(params)
    if (response.data) {
      taskList.value = response.data
    }
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

// 视图模式切换
const handleViewModeChange = () => {
  loadTaskList()
}

// 监听筛选条件变化，实时加载任务列表
watch([() => filters.keyword, () => filters.status, viewMode], () => {
  loadTaskList()
}, { deep: true })

// 获取状态文本
const getStatusText = (status: TaggingStatusEnum) => {
  const map: Record<TaggingStatusEnum, string> = {
    [TaggingStatusEnum.PENDING]: '待打标',
    [TaggingStatusEnum.TAGGED]: '已打标',
    [TaggingStatusEnum.REVIEWED]: '已审核通过',
    [TaggingStatusEnum.REJECTED]: '审核未通过'
  }
  return map[status] || status
}

// 获取状态类型
const getStatusType = (status: TaggingStatusEnum) => {
  const map: Record<TaggingStatusEnum, string> = {
    [TaggingStatusEnum.PENDING]: 'info',
    [TaggingStatusEnum.TAGGED]: 'warning',
    [TaggingStatusEnum.REVIEWED]: 'success',
    [TaggingStatusEnum.REJECTED]: 'danger'
  }
  return map[status] || ''
}

// 开始打标
const handleStartTagging = (task: TaggingTaskResponse) => {
  // 确保所有记录的 selected_options 都被初始化
  if (task.records) {
    task.records.forEach(record => {
      if (!record.selected_options) {
        record.selected_options = []
      }
    })
  }
  currentTask.value = task
  currentQuestionIndex.value = 0
  audioError.value = null
  if (task.music.filepath) {
    loadAudioFile(task.music.filepath)
  }
}

// 返回任务列表
const handleBackToList = () => {
  currentTask.value = null
  currentQuestionIndex.value = 0
  audioError.value = null
  audioUrl.value = ''
  // 清理 blob URL
  if (currentBlobUrl) {
    URL.revokeObjectURL(currentBlobUrl)
    currentBlobUrl = null
  }
  loadTaskList()
}

// 下一个任务
const handleNextTask = () => {
  if (!currentTask.value) return
  
  const currentIndex = taskList.value.findIndex(t => t.id === currentTask.value!.id)
  if (currentIndex >= 0 && currentIndex < taskList.value.length - 1) {
    const nextTask = taskList.value[currentIndex + 1]
    // 确保所有记录的 selected_options 都被初始化
    if (nextTask.records) {
      nextTask.records.forEach(record => {
        if (!record.selected_options) {
          record.selected_options = []
        }
      })
    }
    currentTask.value = nextTask
    currentQuestionIndex.value = 0
    audioError.value = null
    if (currentTask.value.music.filepath) {
      loadAudioFile(currentTask.value.music.filepath)
    }
  }
}

// 处理单选变化
const handleRadioChange = (record: any, value: string) => {
  record.selected_options = [value]
  // 自动保存
  handleAutoSave(record)
}

// 自动保存当前题目（用户选择选项时触发）
const handleAutoSave = async (record: any) => {
  if (!currentTask.value || !record.selected_options || record.selected_options.length === 0) {
    return
  }

  // 防止重复保存
  if (saving.value) return
  
  saving.value = true
  try {
    await tagMusic({
      id: record.id,
      selected_options: record.selected_options
    })
    // 不显示成功消息，避免频繁提示
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
    
    // 自动跳转到下一个任务
    if (hasNextTask.value) {
      handleNextTask()
    } else {
      // 没有下一个任务，返回列表
      handleBackToList()
    }
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    finishing.value = false
  }
}

// 处理音频播放结束
const handleAudioEnded = () => {
  // 音频播放结束
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
  }, 1000) // 延迟1秒检查，给音频足够时间加载
}

// 创建打标任务
const handleCreate = async () => {
  createForm.music_ids = []
  createForm.question_ids = []
  createForm.tagger_ids = []
  createForm.reviewer_id = undefined
  
  // 加载音乐列表
  try {
    const musicResponse = await getMusicList()
    if (musicResponse.data) {
      musicList.value = musicResponse.data
    }
  } catch (error) {
    // 错误已在拦截器中处理
  }
  
  // 加载题目列表
  try {
    const questionResponse = await getTaggingQuestionList()
    if (questionResponse.data) {
      questionList.value = questionResponse.data
    }
  } catch (error) {
    // 错误已在拦截器中处理
  }
  
  // 加载打标员列表（包括管理员）
  try {
    const taggerResponse = await getUserList({ role: UserRoleEnum.TAGGER })
    const adminResponse = await getUserList({ role: UserRoleEnum.ADMIN })
    if (taggerResponse.data && adminResponse.data) {
      taggerList.value = [...taggerResponse.data, ...adminResponse.data]
    }
  } catch (error) {
    // 错误已在拦截器中处理
  }
  
  // 加载审核员列表（包括管理员）
  try {
    const reviewerResponse = await getUserList({ role: UserRoleEnum.REVIEWER })
    const adminResponse = await getUserList({ role: UserRoleEnum.ADMIN })
    if (reviewerResponse.data && adminResponse.data) {
      reviewerList.value = [...reviewerResponse.data, ...adminResponse.data]
    }
  } catch (error) {
    // 错误已在拦截器中处理
  }
  
  createDialogVisible.value = true
}

// 提交创建（支持批量创建：每个音乐每个打标员）
const handleCreateSubmit = async () => {
  if (!createFormRef.value) return
  
  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        // 批量创建任务：为每个音乐每个打标员创建一个任务
        const promises: Promise<any>[] = []
        createForm.music_ids.forEach(musicId => {
          createForm.tagger_ids.forEach(taggerId => {
            promises.push(
              operateTaggingTask({
                operation: OperationEnum.CREATE,
                music_id: musicId,
                question_ids: createForm.question_ids,
                tagger_id: taggerId,
                reviewer_id: createForm.reviewer_id
              })
            )
          })
        })
        
        await Promise.all(promises)
        const totalTasks = createForm.music_ids.length * createForm.tagger_ids.length
        ElMessage.success(`成功创建 ${totalTasks} 个打标任务`)
        createDialogVisible.value = false
        loadTaskList()
      } catch (error) {
        // 错误已在拦截器中处理
      } finally {
        loading.value = false
      }
    }
  })
}

// 加载审核音频文件
const loadReviewAudioFile = async (filepath: string) => {
  reviewAudioError.value = null
  reviewAudioLoading.value = true
  
  if (reviewBlobUrl) {
    URL.revokeObjectURL(reviewBlobUrl)
    reviewBlobUrl = null
  }
  
  if (filepath.startsWith('http://') || filepath.startsWith('https://')) {
    reviewAudioUrl.value = filepath
    reviewAudioLoading.value = false
    return
  }
  
  try {
    const token = localStorage.getItem('token')
    const response = await fetch(`http://127.0.0.1:8000/music/file?path=${encodeURIComponent(filepath)}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const blob = await response.blob()
    reviewBlobUrl = URL.createObjectURL(blob)
    reviewAudioUrl.value = reviewBlobUrl

    if (reviewAudioRef.value) {
      reviewAudioRef.value.oncanplay = () => {
        reviewAudioError.value = null
        reviewAudioLoading.value = false
      }
      // 监听播放状态变化
      reviewAudioRef.value.addEventListener('play', () => {
        reviewIsPlaying.value = true
      })
      reviewAudioRef.value.addEventListener('pause', () => {
        reviewIsPlaying.value = false
      })
      // 设置初始音量
      reviewAudioRef.value.volume = reviewVolume.value / 100
    }
  } catch (error) {
    console.error('Failed to load audio:', error)
    reviewAudioError.value = '无法加载音频文件，请检查文件路径和权限'
    reviewAudioUrl.value = ''
  } finally {
    reviewAudioLoading.value = false
  }
}

// 处理审核音频错误
const handleReviewAudioError = (event: Event) => {
  const audio = event.target as HTMLAudioElement
  if (audio && audio.error) {
    let errorMessage = '音频加载失败'
    switch (audio.error.code) {
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
    reviewAudioError.value = errorMessage
  }
}

// 审核界面的音频控制函数
const toggleReviewPlayPause = () => {
  if (!reviewAudioRef.value) return
  if (reviewIsPlaying.value) {
    reviewAudioRef.value.pause()
  } else {
    reviewAudioRef.value.play()
  }
  reviewIsPlaying.value = !reviewIsPlaying.value
}

const handleReviewTimeUpdate = () => {
  if (reviewAudioRef.value) {
    reviewCurrentTime.value = reviewAudioRef.value.currentTime
  }
}

const handleReviewLoadedMetadata = () => {
  if (reviewAudioRef.value) {
    reviewDuration.value = reviewAudioRef.value.duration
    reviewVolume.value = reviewAudioRef.value.volume * 100
  }
}

const handleReviewSeek = (value: number) => {
  if (reviewAudioRef.value) {
    reviewAudioRef.value.currentTime = value
    reviewCurrentTime.value = value
  }
}

const handleReviewVolumeChange = (value: number) => {
  if (reviewAudioRef.value) {
    reviewAudioRef.value.volume = value / 100
    reviewVolume.value = value
  }
}

const toggleReviewMute = () => {
  if (!reviewAudioRef.value) return
  if (reviewVolume.value > 0) {
    reviewAudioRef.value.volume = 0
    reviewVolume.value = 0
  } else {
    reviewAudioRef.value.volume = 1
    reviewVolume.value = 100
  }
}

// 审核
const handleReview = async (row: TaggingTaskResponse) => {
  currentTaskId.value = row.id
  reviewTask.value = row
  reviewForm.result = '' as ReviewResultEnum | ''
  reviewForm.comment = ''
  reviewDialogVisible.value = true
  
  // 加载音频
  if (row.music && row.music.filepath) {
    await loadReviewAudioFile(row.music.filepath)
  }
}

// 提交审核
const handleReviewSubmit = async () => {
  if (!reviewFormRef.value || !currentTaskId.value) return
  
  await reviewFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await operateTaggingTask({
          operation: OperationEnum.REVIEW,
          id: currentTaskId.value!,
          review_result: reviewForm.result as ReviewResultEnum,
          review_comment: reviewForm.comment || undefined
        })
        ElMessage.success('审核完成')
        reviewDialogVisible.value = false
        // 清理音频资源
        if (reviewBlobUrl) {
          URL.revokeObjectURL(reviewBlobUrl)
          reviewBlobUrl = null
        }
        reviewAudioUrl.value = ''
        reviewTask.value = null
        loadTaskList()
      } catch (error) {
        // 错误已在拦截器中处理
      } finally {
        loading.value = false
      }
    }
  })
}

// 删除打标任务
const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个打标任务吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    loading.value = true
    try {
      await operateTaggingTask({
        operation: OperationEnum.DELETE,
        id
      })
      ElMessage.success('删除成功')
      loadTaskList()
    } catch (error) {
      // 错误已在拦截器中处理
    } finally {
      loading.value = false
    }
  } catch {
    // 用户取消
  }
}

// 监听任务变化，自动加载音频并初始化选项
watch(currentTask, (newTask) => {
  if (newTask) {
    // 确保所有记录的 selected_options 都被初始化
    if (newTask.records) {
      newTask.records.forEach(record => {
        if (!record.selected_options) {
          record.selected_options = []
        }
      })
    }
    if (newTask.music.filepath) {
      loadAudioFile(newTask.music.filepath)
    }
  }
}, { immediate: true })

onMounted(() => {
  loadTaskList()
})

// 监听审核对话框关闭，清理资源
watch(reviewDialogVisible, (visible) => {
  if (!visible) {
    // 对话框关闭时清理音频资源
    if (reviewBlobUrl) {
      URL.revokeObjectURL(reviewBlobUrl)
      reviewBlobUrl = null
    }
    reviewAudioUrl.value = ''
    reviewAudioError.value = null
    reviewTask.value = null
  }
})

onUnmounted(() => {
  // 清理 blob URL
  if (currentBlobUrl) {
    URL.revokeObjectURL(currentBlobUrl)
    currentBlobUrl = null
  }
  if (reviewBlobUrl) {
    URL.revokeObjectURL(reviewBlobUrl)
    reviewBlobUrl = null
  }
})
</script>

<style scoped>
.tagging-task-container {
  padding: 20px;
}

.task-list-view .header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.task-list-view .header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header h2 {
  margin: 0;
  color: #409eff;
}

.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  align-items: center;
}

.tagging-view {
  max-width: 1200px;
  margin: 0 auto;
}

.tagging-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.tagging-header h2 {
  margin: 0;
  color: #409eff;
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

.music-info h3 {
  margin: 0 0 10px 0;
  color: #409eff;
}

.audio-player {
  margin: 30px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.audio-player audio {
  display: none; /* 隐藏原生控件 */
}

.custom-audio-controls {
  display: flex;
  align-items: center;
  gap: 15px;
  width: 100%;
  max-width: 600px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.progress-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.progress-slider {
  width: 100%;
}

.time-display {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.volume-control {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.volume-slider {
  margin: 0;
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

.question-header h4 {
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

.no-questions {
  margin: 30px 0;
  text-align: center;
}

/* 审核对话框样式 */
.review-content {
  max-height: 70vh;
  overflow-y: auto;
}

.review-music-info {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.review-music-info h3 {
  margin: 0 0 10px 0;
  color: #303133;
}

.review-music-info p {
  margin: 5px 0;
  color: #606266;
  font-size: 14px;
}

.review-audio-player {
  margin-bottom: 30px;
  padding: 15px;
  background-color: #fafafa;
  border-radius: 8px;
  position: relative;
}

.review-audio-player audio {
  display: none; /* 隐藏原生控件 */
}

.review-audio-player .custom-audio-controls {
  max-width: 100%;
}

.review-questions {
  margin-bottom: 30px;
}

.review-questions h3 {
  margin-bottom: 20px;
  color: #303133;
  border-bottom: 2px solid #409eff;
  padding-bottom: 10px;
}

.review-question-item {
  margin-bottom: 25px;
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background-color: #fff;
}

.review-question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.review-question-header h4 {
  margin: 0;
  color: #303133;
  flex: 1;
}

.review-question-description {
  color: #606266;
  margin: 10px 0 15px 0;
  font-size: 14px;
}

.review-options {
  margin-top: 15px;
}

.review-option-item {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  margin-bottom: 10px;
  border: 2px solid #e4e7ed;
  border-radius: 6px;
  background-color: #fafafa;
  transition: all 0.3s;
}

.review-option-item.selected {
  border-color: #67c23a;
  background-color: #f0f9ff;
}

.review-option-item.not-selected {
  border-color: #e4e7ed;
  background-color: #fafafa;
  opacity: 0.7;
}

.review-option-item .el-icon {
  margin-right: 10px;
  color: #67c23a;
  font-size: 18px;
}

.review-option-item span {
  flex: 1;
  color: #303133;
}

.no-answer {
  margin-top: 15px;
  padding: 10px;
  text-align: center;
}

.review-form-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 2px solid #e4e7ed;
}
</style>
