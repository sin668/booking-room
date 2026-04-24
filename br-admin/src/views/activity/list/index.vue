<template>
  <n-flex vertical>
    <n-card :bordered="false">
      <BasicForm @register="register" @submit="handleSubmit" @reset="handleReset" />
    </n-card>
    <n-card :bordered="false">
      <BasicTable
        :columns="columns"
        :request="loadDataTable"
        :row-key="(row: ActivityItem) => row.id"
        ref="actionRef"
        :actionColumn="actionColumn"
        :scroll-x="1100"
        :striped="true"
      >
        <template #tableTitle>
          <n-button type="primary" @click="addTable">
            <template #icon>
              <n-icon><PlusOutlined /></n-icon>
            </template>
            新建活动
          </n-button>
        </template>
      </BasicTable>

      <ActivityEditModal
        v-model:show="showModal"
        :editData="editData"
        @success="handleSuccess"
      />
    </n-card>
  </n-flex>
</template>

<script lang="ts" setup>
  import { h, reactive, ref } from 'vue';
  import { BasicTable, TableAction } from '@/components/Table';
  import { BasicForm, FormSchema, useForm } from '@/components/Form/index';
  import { PlusOutlined } from '@vicons/antd';
  import {
    getActivityList,
    deleteActivity,
    toggleActivityStatus,
    type ActivityItem,
  } from '@/api/activity';
  import { columns } from './columns';
  import ActivityEditModal from './ActivityEditModal.vue';

  const schemas: FormSchema[] = [
    {
      field: 'keyword',
      component: 'NInput',
      label: '关键词',
      componentProps: { placeholder: '搜索标题或描述' },
    },
    {
      field: 'is_active',
      component: 'NSelect',
      label: '状态',
      componentProps: {
        placeholder: '全部',
        options: [
          { label: '全部', value: '' },
          { label: '已上架', value: 'true' },
          { label: '已下架', value: 'false' },
        ],
      },
    },
  ];

  const actionRef = ref();
  const showModal = ref(false);
  const editData = ref<ActivityItem | null>(null);

  const [register, { getFieldsValue }] = useForm({
    gridProps: { cols: '1 s:1 m:2 l:3 xl:4 2xl:4' },
    labelWidth: 80,
    schemas,
  });

  const loadDataTable = async (res: any) => {
    const formValues = getFieldsValue();
    const queryParams: Record<string, any> = { ...formValues, ...res };

    // Convert camelCase to snake_case for API
    queryParams.page_size = queryParams.pageSize;
    delete queryParams.pageSize;

    // Convert is_active from string to boolean or remove
    if (queryParams.is_active === '' || queryParams.is_active === undefined) {
      delete queryParams.is_active;
    } else {
      queryParams.is_active = queryParams.is_active === 'true';
    }

    const result = await getActivityList(queryParams);
    return {
      list: result.items,
      itemCount: result.total,
      pageCount: Math.ceil(result.total / queryParams.page_size) || 1,
      page: result.page,
    };
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
          },
          {
            label: '删除',
            onClick: handleDelete.bind(null, record),
          },
        ],
        dropDownActions: [
          {
            label: record.is_active ? '下架' : '上架',
            key: record.is_active ? 'offline' : 'online',
          },
        ],
        select: (key: string) => {
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
