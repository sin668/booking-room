<template>
  <basicModal @register="modalRegister" ref="modalRef" @on-ok="okModal">
    <div class="pt-8">
      <BasicForm @register="registerForm" />
    </div>
  </basicModal>
</template>

<script lang="ts" setup>
  import { nextTick } from 'vue';
  import { FormSchema, useForm } from '@/components/Form';
  import { basicModal, useModal } from '@/components/Modal';
  import { updateUser } from '@/api/system/user';

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
      component: 'NInput',
      label: '头像URL',
      componentProps: {
        placeholder: '请输入头像URL',
      },
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
