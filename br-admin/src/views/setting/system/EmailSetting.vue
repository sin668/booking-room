<template>
  <n-grid cols="2 s:2 m:2 l:3 xl:3 2xl:3" responsive="screen">
    <n-grid-item>
      <n-form :label-width="120" :model="formValue" :rules="rules" ref="formRef">
        <n-form-item label="SMTP服务器地址" path="smtp_host">
          <n-input v-model:value="formValue.smtp_host" placeholder="请输入SMTP服务器地址" />
        </n-form-item>
        <n-form-item label="SMTP服务器端口" path="smtp_port">
          <n-input-number v-model:value="formValue.smtp_port" :min="1" />
        </n-form-item>
        <n-form-item label="SMTP用户名" path="smtp_username">
          <n-input v-model:value="formValue.smtp_username" placeholder="请输入SMTP用户名" />
        </n-form-item>
        <n-form-item label="SMTP密码" path="smtp_password">
          <n-input
            v-model:value="formValue.smtp_password"
            type="password"
            placeholder="不修改则留空"
          />
        </n-form-item>
        <n-form-item label="发件人邮箱" path="smtp_sender">
          <n-input v-model:value="formValue.smtp_sender" placeholder="请输入发件人邮箱" />
        </n-form-item>
        <n-form-item label="启用 TLS" path="smtp_tls">
          <n-switch v-model:value="formValue.smtp_tls" />
        </n-form-item>
        <n-form-item label="密码状态">
          <n-tag :type="formValue.smtp_password_set ? 'success' : 'warning'">
            {{ formValue.smtp_password_set ? '已设置' : '未设置' }}
          </n-tag>
        </n-form-item>
        <n-form-item label="测试收件人" path="test_to_email">
          <n-input v-model:value="testToEmail" placeholder="请输入测试收件人邮箱" />
        </n-form-item>
        <n-form-item label="邮件测试">
          <n-button
            v-permission="{ action: ['system:settings:email'] }"
            :loading="testLoading"
            @click="handleTest"
          >
            邮件测试
          </n-button>
        </n-form-item>
        <div>
          <n-space>
            <n-button
              v-permission="{ action: ['system:settings:update'] }"
              type="primary"
              :loading="subLoading"
              @click="formSubmit"
            >
              更新邮件信息
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
  import { getSystemSettings, updateEmailSettings, testEmailSettings } from '@/api/system/setting';

  const formRef: any = ref(null);
  const message = useMessage();
  const subLoading = ref(false);
  const testLoading = ref(false);
  const testToEmail = ref('');

  const rules = {
    smtp_host: { required: true, message: '请输入SMTP服务器地址', trigger: 'blur' },
    smtp_port: { required: true, message: '请输入SMTP服务器端口', trigger: 'blur' },
    smtp_sender: { required: true, message: '请输入发件人邮箱', trigger: 'blur' },
  };

  const formValue = reactive({
    smtp_host: '',
    smtp_port: 25 as number | undefined,
    smtp_username: '',
    smtp_password: '',
    smtp_sender: '',
    smtp_tls: false,
    smtp_password_set: false,
  });

  async function loadSettings() {
    const result = await getSystemSettings();
    Object.assign(formValue, result.email || {});
  }

  async function formSubmit() {
    formRef.value.validate(async (errors) => {
      if (!errors) {
        subLoading.value = true;
        try {
          await updateEmailSettings({ ...formValue });
          message.success('保存成功');
          formValue.smtp_password = '';
          await loadSettings();
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

  async function handleTest() {
    if (!testToEmail.value) {
      message.error('请输入测试收件人邮箱');
      return;
    }
    testLoading.value = true;
    try {
      await testEmailSettings(testToEmail.value);
      message.success('测试邮件发送成功');
    } catch (error: any) {
      message.error(error?.message || '测试失败');
    } finally {
      testLoading.value = false;
    }
  }

  onMounted(() => {
    loadSettings();
  });
</script>
