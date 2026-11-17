<template>
  <n-flex vertical>
    <n-card :bordered="false">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <n-button text @click="goBack">
            <template #icon><n-icon><ArrowLeftOutlined /></n-icon></template>
          </n-button>
          <h2 class="text-lg font-semibold m-0">{{ isEdit ? '编辑角色' : '新增角色' }}</h2>
        </div>
        <n-space>
          <n-button @click="goBack">取消</n-button>
          <n-button type="primary" :loading="saving" @click="handleSave">
            <template #icon><n-icon><SaveOutlined /></n-icon></template>
            保存
          </n-button>
        </n-space>
      </div>
    </n-card>

    <n-spin :show="loading">
      <div class="max-w-3xl mx-auto w-full space-y-4 py-4">
        <!-- 基本信息 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><InfoCircleOutlined /></n-icon>
              <span class="text-sm font-bold">基本信息</span>
            </div>
          </template>
          <n-form :model="formValues" :rules="rules" ref="formRef" label-placement="top">
            <n-grid :cols="2" :x-gap="16">
              <n-form-item-gi label="角色名称" path="name">
                <n-input v-model:value="formValues.name" placeholder="请输入角色名称" :maxlength="50" />
              </n-form-item-gi>
              <n-form-item-gi label="角色编码" path="code">
                <n-input
                  v-model:value="formValues.code"
                  placeholder="请输入角色编码"
                  :maxlength="50"
                  :disabled="isEdit"
                />
              </n-form-item-gi>
              <n-form-item-gi label="状态" path="status">
                <n-radio-group v-model:value="formValues.status">
                  <n-space>
                    <n-radio value="active">启用</n-radio>
                    <n-radio value="disabled">禁用</n-radio>
                  </n-space>
                </n-radio-group>
              </n-form-item-gi>
              <n-form-item-gi label="角色说明" path="description" :span="2">
                <n-input
                  v-model:value="formValues.description"
                  type="textarea"
                  placeholder="请输入角色说明"
                  :maxlength="200"
                />
              </n-form-item-gi>
            </n-grid>
          </n-form>
        </n-card>

        <!-- 菜单权限 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><MenuOutlined /></n-icon>
              <span class="text-sm font-bold">菜单权限</span>
            </div>
          </template>
          <template #header-extra>
            <n-space>
              <n-button size="small" type="info" ghost @click="packHandle">
                全部{{ expandedKeys.length ? '收起' : '展开' }}
              </n-button>
              <n-button size="small" type="info" ghost @click="checkedAllHandle">
                全部{{ checkedAll ? '取消' : '选择' }}
              </n-button>
            </n-space>
          </template>
          <n-tree
            block-line
            cascade
            checkable
            :virtual-scroll="true"
            :data="treeData"
            :expandedKeys="expandedKeys"
            :checked-keys="checkedKeys"
            style="max-height: 600px; overflow: auto"
            @update:checked-keys="checkedTree"
            @update:expanded-keys="onExpandedKeys"
          />
        </n-card>
      </div>
    </n-spin>
  </n-flex>
</template>

