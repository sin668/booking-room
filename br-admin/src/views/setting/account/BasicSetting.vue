<template>
  <n-grid cols="2 s:2 m:2 l:3 xl:3 2xl:3" responsive="screen">
    <n-grid-item>
      <n-form :label-width="80" :model="formValue" :rules="rules" ref="formRef">
        <n-form-item label="头像" path="avatar">
          <div class="flex items-start gap-4">
            <div
              class="w-24 h-24 rounded-full overflow-hidden border border-gray-200 flex-shrink-0 flex items-center justify-center bg-gray-50"
            >
              <n-image
                v-if="formValue.avatar"
                :src="formValue.avatar"
                width="96"
                height="96"
                object-fit="cover"
                preview-disabled
              />
              <n-text v-else depth="3" class="text-xs">暂无头像</n-text>
            </div>
            <div class="flex-1">
              <n-upload
                :max="1"
                accept="image/*"
                :custom-request="handleAvatarUpload"
                :show-file-list="false"
              >
                <n-button secondary type="info">上传头像</n-button>
              </n-upload>
              <n-text depth="3" class="text-xs mt-2 block"
                >建议尺寸 200×200px，支持 JPG/PNG 格式，最大 2MB</n-text
              >
            </div>
          </div>
        </n-form-item>

        <n-form-item path="username">
          <template #label>
            <div class="flex items-center">
              用户名
              <n-tooltip trigger="hover">
                <template #trigger>
                  <n-icon size="16" class="ml-1 text-gray-400 cursor-pointer">
                    <QuestionCircleOutlined />
                  </n-icon>
                </template>
                用户名修改后 30 天内不可再次修改
              </n-tooltip>
            </div>
          </template>
          <n-input
            v-model:value="formValue.username"
            :placeholder="usernamePlaceholder"
            :disabled="usernameCooldown > 0"
          />
        </n-form-item>

        <n-form-item label="昵称" path="nickname">
          <n-input v-model:value="formValue.nickname" placeholder="请输入昵称" />
        </n-form-item>

        <n-form-item label="邮箱" path="email">
          <n-input placeholder="请输入邮箱" v-model:value="formValue.email" />
        </n-form-item>

        <n-form-item label="性别" path="gender">
          <n-select
            v-model:value="formValue.gender"
            :options="genderOptions"
            clearable
            placeholder="请选择性别"
          />
        </n-form-item>

        <n-form-item label="生日" path="birthday">
          <n-date-picker
            v-model:formatted-value="formValue.birthday"
            value-format="yyyy-MM-dd"
            type="date"
            clearable
            style="width: 100%"
          />
        </n-form-item>

        <n-form-item label="个性签名" path="signature">
          <n-input
            v-model:value="formValue.signature"
            type="textarea"
            :maxlength="200"
            show-count
            placeholder="请输入个性签名"
          />
        </n-form-item>

        <div>
          <n-space>
            <n-button type="primary" :loading="subLoading" @click="formSubmit">
              更新基本信息
            </n-button>
          </n-space>
        </div>
      </n-form>
    </n-grid-item>
  </n-grid>
</template>

<script lang="ts" setup>
  import { computed, onMounted, reactive, ref } from 'vue';
  import { useMessage, type UploadFileInfo } from 'naive-ui';
  import { QuestionCircleOutlined } from '@vicons/antd';
  import * as userApi from '@/api/system/user';
  import { useUser } from '@/store/modules/user';
  import { uploadImage } from '@/api/upload';

  const COOLDOWN_DAYS = 30;
  const DAY_MS = 24 * 60 * 60 * 1000;

  function cooldownRemainingDays(updatedAt?: string | null): number {
    if (!updatedAt) return 0;
    const elapsed = Date.now() - new Date(updatedAt).getTime();
    const remain = Math.ceil((COOLDOWN_DAYS * DAY_MS - elapsed) / DAY_MS);
    return remain > 0 ? remain : 0;
  }

  const rules = {
    username: {
      required: true,
      message: '请输入用户名',
      trigger: 'blur',
    },
  };
  const formRef: any = ref(null);
  const message = useMessage();
  const userStore = useUser();
  const subLoading = ref(false);

  const genderOptions = [
    { label: '男', value: 'male' },
    { label: '女', value: 'female' },
    { label: '保密', value: 'secret' },
  ];

  const formValue = reactive({
    username: '',
    nickname: '',
    email: '',
    avatar: '',
    gender: null as string | null,
    birthday: null as string | null,
    signature: '',
  });

  const usernameCooldown = ref(0);

  const usernamePlaceholder = computed(() =>
    usernameCooldown.value > 0
      ? `用户名修改后 30 天内不可再次修改（剩余 ${usernameCooldown.value} 天）`
      : '请输入用户名'
  );

  async function loadProfile() {
    const result = await userApi.getUserInfo();
    Object.assign(formValue, {
      username: result.username || '',
      nickname: result.nickname || result.username || '',
      email: result.email || '',
      avatar: result.avatar || '',
      gender: result.gender || null,
      birthday: result.birthday || null,
      signature: result.signature || '',
    });
    usernameCooldown.value = cooldownRemainingDays(result.username_updated_at);
  }

  async function handleAvatarUpload({
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
      formValue.avatar = result.url;
      onFinish();
    } catch (error: any) {
      onError();
      message.error(error?.message || '头像上传失败');
    }
  }

  async function formSubmit() {
    formRef.value.validate(async (errors) => {
      if (!errors) {
        subLoading.value = true;
        try {
          const result = await userApi.updateProfile({ ...formValue });
          userStore.setNickname(result.nickname || result.username || formValue.nickname);
          userStore.setAvatar(result.avatar || '');
          usernameCooldown.value = cooldownRemainingDays(result.username_updated_at);
          message.success('保存成功');
        } catch (error: any) {
          message.error(error?.message || '保存失败');
        } finally {
          subLoading.value = false;
        }
      } else {
        message.error('验证失败，请填写完整信息');
      }
    });
  }

  onMounted(() => {
    loadProfile();
  });
</script>
