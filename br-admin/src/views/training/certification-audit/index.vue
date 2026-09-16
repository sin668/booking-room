<template>
  <div class="certification-audit">
    <!-- Stats cards -->
    <n-grid :cols="4" :x-gap="16" class="mb-4">
      <n-gi>
        <n-card>
          <div class="stat-card">
            <div>
              <div class="stat-label">待审核</div>
              <div class="stat-value">{{ stats.pending }}</div>
            </div>
            <div class="stat-icon pending">
              <n-icon size="24"><TimeOutline /></n-icon>
            </div>
          </div>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card>
          <div class="stat-card">
            <div>
              <div class="stat-label">本月通过</div>
              <div class="stat-value">{{ stats.approvedThisMonth }}</div>
            </div>
            <div class="stat-icon approved">
              <n-icon size="24"><CheckmarkOutline /></n-icon>
            </div>
          </div>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card>
          <div class="stat-card">
            <div>
              <div class="stat-label">已认证总数</div>
              <div class="stat-value">{{ stats.totalApproved }}</div>
            </div>
            <div class="stat-icon total">
              <n-icon size="24"><SchoolOutline /></n-icon>
            </div>
          </div>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card>
          <div class="stat-card">
            <div>
              <div class="stat-label">教师资格总数</div>
              <div class="stat-value">{{ stats.teacherTotal }}</div>
            </div>
            <div class="stat-icon teacher">
              <n-icon size="24"><PersonOutline /></n-icon>
            </div>
          </div>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- Filters -->
    <n-card class="mb-4">
      <div class="filter-row">
        <n-tabs v-model:value="statusFilter" type="segment" class="status-tabs">
          <n-tab-pane name="" tab="全部" />
          <n-tab-pane name="pending" tab="待审核" />
          <n-tab-pane name="approved" tab="已通过" />
          <n-tab-pane name="rejected" tab="已拒绝" />
        </n-tabs>
        <n-select
          v-model:value="typeFilter"
          placeholder="认证类型"
          style="width: 150px"
          :options="typeOptions"
        />
        <n-input
          v-model:value="searchKeyword"
          placeholder="搜索用户..."
          style="width: 200px"
          clearable
          @keyup.enter="loadData"
        >
          <template #prefix>
            <n-icon><SearchOutline /></n-icon>
          </template>
        </n-input>
      </div>
    </n-card>

    <!-- Certification list -->
    <n-card>
      <n-data-table
        :columns="columns"
        :data="tableData"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row) => row.id"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </n-card>

    <!-- Review modal -->
    <n-modal v-model:show="showReviewModal" preset="dialog" :title="modalTitle">
      <div class="review-content">
        <div class="review-user">
          <n-avatar round :size="48" :src="currentUser.user_avatar" />
          <div class="review-user-info">
            <div class="review-user-name">{{ currentUser.user_nickname }}</div>
            <div class="review-user-phone">{{ currentUser.user_phone }}</div>
          </div>
        </div>

        <n-divider />

        <div v-if="currentCert.verification_type === 'real_name'" class="cert-detail">
          <n-descriptions label-placement="left" bordered :column="2">
            <n-descriptions-item label="姓名">{{ currentCert.real_name }}</n-descriptions-item>
            <n-descriptions-item label="身份证号">{{ currentCert.id_card_masked }}</n-descriptions-item>
          </n-descriptions>
        </div>

        <div v-if="currentCert.verification_type === 'education'" class="cert-detail">
          <n-descriptions label-placement="left" bordered :column="2">
            <n-descriptions-item label="学校">{{ currentCert.school }}</n-descriptions-item>
            <n-descriptions-item label="学历">{{ currentCert.education_level }}</n-descriptions-item>
            <n-descriptions-item label="专业">{{ currentCert.major || '-' }}</n-descriptions-item>
            <n-descriptions-item label="毕业年份">{{ currentCert.graduation_year || '-' }}</n-descriptions-item>
          </n-descriptions>
          <div v-if="currentCert.diploma_image_url" class="cert-images">
            <div class="image-label">学历证书：</div>
            <n-image
              :src="currentCert.diploma_image_url"
              width="200"
              preview-disabled
              object-fit="cover"
            />
          </div>
        </div>

        <div v-if="currentCert.verification_type === 'teacher'" class="cert-detail">
          <n-descriptions label-placement="left" bordered :column="2">
            <n-descriptions-item label="证书号">{{ currentCert.teacher_certificate_number }}</n-descriptions-item>
            <n-descriptions-item label="科目">{{ currentCert.teaching_subject || '-' }}</n-descriptions-item>
          </n-descriptions>
          <div v-if="currentCert.certificate_image_url" class="cert-images">
            <div class="image-label">资格证书：</div>
            <n-image
              :src="currentCert.certificate_image_url"
              width="200"
              preview-disabled
              object-fit="cover"
            />
          </div>
        </div>

        <n-divider />

        <n-form v-if="!isApproved" ref="reviewFormRef" :model="reviewForm" :rules="reviewRules">
          <n-form-item label="审核结果" path="approved">
            <n-radio-group v-model:value="reviewForm.approved">
              <n-radio :value="true">通过</n-radio>
              <n-radio :value="false">拒绝</n-radio>
            </n-radio-group>
          </n-form-item>
          <n-form-item v-if="!reviewForm.approved" label="拒绝原因" path="rejection_reason">
            <n-input
              v-model:value="reviewForm.rejection_reason"
              type="textarea"
              placeholder="请输入拒绝原因"
              :rows="3"
            />
          </n-form-item>
        </n-form>
      </div>

      <template #action>
        <n-space>
          <n-button @click="showReviewModal = false">取消</n-button>
          <n-button v-if="!isApproved" type="primary" :loading="submitting" @click="handleSubmitReview">
            提交审核
          </n-button>
        </n-space>
      </template>
    </n-modal>
    <!-- Image preview modal -->
    <n-modal v-model:show="showImagePreview" preset="card" title="证书照片预览" style="width: 600px;">
      <n-image :src="previewImage" width="100%" object-fit="contain" />
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, h, watch } from 'vue'
import { useMessage, NTag } from 'naive-ui'
import { TableAction } from '@/components/Table'
import {
  TimeOutline,
  CheckmarkOutline,
  SchoolOutline,
  PersonOutline,
  SearchOutline,
} from '@vicons/ionicons5'
import { getCertifications, reviewCertification } from '@/api/certification'

