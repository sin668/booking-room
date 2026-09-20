<template>
  <n-flex vertical>
    <n-card :bordered="false">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <n-button text @click="goBack">
            <template #icon><n-icon><ArrowLeftOutlined /></n-icon></template>
          </n-button>
          <h2 class="text-lg font-semibold m-0">{{ isEdit ? '编辑用户' : '新增用户' }}</h2>
        </div>
        <n-space>
          <n-button @click="goBack">取消</n-button>
          <n-button type="primary" :loading="saving" @click="handleSave">
            <template #icon><n-icon><SaveOutlined /></n-icon></template>
            保存
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
              <n-form-item-gi label="用户名" path="username">
                <n-input
                  v-model:value="formValues.username"
                  placeholder="请输入用户名"
                  :maxlength="50"
                  :disabled="isEdit"
                />
              </n-form-item-gi>
              <n-form-item-gi label="手机号" path="phone">
                <n-input
                  v-model:value="formValues.phone"
                  placeholder="请输入手机号"
                  :maxlength="20"
                  :disabled="isEdit"
                />
              </n-form-item-gi>
              <n-form-item-gi v-if="!isEdit" label="密码" path="password">
                <n-input
                  v-model:value="formValues.password"
                  type="password"
                  show-password-on="click"
                  placeholder="请输入密码"
                  :maxlength="50"
                />
              </n-form-item-gi>
              <n-form-item-gi label="昵称" path="nickname">
                <n-input v-model:value="formValues.nickname" placeholder="请输入昵称" :maxlength="50" />
              </n-form-item-gi>
              <n-form-item-gi v-if="isEdit" label="邮箱" path="email">
                <n-input v-model:value="formValues.email" placeholder="请输入邮箱" :maxlength="100" />
              </n-form-item-gi>
              <n-form-item-gi v-if="isEdit" label="状态" path="status">
                <n-radio-group v-model:value="formValues.status">
                  <n-space>
                    <n-radio value="active">正常</n-radio>
                    <n-radio value="disabled">禁用</n-radio>
                  </n-space>
                </n-radio-group>
              </n-form-item-gi>
            </n-grid>
          </n-form>
        </n-card>

        <!-- 头像 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><PictureOutlined /></n-icon>
              <span class="text-sm font-bold">头像</span>
            </div>
          </template>
          <div class="flex items-start gap-4">
            <div class="w-24 h-24 rounded-full overflow-hidden border border-gray-200 flex-shrink-0 flex items-center justify-center bg-gray-50">
              <n-image
                v-if="formValues.avatar"
                :src="formValues.avatar"
                width="96"
                height="96"
                object-fit="cover"
                preview-disabled
              />
              <n-text v-else depth="3" class="text-xs">暂无头像</n-text>
            </div>
            <div class="flex-1">
              <n-upload :max="1" accept="image/*" :custom-request="handleUpload" :show-file-list="false">
                <n-button secondary type="info">上传头像</n-button>
              </n-upload>
              <n-text depth="3" class="text-xs mt-2 block">建议尺寸 200×200px，支持 JPG/PNG 格式</n-text>
            </div>
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
  } from '@vicons/antd';
  import { getUserDetail, createUser, updateUser } from '@/api/system/user';
  import { uploadImage } from '@/api/upload';
  import { useTabsViewStore } from '@/store/modules/tabsView';

  const route = useRoute();
  const router = useRouter();
  const tabsViewStore = useTabsViewStore();
  const userId = computed(() => {
    const id = route.params.id;
    return id ? String(id) : null;
  });
  const isEdit = computed(() => userId.value !== null);

  const formRef = ref<FormInst | null>(null);
  const loading = ref(false);
  const saving = ref(false);

  const formValues = reactive({
    user_type: 'admin',
    phone: '',
    username: '',
    password: '',
    nickname: '',
    email: '',
    avatar: '',
    status: 'active',
  });

  const rules = computed<FormRules>(() => {
    const base: FormRules = {
      nickname: { required: false },
    };
    if (!isEdit.value) {
      base.password = { required: true, message: '请输入密码', trigger: 'blur' };
      base.username = { required: true, message: '请输入用户名', trigger: 'blur' };
    }
    return base;
  });

  onMounted(async () => {
    removeTab((t) => t.name === 'system_user');
    if (userId.value) {
      await loadUser(userId.value);
    }
  });

  function removeTab(matcher: (t: any) => boolean) {
    try {
      const idx = tabsViewStore.tabsList.findIndex(matcher);
      if (idx > -1) {
        tabsViewStore.tabsList.splice(idx, 1);
      }
    } catch {}
  }

  function backToList() {
    removeTab((t) => t.fullPath === route.fullPath);
    if (window.history.state && window.history.state.back) {
      router.back();
    } else {
      router.push({ name: 'system_user' });
    }
  }

  async function loadUser(id: string) {
    loading.value = true;
    try {
      const detail = await getUserDetail(id);
      formValues.user_type = detail.user_type || 'app';
      formValues.phone = detail.phone || '';
      formValues.username = detail.username || '';
      formValues.nickname = detail.nickname || '';
      formValues.email = detail.email || '';
      formValues.avatar = detail.avatar || '';
      formValues.status = detail.status || 'active';
    } catch {
      window['$message']?.error('加载用户信息失败');
    } finally {
      loading.value = false;
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
      const result = await uploadImage(file.file, 'avatar');
      formValues.avatar = result.url;
      onFinish();
    } catch {
      onError();
      window['$message']?.error('上传失败');
    }
  }

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
      if (isEdit.value && userId.value) {
        const payload: Record<string, any> = {
          nickname: formValues.nickname || null,
          email: formValues.email || null,
          avatar: formValues.avatar || null,
          status: formValues.status,
        };
        await updateUser(userId.value, payload);
        window['$message']?.success('用户信息更新成功');
        saved = true;
      } else {
        const payload: Record<string, any> = {
          user_type: 'admin',
          username: formValues.username,
          password: formValues.password,
          nickname: formValues.nickname || undefined,
        };
        if (formValues.phone) {
          payload.phone = formValues.phone;
        }
        await createUser(payload);
        window['$message']?.success('用户创建成功');
        saved = true;
      }
    } catch (e: any) {
      window['$message']?.error(e?.message || '保存失败');
    } finally {
      saving.value = false;
    }
    if (saved) {
      backToList();
    }
  }

  function goBack() {
    backToList();
  }
