<template>
  <div class="tagging-record-container">
    <div class="header">
      <h2>打标记录</h2>
      <el-button
        v-if="userStore.isAdmin"
        type="primary"
        @click="handleCreate"
      >
        创建打标记录
      </el-button>
    </div>

    <!-- 筛选条件 -->
    <div class="filter-bar">
      <el-input
        v-model="filters.keyword"
        placeholder="搜索ID或音乐文件路径"
        clearable
        style="width: 250px"
        @clear="handleSearch"
        @keyup.enter="handleSearch"
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
        <el-option label="待打标" value="pending" />
        <el-option label="已打标" value="tagged" />
        <el-option label="已审核通过" value="reviewed" />
        <el-option label="审核未通过" value="rejected" />
      </el-select>
      <el-button type="primary" @click="handleSearch">搜索</el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>

    <el-table
      :data="recordList"
      v-loading="loading"
      stripe
      style="width: 100%"
    >
      <el-table-column prop="music.filepath" label="音乐文件路径" />
      <el-table-column prop="tagging_item.name" label="打标项" />
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="tagger.username" label="打标员" width="120" />
      <el-table-column prop="reviewer.username" label="审核员" width="120" />
      <el-table-column prop="create_time" label="创建时间" width="180" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="userStore.isTagger && (row.status === 'pending' || row.status === 'rejected')"
            type="primary"
            size="small"
            @click="handleFinish(row)"
          >
            完成打标
          </el-button>
          <el-button
            v-if="userStore.isReviewer && row.status === 'tagged'"
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

    <!-- 完成打标对话框 -->
    <el-dialog
      v-model="finishDialogVisible"
      title="完成打标"
      width="500px"
    >
      <el-form :model="finishForm" :rules="finishRules" ref="finishFormRef" label-width="100px">
        <el-form-item label="打标项" prop="tagging_item_id">
          <el-select v-model="finishForm.tagging_item_id" placeholder="请选择打标项" style="width: 100%">
            <el-option
              v-for="item in taggingItemList"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="finishForm.comment"
            type="textarea"
            :rows="3"
            placeholder="请输入备注（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="finishDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleFinishSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 审核对话框 -->
    <el-dialog
      v-model="reviewDialogVisible"
      title="审核打标记录"
      width="500px"
    >
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
      <template #footer>
        <el-button @click="reviewDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleReviewSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 创建打标记录对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="创建打标记录"
      width="600px"
    >
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="100px">
        <el-form-item label="音乐" prop="music_id">
          <el-select v-model="createForm.music_id" placeholder="请选择音乐" filterable style="width: 100%">
            <el-option
              v-for="music in musicList"
              :key="music.id"
              :label="music.filepath"
              :value="music.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="打标员" prop="tagger_id">
          <el-select v-model="createForm.tagger_id" placeholder="请选择打标员" filterable style="width: 100%">
            <el-option
              v-for="user in taggerList"
              :key="user.id"
              :label="user.username"
              :value="user.id"
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import {
  getTaggingRecordList,
  operateTaggingRecord,
  finishTaggingRecord,
  reviewTaggingRecord,
  getTaggingItemList
} from '../api/tagging'
import { getMusicList } from '../api/music'
import { getUserList } from '../api/user'
import type {
  TaggingRecordResponse,
  TaggingItemResponse,
  MusicResponse,
  UserResponse
} from '../types/interfaces'
import { TaggingStatusEnum, OperationEnum, ReviewResultEnum, UserRoleEnum } from '../types/enums'

const userStore = useUserStore()
const recordList = ref<TaggingRecordResponse[]>([])
const loading = ref(false)

// 筛选条件
const filters = reactive({
  keyword: '',
  status: '' as string | TaggingStatusEnum
})

// 完成打标相关
const finishDialogVisible = ref(false)
const finishFormRef = ref<FormInstance>()
const currentRecordId = ref<number | null>(null)
const taggingItemList = ref<TaggingItemResponse[]>([])

const finishForm = reactive({
  tagging_item_id: undefined as number | undefined,
  comment: ''
})

const finishRules: FormRules = {
  tagging_item_id: [
    { required: true, message: '请选择打标项', trigger: 'change' }
  ]
}

// 审核相关
const reviewDialogVisible = ref(false)
const reviewFormRef = ref<FormInstance>()

const reviewForm = reactive({
  result: '' as ReviewResultEnum | '',
  comment: ''
})

const reviewRules: FormRules = {
  result: [
    { required: true, message: '请选择审核结果', trigger: 'change' }
  ]
}

// 创建打标记录相关
const createDialogVisible = ref(false)
const createFormRef = ref<FormInstance>()
const musicList = ref<MusicResponse[]>([])
const taggerList = ref<UserResponse[]>([])
const reviewerList = ref<UserResponse[]>([])

