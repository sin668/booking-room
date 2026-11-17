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
  </div>
</template>

<script lang="ts" setup>
  import { h, reactive, ref, unref } from 'vue';
  import { useRouter } from 'vue-router';
  import { BasicTable, TableAction } from '@/components/Table';
  import { getRoleList, deleteRole } from '@/api/system/role';
  import { columns } from './columns';
  import { PlusOutlined } from '@vicons/antd';

  const router = useRouter();
  const actionRef = ref();

  const params = reactive({
    name: '',
    code: '',
  });

  const actionColumn = reactive({
    width: 200,
    title: '操作',
    key: 'action',
    fixed: 'right',
    render(record) {
      return h(TableAction, {
        style: 'button',
        actions: [
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
    router.push({ name: 'system_role_edit' });
  }

  function onCheckedRow(rowKeys: any[]) {
    console.log(rowKeys);
  }

  function reloadTable() {
    actionRef.value.reload();
  }

  function handleEdit(record: Recordable) {
    router.push({ name: 'system_role_edit', params: { id: record.id } });
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
</script>
