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
        :row-key="(row: AdminCouponItem) => row.id"
        :actionColumn="actionColumn"
        :scroll-x="1280"
        :striped="true"
      >
        <template #tableTitle>
          <n-button v-permission="{ action: ['coupon:create'] }" type="primary" @click="addTable">
            <template #icon>
              <n-icon><PlusOutlined /></n-icon>
            </template>
            新建卡券
          </n-button>
        </template>
      </BasicTable>

      <CouponEditModal v-model:show="showModal" :editData="editData" @success="handleSuccess" />
    </n-card>
  </n-flex>
</template>

<script setup lang="ts">
  import { h, reactive, ref } from 'vue';
  import { PlusOutlined } from '@vicons/antd';
  import { BasicForm, useForm } from '@/components/Form';
  import { BasicTable, TableAction } from '@/components/Table';
  import {
    deleteCoupon,
    getCouponList,
    toggleCouponStatus,
    type AdminCouponItem,
  } from '@/api/coupon';
  import { toBasicTableResult } from '@/api/contracts/admin';
  import { buildCouponTableColumns, isCouponExpired } from './columns';
  import CouponEditModal from './CouponEditModal.vue';

  const actionRef = ref();
  const showModal = ref(false);
  const editData = ref<AdminCouponItem | null>(null);
  const columns = buildCouponTableColumns();

  const [register, { getFieldsValue }] = useForm({
    gridProps: { cols: '1 s:1 m:2 l:3 xl:4 2xl:4' },
    labelWidth: 80,
    schemas: [
      {
        field: 'keyword',
        component: 'NInput',
        label: '关键词',
        componentProps: { placeholder: '搜索卡券名称或描述' },
      },
      {
        field: 'type',
        component: 'NSelect',
        label: '类型',
        componentProps: {
          placeholder: '全部',
          options: [
            { label: '满减券', value: 'threshold_amount_off' },
            { label: '立减券', value: 'amount_off' },
            { label: '折扣券', value: 'percentage_off' },
          ],
        },
      },
      {
        field: 'scope',
        component: 'NSelect',
        label: '范围',
        componentProps: {
          placeholder: '全部',
          options: [
            { label: '全场通用', value: 'all' },
            { label: '首次预约', value: 'first_booking' },
            { label: 'VIP专享', value: 'vip_only' },
            { label: '指定区域', value: 'seat_zone' },
          ],
        },
      },
      {
        field: 'is_active',
        component: 'NSelect',
        label: '状态',
        componentProps: {
          placeholder: '全部',
          options: [
            { label: '启用', value: 'true' },
            { label: '停用', value: 'false' },
          ],
        },
      },
    ],
  });

  const loadDataTable = async (res: any) => {
    const queryParams: Record<string, any> = { ...getFieldsValue(), ...res };
    queryParams.page_size = queryParams.pageSize;
    delete queryParams.pageSize;
    Object.keys(queryParams).forEach((key) => {
      if (queryParams[key] === '' || queryParams[key] === undefined || queryParams[key] === null) {
        delete queryParams[key];
      }
    });
    if (queryParams.is_active !== undefined) {
      queryParams.is_active = queryParams.is_active === 'true';
    }
    const result = await getCouponList(queryParams);
    return toBasicTableResult(result);
  };

  const actionColumn = reactive({
    width: 220,
    title: '操作',
    key: 'action',
    fixed: 'right',
    render(record: AdminCouponItem) {
      return h(TableAction as any, {
        style: 'button',
        actions: [
          {
            label: '编辑',
            onClick: handleEdit.bind(null, record),
            auth: ['coupon:update'],
          },
          {
            label: '删除',
            onClick: handleDelete.bind(null, record),
            auth: ['coupon:delete'],
          },
        ],
        dropDownActions: [
          {
            label: record.is_active ? '停用' : '启用',
            key: record.is_active ? 'disable' : 'enable',
            auth: ['coupon:update'],
            disabled: isCouponExpired(record),
          },
        ],
        select: () => handleToggleStatus(record),
      });
    },
  });

  function addTable() {
    editData.value = null;
    showModal.value = true;
  }

  function handleEdit(record: AdminCouponItem) {
    editData.value = record;
    showModal.value = true;
  }

  function handleDelete(record: AdminCouponItem) {
    window['$dialog'].warning({
      title: '确认删除',
      content: `确定要删除卡券「${record.name}」吗？`,
      positiveText: '确认删除',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await deleteCoupon(record.id);
          window['$message'].success('删除成功');
          reloadTable();
        } catch (error) {
          const message = error instanceof Error && error.message ? error.message : '删除失败';
          window['$message'].error(message);
        }
      },
    });
  }

  function handleToggleStatus(record: AdminCouponItem) {
    toggleCouponStatus(record.id, !record.is_active)
      .then(() => {
        window['$message'].success(record.is_active ? '已停用' : '已启用');
        reloadTable();
      })
      .catch((error) => {
        const message = error instanceof Error && error.message ? error.message : '操作失败';
        window['$message'].error(message);
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
    actionRef.value?.reload();
  }
</script>
