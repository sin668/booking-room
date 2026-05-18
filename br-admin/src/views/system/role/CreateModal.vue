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
  import { createRole } from '@/api/system/role';

  const emit = defineEmits(['success']);

  const schemas: FormSchema[] = [
    {
      field: 'name',
      component: 'NInput',
      label: '角色名称',
      componentProps: {
        placeholder: '请输入角色名称',
      },
      rules: [{ required: true, message: '请输入角色名称', trigger: ['blur'] }],
    },
    {
      field: 'code',
      component: 'NInput',
      label: '角色编码',
      componentProps: {
        placeholder: '请输入角色编码',
      },
      rules: [{ required: true, message: '请输入角色编码', trigger: ['blur'] }],
    },
    {
      field: 'description',
      component: 'NInput',
      label: '角色说明',
      componentProps: {
        type: 'textarea',
        placeholder: '请输入角色说明',
      },
    },
    {
      field: 'status',
      component: 'NSelect',
      label: '状态',
      componentProps: {
        options: [
          { label: '启用', value: 'active' },
          { label: '禁用', value: 'disabled' },
        ],
      },
      defaultValue: 'active',
    },
  ];

  const [registerForm, { submit }] = useForm({
    gridProps: { cols: 1 },
    collapsedRows: 4,
    labelWidth: 80,
    layout: 'horizontal',
    submitButtonText: '保存',
    showActionButtonGroup: false,
    schemas,
  });

  const [modalRegister, { openModal, closeModal, setSubLoading }] = useModal({
    title: '新增角色',
    subBtuText: '保存',
  });

  async function okModal() {
    const formRes = await submit();
    if (formRes) {
      try {
        await createRole(formRes);
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
    openModal,
  });
</script>
