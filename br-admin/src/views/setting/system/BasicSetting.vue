<template>
  <n-grid cols="2 s:2 m:2 l:3 xl:3 2xl:3" responsive="screen">
    <n-grid-item>
      <n-form :label-width="100" :model="formValue" :rules="rules" ref="formRef">
        <n-form-item label="网站名称" path="site_name">
          <n-input v-model:value="formValue.site_name" placeholder="请输入网站名称" />
        </n-form-item>
        <n-form-item label="备案编号" path="icp_code">
          <n-input placeholder="请输入备案编号" v-model:value="formValue.icp_code" />
        </n-form-item>
        <n-form-item label="联系电话" path="contact_phone">
          <n-input placeholder="请输入联系电话" v-model:value="formValue.contact_phone" />
        </n-form-item>
        <n-form-item label="联系地址" path="contact_address">
          <n-input
            v-model:value="formValue.contact_address"
            type="textarea"
            placeholder="请输入联系地址"
          />
        </n-form-item>
        <n-form-item label="登录验证码" path="login_captcha">
          <n-switch v-model:value="formValue.login_captcha" />
        </n-form-item>
        <n-form-item label="系统开启" path="system_open">
          <n-switch v-model:value="formValue.system_open" />
        </n-form-item>
        <n-form-item label="关闭提示" path="close_text">
          <n-input
            v-model:value="formValue.close_text"
            type="textarea"
            placeholder="请输入关闭提示"
          />
        </n-form-item>
        <n-form-item label="登录描述" path="login_desc">
          <n-input
            v-model:value="formValue.login_desc"
            type="textarea"
            placeholder="请输入登录描述"
          />
        </n-form-item>
        <div>
          <n-space>
            <n-button
              v-permission="{ action: ['system:settings:update'] }"
              type="primary"
              :loading="subLoading"
              @click="formSubmit"
            >
              更新基础信息
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
  import { getSystemSettings, updateBasicSettings } from '@/api/system/setting';

  const formRef: any = ref(null);
  const message = useMessage();
  const subLoading = ref(false);

  const rules = {
    site_name: {
      required: true,
      message: '请输入网站名称',
      trigger: 'blur',
    },
  };

  const formValue = reactive({
    site_name: '',
    icp_code: '',
    contact_phone: '',
    contact_address: '',
    login_captcha: false,
    system_open: true,
    close_text: '',
    login_desc: '',
  });

  async function loadSettings() {
    const result = await getSystemSettings();
    Object.assign(formValue, result.basic || {});
  }

  async function formSubmit() {
    formRef.value.validate(async (errors) => {
      if (!errors) {
        subLoading.value = true;
        try {
          await updateBasicSettings({ ...formValue });
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
    loadSettings();
  });
</script>
