<template>
  <n-flex vertical>
    <!-- 顶部操作栏 -->
    <n-card :bordered="false">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <n-button text @click="goBack">
            <template #icon><n-icon><ArrowLeftOutlined /></n-icon></template>
          </n-button>
          <h2 class="text-lg font-semibold m-0">{{ isEdit ? '编辑活动' : '新建活动' }}</h2>
        </div>
        <n-space>
          <n-button @click="goBack">取消</n-button>
          <n-button type="primary" :loading="saving" @click="handleSave">
            <template #icon><n-icon><SaveOutlined /></n-icon></template>
            保存活动
          </n-button>
        </n-space>
      </div>
    </n-card>

    <n-spin :show="loading">
      <div class="max-w-3xl mx-auto w-full space-y-4 py-4">
        <!-- 基本信息 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><InfoCircleOutlined /></n-icon>
              <span class="text-sm font-bold">基本信息</span>
            </div>
          </template>
          <n-form :model="formValues" :rules="rules" ref="formRef" label-placement="top">
            <n-grid :cols="2" :x-gap="16">
              <n-form-item-gi :span="2" label="标题" path="title">
                <n-input
                  v-model:value="formValues.title"
                  placeholder="请输入活动标题"
                  :maxlength="100"
                  show-count
                />
              </n-form-item-gi>
              <n-form-item-gi :span="2" label="描述" path="description">
                <n-input
                  v-model:value="formValues.description"
                  type="textarea"
                  placeholder="请输入活动描述"
                  :maxlength="500"
                  show-count
                  :rows="3"
                />
              </n-form-item-gi>
              <n-form-item-gi label="参与人数" path="participant_count" :show-feedback="false">
                <n-input-number
                  v-model:value="formValues.participant_count"
                  :min="0"
                  style="width: 100%"
                />
              </n-form-item-gi>
              <n-form-item-gi label="排序值" path="sort_order" :show-feedback="false">
                <n-input-number v-model:value="formValues.sort_order" style="width: 100%" />
              </n-form-item-gi>
            </n-grid>
          </n-form>
        </n-card>

        <!-- 活动封面 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><PictureOutlined /></n-icon>
              <span class="text-sm font-bold">活动封面</span>
            </div>
          </template>
          <div class="flex items-start gap-4">
            <div
              class="w-40 h-28 rounded-lg overflow-hidden border border-gray-200 flex-shrink-0 flex items-center justify-center bg-gray-50"
            >
              <n-image
                v-if="formValues.cover_image"
                :src="formValues.cover_image"
                width="160"
                height="112"
                object-fit="cover"
                preview-disabled
              />
              <n-text v-else depth="3" class="text-xs">暂无封面</n-text>
            </div>
            <div class="flex-1">
              <n-upload :max="1" accept="image/*" :custom-request="handleUpload" :show-file-list="false">
                <n-button secondary type="info">上传图片</n-button>
              </n-upload>
              <n-text depth="3" class="text-xs mt-2 block">建议尺寸 750×420px，支持 JPG/PNG 格式，最大 2MB</n-text>
            </div>
          </div>
        </n-card>

        <!-- 活动内容 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><AlignLeftOutlined /></n-icon>
              <span class="text-sm font-bold">活动内容</span>
            </div>
          </template>
          <div class="activity-rich-editor">
            <QuillEditor
              v-model:content="formValues.content_html"
              content-type="html"
              theme="snow"
              :toolbar="richTextToolbar"
              placeholder="请输入活动规则、图文说明或使用须知"
            />
          </div>
        </n-card>

        <!-- 关联卡券 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><GiftOutlined /></n-icon>
              <span class="text-sm font-bold">关联卡券</span>
            </div>
          </template>
          <ActivityCouponConfig
            :coupons="formValues.activity_coupons || []"
            @update:coupons="(coupons) => (formValues.activity_coupons = coupons)"
          />
        </n-card>

        <!-- 发布设置 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><SettingOutlined /></n-icon>
              <span class="text-sm font-bold">发布设置</span>
            </div>
          </template>
          <div class="flex items-center gap-2">
            <n-switch v-model:value="formValues.is_active" />
            <n-text depth="3" class="text-xs">{{ formValues.is_active ? '已上架' : '已下架' }}</n-text>
          </div>
        </n-card>
      </div>
    </n-spin>
  </n-flex>
</template>

