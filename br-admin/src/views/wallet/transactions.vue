<template>
  <div>
    <n-grid cols="1 s:2 m:4" :x-gap="16" :y-gap="16" responsive="screen">
      <n-gi v-for="item in statCards" :key="item.key">
        <n-card :bordered="false" class="stat-card">
          <div class="stat-label">{{ item.label }}</div>
          <div class="stat-value" :class="item.className">{{ formatMoney(item.value) }}</div>
        </n-card>
      </n-gi>
    </n-grid>

    <n-card :bordered="false" class="mt-4 proCard">
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <n-select
          v-model:value="params.type"
          :options="typeOptions"
          placeholder="交易类型"
          clearable
          style="width: 140px"
          @update:value="reloadTable"
        />
        <n-select
          v-model:value="params.status"
          :options="statusOptions"
          placeholder="状态"
          clearable
          style="width: 140px"
          @update:value="reloadTable"
        />
        <n-date-picker
          v-model:value="params.dateRange"
          type="daterange"
          clearable
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 260px"
          @update:value="handleDateRangeChange"
        />
        <n-button type="primary" @click="reloadTable">搜索</n-button>
        <n-button
          v-permission="{ action: ['wallet:export'] }"
          :loading="exporting"
          @click="handleExport"
        >
          导出
        </n-button>
      </div>

      <BasicTable
        ref="actionRef"
        :columns="columns"
        :request="loadDataTable"
        :row-key="(row: WalletTransactionItem) => row.id"
        :scroll-x="1200"
        :striped="true"
      />
    </n-card>
  </div>
</template>

