<template>
  <n-modal
    :show="show"
    preset="card"
    title="评价审核"
    style="width: 720px; max-width: 95vw"
    :mask-closable="false"
    @update:show="(val) => emit('update:show', val)"
  >
    <n-flex v-if="review" vertical :size="16">
      <!-- 发表者 -->
      <div class="flex items-center gap-2">
        <n-avatar :src="review.user_avatar || undefined" round :size="40" style="flex-shrink: 0" />
        <div class="flex flex-col">
          <span class="text-sm font-medium">{{ review.user_nickname || '匿名用户' }}</span>
          <span class="text-xs" style="color: #999">
            订单号 {{ review.booking_id }} · 发表于 {{ formatAdminDateTime(review.created_at) }}
          </span>
        </div>
        <n-tag v-if="review.is_anonymous" type="info" size="small" :bordered="false">匿名</n-tag>
        <n-tag :type="statusTag.type" size="small">{{ statusTag.label }}</n-tag>
      </div>

      <n-rate :value="review.rating" readonly size="small" />

      <!-- 评价全文 -->
      <div class="review-content">{{ review.content }}</div>

      <!-- 图片：n-image-group 让预览可在同一条评价的多张图片间前后翻阅 -->
      <n-image-group v-if="review.images.length">
        <div class="flex flex-wrap gap-2">
          <n-image
            v-for="url in review.images"
            :key="url"
            :src="url"
            width="88"
            height="88"
            object-fit="cover"
            class="review-image"
          />
        </div>
      </n-image-group>

      <!-- 标签 -->
      <div v-if="review.tags.length" class="flex flex-wrap gap-2">
        <n-tag v-for="tag in review.tags" :key="tag" size="small" :bordered="false">
          {{ tag }}
        </n-tag>
      </div>

      <n-descriptions :column="2" label-placement="left" size="small" bordered>
        <n-descriptions-item label="所属学习室">{{ review.room_name || '-' }}</n-descriptions-item>
        <n-descriptions-item label="座位编号">{{ review.seat_number || '-' }}</n-descriptions-item>
        <n-descriptions-item label="所属课程">{{ review.course_name || '-' }}</n-descriptions-item>
        <n-descriptions-item label="所属老师">{{ review.teacher_name || '-' }}</n-descriptions-item>
        <n-descriptions-item label="订单标识">{{ review.booking_id }}</n-descriptions-item>
        <n-descriptions-item label="当前状态">{{ statusTag.label }}</n-descriptions-item>
      </n-descriptions>

      <n-alert v-if="review.reject_reason" type="warning" :bordered="false">
        既有驳回理由：{{ review.reject_reason }}
      </n-alert>
      <n-alert v-if="review.reply_content" type="info" :bordered="false">
        既有机构回复：{{ review.reply_content }}
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
            v-permission="{ action: ['training:reviews:audit'] }"
            type="primary"
            :loading="auditing"
            @click="handleApprove"
          >
            通过
          </n-button>
          <n-button
            v-permission="{ action: ['training:reviews:audit'] }"
            type="error"
            :loading="auditing"
            @click="handleReject"
          >
            驳回
          </n-button>
        </div>
      </div>

      <n-divider style="margin: 0" />

      <!-- 机构回复 -->
      <div class="flex flex-col gap-2">
        <span class="text-sm font-medium">机构回复</span>
        <n-input
          v-model:value="replyContent"
          type="textarea"
          :maxlength="500"
          :rows="3"
          show-count
          placeholder="回复内容，留空保存表示清空既有回复"
        />
        <div>
          <n-button
            v-permission="{ action: ['training:reviews:reply'] }"
            type="primary"
            secondary
            :loading="replying"
            @click="handleSaveReply"
          >
            保存回复
          </n-button>
        </div>
      </div>
    </n-flex>
  </n-modal>
</template>

<script lang="ts" setup>
  import { computed, ref, watch } from 'vue';
  import {
    updateAdminReviewReply,
    updateAdminReviewStatus,
    type AdminReviewItem,
  } from '@/api/review';
  import { formatAdminDateTime, getTagConfig } from '@/views/business/shared/formatters';
  import { REVIEW_STATUS_TAGS } from '@/views/business/shared/options';

  const props = defineProps<{
    show: boolean;
    review: AdminReviewItem | null;
  }>();

  // 只声明这两个事件：裸 n-modal 不走 useModal，不存在 register 事件（BUG-18 防线）
  const emit = defineEmits<{
    (e: 'update:show', val: boolean): void;
    (e: 'success'): void;
  }>();

  const rejectReason = ref('');
  const replyContent = ref('');
  const auditing = ref(false);
  const replying = ref(false);

  const statusTag = computed(() => getTagConfig(REVIEW_STATUS_TAGS, props.review?.status));

  // 打开时按当前这条评价重置本地输入，关闭后再打开另一条不残留上一条内容
  watch(
    () => props.show,
    (val) => {
      if (!val) return;
      rejectReason.value = '';
      replyContent.value = props.review?.reply_content || '';
      auditing.value = false;
      replying.value = false;
    }
  );

  async function handleApprove() {
    if (!props.review) return;
    auditing.value = true;
    try {
      await updateAdminReviewStatus(props.review.id, { status: 'approved' });
      window.$message?.success('已通过审核');
      emit('success');
      emit('update:show', false);
    } catch {
      // 后端 detail 已由 alova 全局响应拦截器提示，此处保持弹窗打开且不误标为已变更
    } finally {
      auditing.value = false;
    }
  }

  async function handleReject() {
    if (!props.review) return;
    const reason = rejectReason.value.trim();
    if (!reason) {
      window.$message?.warning('请填写驳回理由');
      return;
    }
    auditing.value = true;
    try {
      await updateAdminReviewStatus(props.review.id, {
        status: 'rejected',
        reject_reason: reason,
      });
      window.$message?.success('已驳回该评价');
      emit('success');
      emit('update:show', false);
    } catch {
      // 同上：全局拦截器已提示，不重复 toast
    } finally {
      auditing.value = false;
    }
  }

  async function handleSaveReply() {
    if (!props.review) return;
    replying.value = true;
    try {
      await updateAdminReviewReply(props.review.id, replyContent.value.trim());
      window.$message?.success('回复已保存');
      emit('success');
      emit('update:show', false);
    } catch {
      // 同上：全局拦截器已提示，不重复 toast
    } finally {
      replying.value = false;
    }
  }
</script>

<style scoped>
  .review-content {
    font-size: 14px;
    line-height: 1.7;
    color: #333;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .review-image {
    border-radius: 6px;
    overflow: hidden;
  }
</style>
