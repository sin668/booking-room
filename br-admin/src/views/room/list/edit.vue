<template>
  <n-flex vertical>
    <!-- 顶部操作栏 -->
    <n-card :bordered="false">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <n-button text @click="goBack">
            <template #icon><n-icon><ArrowLeftOutlined /></n-icon></template>
          </n-button>
          <h2 class="text-lg font-semibold m-0">{{ isEdit ? '编辑学习室' : '新建学习室' }}</h2>
        </div>
        <n-space>
          <n-button @click="goBack">取消</n-button>
          <n-button type="primary" :loading="saving" @click="handleSave">
            <template #icon><n-icon><SaveOutlined /></n-icon></template>
            保存学习室
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
              <n-form-item-gi :span="2" label="名称" path="name">
                <n-input
                  v-model:value="formValues.name"
                  placeholder="请输入学习室名称"
                  :maxlength="100"
                  show-count
                />
              </n-form-item-gi>
              <n-form-item-gi :span="2" label="地址" path="address">
                <n-input
                  v-model:value="formValues.address"
                  placeholder="请输入详细地址"
                  :maxlength="255"
                  show-count
                />
              </n-form-item-gi>
              <n-form-item-gi label="所在城市" path="city_id">
                <n-select
                  v-model:value="formValues.city_id"
                  :options="cityOptions"
                  placeholder="请选择所在城市"
                  clearable
                />
              </n-form-item-gi>
              <n-form-item-gi label="类型" path="room_type">
                <n-select v-model:value="formValues.room_type" :options="roomTypeOptions" />
              </n-form-item-gi>
              <n-form-item-gi label="营业时间" path="business_hours" :show-feedback="false">
                <n-input
                  v-model:value="formValues.business_hours"
                  placeholder="如 08:00-22:00"
                  :maxlength="50"
                />
              </n-form-item-gi>
              <n-form-item-gi label="最低价格" path="min_price" :show-feedback="false">
                <n-input-number
                  v-model:value="formValues.min_price"
                  :min="0"
                  :precision="2"
                  style="width: 100%"
                />
              </n-form-item-gi>
            </n-grid>
          </n-form>
        </n-card>

        <!-- 封面图片 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><PictureOutlined /></n-icon>
              <span class="text-sm font-bold">封面图片</span>
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
              <n-upload
                :max="1"
                accept="image/*"
                :custom-request="handleCoverUpload"
                :show-file-list="false"
              >
                <n-button secondary type="info">上传图片</n-button>
              </n-upload>
              <n-text depth="3" class="text-xs mt-2 block"
                >建议尺寸 750×420px，支持 JPG/PNG 格式，最大 2MB</n-text
              >
            </div>
          </div>
        </n-card>

        <!-- 环境图片 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><FileImageOutlined /></n-icon>
              <span class="text-sm font-bold">环境图片</span>
            </div>
          </template>
          <div class="flex flex-wrap gap-3">
            <div
              v-for="(image, index) in environmentImages"
              :key="image"
              class="env-image-item"
            >
              <n-image
                :src="image"
                width="120"
                height="90"
                object-fit="cover"
                preview-disabled
              />
              <n-button
                class="env-image-remove"
                size="tiny"
                quaternary
                circle
                @click="removeEnvironmentImage(index)"
              >
                <template #icon><n-icon><CloseOutlined /></n-icon></template>
              </n-button>
            </div>
            <n-upload
              v-if="environmentImages.length < 5"
              :max="1"
              accept="image/*"
              :custom-request="handleEnvironmentUpload"
              :show-file-list="false"
            >
              <div class="env-image-add">
                <n-icon size="20"><PlusOutlined /></n-icon>
                <n-text depth="3" class="text-xs">上传图片</n-text>
              </div>
            </n-upload>
          </div>
          <n-text depth="3" class="text-xs mt-3 block"
            >最多上传 5 张环境图片，当前 {{ environmentImages.length }}/5</n-text
          >
        </n-card>

        <!-- 简介 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><AlignLeftOutlined /></n-icon>
              <span class="text-sm font-bold">简介</span>
            </div>
          </template>
          <n-input
            v-model:value="formValues.description"
            type="textarea"
            placeholder="请输入学习室简介"
            :maxlength="1000"
            show-count
            :rows="4"
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
            <n-switch :value="isPublished" @update:value="handlePublishChange" />
            <n-text depth="3" class="text-xs">{{ isPublished ? '已上架' : '已下架' }}</n-text>
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
  import {
    ArrowLeftOutlined,
    SaveOutlined,
    InfoCircleOutlined,
    PictureOutlined,
    FileImageOutlined,
    AlignLeftOutlined,
    SettingOutlined,
    CloseOutlined,
    PlusOutlined,
  } from '@vicons/antd';
  import {
    createRoom,
    getCityList,
    getRoomById,
    updateRoom,
    type CityItem,
    type RoomType,
  } from '@/api/room';
  import { uploadImage } from '@/api/upload';
  import { useTabsViewStore } from '@/store/modules/tabsView';

  interface RoomFormValues {
    name: string;
    address: string;
    description: string;
    cover_image: string;
    business_hours: string;
    city_id: number | null;
    room_type: RoomType;
    min_price: number;
  }

  const route = useRoute();
  const router = useRouter();
  const tabsViewStore = useTabsViewStore();
  const roomId = computed(() => {
    const id = route.params.id;
    return id ? Number(id) : null;
  });
  const isEdit = computed(() => roomId.value !== null);

  const formRef = ref<FormInst | null>(null);
  const loading = ref(false);
  const saving = ref(false);

  const cityOptions = ref<{ label: string; value: number }[]>([]);
  const roomTypeOptions = [
    { label: '学习室', value: 'study' },
    { label: '培训室', value: 'training' },
    { label: '综合室', value: 'comprehensive' },
  ];

  const formValues = reactive<RoomFormValues>({
    name: '',
    address: '',
    description: '',
    cover_image: '',
    business_hours: '',
    city_id: null,
    room_type: 'study',
    min_price: 0,
  });
  const environmentImages = ref<string[]>([]);
  const isPublished = ref(true);

  const rules: FormRules = {
    name: { required: true, message: '请输入名称', trigger: ['blur', 'input'] },
    address: { required: true, message: '请输入地址', trigger: ['blur', 'input'] },
  };

  onMounted(async () => {
    // 进入编辑页时移除列表 tab，让编辑页接管标签位置
    removeTab((t) => t.name === 'room_list');
    await loadCityOptions();
    if (roomId.value) {
      await loadRoom(roomId.value);
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
      router.push({ name: 'room_list' });
    }
  }

  async function loadCityOptions() {
    try {
      const cities: CityItem[] = await getCityList();
      cityOptions.value = cities.map((city) => ({ label: city.name, value: city.id }));
    } catch {
      // 城市加载失败不阻断编辑
    }
  }

  async function loadRoom(id: number) {
    loading.value = true;
    try {
      const detail = await getRoomById(id);
      formValues.name = detail.name;
      formValues.address = detail.address;
      formValues.description = detail.description ?? '';
      formValues.cover_image = detail.cover_image ?? '';
      formValues.business_hours = detail.business_hours ?? '';
      formValues.city_id = detail.city_id;
      formValues.room_type = detail.room_type;
      formValues.min_price = Number(detail.min_price ?? 0);
      environmentImages.value = [...(detail.environment_images ?? [])];
      isPublished.value = detail.status === 'open';
    } catch (error) {
      window['$message']?.error(getReadableError(error, '学习室详情加载失败，请稍后重试'));
    } finally {
      loading.value = false;
    }
  }

  // 封面上传
  async function handleCoverUpload({
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
      const result = await uploadImage(file.file, 'room-cover');
      formValues.cover_image = result.url;
      onFinish();
    } catch {
      onError();
      window['$message']?.error('上传失败');
    }
  }

  // 环境图片上传
  async function handleEnvironmentUpload({
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
    if (environmentImages.value.length >= 5) {
      onError();
      window['$message']?.warning('最多上传 5 张环境图片');
      return;
    }
    try {
      const result = await uploadImage(file.file, 'room-environment');
      environmentImages.value.push(result.url);
      onFinish();
    } catch {
      onError();
      window['$message']?.error('上传失败');
    }
  }

  function removeEnvironmentImage(index: number) {
    environmentImages.value.splice(index, 1);
  }

  function handlePublishChange(value: boolean) {
    isPublished.value = value;
  }

  // 保存学习室
  async function handleSave() {
    try {
      await formRef.value?.validate();
    } catch {
      window['$message']?.warning('请检查必填项');
      return;
    }

    saving.value = true;
    let saved = false;
    try {
      const payload = {
        name: formValues.name,
        address: formValues.address,
        description: formValues.description || '',
        cover_image: formValues.cover_image || '',
        environment_images: environmentImages.value,
        business_hours: formValues.business_hours || '',
        city_id: formValues.city_id,
        room_type: formValues.room_type,
        min_price: formValues.min_price,
        status: isPublished.value ? 'open' : 'closed',
      };
      if (roomId.value) {
        await updateRoom(roomId.value, payload);
        window['$message']?.success('学习室更新成功');
        saved = true;
      } else {
        await createRoom(payload);
        window['$message']?.success('学习室创建成功');
        saved = true;
      }
    } catch (error) {
      window['$message']?.error(getReadableError(error, '保存失败，请检查填写内容'));
    } finally {
      saving.value = false;
    }
    // 保存成功后返回列表页
    if (saved) {
      backToList();
    }
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
  .env-image-item {
    position: relative;
    width: 120px;
    height: 90px;
    border-radius: 0.5rem;
    overflow: hidden;
    border: 1px solid #e5e7eb;
  }

  .env-image-remove {
    position: absolute;
    top: 2px;
    right: 2px;
    background: rgba(0, 0, 0, 0.45);
    color: #fff;
  }

  .env-image-add {
    width: 120px;
    height: 90px;
    border: 1px dashed #d1d5db;
    border-radius: 0.5rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
    cursor: pointer;

    &:hover {
      border-color: #4f6ef7;
    }
  }

  .flex {
    display: flex;
  }
  .flex-wrap {
    flex-wrap: wrap;
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
  .mt-3 {
    margin-top: 0.75rem;
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
