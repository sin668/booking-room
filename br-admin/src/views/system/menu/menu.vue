<template>
  <div>
    <div class="n-layout-page-header">
      <n-card :bordered="false" title="菜单权限管理"> 管理目录、菜单与按钮权限。 </n-card>
    </div>
    <n-grid class="mt-4" cols="1 s:1 m:1 l:3 xl:3 2xl:3" responsive="screen" :x-gap="12">
      <n-gi span="1">
        <n-card :segmented="{ content: true }" :bordered="false" size="small">
          <template #header>
            <n-space>
              <n-dropdown trigger="hover" @select="selectAddMenu" :options="addMenuOptions">
                <n-button
                  v-permission="{ action: ['system:menu:create'] }"
                  type="info"
                  ghost
                  icon-placement="right"
                >
                  添加菜单
                  <template #icon>
                    <div class="flex items-center">
                      <n-icon size="14">
                        <DownOutlined />
                      </n-icon>
                    </div>
                  </template>
                </n-button>
              </n-dropdown>
              <n-button type="info" ghost icon-placement="left" @click="packHandle">
                全部{{ expandedKeys.length ? '收起' : '展开' }}
                <template #icon>
                  <div class="flex items-center">
                    <n-icon size="14">
                      <AlignLeftOutlined />
                    </n-icon>
                  </div>
                </template>
              </n-button>
            </n-space>
          </template>
          <n-input v-model:value="pattern" placeholder="输入菜单名称搜索">
            <template #suffix>
              <n-icon size="18" class="cursor-pointer">
                <SearchOutlined />
              </n-icon>
            </template>
          </n-input>
          <div class="py-3 menu-list">
            <n-spin v-if="loading" size="medium" />
            <n-tree
              v-else
              block-line
              cascade
              checkable
              :virtual-scroll="true"
              :pattern="pattern"
              :data="treeData"
              :expandedKeys="expandedKeys"
              style="max-height: 650px; overflow: hidden"
              @update:selected-keys="selectedTree"
              @update:expanded-keys="onExpandedKeys"
            />
          </div>
        </n-card>
      </n-gi>
      <n-gi span="2">
        <n-card :segmented="{ content: true }" :bordered="false" size="small">
          <template #header>
            <n-space>
              <n-icon size="18">
                <FormOutlined />
              </n-icon>
              <span>编辑菜单{{ treeItemTitle ? `：${treeItemTitle}` : '' }}</span>
            </n-space>
          </template>
          <n-alert type="info" closable> 从菜单列表选择一项后，进行编辑 </n-alert>
          <n-form
            v-if="isEditMenu"
            ref="formRef"
            :model="formParams"
            :rules="rules"
            label-placement="left"
            :label-width="110"
            class="py-4"
          >
            <n-form-item label="类型" path="type">
              <n-select v-model:value="formParams.type" :options="typeOptions" />
            </n-form-item>
            <n-form-item label="标题" path="title">
              <n-input v-model:value="formParams.title" placeholder="请输入标题" />
            </n-form-item>
            <template v-if="formParams.type !== 'button'">
              <n-form-item label="路径" path="path">
                <n-input v-model:value="formParams.path" placeholder="请输入路径" />
              </n-form-item>
              <n-form-item label="路由名称" path="name">
                <n-input v-model:value="formParams.name" placeholder="请输入路由名称" />
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
                <n-input v-model:value="formParams.redirect" placeholder="请输入重定向" />
              </n-form-item>
              <n-form-item label="图标" path="icon">
                <n-input v-model:value="formParams.icon" placeholder="请输入图标" />
              </n-form-item>
              <n-form-item label="权限码" path="permission_code">
                <n-input
                  v-model:value="formParams.permission_code"
                  placeholder="可选，目录/菜单权限码"
                />
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
                  v-model:value="formParams.permission_code"
                  placeholder="例如 system:menu:create"
                />
              </n-form-item>
            </template>
            <n-form-item label="排序" path="sort">
              <n-input-number v-model:value="formParams.sort" :min="0" />
            </n-form-item>
            <n-form-item label="启用" path="enabled">
              <n-switch v-model:value="formParams.enabled" />
            </n-form-item>
            <n-form-item style="margin-left: 110px">
              <n-space>
                <n-button
                  v-permission="{ action: ['system:menu:update'] }"
                  type="primary"
                  :loading="subLoading"
                  @click="formSubmit"
                >
                  保存修改
                </n-button>
                <n-button @click="handleReset">重置</n-button>
                <n-button v-permission="{ action: ['system:menu:delete'] }" @click="handleDel">
                  删除
                </n-button>
              </n-space>
            </n-form-item>
          </n-form>
        </n-card>
      </n-gi>
    </n-grid>
    <CreateDrawer ref="createDrawerRef" :title="drawerTitle" @success="loadMenus" />
  </div>
</template>

