<template>
  <div class="tagging-question-container">
    <div class="header">
      <h2>题目管理</h2>
      <el-button
        v-if="userStore.isAdmin"
        type="primary"
        @click="handleCreate"
      >
        创建题目
      </el-button>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索题目标题"
        clearable
        style="width: 300px"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <el-table
      :data="questionList"
      v-loading="loading"
      stripe
      style="width: 100%"
    >
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="description" label="描述" />
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_multiple_choice ? 'success' : 'info'">
            {{ row.is_multiple_choice ? '多选题' : '单选题' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="选项" width="200">
        <template #default="{ row }">
          <div class="options-list">
            <el-tag
              v-for="(option, index) in row.options"
              :key="index"
              size="small"
              class="option-tag"
            >
              {{ option }}
            </el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="create_time" label="创建时间" width="180" />
      <el-table-column label="操作" width="150" v-if="userStore.isAdmin">
        <template #default="{ row }">
          <el-button
            type="primary"
            size="small"
            @click="handleEdit(row)"
            class="action-btn"
          >
            编辑
          </el-button>
          <el-button
            type="danger"
            size="small"
            @click="handleDelete(row.id)"
            class="action-btn"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入题目标题" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入题目描述（可选）"
          />
        </el-form-item>
        <el-form-item label="题目类型" prop="is_multiple_choice">
          <el-radio-group v-model="form.is_multiple_choice">
            <el-radio :value="false">单选题</el-radio>
            <el-radio :value="true">多选题</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="选项" prop="options">
          <div class="options-container">
            <div v-for="(option, index) in form.options" :key="index" class="option-item">
              <el-input
                v-model="form.options[index]"
                placeholder="请输入选项内容"
                class="option-input"
              />
              <el-button
                type="danger"
                size="small"
                @click="removeOption(index)"
                :disabled="form.options.length <= 2"
                class="option-delete-btn"
              >
                删除
              </el-button>
            </div>
            <el-button
              type="primary"
              size="small"
              @click="addOption"
              class="add-option-btn"
            >
              添加选项
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import {
  getTaggingQuestionList,
  operateTaggingQuestion
} from '../api/tagging'
import type { TaggingQuestionResponse, TaggingQuestionOperate } from '../types/interfaces'
import { OperationEnum } from '../types/enums'

const userStore = useUserStore()
const allQuestionList = ref<TaggingQuestionResponse[]>([])
const questionList = ref<TaggingQuestionResponse[]>([])
const loading = ref(false)
const searchKeyword = ref('')
const dialogVisible = ref(false)
const formRef = ref<FormInstance>()
const isEdit = ref(false)
const editId = ref<number | null>(null)

const form = reactive({
  title: '',
  description: '',
  is_multiple_choice: false,
  options: ['', '']
})

const rules: FormRules = {
  title: [
    { required: true, message: '请输入标题', trigger: 'blur' }
  ],
  options: [
    { required: true, message: '至少需要2个选项', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value.length < 2) {
          callback(new Error('至少需要2个选项'))
        } else if (value.some((opt: string) => !opt.trim())) {
          callback(new Error('选项内容不能为空'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const dialogTitle = computed(() => isEdit.value ? '编辑题目' : '创建题目')

// 加载题目列表
const loadQuestionList = async () => {
  loading.value = true
  try {
    const response = await getTaggingQuestionList()
    if (response.data) {
      allQuestionList.value = response.data
      filterQuestionList()
    }
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

// 过滤题目列表
const filterQuestionList = () => {
  if (!searchKeyword.value.trim()) {
    questionList.value = allQuestionList.value
  } else {
    const keyword = searchKeyword.value.toLowerCase()
    questionList.value = allQuestionList.value.filter(q => 
      q.title.toLowerCase().includes(keyword) ||
      (q.description && q.description.toLowerCase().includes(keyword))
    )
  }
}

// 监听搜索关键词变化，实时过滤
watch(searchKeyword, () => {
  filterQuestionList()
})

// 打开创建对话框
const handleCreate = () => {
  isEdit.value = false
  editId.value = null
  form.title = ''
  form.description = ''
  form.is_multiple_choice = false
  form.options = ['', '']
  dialogVisible.value = true
}

// 打开编辑对话框
const handleEdit = (row: TaggingQuestionResponse) => {
  isEdit.value = true
  editId.value = row.id
  form.title = row.title
  form.description = row.description || ''
  form.is_multiple_choice = row.is_multiple_choice
  form.options = [...row.options]
  dialogVisible.value = true
}

// 添加选项
const addOption = () => {
  form.options.push('')
}

// 删除选项
const removeOption = (index: number) => {
  if (form.options.length > 2) {
    form.options.splice(index, 1)
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const data: TaggingQuestionOperate = {
          operation: isEdit.value ? OperationEnum.UPDATE : OperationEnum.CREATE,
          id: isEdit.value && editId.value !== null ? editId.value : undefined,
          title: form.title,
          description: form.description || undefined,
          is_multiple_choice: form.is_multiple_choice,
          options: form.options.filter(opt => opt.trim())
        }
        await operateTaggingQuestion(data)
        ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
        dialogVisible.value = false
        loadQuestionList()
      } catch (error) {
        // 错误已在拦截器中处理
      } finally {
        loading.value = false
      }
    }
  })
}

// 删除题目
const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个题目吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    loading.value = true
    try {
      await operateTaggingQuestion({
        operation: OperationEnum.DELETE,
        id
      })
      ElMessage.success('删除成功')
      loadQuestionList()
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
  loadQuestionList()
})
</script>

<style scoped>
.tagging-question-container {
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

.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.options-list {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  min-height: 32px;
  line-height: 32px;
  padding: 8px 0;
}

.option-tag {
  margin-right: 5px;
  margin-bottom: 5px;
  vertical-align: middle;
}

.options-container {
  width: 100%;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  width: 100%;
}

.option-input {
  flex: 1;
}

.option-delete-btn {
  flex-shrink: 0;
}

.add-option-btn {
  margin-top: 10px;
}

.action-btn {
  margin-right: 5px;
}

.action-btn:last-child {
  margin-right: 0;
}
</style>

