<template>
  <n-grid cols="1" responsive="screen" class="-mt-4">
    <n-grid-item>
      <n-form :label-width="100" :model="formValue" :rules="rules" ref="formRef">
        <n-form-item label="旧密码" path="old_password">
          <n-input
            v-model:value="formValue.old_password"
            type="password"
            placeholder="请输入旧密码"
          />
        </n-form-item>
        <n-form-item label="新密码" path="new_password">
          <n-input
            v-model:value="formValue.new_password"
            type="password"
            placeholder="请输入新密码"
          />
        </n-form-item>
        <n-form-item label="确认密码" path="confirm_password">
          <n-input
            v-model:value="formValue.confirm_password"
            type="password"
            placeholder="请再次输入新密码"
          />
        </n-form-item>
        <div>
          <n-space>
            <n-button type="primary" :loading="subLoading" @click="formSubmit"> 修改密码 </n-button>
          </n-space>
        </div>
      </n-form>
    </n-grid-item>
  </n-grid>
</template>

<script lang="ts" setup>
  import { reactive, ref } from 'vue';
  import { useMessage } from 'naive-ui';
  import { updatePassword } from '@/api/system/user';

  const formRef: any = ref(null);
  const message = useMessage();
  const subLoading = ref(false);

  const formValue = reactive({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });

  const rules = {
    old_password: { required: true, message: '请输入旧密码', trigger: 'blur' },
    new_password: { required: true, message: '请输入新密码', trigger: 'blur' },
    confirm_password: { required: true, message: '请再次输入新密码', trigger: 'blur' },
  };

  function formSubmit() {
    if (formValue.new_password !== formValue.confirm_password) {
      message.error('两次密码输入不一致');
      return;
    }
    formRef.value.validate(async (errors) => {
      if (!errors) {
        subLoading.value = true;
        try {
          await updatePassword(formValue);
          message.success('密码修改成功');
          formValue.old_password = '';
          formValue.new_password = '';
          formValue.confirm_password = '';
        } catch (error: any) {
          message.error(error?.message || '密码修改失败');
        } finally {
          subLoading.value = false;
        }
      } else {
        message.error('验证失败，请填写完整信息');
      }
    });
  }
</script>