<script lang="ts" setup>
  import { computed, onMounted, reactive, ref, unref } from 'vue';
  import { useDialog, useMessage } from 'naive-ui';
  import { DownOutlined, AlignLeftOutlined, SearchOutlined, FormOutlined } from '@vicons/antd';
  import { deleteMenu, getComponentOptions, getMenuList, updateMenu } from '@/api/system/menu';
  import { getTreeItem } from '@/utils';
  import CreateDrawer from './CreateDrawer.vue';

  const message = useMessage();
  const dialog = useDialog();
  const formRef: any = ref(null);
  const createDrawerRef = ref();
  const treeData = ref<any[]>([]);
  const loading = ref(true);
  const subLoading = ref(false);
  const isEditMenu = ref(false);
  const treeItemTitle = ref('');
  const pattern = ref('');
  const drawerTitle = ref('');
  const expandedKeys = ref<any[]>([]);
  const selectedKeys = ref<any[]>([]);
  const selectedNode = ref<any>(null);
  const componentOptions = ref<any[]>([]);

  const typeOptions = [
    { label: '目录', value: 'directory' },
    { label: '菜单', value: 'menu' },
    { label: '按钮', value: 'button' },
  ];

  const addMenuOptions = computed(() => [
    { label: '添加顶级目录', key: 'directory' },
    {
      label: '添加子菜单',
      key: 'menu',
      disabled: !selectedNode.value,
    },
    {
      label: '添加按钮',
      key: 'button',
      disabled: !selectedNode.value,
    },
  ]);

  const formParams = reactive({
    id: '',
    parent_id: null as string | number | null,
    title: '',
    type: 'menu' as 'directory' | 'menu' | 'button',
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

  const rules = {
    title: { required: true, message: '请输入标题', trigger: 'blur' },
    path: {
      validator: (_rule, value) => formParams.type === 'button' || !!value,
      message: '请输入路径',
      trigger: 'blur',
    },
    component: {
      validator: (_rule, value) =>
        formParams.type === 'button' ||
        !value ||
        componentOptions.value.some((item) => item.value === value),
      message: '请选择组件白名单中的值',
      trigger: ['blur', 'change'],
    },
    permission_code: {
      validator: (_rule, value) => formParams.type !== 'button' || !!value,
      message: '请输入按钮权限码',
      trigger: 'blur',
    },
  };

  function selectAddMenu(key: 'directory' | 'menu' | 'button') {
    const parentTitle = selectedNode.value?.label || '';
    drawerTitle.value =
      key === 'directory'
        ? '添加顶级目录'
        : key === 'button'
        ? `添加按钮${parentTitle ? `：${parentTitle}` : ''}`
        : `添加子菜单${parentTitle ? `：${parentTitle}` : ''}`;
    const parentId = key === 'directory' ? null : selectedNode.value?.key ?? null;
    createDrawerRef.value.openDrawer(parentId, key);
  }

  function selectedTree(keys: any[]) {
    selectedKeys.value = keys;
    if (keys.length) {
      const treeItem = getTreeItem(unref(treeData), keys[0]);
      selectedNode.value = treeItem;
      treeItemTitle.value = treeItem?.label || '';
      Object.assign(formParams, {
        ...treeItem,
        id: treeItem?.key,
        title: treeItem?.label,
      });
      isEditMenu.value = true;
    } else {
      selectedNode.value = null;
      treeItemTitle.value = '';
      isEditMenu.value = false;
    }
  }

  async function loadMenus() {
    loading.value = true;
    const result = await getMenuList();
    treeData.value = result.list;
    expandedKeys.value = result.list.map((item: any) => item.key);
    loading.value = false;
  }

  function handleDel() {
    if (!formParams.id) return;
    dialog.info({
      title: '提示',
      content: `您确定想删除此权限吗?`,
      positiveText: '确定',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await deleteMenu(formParams.id);
          message.success('删除成功');
          selectedTree([]);
          await loadMenus();
        } catch (error: any) {
          message.error(error?.message || '删除失败');
        }
      },
    });
  }

  function handleReset() {
    if (!selectedNode.value) return;
    Object.assign(formParams, {
      ...selectedNode.value,
      id: selectedNode.value.key,
      title: selectedNode.value.label,
    });
    formRef.value?.restoreValidation();
  }

  function formSubmit() {
    formRef.value.validate(async (errors: boolean) => {
      if (errors) {
        message.error('请填写完整信息');
        return;
      }
      subLoading.value = true;
      const payload = {
        title: formParams.title,
        type: formParams.type,
        parent_id: formParams.parent_id,
        permission_code: formParams.permission_code || null,
        path: formParams.type === 'button' ? null : formParams.path,
        name: formParams.type === 'button' ? null : formParams.name,
        component: formParams.type === 'button' ? null : formParams.component,
        redirect: formParams.type === 'button' ? null : formParams.redirect,
        icon: formParams.type === 'button' ? null : formParams.icon,
        sort: formParams.sort,
        hidden: formParams.hidden,
        keep_alive: formParams.keep_alive,
        enabled: formParams.enabled,
      };
      try {
        await updateMenu(formParams.id, payload);
        message.success('保存成功');
        await loadMenus();
      } catch (error: any) {
        message.error(error?.message || '保存失败');
      } finally {
        subLoading.value = false;
      }
    });
  }

  function packHandle() {
    expandedKeys.value = expandedKeys.value.length
      ? []
      : treeData.value.map((item: any) => item.key);
  }

  function onExpandedKeys(keys) {
    expandedKeys.value = keys;
  }

  onMounted(async () => {
    componentOptions.value = await getComponentOptions();
    await loadMenus();
  });
</script>
