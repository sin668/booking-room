<template>
  <basicModal @register="modalRegister" ref="modalRef" @on-ok="okModal">
    <div class="pt-8">
      <BasicForm @register="registerForm">
        <template #avatarSlot="{ model, field }">
          <n-space vertical>
            <n-upload
              :max="1"
              accept="image/*"
              :custom-request="handleAvatarUpload"
            >
              <n-button>上传头像</n-button>
            </n-upload>
            <n-image
              v-if="model[field]"
              :src="model[field]"
              width="80"
              height="80"
              object-fit="cover"
              preview-disabled
            />
            <n-input v-model:value="model[field]" placeholder="请输入头像URL" />
          </n-space>
        </template>
      </BasicForm>
    </div>
  </basicModal>
</template>

<script lang="ts" setup>
  import { nextTick } from 'vue';
  import type { UploadFileInfo } from 'naive-ui';
  import { FormSchema, useForm } from '@/components/Form';
  import { basicModal, useModal } from '@/components/Modal';
  import { updateUser } from '@/api/system/user';
  import { uploadImage } from '@/api/upload';

  const emit = defineEmits(['success']);

  const schemas: FormSchema[] = [
    {
      field: 'nickname',
      component: 'NInput',
      label: '昵称',
      componentProps: {
        placeholder: '请输入昵称',
      },
    },
    {
      field: 'email',
      component: 'NInput',
      label: '邮箱',
      componentProps: {
        placeholder: '请输入邮箱',
      },
    },
    {
      field: 'mobile',
      component: 'NInput',
      label: '手机号',
      componentProps: {
        placeholder: '请输入手机号',
      },
    },
    {
      field: 'avatar',
      label: '头像',
      slot: 'avatarSlot',
    },
  ];

  let currentId: string | number | undefined;

  const [registerForm, { submit, setFieldsValue }] = useForm({
    gridProps: { cols: 1 },
    collapsedRows: 4,
    labelWidth: 80,
    layout: 'horizontal',
    submitButtonText: '保存',
    showActionButtonGroup: false,
    schemas,
  });

  const [modalRegister, { openModal, closeModal, setSubLoading }] = useModal({
    title: '编辑用户',
    subBtuText: '保存',
  });

  function showModal(record: any) {
    currentId = record?.id;
    openModal();
    nextTick(() => {
      record && setFieldsValue({ ...record });
    });
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
      await setFieldsValue({ avatar: result.url });
      onFinish();
    } catch (error: any) {
      onError();
      window['$message']?.error(error?.message || '头像上传失败');
    }
  }

  async function okModal() {
    const formRes = await submit();
    if (formRes && currentId != null) {
      try {
        await updateUser(currentId, formRes);
        closeModal();
        emit('success');
      } catch {
        setSubLoading(false);
      }
    } else {
      setSubLoading(false);
    }
  }

  defineExpose({
    showModal,
  });
</script>
