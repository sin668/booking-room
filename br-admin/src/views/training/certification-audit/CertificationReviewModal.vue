<template>
  <n-modal
    :show="show"
    preset="card"
    :title="isPending ? '审核认证' : '查看资料'"
    style="width: 640px; max-width: 95vw"
    :mask-closable="false"
    @update:show="(val) => emit('update:show', val)"
  >
    <n-flex v-if="cert" vertical :size="16">
      <!-- 用户 -->
      <div class="flex items-center gap-2">
        <n-avatar round :size="44" style="flex-shrink: 0" />
        <div class="flex flex-col">
          <span class="text-sm font-medium">{{ cert.user_nickname || '-' }}</span>
          <span class="text-xs" style="color: #999">{{ cert.user_phone || '' }}</span>
        </div>
        <n-tag :type="statusTag.type" size="small">{{ statusTag.label }}</n-tag>
      </div>

      <!-- 实名认证 -->
      <n-descriptions
        v-if="cert.verification_type === 'real_name'"
        :column="2"
        label-placement="left"
        size="small"
        bordered
      >
        <n-descriptions-item label="姓名">{{ cert.real_name || '-' }}</n-descriptions-item>
        <n-descriptions-item label="身份证号">
          {{ cert.id_card_masked || '-' }}
        </n-descriptions-item>
      </n-descriptions>

      <!-- 学历认证 -->
      <template v-if="cert.verification_type === 'education'">
        <n-descriptions :column="2" label-placement="left" size="small" bordered>
          <n-descriptions-item label="学校">{{ cert.school || '-' }}</n-descriptions-item>
          <n-descriptions-item label="学历">
            {{ cert.education_level || '-' }}
          </n-descriptions-item>
          <n-descriptions-item label="专业">{{ cert.major || '-' }}</n-descriptions-item>
          <n-descriptions-item label="毕业年份">
            {{ cert.graduation_year || '-' }}
          </n-descriptions-item>
        </n-descriptions>
        <div v-if="cert.diploma_image_url">
          <div class="image-label">学历证书：</div>
          <n-image :src="cert.diploma_image_url" width="200" object-fit="cover" />
        </div>
      </template>

      <!-- 教师资格 -->
      <template v-if="cert.verification_type === 'teacher'">
        <n-descriptions :column="2" label-placement="left" size="small" bordered>
          <n-descriptions-item label="证书号">
            {{ cert.teacher_certificate_number || '-' }}
          </n-descriptions-item>
          <n-descriptions-item label="科目">
            {{ cert.teaching_subject || '-' }}
          </n-descriptions-item>
        </n-descriptions>
        <div v-if="cert.certificate_image_url">
          <div class="image-label">资格证书：</div>
          <n-image :src="cert.certificate_image_url" width="200" object-fit="cover" />
        </div>
      </template>

      <n-alert v-if="cert.rejection_reason" type="warning" :bordered="false">
        既有拒绝理由：{{ cert.rejection_reason }}
      </n-alert>

      <template v-if="isPending">
        <n-divider style="margin: 0" />
        <div class="flex flex-col gap-3">
          <div class="flex items-center gap-3">
            <span class="text-sm font-medium" style="width: 72px">审核结果</span>
            <n-radio-group v-model:value="approved">
              <n-radio :value="true">通过</n-radio>
              <n-radio :value="false">拒绝</n-radio>
            </n-radio-group>
          </div>
          <div v-if="!approved" class="flex items-start gap-3">
            <span class="text-sm font-medium" style="width: 72px; line-height: 34px">
              拒绝原因
            </span>
            <n-input
              v-model:value="rejectionReason"
              type="textarea"
              :maxlength="200"
              :rows="3"
              show-count
              placeholder="请输入拒绝原因"
              style="flex: 1"
            />
          </div>
          <div class="flex gap-2" style="justify-content: flex-end">
            <n-button @click="emit('update:show', false)">取消</n-button>
            <n-button
              v-permission="{ action: ['training:certification:audit:action'] }"
              type="primary"
              :loading="submitting"
              @click="handleSubmit"
            >
              提交审核
            </n-button>
          </div>
        </div>
      </template>
    </n-flex>
  </n-modal>
</template>

<script lang="ts" setup>
  import { computed, ref, watch } from 'vue';
  import { reviewCertification, type CertificationItem } from '@/api/certification';

  const props = defineProps<{
    show: boolean;
    cert: CertificationItem | null;
  }>();

  // 只声明这两个事件：裸 n-modal 不走 useModal，不存在 register 事件（BUG-18 防线）
  const emit = defineEmits<{
    (e: 'update:show', val: boolean): void;
    (e: 'success'): void;
  }>();

  const CERT_STATUS_TAGS: Record<string, { label: string; type: 'warning' | 'success' | 'error' | 'default' }> = {
    pending: { label: '待审核', type: 'warning' },
    approved: { label: '已通过', type: 'success' },
    rejected: { label: '已拒绝', type: 'error' },
  };

  const approved = ref(true);
  const rejectionReason = ref('');
  const submitting = ref(false);

  const isPending = computed(() => props.cert?.status === 'pending');
  const statusTag = computed(() => {
    const key = String(props.cert?.status ?? '');
    return CERT_STATUS_TAGS[key] || { label: key || '未知', type: 'default' as const };
  });

  // 打开时按当前这条认证重置本地输入，关闭后再打开另一条不残留上一条内容
  watch(
    () => props.show,
    (val) => {
      if (!val) return;
      approved.value = true;
      rejectionReason.value = '';
      submitting.value = false;
    }
  );

  async function handleSubmit() {
    if (!props.cert) return;
    if (!approved.value && !rejectionReason.value.trim()) {
      window.$message?.warning('请输入拒绝原因');
      return;
    }
    submitting.value = true;
    try {
      await reviewCertification(props.cert.id, {
        approved: approved.value,
        rejection_reason: approved.value ? undefined : rejectionReason.value.trim(),
      });
      window.$message?.success('审核成功');
      emit('success');
      emit('update:show', false);
    } catch {
      // 后端 detail 已由 alova 全局响应拦截器提示，此处保持弹窗打开且不误标为已变更
    } finally {
      submitting.value = false;
    }
  }
</script>

<style scoped>
  .image-label {
    font-size: 14px;
    color: #666;
    margin-bottom: 8px;
  }
</style>
