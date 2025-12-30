<template>
  <div class="music-container">
    <div class="header">
      <h2>音乐管理</h2>
      <div class="header-actions">
        <el-button
          v-if="userStore.isAdmin"
          type="success"
          @click="handleDownload"
          :loading="downloading"
          :disabled="selectedMusicIds.length === 0"
        >
          导出打标记录 ({{ selectedMusicIds.length }})
        </el-button>
        <el-upload
          v-if="userStore.isAdmin"
          :auto-upload="false"
          :on-change="handleFileChange"
          :show-file-list="false"
          accept=".json"
        >
          <template #trigger>
            <el-button type="primary" :loading="loading">
              通过 JSON 文件加载音乐
            </el-button>
          </template>
        </el-upload>
      </div>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索音乐文件名"
        clearable
        style="width: 300px"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <el-table
      :data="musicList"
      v-loading="loading"
      stripe
      style="width: 100%"
      @selection-change="handleSelectionChange"
    >
      <el-table-column
        v-if="userStore.isAdmin"
        type="selection"
        width="55"
      />
      <el-table-column prop="filename" label="文件名" />
      <el-table-column prop="valid_tagging_count" label="有效打标数" width="120" />
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

    <!-- 分页组件 -->
    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :page-sizes="[10, 20, 50, 100]"
      :total="pagination.total"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="handleSizeChange"
      @current-change="handlePageChange"
      style="margin-top: 20px; justify-content: flex-end"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import { getMusicList, createMusic, deleteMusic } from '../api/music'
import { downloadTaggingRecords } from '../api/tagging'
import type { MusicResponse } from '../types/interfaces'

const userStore = useUserStore()
const musicList = ref<MusicResponse[]>([])
const loading = ref(false)
const downloading = ref(false)
const searchKeyword = ref('')
const selectedMusicIds = ref<number[]>([])

// 分页信息
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})

// 加载音乐列表
const loadMusicList = async () => {
  loading.value = true
  try {
    const response = await getMusicList({
      filename: searchKeyword.value || undefined,
      page: pagination.value.page,
      page_size: pagination.value.pageSize
    })
    if (response && response.data) {
      // response 是 ApiResponse，response.data 是分页数据 {items: [], total: 0, ...}
      musicList.value = response.data.items || []
      pagination.value.total = response.data.total || 0
    } else {
      musicList.value = []
      pagination.value.total = 0
    }
  } catch (error) {
    // 错误已在拦截器中处理
    musicList.value = []
    pagination.value.total = 0
  } finally {
    loading.value = false
  }
}

// 分页大小变化
const handleSizeChange = (size: number) => {
  pagination.value.pageSize = size
  pagination.value.page = 1
  loadMusicList()
}

// 页码变化
const handlePageChange = (page: number) => {
  pagination.value.page = page
  loadMusicList()
}

// 监听搜索关键词变化，实时加载音乐列表
watch(searchKeyword, () => {
  pagination.value.page = 1 // 搜索时重置到第一页
  loadMusicList()
})

// 处理文件选择
const handleFileChange = async (file: any) => {
  // 验证文件类型
  if (!file.raw.name.endsWith('.json')) {
    ElMessage.error('请选择 JSON 文件')
    return
  }

  loading.value = true
  try {
    const response = await createMusic(file.raw)
    if (response.data) {
      const { success_count, error_count, error_paths } = response.data
      
      if (success_count > 0) {
        ElMessage.success(`成功加载 ${success_count} 首音乐`)
      }
      
      if (error_count > 0) {
        // 显示错误信息
        const errorMsg = error_paths.slice(0, 5).join('\n')
        const moreErrors = error_paths.length > 5 ? `\n... 还有 ${error_paths.length - 5} 个错误` : ''
        ElMessage.warning({
          message: `有 ${error_count} 个文件加载失败：\n${errorMsg}${moreErrors}`,
          duration: 5000,
          showClose: true
        })
      }
      
      if (success_count === 0 && error_count > 0) {
        ElMessage.error('所有文件加载失败，请检查 JSON 文件格式和文件路径')
      }
      
      loadMusicList()
    }
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

// 选择变化
const handleSelectionChange = (selection: MusicResponse[]) => {
  selectedMusicIds.value = selection.map(m => m.id)
}

// 下载打标记录
const handleDownload = async () => {
  if (selectedMusicIds.value.length === 0) {
    ElMessage.warning('请至少选择一首音乐')
    return
  }

  downloading.value = true
  try {
    const blob = await downloadTaggingRecords(selectedMusicIds.value)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `tagging_records_${new Date().getTime()}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  } catch (error) {
    ElMessage.error('下载失败')
  } finally {
    downloading.value = false
  }
}

// 删除音乐
const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这首音乐吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    loading.value = true
    try {
      await deleteMusic(id)
      ElMessage.success('删除成功')
      loadMusicList()
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
  loadMusicList()
})
</script>

<style scoped>
.music-container {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
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
}
</style>

