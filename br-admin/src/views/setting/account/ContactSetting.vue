<template>
  <n-grid cols="1" responsive="screen">
    <n-grid-item>
      <n-form :label-width="100" :model="formValue" :rules="rules" ref="formRef">
        <n-form-item path="phone">
          <template #label>
            <div class="flex items-center">
              联系电话
              <n-tooltip trigger="hover">
                <template #trigger>
                  <n-icon size="16" class="ml-1 text-gray-400 cursor-pointer">
                    <QuestionCircleOutlined />
                  </n-icon>
                </template>
                联系电话修改后 30 天内不可再次修改
              </n-tooltip>
            </div>
          </template>
          <n-input
            v-model:value="formValue.phone"
            :placeholder="phonePlaceholder"
            :disabled="phoneCooldown > 0"
          />
        </n-form-item>

        <n-form-item label="手机验证码" path="sms_code">
          <n-input-group>
            <n-input
              v-model:value="formValue.sms_code"
              :maxlength="6"
              placeholder="请输入 6 位验证码"
              :disabled="phoneCooldown > 0"
            />
            <n-button
              type="primary"
              ghost
              :disabled="phoneCooldown > 0 || codeCountdown > 0 || sendingCode"
              :loading="sendingCode"
              @click="handleSendCode"
            >
              {{ codeCountdown > 0 ? `${codeCountdown}s 后重发` : '获取验证码' }}
            </n-button>
          </n-input-group>
        </n-form-item>

        <div>
          <n-space>
            <n-button
              type="primary"
              :loading="subLoading"
              :disabled="phoneCooldown > 0"
              @click="formSubmit"
            >
              保存联系电话
            </n-button>
          </n-space>
          <n-text v-if="phoneCooldown > 0" depth="3" class="text-xs">
            联系电话修改后 30 天内不可再次修改，剩余 {{ phoneCooldown }} 天
          </n-text>
          <n-text v-else-if="currentPhone" depth="3" class="text-xs">
            当前手机号：{{ currentPhone }}
          </n-text>
        </div>
      </n-form>
    </n-grid-item>
  </n-grid>
</template>

<script lang="ts" setup>
  import { computed, onMounted, onUnmounted, reactive, ref } from 'vue';
  import { useMessage } from 'naive-ui';
  import { QuestionCircleOutlined } from '@vicons/antd';
  import * as userApi from '@/api/system/user';
  import { useUser } from '@/store/modules/user';

  const COOLDOWN_DAYS = 30;
  const DAY_MS = 24 * 60 * 60 * 1000;
  const SEND_CODE_SECONDS = 60;
  const PHONE_PATTERN = /^1[3-9]\d{9}$/;

  function cooldownRemainingDays(updatedAt?: string | null): number {
    if (!updatedAt) return 0;
    const elapsed = Date.now() - new Date(updatedAt).getTime();
    const remain = Math.ceil((COOLDOWN_DAYS * DAY_MS - elapsed) / DAY_MS);
    return remain > 0 ? remain : 0;
  }

  const formRef: any = ref(null);
  const message = useMessage();
  const userStore = useUser();
  const subLoading = ref(false);
  const sendingCode = ref(false);
  const currentPhone = ref('');
  const phoneCooldown = ref(0);
  const codeCountdown = ref(0);
  let countdownTimer: ReturnType<typeof setInterval> | null = null;

  const formValue = reactive({
    phone: '',
    sms_code: '',
  });

  const rules = {
    phone: {
      required: true,
      pattern: PHONE_PATTERN,
      message: '请输入正确的手机号',
      trigger: ['input', 'blur'],
    },
    sms_code: {
      required: true,
      pattern: /^\d{6}$/,
      message: '请输入 6 位验证码',
      trigger: ['input', 'blur'],
    },
  };

  const phonePlaceholder = computed(() =>
    phoneCooldown.value > 0
      ? `联系电话修改后 30 天内不可再次修改（剩余 ${phoneCooldown.value} 天）`
      : '请输入新的联系电话'
  );

  async function loadProfile() {
    const result = await userApi.getUserInfo();
    currentPhone.value = result.phone || '';
    phoneCooldown.value = cooldownRemainingDays(result.phone_updated_at);
    if (phoneCooldown.value > 0) {
      formValue.phone = '';
    }
  }

  function startCountdown() {
    codeCountdown.value = SEND_CODE_SECONDS;
    countdownTimer = setInterval(() => {
      codeCountdown.value -= 1;
      if (codeCountdown.value <= 0 && countdownTimer) {
        clearInterval(countdownTimer);
        countdownTimer = null;
      }
    }, 1000);
  }

  async function handleSendCode() {
    if (!PHONE_PATTERN.test(formValue.phone)) {
      message.error('请先输入正确的手机号');
      return;
    }
    sendingCode.value = true;
    try {
      await userApi.sendSmsCode(formValue.phone);
      message.success('验证码已发送');
      startCountdown();
    } catch (error: any) {
      message.error(error?.message || '验证码发送失败');
    } finally {
      sendingCode.value = false;
    }
  }

  function formSubmit() {
    formRef.value.validate(async (errors) => {
      if (!errors) {
        subLoading.value = true;
        try {
          await userApi.changeAdminPhone({
            phone: formValue.phone,
            sms_code: formValue.sms_code,
          });
          message.success('联系电话已更新');
          formValue.sms_code = '';
          await loadProfile();
          await userStore.getInfo();
        } catch (error: any) {
          message.error(error?.message || '联系电话更新失败');
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

  onUnmounted(() => {
    if (countdownTimer) clearInterval(countdownTimer);
  });
</script>