const message = useMessage()

// Stats
const stats = reactive({
  pending: 0,
  approvedThisMonth: 0,
  totalApproved: 0,
  teacherTotal: 0,
})

// Filters
const statusFilter = ref('pending')
const typeFilter = ref(null)
const searchKeyword = ref('')

const typeOptions = [
  { label: '全部类型', value: null },
  { label: '实名认证', value: 'real_name' },
  { label: '学历认证', value: 'education' },
  { label: '教师资格', value: 'teacher' },
]

// Table data
const loading = ref(false)
const tableData = ref([])
const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
})

// Review modal
const showReviewModal = ref(false)
const modalTitle = ref('审核认证')
const currentCert = ref({})
const currentUser = ref({})
const isApproved = ref(false)
const submitting = ref(false)
const reviewFormRef = ref(null)
const reviewForm = reactive({
  approved: true,
  rejection_reason: '',
})

// Image preview
const showImagePreview = ref(false)
const previewImage = ref('')

const reviewRules = {
  rejection_reason: {
    required: true,
    message: '请输入拒绝原因',
    trigger: 'blur',
  },
}

const CERT_STATUS_TAGS = {
  pending: { label: '待审核', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已拒绝', type: 'error' },
}

// Table columns
const columns = [
  {
    title: '用户',
    key: 'user',
    width: 200,
    render: (row) => {
      return h('div', { class: 'user-cell' }, [
        h('span', { class: 'user-name' }, row.user_nickname || '-'),
        h('span', { class: 'user-phone' }, row.user_phone || ''),
      ])
    },
  },
  {
    title: '认证类型',
    key: 'verification_type',
    width: 120,
    render: (row) => {
      const typeMap = {
        real_name: '实名认证',
        education: '学历认证',
        teacher: '教师资格',
      }
      return typeMap[row.verification_type] || row.verification_type
    },
  },
  {
    title: '认证信息',
    key: 'info',
    width: 250,
    render: (row) => {
      if (row.verification_type === 'real_name') {
        return `${row.real_name || '-'}`
      }
      if (row.verification_type === 'education') {
        return `${row.school || '-'} / ${row.education_level || '-'}`
      }
      if (row.verification_type === 'teacher') {
        return `${row.teacher_certificate_number || '-'}`
      }
      return '-'
    },
  },
  {
    title: '证书照片',
    key: 'cert_images',
    width: 120,
    render: (row) => {
      let imageUrl = null
      if (row.verification_type === 'education') {
        imageUrl = row.diploma_image_url
      } else if (row.verification_type === 'teacher') {
        imageUrl = row.certificate_image_url
      }
      if (!imageUrl) return h('span', { style: 'color: #999' }, '-')
      return h('img', {
        src: imageUrl,
        style: 'width: 48px; height: 48px; object-fit: cover; border-radius: 4px; cursor: pointer; border: 1px solid #eee;',
        onClick: () => {
          previewImage.value = imageUrl
          showImagePreview.value = true
        },
      })
    },
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row) => {
      const tag = CERT_STATUS_TAGS[row.status] || { label: row.status || '未知', type: 'default' }
      return h(NTag, { type: tag.type, size: 'small' }, { default: () => tag.label })
    },
  },
  {
    title: '提交时间',
    key: 'submitted_at',
    width: 180,
    render: (row) => {
      return new Date(row.submitted_at).toLocaleString('zh-CN')
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    fixed: 'right',
    render: (row) => {
      return h(TableAction, {
        actions: [
          {
            label: '审核',
            type: 'primary',
            onClick: () => openReviewModal(row),
          },
        ],
      })
    },
  },
]

// Load data
async function loadData() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (statusFilter.value) {
      params.status_filter = statusFilter.value
    }
    if (typeFilter.value) {
      params.type_filter = typeFilter.value
    }

    const res = await getCertifications(params)
    tableData.value = res.items || []
    pagination.itemCount = res.total || 0

    // Update stats (simplified - in real app, fetch from API)
    stats.pending = res.items?.filter(i => i.status === 'pending').length || 0
  } catch (error) {
    message.error(error.message || '加载失败')
  } finally {
    loading.value = false
  }
}

