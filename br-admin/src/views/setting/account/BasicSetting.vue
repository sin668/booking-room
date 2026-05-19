<template>
  <n-grid cols="2 s:2 m:2 l:3 xl:3 2xl:3" responsive="screen">
    <n-grid-item>
      <n-form :label-width="80" :model="formValue" :rules="rules" ref="formRef">
        <n-form-item label="昵称" path="nickname">
          <n-input v-model:value="formValue.nickname" placeholder="请输入昵称" />
        </n-form-item>

        <n-form-item label="邮箱" path="email">
          <n-input placeholder="请输入邮箱" v-model:value="formValue.email" />
        </n-form-item>

        <n-form-item label="联系电话" path="mobile">
          <n-input placeholder="请输入联系电话" v-model:value="formValue.mobile" />
        </n-form-item>

        <n-form-item label="头像" path="avatar">
          <n-input v-model:value="formValue.avatar" placeholder="请输入头像地址" />
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
  import { onMounted, reactive, ref } from 'vue';
  import { useMessage } from 'naive-ui';
  import * as userApi from '@/api/system/user';
  import { useUser } from '@/store/modules/user';

  const rules = {
    nickname: {
      required: true,
      message: '请输入昵称',
      trigger: 'blur',
    },
    email: {
      required: true,
      message: '请输入邮箱',
      trigger: 'blur',
    },
    mobile: {
      required: true,
      message: '请输入联系电话',
      trigger: 'input',
    },
  };
  const formRef: any = ref(null);
  const message = useMessage();
  const userStore = useUser();
  const subLoading = ref(false);

  const formValue = reactive({
    nickname: '',
    mobile: '',
    email: '',
    avatar: '',
  });

  async function loadProfile() {
    const result = await userApi.getUserInfo();
    Object.assign(formValue, {
      nickname: result.nickname || result.username || '',
      mobile: result.mobile || '',
      email: result.email || '',
      avatar: result.avatar || '',
    });
  }

  async function formSubmit() {
    formRef.value.validate(async (errors) => {
      if (!errors) {
        subLoading.value = true;
        try {
          const result = await userApi.updateProfile({ ...formValue });
          userStore.setNickname(result.nickname || result.username || formValue.nickname);
          userStore.setAvatar(result.avatar || '');
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
