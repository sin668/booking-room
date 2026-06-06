<template>
  <n-modal
    :show="showModal"
    :show-icon="false"
    preset="dialog"
    style="width: 920px; max-width: calc(100vw - 32px)"
    :title="editData ? '编辑活动' : '新建活动'"
    @update:show="(val: boolean) => emit('update:show', val)"
  >
    <n-spin :show="detailLoading">
      <n-form
        ref="formRef"
        :model="formValues"
        :rules="rules"
        label-placement="left"
        :label-width="90"
        class="py-4"
      >
        <n-form-item label="标题" path="title">
          <n-input
            v-model:value="formValues.title"
            placeholder="请输入标题"
            :maxlength="100"
            show-count
          />
        </n-form-item>

        <n-form-item label="描述" path="description">
          <n-input
            v-model:value="formValues.description"
            type="textarea"
            placeholder="请输入描述"
            :maxlength="500"
            show-count
            :rows="3"
          />
        </n-form-item>

        <n-form-item label="活动正文" path="content_html">
          <div class="activity-rich-editor">
            <QuillEditor
              v-model:content="formValues.content_html"
              content-type="html"
              theme="snow"
              :toolbar="richTextToolbar"
              placeholder="请输入活动规则、图文说明或使用须知"
            />
          </div>
        </n-form-item>

        <n-form-item label="封面图" path="cover_image">
          <n-space vertical>
            <n-upload :max="1" accept="image/*" :custom-request="handleUpload">
              <n-button>上传图片</n-button>
            </n-upload>
            <n-image
              v-if="formValues.cover_image"
              :src="formValues.cover_image"
              width="80"
              height="80"
              object-fit="cover"
              preview-disabled
            />
          </n-space>
        </n-form-item>

        <n-form-item label="参与人数" path="participant_count">
          <n-input-number
            v-model:value="formValues.participant_count"
            :min="0"
            style="width: 100%"
          />
        </n-form-item>

        <n-form-item label="排序值" path="sort_order">
          <n-input-number v-model:value="formValues.sort_order" style="width: 100%" />
        </n-form-item>

        <n-form-item label="是否上架" path="is_active">
          <n-switch v-model:value="formValues.is_active" />
        </n-form-item>

        <n-form-item label="活动卡券">
          <ActivityCouponConfig
            :coupons="formValues.activity_coupons || []"
            @update:coupons="(coupons) => (formValues.activity_coupons = coupons)"
          />
        </n-form-item>
      </n-form>
    </n-spin>

    <template #action>
      <n-space>
        <n-button @click="() => emit('update:show', false)">取消</n-button>
        <n-button type="info" :loading="formBtnLoading" @click="confirmForm">确定</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script lang="ts" setup>
  import { computed, reactive, ref, watch } from 'vue';
  import type { FormInst, FormRules, UploadFileInfo } from 'naive-ui';
  import { QuillEditor } from '@vueup/vue-quill';
  import '@vueup/vue-quill/dist/vue-quill.snow.css';
  import {
    createActivity,
    getActivityById,
    updateActivity,
    type ActivityCouponFormItem,
    type ActivityFormParams,
    type ActivityItem,
  } from '@/api/activity';
  import { uploadImage } from '@/api/upload';
  import ActivityCouponConfig from './ActivityCouponConfig.vue';
  import { validateActivityCoupons } from './builders';

  const props = defineProps<{
    show: boolean;
    editData: ActivityItem | null;
  }>();

  const emit = defineEmits<{
    (e: 'update:show', value: boolean): void;
    (e: 'success'): void;
  }>();

  const showModal = computed({
    get: () => props.show,
    set: (val: boolean) => emit('update:show', val),
  });

  const formRef = ref<FormInst | null>(null);
  const formBtnLoading = ref(false);
  const detailLoading = ref(false);

  const richTextToolbar = [
    ['bold', 'italic', 'underline', 'strike'],
    [{ header: [1, 2, 3, false] }],
    [{ list: 'ordered' }, { list: 'bullet' }],
    [{ align: [] }],
    ['link', 'image'],
    ['clean'],
  ];

  const defaultValues: ActivityFormParams = {
    title: '',
    description: '',
    content_html: '',
    cover_image: '',
    participant_count: 0,
    sort_order: 0,
    is_active: true,
    activity_coupons: [],
  };

  const formValues = reactive<ActivityFormParams>({ ...defaultValues });

  const rules: FormRules = {
    title: {
      required: true,
      trigger: ['blur', 'input'],
      message: '请输入标题',
    },
  };

  watch(
    () => props.show,
    async (val) => {
      if (!val) return;
      if (props.editData) {
        await loadActivityDetail(props.editData);
      } else {
        resetFormValues();
      }
    }
  );

  function resetFormValues() {
    Object.assign(formValues, {
      ...defaultValues,
      activity_coupons: [],
    });
  }

  function fillFormValues(data: ActivityItem) {
    formValues.title = data.title;
    formValues.description = data.description ?? '';
    formValues.content_html = data.content_html ?? '';
    formValues.cover_image = data.cover_image ?? '';
    formValues.participant_count = data.participant_count;
    formValues.sort_order = data.sort_order;
    formValues.is_active = data.is_active;
    formValues.activity_coupons = cloneActivityCoupons(data.activity_coupons || []);
  }

  function cloneActivityCoupons(coupons: ActivityCouponFormItem[]): ActivityCouponFormItem[] {
    return coupons.map((coupon, index) => {
      const template = coupon.coupon;
      return {
        ...coupon,
        coupon_id: coupon.coupon_id ?? template?.id ?? null,
        total_quantity: coupon.total_quantity ?? 0,
        claimed_quantity: coupon.claimed_quantity ?? 0,
        per_user_limit: coupon.per_user_limit ?? 1,
        claim_starts_at: coupon.claim_starts_at ?? null,
        claim_ends_at: coupon.claim_ends_at ?? null,
        is_active: coupon.is_active ?? true,
        sort_order: coupon.sort_order ?? index + 1,
        display_title: coupon.display_title ?? '',
        display_description: coupon.display_description ?? '',
        coupon_title: coupon.coupon_title ?? template?.name ?? '',
        coupon_type: coupon.coupon_type ?? template?.type ?? '',
        discount_rule: coupon.discount_rule ?? formatCouponRule(template),
        valid_from: coupon.valid_from ?? template?.valid_from ?? null,
        expires_at: coupon.expires_at ?? template?.expires_at ?? null,
      };
    });
  }

  async function loadActivityDetail(data: ActivityItem) {
    fillFormValues(data);
    detailLoading.value = true;
    try {
      const detail = await getActivityById(data.id);
      fillFormValues(detail);
    } catch (error) {
      window['$message'].error(getReadableError(error, '活动详情加载失败，请稍后重试'));
    } finally {
      detailLoading.value = false;
    }
  }

  async function handleUpload({
    file,
    onFinish,
    onError,
  }: {
    file: UploadFileInfo;
    onFinish: () => void;
    onError: () => void;
  }) {
    if (!file.file) {
      onError();
      return;
    }
    try {
      const result = await uploadImage(file.file, 'activity-cover');
      formValues.cover_image = result.url;
      onFinish();
    } catch {
      onError();
      window['$message'].error('上传失败');
    }
  }

  function confirmForm() {
    formBtnLoading.value = true;
    formRef.value?.validate(async (errors) => {
      if (!errors) {
        const couponErrors = validateActivityCoupons(formValues.activity_coupons || []);
        if (couponErrors.length > 0) {
          window['$message'].error(couponErrors[0]);
          formBtnLoading.value = false;
          return;
        }
        try {
          const payload = normalizeActivityPayload(formValues);
          if (props.editData) {
            await updateActivity(props.editData.id, payload);
          } else {
            await createActivity(payload);
          }
          window['$message'].success('操作成功');
          emit('update:show', false);
          emit('success');
        } catch (error) {
          window['$message'].error(getReadableError(error, '操作失败，请检查活动正文或卡券配置'));
        }
      }
      formBtnLoading.value = false;
    });
  }

  function normalizeActivityPayload(values: ActivityFormParams): ActivityFormParams {
    return {
      ...values,
      content_html: values.content_html || '',
      activity_coupons: (values.activity_coupons || [])
        .filter((coupon) => !coupon._destroy)
        .map((coupon, index) => ({
          ...coupon,
          sort_order: coupon.sort_order || index + 1,
          display_title: coupon.display_title || '',
          display_description: coupon.display_description || '',
        })),
    };
  }

  function formatCouponRule(template: ActivityCouponFormItem['coupon']) {
    if (!template) return '';
    const minAmount = Number(template.min_order_amount ?? 0);
    const discountAmount = Number(template.discount_amount ?? 0);
    if (template.type === 'threshold_amount_off') {
      return `满 ${minAmount} 减 ${discountAmount}`;
    }
    if (template.type === 'amount_off') {
      return `立减 ${discountAmount}`;
    }
    if (template.type === 'percentage_off') {
      return `${template.discount_percent ?? ''} 折`;
    }
    return template.type || '';
  }

  function getReadableError(error: unknown, fallback: string) {
    if (error instanceof Error && error.message) {
      return error.message;
    }
    return fallback;
  }
</script>

<style scoped lang="less">
  .activity-rich-editor {
    width: 100%;

    :deep(.ql-container) {
      min-height: 220px;
    }

    :deep(.ql-editor) {
      min-height: 220px;
    }
  }
</style>
