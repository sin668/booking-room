<template>
  <div>
    <div class="n-layout-page-header">
      <n-card :bordered="false" title="用户管理"> 管理系统用户与App用户。 </n-card>
    </div>
    <n-card :bordered="false" class="mt-4 proCard">
      <div class="mb-4 flex items-center gap-3">
        <n-select
          v-model:value="params.user_type"
          :options="userTypeOptions"
          placeholder="用户类型"
          clearable
          style="width: 140px"
          @update:value="reloadTable"
        />
        <n-input
          v-model:value="params.keyword"
          placeholder="关键词搜索"
          clearable
          style="width: 200px"
          @keyup.enter="reloadTable"
        />
        <n-select
          v-model:value="params.status"
          :options="statusOptions"
          placeholder="状态"
          clearable
          style="width: 140px"
          @update:value="reloadTable"
        />
        <n-button type="primary" @click="reloadTable">搜索</n-button>
      </div>
      <BasicTable
        :columns="columns"
        :request="loadDataTable"
        :row-key="(row) => row.id"
        ref="actionRef"
        :actionColumn="actionColumn"
      >
        <template #tableTitle>
          <n-button
            v-permission="{ action: ['system:user:create'] }"
            type="primary"
            @click="addUser"
          >
            <template #icon>
              <n-icon>
                <PlusOutlined />
              </n-icon>
            </template>
            新增用户
          </n-button>
        </template>

        <template #action>
          <TableAction />
        </template>
      </BasicTable>
    </n-card>

    <CreateModal ref="createModalRef" @success="reloadTable" />
    <EditModal ref="editModalRef" @success="reloadTable" />
    <RoleModal ref="roleModalRef" @success="reloadTable" />
  </div>
</template>

<script lang="ts" setup>
  import { h, reactive, ref } from 'vue';
  import { useMessage } from 'naive-ui';
  import { BasicTable, TableAction } from '@/components/Table';
  import { getUserList, deleteUser, resetUserPassword, toggleUserStatus } from '@/api/system/user';
  import { columns } from './columns';
  import { PlusOutlined } from '@vicons/antd';
  import CreateModal from './CreateModal.vue';
  import EditModal from './EditModal.vue';
  import RoleModal from './RoleModal.vue';

  const message = useMessage();
  const actionRef = ref();
  const createModalRef = ref();
  const editModalRef = ref();
  const roleModalRef = ref();

  const params = reactive({
    user_type: null as string | null,
    keyword: '',
    status: null as string | null,
  });

  const userTypeOptions = [
    { label: '全部', value: null },
    { label: 'App用户', value: 'app' },
    { label: '管理员', value: 'admin' },
  ];

  const statusOptions = [
    { label: '全部', value: null },
    { label: '正常', value: 'active' },
    { label: '封禁', value: 'banned' },
    { label: '禁用', value: 'disabled' },
  ];

  const actionColumn = reactive({
    width: 340,
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
            auth: ['system:user:update'],
            ifShow: () => true,
          },
          {
            label: '分配角色',
            onClick: handleAssignRole.bind(null, record),
            ifShow: () => true,
          },
          {
            label: '重置密码',
            onClick: handleResetPassword.bind(null, record),
            auth: ['system:user:reset-password'],
            ifShow: () => true,
          },
          {
            label: '切换状态',
            onClick: handleToggleStatus.bind(null, record),
            auth: ['system:user:status'],
            ifShow: () => true,
          },
          {
            label: '删除',
            onClick: handleDelete.bind(null, record),
            auth: ['system:user:delete'],
            ifShow: () => true,
          },
        ],
      });
    },
  });

  const loadDataTable = async (res: any) => {
    const _params = {
      user_type: params.user_type || undefined,
      keyword: params.keyword || undefined,
      status: params.status || undefined,
      ...res,
    };
    const result = await getUserList(_params);
    return {
      list: result.list,
      itemCount: result.itemCount,
      pageCount: result.pageCount,
      page: result.page,
    };
  };

  function reloadTable() {
    actionRef.value.reload();
  }

  function addUser() {
    createModalRef.value.openModal();
  }

  function handleEdit(record: any) {
    editModalRef.value.showModal(record);
  }

  function handleAssignRole(record: any) {
    roleModalRef.value.showModal(record);
  }

  function handleDelete(record: any) {
    window['$dialog'].warning({
      title: '确认删除',
      content: `确定要删除用户「${record.nickname || record.phone}」吗？`,
      positiveText: '确认删除',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await deleteUser(record.id);
          window['$message'].success('删除成功');
          reloadTable();
        } catch (error: any) {
          window['$message'].error(error?.message || '删除失败');
        }
      },
    });
  }

  function handleResetPassword(record: any) {
    let newPassword = '';
    window['$dialog'].warning({
      title: '重置密码',
      content: () =>
        h('div', {}, [
          h(
            'p',
            { class: 'mb-2' },
            `确定要重置用户「${record.nickname || record.phone}」的密码吗？`
          ),
          h('n-input', {
            type: 'password',
            showPasswordOn: 'click',
            placeholder: '请输入新密码',
            onUpdateValue: (val: string) => {
              newPassword = val;
            },
          }),
        ]),
      positiveText: '确认重置',
      negativeText: '取消',
      onPositiveClick: async () => {
        if (!newPassword) {
          window['$message'].warning('请输入新密码');
          return false;
        }
        try {
          await resetUserPassword(record.id, newPassword);
          window['$message'].success('密码重置成功');
        } catch (error: any) {
          window['$message'].error(error?.message || '重置失败');
        }
      },
    });
  }

  function handleToggleStatus(record: any) {
    const currentStatus = record.status;
    const targetStatus = currentStatus === 'active' ? 'disabled' : 'active';
    const targetLabel = targetStatus === 'active' ? '启用' : '禁用';
    window['$dialog'].warning({
      title: '切换用户状态',
      content: `确定要将用户「${record.nickname || record.phone}」${targetLabel}吗？`,
      positiveText: `确认${targetLabel}`,
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await toggleUserStatus(record.id, targetStatus);
          window['$message'].success(`已${targetLabel}`);
          reloadTable();
        } catch (error: any) {
          window['$message'].error(error?.message || '操作失败');
        }
      },
    });
  }
</script>
