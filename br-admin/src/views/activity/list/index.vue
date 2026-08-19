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
    </n-card>
  </n-flex>
</template>

<script lang="ts" setup>
  import { h, reactive, ref } from 'vue';
  import { useRouter } from 'vue-router';
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

  const router = useRouter();
  const actionRef = ref();
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
    router.push({ name: 'activity_edit' });
  }

  function handleEdit(record: ActivityItem) {
    router.push({ name: 'activity_edit', params: { id: record.id } });
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
    const nextStatus = !record.is_active;
    if (nextStatus && hasEnabledActivityCoupons(record)) {
      window['$dialog'].warning({
        title: '确认上架活动',
        content: '该活动包含启用的关联卡券，上架后将同步展示关联卡券。确定继续上架吗？',
        positiveText: '确认上架',
        negativeText: '取消',
        onPositiveClick: () => toggleStatus(record, nextStatus),
      });
      return;
    }
    toggleStatus(record, nextStatus);
  }

  function hasEnabledActivityCoupons(record: ActivityItem) {
    return (
      record.activity_coupons?.some((coupon) => coupon.is_active) ||
      (record.activity_coupon_count ?? 0) > 0
    );
  }

  function toggleStatus(record: ActivityItem, nextStatus: boolean) {
    toggleActivityStatus(record.id, nextStatus)
      .then(() => {
        window['$message'].success(record.is_active ? '已下架' : '已上架');
        reloadTable();
      })
      .catch((error) => {
        window['$message'].error(getReadableError(error, '操作失败，请检查活动卡券配置'));
      });
  }

  function getReadableError(error: unknown, fallback: string) {
    if (error instanceof Error && error.message) {
      return error.message;
    }
    return fallback;
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
