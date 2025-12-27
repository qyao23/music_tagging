<template>
  <div class="tagging-item-container">
    <div class="header">
      <h2>打标项管理</h2>
      <el-button
        v-if="userStore.isAdmin"
        type="primary"
        @click="handleCreate"
      >
        创建打标项
      </el-button>
    </div>

    <el-table
      :data="itemList"
      v-loading="loading"
      stripe
      style="width: 100%"
    >
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="description" label="描述" />
      <el-table-column prop="create_time" label="创建时间" width="180" />
      <el-table-column label="操作" width="120" v-if="userStore.isAdmin">
        <template #default="{ row }">
          <el-button
            type="danger"
            size="small"
            @click="handleDelete(row.id)"
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
      width="500px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入打标项名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述"
          />
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { useUserStore } from '../stores/user'
import {
  getTaggingItemList,
  createTaggingItem,
  deleteTaggingItem
} from '../api/tagging'
import type { TaggingItemResponse } from '../types/interfaces'

const userStore = useUserStore()
const itemList = ref<TaggingItemResponse[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  description: ''
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入名称', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入描述', trigger: 'blur' }
  ]
}

const dialogTitle = ref('创建打标项')

// 加载打标项列表
const loadItemList = async () => {
  loading.value = true
  try {
    const response = await getTaggingItemList()
    if (response.data) {
      itemList.value = response.data
    }
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

// 打开创建对话框
const handleCreate = () => {
  form.name = ''
  form.description = ''
  dialogTitle.value = '创建打标项'
  dialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await createTaggingItem({
          name: form.name,
          description: form.description
        })
        ElMessage.success('创建成功')
        dialogVisible.value = false
        loadItemList()
      } catch (error) {
        // 错误已在拦截器中处理
      } finally {
        loading.value = false
      }
    }
  })
}

// 删除打标项
const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个打标项吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    loading.value = true
    try {
      await deleteTaggingItem(id)
      ElMessage.success('删除成功')
      loadItemList()
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
  loadItemList()
})
</script>

<style scoped>
.tagging-item-container {
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
</style>