<script lang="ts" setup>
  import { computed, h, onMounted, reactive, ref } from 'vue';
  import { NTag } from 'naive-ui';
  import type { BasicColumn } from '@/components/Table';
  import { BasicTable } from '@/components/Table';
  import {
    exportWalletTransactions,
    getWalletList,
    getWalletStatistics,
    type WalletListParams,
    type WalletStatistics,
    type WalletTransactionItem,
  } from '@/api/wallet';

  const actionRef = ref();
  const exporting = ref(false);

  const params = reactive({
    type: null as string | null,
    status: null as string | null,
    dateRange: null as [number, number] | null,
  });

  const statistics = reactive<WalletStatistics>({
    total_recharge: 0,
    total_consume: 0,
    total_refund: 0,
    net_income: 0,
    active_users: 0,
    total_transactions: 0,
  });

  const typeOptions = [
    { label: '全部', value: null },
    { label: '充值', value: 'recharge' },
    { label: '消费', value: 'consume' },
    { label: '退款', value: 'refund' },
  ];

  const statusOptions = [
    { label: '全部', value: null },
    { label: '待处理', value: 'pending' },
    { label: '已完成', value: 'completed' },
    { label: '失败', value: 'failed' },
    { label: '已取消', value: 'cancelled' },
  ];

  type TagType = 'success' | 'warning' | 'error' | 'default';

  const transactionTypeMap: Record<string, { label: string; type: TagType }> = {
    recharge: { label: '充值', type: 'success' },
    consume: { label: '消费', type: 'warning' },
    refund: { label: '退款', type: 'error' },
  };

  const statusMap: Record<string, { label: string; type: TagType }> = {
    pending: { label: '待处理', type: 'warning' },
    completed: { label: '已完成', type: 'success' },
    failed: { label: '失败', type: 'error' },
    cancelled: { label: '已取消', type: 'default' },
  };

  const statCards = computed(() => [
    {
      key: 'total_recharge',
      label: '总充值',
      value: statistics.total_recharge,
      className: 'text-green',
    },
    {
      key: 'total_consume',
      label: '总消费',
      value: statistics.total_consume,
      className: 'text-orange',
    },
    {
      key: 'total_refund',
      label: '总退款',
      value: statistics.total_refund,
      className: 'text-red',
    },
    {
      key: 'net_income',
      label: '净收入',
      value: statistics.net_income,
      className: 'text-blue',
    },
  ]);

  const columns: BasicColumn<WalletTransactionItem>[] = [
    {
      title: '交易时间',
      key: 'created_at',
      width: 170,
      render(record) {
        return formatDateTime(record.created_at);
      },
    },
    {
      title: '用户',
      key: 'user',
      width: 180,
      render(record) {
        return h('div', { class: 'user-cell' }, [
          h('div', { class: 'user-name' }, record.user_nickname || '未设置昵称'),
          h('div', { class: 'user-phone' }, record.user_phone || '-'),
        ]);
      },
    },
    {
      title: '交易类型',
      key: 'type',
      width: 110,
      render(record) {
        const config = transactionTypeMap[record.type] || { label: record.type, type: 'default' };
        return h(NTag, { type: config.type, size: 'small' }, { default: () => config.label });
      },
    },
    {
      title: '金额',
      key: 'amount',
      width: 130,
      render(record) {
        const isRecharge = record.type === 'recharge';
        return h(
          'span',
          { class: isRecharge ? 'amount-positive' : 'amount-negative' },
          `${isRecharge ? '+' : '-'}${formatMoney(record.amount)}`
        );
      },
    },
    {
      title: '余额',
      key: 'balance_after',
      width: 120,
      render(record) {
        return formatMoney(record.balance_after);
      },
    },
    {
      title: '状态',
      key: 'status',
      width: 110,
      render(record) {
        const config = statusMap[record.status] || { label: record.status, type: 'default' };
        return h(NTag, { type: config.type, size: 'small' }, { default: () => config.label });
      },
    },
    {
      title: '支付方式',
      key: 'payment_method',
      width: 130,
      render(record) {
        return record.payment_method || '-';
      },
    },
  ];

  function formatMoney(value: number | string | null | undefined) {
    const amount = Number(value || 0);
    return `¥${amount.toFixed(2)}`;
  }

  function formatDate(value: number) {
    const date = new Date(value);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  function formatDateTime(value: string | null | undefined) {
    if (!value) return '-';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    const time = `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(
      2,
      '0'
    )}`;
    return `${formatDate(date.getTime())} ${time}`;
  }

  function buildFilterParams(): WalletListParams {
    const query: WalletListParams = {
      type: params.type || undefined,
      status: params.status || undefined,
    };

    return {
      ...query,
      ...buildStatisticsParams(),
    };
  }

  function buildStatisticsParams(): Pick<WalletListParams, 'date_start' | 'date_end'> {
    const query: Pick<WalletListParams, 'date_start' | 'date_end'> = {};

    if (params.dateRange?.[0] && params.dateRange?.[1]) {
      query.date_start = formatDate(params.dateRange[0]);
      query.date_end = formatDate(params.dateRange[1]);
    }

    return query;
  }

  async function loadStatistics() {
    const result = await getWalletStatistics(buildStatisticsParams());
    Object.assign(statistics, result);
  }

  const loadDataTable = async (res: any) => {
    return getWalletList({
      ...buildFilterParams(),
      ...res,
    });
  };

  async function reloadTable() {
    await actionRef.value?.reload();
  }

  function handleDateRangeChange() {
    void loadStatistics();
    void reloadTable();
  }

  async function handleExport() {
    try {
      exporting.value = true;
      await exportWalletTransactions(buildFilterParams());
      window['$message']?.success('导出成功');
    } catch (error: any) {
      window['$message']?.error(error?.message || '导出失败');
    } finally {
      exporting.value = false;
    }
  }

  onMounted(() => {
    loadStatistics();
  });
</script>

<style scoped>
  .stat-card {
    min-height: 108px;
  }

  .stat-label {
    color: #6b7280;
    font-size: 14px;
    line-height: 22px;
  }

  .stat-value {
    margin-top: 10px;
    font-size: 28px;
    font-weight: 600;
    line-height: 36px;
  }

  .text-green,
  .amount-positive {
    color: #18a058;
  }

  .text-orange {
    color: #f0a020;
  }

  .text-red,
  .amount-negative {
    color: #d03050;
  }

  .text-blue {
    color: #2080f0;
  }

  .user-cell {
    line-height: 20px;
  }

  .user-name {
    color: #1f2937;
    font-weight: 500;
  }

  .user-phone {
    color: #6b7280;
    font-size: 12px;
  }
</style>