// Watch filter changes
watch([statusFilter, typeFilter], () => {
  pagination.page = 1
  loadData()
})

function handleFilterChange() {
  pagination.page = 1
  loadData()
}

function handlePageChange(page) {
  pagination.page = page
  loadData()
}

function handlePageSizeChange(pageSize) {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadData()
}

// Review modal
function openReviewModal(row) {
  currentCert.value = row
  currentUser.value = {
    user_nickname: row.user_nickname,
    user_phone: row.user_phone,
  }
  
  // 待审核状态显示审核表单，已审核状态显示只读
  if (row.status === 'pending') {
    isApproved.value = false
    reviewForm.approved = true
    reviewForm.rejection_reason = ''
    modalTitle.value = '审核认证'
  } else {
    isApproved.value = true
    modalTitle.value = '查看资料'
  }
  
  showReviewModal.value = true
}

async function handleSubmitReview() {
  if (!reviewForm.approved && !reviewForm.rejection_reason) {
    message.warning('请输入拒绝原因')
    return
  }

  submitting.value = true
  try {
    await reviewCertification(currentCert.value.id, {
      approved: reviewForm.approved,
      rejection_reason: reviewForm.rejection_reason,
    })
    message.success('审核成功')
    showReviewModal.value = false
    loadData()
  } catch (error) {
    message.error(error.message || '审核失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.certification-audit {
  padding: 24px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-tabs {
  flex-shrink: 0;
}

.stat-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stat-label {
  font-size: 14px;
  color: #999;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #2D3436;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;

  &.pending {
    background: rgba(255, 149, 0, 0.1);
    color: #FF9500;
  }

  &.approved {
    background: rgba(7, 193, 96, 0.1);
    color: #07C160;
  }

  &.total {
    background: rgba(79, 110, 247, 0.1);
    color: #4F6EF7;
  }

  &.teacher {
    background: rgba(108, 92, 231, 0.1);
    color: #6C5CE7;
  }
}

.user-cell {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 14px;
  color: #2D3436;
  font-weight: 500;
}

.user-phone {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.review-content {
  max-height: 60vh;
  overflow-y: auto;
}

.review-user {
  display: flex;
  align-items: center;
  gap: 16px;
}

.review-user-info {
  flex: 1;
}

.review-user-name {
  font-size: 16px;
  font-weight: 600;
  color: #2D3436;
}

.review-user-phone {
  font-size: 14px;
  color: #999;
  margin-top: 4px;
}

.cert-detail {
  margin-top: 16px;
}

.cert-images {
  margin-top: 16px;
}

.image-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}
</style>