<script lang="ts" setup>
  import { computed, onMounted, reactive, ref } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import type { FormInst, FormRules } from 'naive-ui';
  import {
    ArrowLeftOutlined,
    SaveOutlined,
    InfoCircleOutlined,
    MenuOutlined,
  } from '@vicons/antd';
  import {
    getRoleDetail,
    createRole,
    updateRole,
    getRoleMenus,
    updateRoleMenus,
  } from '@/api/system/role';
  import { getTreeAll } from '@/utils';
  import { getMenuList } from '@/api/system/menu';
  import { useTabsViewStore } from '@/store/modules/tabsView';
  import type { MenuTreeNode } from '@/api/system/menu';

  const route = useRoute();
  const router = useRouter();
  const tabsViewStore = useTabsViewStore();
  const roleId = computed(() => {
    const id = route.params.id;
    return id ? String(id) : null;
  });
  const isEdit = computed(() => roleId.value !== null);

  const formRef = ref<FormInst | null>(null);
  const loading = ref(false);
  const saving = ref(false);

  const formValues = reactive({
    name: '',
    code: '',
    description: '',
    status: 'active',
  });

  const rules: FormRules = {
    name: { required: true, message: '请输入角色名称', trigger: 'blur' },
    code: { required: true, message: '请输入角色编码', trigger: 'blur' },
  };

  const treeData = ref<MenuTreeNode[]>([]);
  const expandedKeys = ref<string[]>([]);
  const checkedKeys = ref<(string | number)[]>([]);
  const checkedAll = ref(false);

  onMounted(async () => {
    removeTab((t) => t.name === 'system_role');
    await loadMenuTree();
    if (roleId.value) {
      await loadRole(roleId.value);
    }
  });

  function removeTab(matcher: (t: any) => boolean) {
    try {
      const idx = tabsViewStore.tabsList.findIndex(matcher);
      if (idx > -1) {
        tabsViewStore.tabsList.splice(idx, 1);
      }
    } catch {}
  }

  function backToList() {
    removeTab((t) => t.fullPath === route.fullPath);
    if (window.history.state && window.history.state.back) {
      router.back();
    } else {
      router.push({ name: 'system_role' });
    }
  }

  async function loadMenuTree() {
    // 新增时也需要完整菜单树；编辑时再叠加已勾选 keys
    const { list } = await getMenuList();
    treeData.value = list;
    expandedKeys.value = treeData.value.map((item) => item.key as string);
  }

  async function loadRole(id: string) {
    loading.value = true;
    try {
      const detail = await getRoleDetail(id);
      formValues.name = detail.name || '';
      formValues.code = detail.code || '';
      formValues.description = detail.description || '';
      formValues.status = detail.status || 'active';
      const result = await getRoleMenus(id);
      treeData.value = result.tree;
      expandedKeys.value = result.tree.map((item) => item.key as string);
      checkedKeys.value = result.checkedKeys;
    } catch {
      window['$message']?.error('加载角色信息失败');
    } finally {
      loading.value = false;
    }
  }

  function checkedTree(keys) {
    checkedKeys.value = keys;
  }

  function onExpandedKeys(keys) {
    expandedKeys.value = keys;
  }

  function packHandle() {
    expandedKeys.value = expandedKeys.value.length
      ? []
      : treeData.value.map((item: any) => item.key);
  }

  function checkedAllHandle() {
    if (!checkedAll.value) {
      checkedKeys.value = getTreeAll(treeData.value);
      checkedAll.value = true;
    } else {
      checkedKeys.value = [];
      checkedAll.value = false;
    }
  }

  async function handleSave() {
    try {
      await formRef.value?.validate();
    } catch {
      window['$message']?.warning('请检查必填项');
      return;
    }

    saving.value = true;
    let saved = false;
    try {
      const payload = {
        name: formValues.name,
        code: formValues.code,
        description: formValues.description || undefined,
        status: formValues.status as 'active' | 'disabled',
      };
      let id = roleId.value;
      if (isEdit.value && id) {
        await updateRole(id, payload);
      } else {
        const created = await createRole(payload);
        id = String(created.id);
      }
      await updateRoleMenus(id!, checkedKeys.value);
      window['$message']?.success(isEdit.value ? '角色更新成功' : '角色创建成功');
      saved = true;
    } catch (e: any) {
      window['$message']?.error(e?.message || '保存失败');
    } finally {
      saving.value = false;
    }
    if (saved) {
      backToList();
    }
  }

  function goBack() {
    backToList();
  }
</script>

<style scoped>
  .flex { display: flex; }
  .items-center { align-items: center; }
  .justify-between { justify-content: space-between; }
  .gap-2 { gap: 0.5rem; }
  .gap-3 { gap: 0.75rem; }
  .space-y-4 > * + * { margin-top: 1rem; }
  .w-full { width: 100%; }
  .max-w-3xl { max-width: 48rem; }
  .mx-auto { margin-left: auto; margin-right: auto; }
  .py-4 { padding-top: 1rem; padding-bottom: 1rem; }
  .m-0 { margin: 0; }
  .text-sm { font-size: 0.875rem; }
  .text-lg { font-size: 1.125rem; }
  .font-semibold { font-weight: 600; }
  .font-bold { font-weight: 700; }
  .shadow-sm { box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05); }
</style>