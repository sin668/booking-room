<template>
  <n-modal
    :show="show"
    preset="card"
    title="供需信息审核"
    style="width: 720px; max-width: 95vw"
    :mask-closable="false"
    @update:show="(val) => emit('update:show', val)"
  >
    <n-flex v-if="listing" vertical :size="16">
      <!-- 发布者 -->
      <div class="flex items-center gap-2">
        <n-avatar
          :src="listing.publisher_avatar || undefined"
          round
          :size="40"
          style="flex-shrink: 0"
        />
        <div class="flex flex-col">
          <span class="text-sm font-medium">{{ listing.publisher_nickname || '未知用户' }}</span>
          <span class="text-xs" style="color: #999">
            发布于 {{ formatAdminDateTime(listing.created_at) }} · 浏览 {{ listing.view_count }}
          </span>
        </div>
        <n-tag
          v-if="listing.publisher_education_verified"
          type="warning"
          size="small"
          :bordered="false"
        >
          学历认证
        </n-tag>
        <n-tag
          v-if="listing.publisher_teacher_verified"
          type="success"
          size="small"
          :bordered="false"
        >
          教师资格
        </n-tag>
        <n-tag :type="statusTag.type" size="small">{{ statusTag.label }}</n-tag>
      </div>

      <!-- 标题与类型 -->
      <div class="flex items-center gap-2">
        <n-tag :type="typeTag.type" size="small">{{ typeTag.label }}</n-tag>
        <span class="text-base font-medium">{{ listing.title }}</span>
      </div>

      <n-descriptions :column="2" label-placement="left" size="small" bordered>
        <n-descriptions-item label="科目">{{ listing.subject || '-' }}</n-descriptions-item>
        <n-descriptions-item label="授课方式">
          {{ listing.teaching_mode || '-' }}
        </n-descriptions-item>
        <n-descriptions-item label="价格">{{ priceText }}</n-descriptions-item>
        <n-descriptions-item label="地区">{{ listing.area || '-' }}</n-descriptions-item>
        <n-descriptions-item label="当前状态">{{ statusTag.label }}</n-descriptions-item>
        <n-descriptions-item label="浏览次数">{{ listing.view_count }}</n-descriptions-item>
      </n-descriptions>

      <!-- 详细描述 -->
      <div v-if="listing.description" class="listing-desc">{{ listing.description }}</div>

      <!-- 可授课/期望时间 -->
      <div v-if="listing.available_times.length" class="flex flex-wrap gap-2">
        <n-tag
          v-for="slot in listing.available_times"
          :key="slot"
          size="small"
          :bordered="false"
        >
          {{ slot }}
        </n-tag>
      </div>

      <!-- 图片 -->
      <n-image-group v-if="listing.images.length">
        <div class="flex flex-wrap gap-2">
          <n-image
            v-for="url in listing.images"
            :key="url"
            :src="url"
            width="88"
            height="88"
            object-fit="cover"
            class="listing-image"
          />
        </div>
      </n-image-group>

      <n-alert v-if="listing.reject_reason" type="warning" :bordered="false">
        既有驳回理由：{{ listing.reject_reason }}
      </n-alert>

      <n-divider style="margin: 0" />

      <!-- 审核操作 -->
      <div class="flex flex-col gap-2">
        <span class="text-sm font-medium">审核</span>
        <n-input
          v-model:value="rejectReason"
          type="textarea"
          :maxlength="200"
          :rows="2"
          show-count
          placeholder="驳回理由（选择驳回时必填）"
        />
        <div class="flex gap-2">
          <n-button
            v-permission="{ action: ['edu:listing:audit'] }"
            type="primary"
            :loading="auditing"
            @click="handleApprove"
          >
            通过
          </n-button>
          <n-button
            v-permission="{ action: ['edu:listing:audit'] }"
            type="error"
            :loading="auditing"
            @click="handleReject"
          >
            驳回
          </n-button>
          <n-button
            v-if="listing.status === 'approved'"
            v-permission="{ action: ['edu:listing:audit'] }"
            :loading="auditing"
            @click="handleOffline"
          >
            下架
          </n-button>
        </div>
      </div>
    </n-flex>
  </n-modal>
</template>

<script lang="ts" setup>
  import { computed, ref, watch } from 'vue';
  import { reviewEduListing, type AdminEduListingItem } from '@/api/eduMarket';
  import { formatAdminDateTime, getTagConfig } from '@/views/business/shared/formatters';
  import { EDU_LISTING_STATUS_TAGS, EDU_LISTING_TYPE_TAGS } from '@/views/business/shared/options';

  const props = defineProps<{
    show: boolean;
    listing: AdminEduListingItem | null;
  }>();

  // 只声明这两个事件：裸 n-modal 不走 useModal，不存在 register 事件（BUG-18 防线）
  const emit = defineEmits<{
    (e: 'update:show', val: boolean): void;
    (e: 'success'): void;
  }>();

  const rejectReason = ref('');
  const auditing = ref(false);

  const statusTag = computed(() => getTagConfig(EDU_LISTING_STATUS_TAGS, props.listing?.status));
  const typeTag = computed(() => getTagConfig(EDU_LISTING_TYPE_TAGS, props.listing?.listing_type));

  const priceText = computed(() => {
    const listing = props.listing;
    if (!listing || listing.price === null || listing.price === undefined || listing.price === '') {
      return '面议';
    }
    const unit = listing.price_unit ? ` ${listing.price_unit}` : '';
    return `¥${Number(listing.price).toFixed(2)}${unit}`;
  });

  // 打开时按当前这条信息重置本地输入，关闭后再打开另一条不残留上一条内容
  watch(
    () => props.show,
    (val) => {
      if (!val) return;
      rejectReason.value = '';
      auditing.value = false;
    }
  );

  async function submit(status: 'approved' | 'rejected' | 'offline', reason?: string) {
    if (!props.listing) return;
    auditing.value = true;
    try {
      await reviewEduListing(props.listing.id, { status, reject_reason: reason ?? null });
      window.$message?.success('操作成功');
      emit('success');
      emit('update:show', false);
    } catch {
      // 后端 detail 已由 alova 全局响应拦截器提示，此处保持弹窗打开且不误标为已变更
    } finally {
      auditing.value = false;
    }
  }

  function handleApprove() {
    submit('approved');
  }

  function handleReject() {
    const reason = rejectReason.value.trim();
    if (!reason) {
      window.$message?.warning('请填写驳回理由');
      return;
    }
    submit('rejected', reason);
  }

  function handleOffline() {
    submit('offline');
  }
</script>

<style scoped>
  .listing-desc {
    font-size: 14px;
    line-height: 1.7;
    color: #333;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .listing-image {
    border-radius: 6px;
    overflow: hidden;
  }
</style>