<script lang="ts" setup>
  import { computed, onMounted, reactive, ref } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import type { FormInst, FormRules, UploadFileInfo } from 'naive-ui';
  import { QuillEditor } from '@vueup/vue-quill';
  import '@vueup/vue-quill/dist/vue-quill.snow.css';
  import {
    ArrowLeftOutlined,
    SaveOutlined,
    InfoCircleOutlined,
    PictureOutlined,
    AlignLeftOutlined,
    GiftOutlined,
    SettingOutlined,
  } from '@vicons/antd';
  import {
    createActivity,
    getActivityById,
    updateActivity,
    type ActivityCouponFormItem,
    type ActivityFormParams,
  } from '@/api/activity';
  import { uploadImage } from '@/api/upload';
  import { useTabsViewStore } from '@/store/modules/tabsView';
  import ActivityCouponConfig from './ActivityCouponConfig.vue';
  import { validateActivityCoupons } from './builders';

  const route = useRoute();
  const router = useRouter();
  const tabsViewStore = useTabsViewStore();
  const activityId = computed(() => {
    const id = route.params.id;
    return id ? Number(id) : null;
  });
  const isEdit = computed(() => activityId.value !== null);

  const formRef = ref<FormInst | null>(null);
  const loading = ref(false);
  const saving = ref(false);

  const richTextToolbar = [
    ['bold', 'italic', 'underline', 'strike'],
    [{ header: [1, 2, 3, false] }],
    [{ list: 'ordered' }, { list: 'bullet' }],
    [{ align: [] }],
    ['link', 'image'],
    ['clean'],
  ];

  const formValues = reactive<ActivityFormParams>({
    title: '',
    description: '',
    content_html: '',
    cover_image: '',
    participant_count: 0,
    sort_order: 0,
    is_active: true,
    activity_coupons: [],
  });

  const rules: FormRules = {
    title: { required: true, message: '请输入活动标题', trigger: ['blur', 'input'] },
  };

  onMounted(async () => {
    // 进入编辑页时移除列表 tab，让编辑页接管标签位置
    removeTab((t) => t.name === 'activity_list');
    if (activityId.value) {
      await loadActivity(activityId.value);
    }
  });

  // 安全移除匹配的标签页（仅 splice，不影响导航主流程）
  function removeTab(matcher: (t: any) => boolean) {
    try {
      const idx = tabsViewStore.tabsList.findIndex(matcher);
      if (idx > -1) {
        tabsViewStore.tabsList.splice(idx, 1);
      }
    } catch {
      // 标签清理失败不阻断页面逻辑
    }
  }

  // 返回列表页（参考座位管理 router.back 实现）
  function backToList() {
    // 关闭当前编辑页 tab，返回后标签栏恢复为列表页
    removeTab((t) => t.fullPath === route.fullPath);
    if (window.history.state && window.history.state.back) {
      router.back();
    } else {
      router.push({ name: 'activity_list' });
    }
  }

  async function loadActivity(id: number) {
    loading.value = true;
    try {
      const detail = await getActivityById(id);
      formValues.title = detail.title;
      formValues.description = detail.description ?? '';
      formValues.content_html = detail.content_html ?? '';
      formValues.cover_image = detail.cover_image ?? '';
      formValues.participant_count = detail.participant_count;
      formValues.sort_order = detail.sort_order;
      formValues.is_active = detail.is_active;
      formValues.activity_coupons = cloneActivityCoupons(detail.activity_coupons || []);
    } catch (error) {
      window['$message']?.error(getReadableError(error, '活动详情加载失败，请稍后重试'));
    } finally {
      loading.value = false;
    }
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
        claim_starts_at: normalizeDateTimeForPicker(coupon.claim_starts_at),
        claim_ends_at: normalizeDateTimeForPicker(coupon.claim_ends_at),
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

  function normalizeDateTimeForPicker(value: string | null | undefined) {
    if (!value) return null;
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value.slice(0, 19).replace('T', ' ');
    }
    const pad = (num: number) => String(num).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(
      date.getHours()
    )}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
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

  // 封面上传
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
      window['$message']?.error('上传失败');
    }
  }

  // 保存活动
  async function handleSave() {
    try {
      await formRef.value?.validate();
    } catch {
      window['$message']?.warning('请检查必填项');
      return;
    }

    const couponErrors = validateActivityCoupons(formValues.activity_coupons || []);
    if (couponErrors.length > 0) {
      window['$message']?.error(couponErrors[0]);
      return;
    }

    saving.value = true;
    let saved = false;
    try {
      const payload = normalizeActivityPayload(formValues);
      if (activityId.value) {
        await updateActivity(activityId.value, payload);
        window['$message']?.success('活动更新成功');
        saved = true;
      } else {
        await createActivity(payload);
        window['$message']?.success('活动创建成功');
        saved = true;
      }
    } catch (error) {
      window['$message']?.error(getReadableError(error, '保存失败，请检查活动正文或卡券配置'));
    } finally {
      saving.value = false;
    }
    // 保存成功后返回列表页
    if (saved) {
      backToList();
    }
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

  function getReadableError(error: unknown, fallback: string) {
    if (error instanceof Error && error.message) {
      return error.message;
    }
    return fallback;
  }

  function goBack() {
    backToList();
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

  .flex {
    display: flex;
  }
  .items-center {
    align-items: center;
  }
  .items-start {
    align-items: flex-start;
  }
  .justify-center {
    justify-content: center;
  }
  .justify-between {
    justify-content: space-between;
  }
  .gap-2 {
    gap: 0.5rem;
  }
  .gap-3 {
    gap: 0.75rem;
  }
  .gap-4 {
    gap: 1rem;
  }
  .space-y-4 > * + * {
    margin-top: 1rem;
  }
  .w-full {
    width: 100%;
  }
  .w-40 {
    width: 10rem;
  }
  .h-28 {
    height: 7rem;
  }
  .max-w-3xl {
    max-width: 48rem;
  }
  .mx-auto {
    margin-left: auto;
    margin-right: auto;
  }
  .py-4 {
    padding-top: 1rem;
    padding-bottom: 1rem;
  }
  .mt-2 {
    margin-top: 0.5rem;
  }
  .m-0 {
    margin: 0;
  }
  .block {
    display: block;
  }
  .text-xs {
    font-size: 0.75rem;
  }
  .text-sm {
    font-size: 0.875rem;
  }
  .text-lg {
    font-size: 1.125rem;
  }
  .font-semibold {
    font-weight: 600;
  }
  .font-bold {
    font-weight: 700;
  }
  .rounded-lg {
    border-radius: 0.5rem;
  }
  .overflow-hidden {
    overflow: hidden;
  }
  .flex-shrink-0 {
    flex-shrink: 0;
  }
  .flex-1 {
    flex: 1 1 0%;
  }
  .border {
    border-width: 1px;
    border-style: solid;
  }
  .border-gray-200 {
    border-color: #e5e7eb;
  }
  .bg-gray-50 {
    background-color: #f9fafb;
  }
  .shadow-sm {
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  }
</style>
