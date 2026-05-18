<template>
  <n-drawer v-model:show="state.isDrawer" :width="width" :placement="state.placement">
    <n-drawer-content :title="title" closable>
      <n-form
        :model="formParams"
        :rules="rules"
        ref="formRef"
        label-placement="left"
        :label-width="110"
      >
        <n-form-item label="类型" path="type">
          <n-select v-model:value="formParams.type" :options="typeOptions" />
        </n-form-item>
        <n-form-item label="标题" path="title">
          <n-input placeholder="请输入标题" v-model:value="formParams.title" />
        </n-form-item>
        <template v-if="formParams.type !== 'button'">
          <n-form-item label="路径" path="path">
            <n-input placeholder="例如 /system/menu" v-model:value="formParams.path" />
          </n-form-item>
          <n-form-item label="路由名称" path="name">
            <n-input placeholder="请输入唯一路由名称" v-model:value="formParams.name" />
          </n-form-item>
          <n-form-item label="组件" path="component">
            <n-select
              v-model:value="formParams.component"
              filterable
              clearable
              :options="componentOptions"
              placeholder="请选择组件"
            />
          </n-form-item>
          <n-form-item label="重定向" path="redirect">
            <n-input placeholder="可选" v-model:value="formParams.redirect" />
          </n-form-item>
          <n-form-item label="图标" path="icon">
            <n-input placeholder="例如 DashboardOutlined" v-model:value="formParams.icon" />
          </n-form-item>
          <n-form-item label="权限码" path="permission_code">
            <n-input placeholder="可选，用于菜单权限" v-model:value="formParams.permission_code" />
          </n-form-item>
          <n-form-item label="隐藏菜单" path="hidden">
            <n-switch v-model:value="formParams.hidden" />
          </n-form-item>
          <n-form-item label="页面缓存" path="keep_alive">
            <n-switch v-model:value="formParams.keep_alive" />
          </n-form-item>
        </template>
        <template v-else>
          <n-form-item label="按钮权限码" path="permission_code">
            <n-input
              placeholder="例如 system:menu:create"
              v-model:value="formParams.permission_code"
            />
          </n-form-item>
        </template>
        <n-form-item label="排序" path="sort">
          <n-input-number v-model:value="formParams.sort" :min="0" />
        </n-form-item>
        <n-form-item label="启用" path="enabled">
          <n-switch v-model:value="formParams.enabled" />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space>
          <n-button type="primary" :loading="state.subLoading" @click="formSubmit">提交</n-button>
          <n-button @click="handleReset">重置</n-button>
        </n-space>
      </template>
    </n-drawer-content>
  </n-drawer>
</template>

<script lang="ts" setup>
  import { computed, reactive, ref } from 'vue';
  import { useMessage } from 'naive-ui';
  import {
    createMenu,
    getComponentOptions,
    type ComponentOption,
    type MenuSaveParams,
  } from '@/api/system/menu';

  defineProps({
    title: {
      type: String,
      default: '添加菜单',
    },
    width: {
      type: Number,
      default: 520,
    },
  });

  const emit = defineEmits(['success']);

  const typeOptions = [
    { label: '目录', value: 'directory' },
    { label: '菜单', value: 'menu' },
    { label: '按钮', value: 'button' },
  ];

  const componentOptions = ref<ComponentOption[]>([]);
  const message = useMessage();
  const formRef: any = ref(null);
  const currentParentId = ref<string | number | null>(null);
  const defaultValueRef = () => ({
    parent_id: null as string | number | null,
    title: '',
    type: 'menu' as const,
    permission_code: '',
    path: '',
    name: '',
    component: '',
    redirect: '',
    icon: '',
    sort: 0,
    hidden: false,
    keep_alive: false,
    enabled: true,
  });
  const formParams = ref(defaultValueRef());
  const state = reactive({
    isDrawer: false,
    subLoading: false,
    placement: 'right' as const,
  });

  const componentValues = computed(() => componentOptions.value.map((item) => item.value));

  const rules = computed(() => ({
    title: {
      required: true,
      message: '请输入标题',
      trigger: 'blur',
    },
    component: {
      validator() {
        return (
          formParams.value.type === 'button' ||
          componentValues.value.includes(formParams.value.component)
        );
      },
      message: '请选择组件白名单中的组件',
      trigger: ['blur', 'change'],
    },
    permission_code: {
      validator() {
        return formParams.value.type !== 'button' || !!formParams.value.permission_code;
      },
      message: '请输入按钮权限码',
      trigger: 'blur',
    },
  }));

  async function openDrawer(
    parentId: string | number | null = null,
    type: 'directory' | 'menu' | 'button' = 'menu'
  ) {
    currentParentId.value = parentId;
    formParams.value = {
      ...defaultValueRef(),
      parent_id: parentId,
      type,
    };
    state.isDrawer = true;
    if (!componentOptions.value.length) {
      componentOptions.value = await getComponentOptions();
    }
  }

  function closeDrawer() {
    state.isDrawer = false;
  }

  function buildPayload(): MenuSaveParams {
    const value = formParams.value;
    const payload: MenuSaveParams = {
      ...value,
      parent_id: currentParentId.value,
      title: value.title,
      type: value.type,
    };
    if (value.type === 'button') {
      payload.path = undefined;
      payload.name = undefined;
      payload.component = undefined;
      payload.redirect = undefined;
      payload.icon = undefined;
      payload.hidden = false;
      payload.keep_alive = false;
    }
    return payload;
  }

  function formSubmit() {
    formRef.value.validate(async (errors) => {
      if (errors) {
        message.error('请填写完整信息');
        return;
      }
      state.subLoading = true;
      try {
        await createMenu(buildPayload());
        message.success('添加成功');
        handleReset();
        closeDrawer();
        emit('success');
      } catch (error: any) {
        message.error(error?.message || '添加失败');
      } finally {
        state.subLoading = false;
      }
    });
  }

  function handleReset() {
    formRef.value?.restoreValidation();
    formParams.value = {
      ...defaultValueRef(),
      parent_id: currentParentId.value,
    };
  }

  defineExpose({
    openDrawer,
  });
</script>
