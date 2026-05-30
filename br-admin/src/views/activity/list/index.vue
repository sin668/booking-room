<template>
  <n-flex vertical>
    <n-card :bordered="false">
      <BasicForm @register="register" @submit="handleSubmit" @reset="handleReset" />
    </n-card>
    <n-card :bordered="false">
      <BasicTable
        ref="actionRef"
        :columns="columns"
        :request="loadDataTable"
        :row-key="(row: ActivityItem) => row.id"
        :actionColumn="actionColumn"
        :scroll-x="1100"
        :striped="true"
      >
        <template #tableTitle>
          <n-button v-permission="{ action: ['activity:create'] }" type="primary" @click="addTable">
            <template #icon>
              <n-icon><PlusOutlined /></n-icon>
            </template>
            新建活动
          </n-button>
        </template>
      </BasicTable>

      <ActivityEditModal v-model:show="showModal" :editData="editData" @success="handleSuccess" />
    </n-card>
  </n-flex>
</template>

<script lang="ts" setup>
  import { h, reactive, ref } from 'vue';
  import { PlusOutlined } from '@vicons/antd';
  import { BasicTable, TableAction } from '@/components/Table';
  import { BasicForm, useForm } from '@/components/Form/index';
  import {
    deleteActivity,
    getActivityList,
    toggleActivityStatus,
    type ActivityItem,
  } from '@/api/activity';
  import { toBasicTableResult } from '@/api/contracts/admin';
  import { buildActivitySearchSchemas, buildActivityTableColumns } from './builders';
  import ActivityEditModal from './ActivityEditModal.vue';

  const actionRef = ref();
  const showModal = ref(false);
  const editData = ref<ActivityItem | null>(null);
  const columns = buildActivityTableColumns();

  const [register, { getFieldsValue }] = useForm({
    gridProps: { cols: '1 s:1 m:2 l:3 xl:4 2xl:4' },
    labelWidth: 80,
    schemas: buildActivitySearchSchemas(),
  });

  const loadDataTable = async (res: any) => {
    const formValues = getFieldsValue();
    const queryParams: Record<string, any> = { ...formValues, ...res };

    queryParams.page_size = queryParams.pageSize;
    delete queryParams.pageSize;

    if (!queryParams.is_active) {
      delete queryParams.is_active;
    } else {
      queryParams.is_active = queryParams.is_active === 'true';
    }

    const result = await getActivityList(queryParams);
    return toBasicTableResult(result);
  };

  const actionColumn = reactive({
    width: 220,
    title: '操作',
    key: 'action',
    fixed: 'right',
    render(record: ActivityItem) {
      return h(TableAction as any, {
        style: 'button',
        actions: [
          {
            label: '编辑',
            onClick: handleEdit.bind(null, record),
            auth: ['activity:update'],
          },
          {
            label: '删除',
            onClick: handleDelete.bind(null, record),
            auth: ['activity:delete'],
          },
        ],
        dropDownActions: [
          {
            label: record.is_active ? '下架' : '上架',
            key: record.is_active ? 'offline' : 'online',
            auth: ['activity:status'],
          },
        ],
        select: () => {
          handleToggleStatus(record);
        },
      });
    },
  });

  function addTable() {
    editData.value = null;
    showModal.value = true;
  }

  function handleEdit(record: ActivityItem) {
    editData.value = record;
    showModal.value = true;
  }

  function handleDelete(record: ActivityItem) {
    window['$dialog'].warning({
      title: '确认删除',
      content: `确定要删除活动「${record.title}」吗？`,
      positiveText: '确认删除',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await deleteActivity(record.id);
          window['$message'].success('删除成功');
          reloadTable();
        } catch {
          window['$message'].error('删除失败');
        }
      },
    });
  }

  function handleToggleStatus(record: ActivityItem) {
    toggleActivityStatus(record.id, !record.is_active)
      .then(() => {
        window['$message'].success(record.is_active ? '已下架' : '已上架');
        reloadTable();
      })
      .catch(() => {
        window['$message'].error('操作失败');
      });
  }

  function handleSuccess() {
    showModal.value = false;
    reloadTable();
  }

  function handleSubmit() {
    reloadTable();
  }

  function handleReset() {
    reloadTable();
  }

  function reloadTable() {
    actionRef.value.reload();
  }
</script>