</script>

<style scoped>
  .flex { display: flex; }
  .items-center { align-items: center; }
  .items-start { align-items: flex-start; }
  .justify-between { justify-content: space-between; }
  .gap-2 { gap: 0.5rem; }
  .gap-3 { gap: 0.75rem; }
  .gap-4 { gap: 1rem; }
  .space-y-4 > * + * { margin-top: 1rem; }
  .w-full { width: 100%; }
  .w-24 { width: 6rem; }
  .h-24 { height: 6rem; }
  .max-w-3xl { max-width: 48rem; }
  .mx-auto { margin-left: auto; margin-right: auto; }
  .py-4 { padding-top: 1rem; padding-bottom: 1rem; }
  .mt-2 { margin-top: 0.5rem; }
  .m-0 { margin: 0; }
  .block { display: block; }
  .text-xs { font-size: 0.75rem; }
  .text-sm { font-size: 0.875rem; }
  .text-lg { font-size: 1.125rem; }
  .font-semibold { font-weight: 600; }
  .font-bold { font-weight: 700; }
  .rounded-full { border-radius: 9999px; }
  .overflow-hidden { overflow: hidden; }
  .flex-shrink-0 { flex-shrink: 0; }
  .flex-1 { flex: 1 1 0%; }
  .border { border-width: 1px; border-style: solid; }
  .border-gray-200 { border-color: #e5e7eb; }
  .bg-gray-50 { background-color: #f9fafb; }
  .shadow-sm { box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05); }
</style>
