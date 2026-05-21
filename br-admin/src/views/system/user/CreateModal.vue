<template>
  <basicModal @register="modalRegister" ref="modalRef" @on-ok="okModal">
    <div class="pt-8">
      <BasicForm @register="registerForm" />
    </div>
  </basicModal>
</template>

<script lang="ts" setup>
  import { FormSchema, useForm } from '@/components/Form';
  import { basicModal, useModal } from '@/components/Modal';
  import { createUser } from '@/api/system/user';

  const emit = defineEmits(['success']);

  const appSchemas: FormSchema[] = [
    {
      field: 'phone',
      component: 'NInput',
      label: '手机号',
      componentProps: {
        placeholder: '请输入手机号',
      },
      rules: [{ required: true, message: '请输入手机号', trigger: ['blur'] }],
    },
    {
      field: 'password',
      component: 'NInputPassword',
      label: '密码',
      componentProps: {
        placeholder: '请输入密码',
        showPasswordOn: 'click',
      },
      rules: [{ required: true, message: '请输入密码', trigger: ['blur'] }],
    },
    {
      field: 'nickname',
      component: 'NInput',
      label: '昵称',
      componentProps: {
        placeholder: '请输入昵称',
      },
    },
  ];

  const adminSchemas: FormSchema[] = [
    {
      field: 'username',
      component: 'NInput',
      label: '用户名',
      componentProps: {
        placeholder: '请输入用户名',
      },
      rules: [{ required: true, message: '请输入用户名', trigger: ['blur'] }],
    },
    {
      field: 'password',
      component: 'NInputPassword',
      label: '密码',
      componentProps: {
        placeholder: '请输入密码',
        showPasswordOn: 'click',
      },
      rules: [{ required: true, message: '请输入密码', trigger: ['blur'] }],
    },
    {
      field: 'nickname',
      component: 'NInput',
      label: '昵称',
      componentProps: {
        placeholder: '请输入昵称',
      },
    },
  ];

  const baseSchema: FormSchema = {
    field: 'user_type',
    component: 'NRadioGroup',
    label: '用户类型',
    defaultValue: 'app',
    componentProps: {
      options: [
        { label: 'App用户', value: 'app' },
        { label: '管理员', value: 'admin' },
      ],
    },
  };

  const [registerForm, { submit, setSchema, setFieldsValue, resetFields }] = useForm({
    gridProps: { cols: 1 },
    collapsedRows: 4,
    labelWidth: 80,
    layout: 'horizontal',
    submitButtonText: '保存',
    showActionButtonGroup: false,
    schemas: [baseSchema, ...appSchemas],
  });

  const [modalRegister, { openModal, closeModal, setSubLoading }] = useModal({
    title: '新增用户',
    subBtuText: '保存',
  });

  function openModalWithType(type?: string) {
    resetFields();
    const userType = type || 'app';
    const dynamicSchemas = userType === 'admin' ? adminSchemas : appSchemas;
    setSchema([baseSchema, ...dynamicSchemas]);
    openModal();
    // Reset user_type after schema update so the radio reflects the correct value
    setFieldsValue({ user_type: userType });
  }

  async function okModal() {
    const formRes = await submit();
    if (formRes) {
      try {
        await createUser(formRes);
        closeModal();
        emit('success');
      } catch {
        setSubLoading(false);
      }
    } else {
      setSubLoading(false);
    }
  }

  defineExpose({ openModal: openModalWithType });
</script>
