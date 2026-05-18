<template>
  <div>
    <div class="n-layout-page-header">
      <n-card :bordered="false" title="角色权限管理"> 管理角色与菜单授权。 </n-card>
    </div>
    <n-card :bordered="false" class="mt-4 proCard">
      <BasicTable
        :columns="columns"
        :request="loadDataTable"
        :row-key="(row) => row.id"
        ref="actionRef"
        :actionColumn="actionColumn"
        @update:checked-row-keys="onCheckedRow"
      >
        <template #tableTitle>
          <n-button
            v-permission="{ action: ['system:role:create'] }"
            type="primary"
            @click="addRole"
          >
            <template #icon>
              <n-icon>
                <PlusOutlined />
              </n-icon>
            </template>
            新增角色
          </n-button>
        </template>

        <template #action>
          <TableAction />
        </template>
      </BasicTable>
    </n-card>

    <n-modal v-model:show="showModal" :show-icon="false" preset="dialog" :title="editRoleTitle">
      <div class="py-3 menu-list">
        <n-tree
          block-line
          cascade
          checkable
          :virtual-scroll="true"
          :data="treeData"
          :expandedKeys="expandedKeys"
          :checked-keys="checkedKeys"
          style="max-height: 950px; overflow: hidden"
          @update:checked-keys="checkedTree"
          @update:expanded-keys="onExpandedKeys"
        />
      </div>
      <template #action>
        <n-space>
          <n-button type="info" ghost icon-placement="left" @click="packHandle">
            全部{{ expandedKeys.length ? '收起' : '展开' }}
          </n-button>
          <n-button type="info" ghost icon-placement="left" @click="checkedAllHandle">
            全部{{ checkedAll ? '取消' : '选择' }}
          </n-button>
          <n-button type="primary" :loading="formBtnLoading" @click="confirmForm">提交</n-button>
        </n-space>
      </template>
    </n-modal>
    <CreateModal ref="createModalRef" @success="reloadTable" />
    <EditModal ref="editModalRef" @success="reloadTable" />
  </div>
</template>

<script lang="ts" setup>
  import { h, reactive, ref, unref } from 'vue';
  import { useMessage } from 'naive-ui';
  import { BasicTable, TableAction } from '@/components/Table';
  import { getRoleList, getRoleMenus, updateRoleMenus, deleteRole } from '@/api/system/role';
  import { columns } from './columns';
  import { PlusOutlined } from '@vicons/antd';
  import { getTreeAll } from '@/utils';
  import CreateModal from './CreateModal.vue';
  import EditModal from './EditModal.vue';
  import type { MenuTreeNode } from '@/api/system/menu';

  const message = useMessage();
  const actionRef = ref();
  const createModalRef = ref();
  const editModalRef = ref();
  const showModal = ref(false);
  const formBtnLoading = ref(false);
  const checkedAll = ref(false);
  const editRoleTitle = ref('');
  const treeData = ref<MenuTreeNode[]>([]);
  const expandedKeys = ref<string[]>([]);
  const checkedKeys = ref<(string | number)[]>([]);
  const activeRoleId = ref<string | number | null>(null);

  const params = reactive({
    name: '',
    code: '',
  });

  const actionColumn = reactive({
    width: 280,
    title: '操作',
    key: 'action',
    fixed: 'right',
    render(record) {
      return h(TableAction, {
        style: 'button',
        actions: [
          {
            label: '菜单权限',
            onClick: handleMenuAuth.bind(null, record),
            auth: ['system:role:assign'],
            ifShow: () => true,
          },
          {
            label: '编辑',
            onClick: handleEdit.bind(null, record),
            auth: ['system:role:update'],
            ifShow: () => true,
          },
          {
            label: '删除',
            onClick: handleDelete.bind(null, record),
            auth: ['system:role:delete'],
            ifShow: () => true,
          },
        ],
      });
    },
  });

  const loadDataTable = async (res: any) => {
    const _params = {
      ...unref(params),
      ...res,
    };
    const result = await getRoleList(_params);
    return {
      list: result.list,
      itemCount: result.itemCount,
      pageCount: result.pageCount,
      page: result.page,
    };
  };

  function addRole() {
    createModalRef.value.openModal();
  }

  function onCheckedRow(rowKeys: any[]) {
    console.log(rowKeys);
  }

  function reloadTable() {
    actionRef.value.reload();
  }

  function handleEdit(record: Recordable) {
    editModalRef.value.showModal(record);
  }

  function handleDelete(record: Recordable) {
    window['$dialog'].warning({
      title: '确认删除',
      content: `确定要删除角色「${record.name}」吗？`,
      positiveText: '确认删除',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await deleteRole(record.id);
          window['$message'].success('删除成功');
          reloadTable();
        } catch (error: any) {
          window['$message'].error(error?.message || '删除失败');
        }
      },
    });
  }

  async function handleMenuAuth(record: Recordable) {
    activeRoleId.value = record.id;
    editRoleTitle.value = `分配 ${record.name} 的菜单权限`;
    const result = await getRoleMenus(record.id);
    treeData.value = result.tree;
    expandedKeys.value = result.tree.map((item) => item.key as string);
    checkedKeys.value = result.checkedKeys;
    showModal.value = true;
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

  async function confirmForm(e: any) {
    e.preventDefault();
    if (activeRoleId.value == null) return;
    formBtnLoading.value = true;
    try {
      await updateRoleMenus(activeRoleId.value, checkedKeys.value);
      showModal.value = false;
      message.success('提交成功');
      reloadTable();
    } catch (error: any) {
      message.error(error?.message || '提交失败');
    } finally {
      formBtnLoading.value = false;
    }
  }
</script>