const createForm = reactive({
  music_id: undefined as number | undefined,
  tagger_id: undefined as number | undefined,
  reviewer_id: undefined as number | undefined
})

const createRules: FormRules = {
  music_id: [
    { required: true, message: '请选择音乐', trigger: 'change' }
  ],
  tagger_id: [
    { required: true, message: '请选择打标员', trigger: 'change' }
  ],
  reviewer_id: [
    { required: true, message: '请选择审核员', trigger: 'change' }
  ]
}

// 加载打标记录列表
const loadRecordList = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.status) params.status = filters.status as TaggingStatusEnum
    
    const response = await getTaggingRecordList(params)
    if (response.data) {
      // 适配新的分页返回格式
      if (Array.isArray(response.data)) {
        recordList.value = response.data
      } else {
        recordList.value = response.data.items || []
      }
    }
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  loadRecordList()
}

// 重置
const handleReset = () => {
  filters.keyword = ''
  filters.status = ''
  loadRecordList()
}

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

// 完成打标
const handleFinish = async (row: TaggingRecordResponse) => {
  currentRecordId.value = row.id
  finishForm.tagging_item_id = undefined
  finishForm.comment = ''
  
  // 加载打标项列表
  try {
    const response = await getTaggingItemList()
    if (response.data) {
      taggingItemList.value = response.data
    }
  } catch (error) {
    // 错误已在拦截器中处理
  }
  
  finishDialogVisible.value = true
}

// 提交完成打标
const handleFinishSubmit = async () => {
  if (!finishFormRef.value || !currentRecordId.value) return
  
  await finishFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await finishTaggingRecord({
          id: currentRecordId.value!,
          tagging_item_id: finishForm.tagging_item_id!,
          comment: finishForm.comment || undefined
        })
        ElMessage.success('打标完成')
        finishDialogVisible.value = false
        loadRecordList()
      } catch (error) {
        // 错误已在拦截器中处理
      } finally {
        loading.value = false
      }
    }
  })
}

// 审核
const handleReview = (row: TaggingRecordResponse) => {
  currentRecordId.value = row.id
  reviewForm.result = '' as ReviewResultEnum | ''
  reviewForm.comment = ''
  reviewDialogVisible.value = true
}

// 提交审核
const handleReviewSubmit = async () => {
  if (!reviewFormRef.value || !currentRecordId.value) return
  
  await reviewFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await reviewTaggingRecord({
          id: currentRecordId.value!,
          result: reviewForm.result as ReviewResultEnum,
          comment: reviewForm.comment || undefined
        })
        ElMessage.success('审核完成')
        reviewDialogVisible.value = false
        loadRecordList()
      } catch (error) {
        // 错误已在拦截器中处理
      } finally {
        loading.value = false
      }
    }
  })
}

// 创建打标记录
const handleCreate = async () => {
  createForm.music_id = undefined
  createForm.tagger_id = undefined
  createForm.reviewer_id = undefined
  
  // 加载音乐列表
  try {
    const musicResponse = await getMusicList({ page: 1, page_size: 100 })
    if (musicResponse.data) {
      // 适配新的分页返回格式
      musicList.value = musicResponse.data.items || []
    }
  } catch (error) {
    // 错误已在拦截器中处理
  }
  
  // 加载打标员列表
  try {
    const taggerResponse = await getUserList({ role: UserRoleEnum.TAGGER })
    if (taggerResponse.data) {
      taggerList.value = taggerResponse.data
    }
  } catch (error) {
    // 错误已在拦截器中处理
  }
  
  // 加载审核员列表
  try {
    const reviewerResponse = await getUserList({ role: UserRoleEnum.REVIEWER })
    if (reviewerResponse.data) {
      reviewerList.value = reviewerResponse.data
    }
  } catch (error) {
    // 错误已在拦截器中处理
  }
  
  createDialogVisible.value = true
}

// 提交创建
const handleCreateSubmit = async () => {
  if (!createFormRef.value) return
  
  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await operateTaggingRecord({
          operation: OperationEnum.CREATE,
          music_id: createForm.music_id,
          tagger_id: createForm.tagger_id,
          reviewer_id: createForm.reviewer_id
        })
        ElMessage.success('创建成功')
        createDialogVisible.value = false
        loadRecordList()
      } catch (error) {
        // 错误已在拦截器中处理
      } finally {
        loading.value = false
      }
    }
  })
}

// 删除打标记录
const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这条打标记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    loading.value = true
    try {
      await operateTaggingRecord({
        operation: OperationEnum.DELETE,
        id
      })
      ElMessage.success('删除成功')
      loadRecordList()
    } catch (error) {
      // 错误已在拦截器中处理
    } finally {
      loading.value = false
    }
  } catch {
    // 用户取消
  }
}

onMounted(() => {
  loadRecordList()
})
</script>

<style scoped>
.tagging-record-container {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  color: #409eff;
}

.filter-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
</style>

