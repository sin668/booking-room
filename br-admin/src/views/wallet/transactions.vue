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
  import { computed, onMounted, reactive, ref } from 'vue';
  import { BasicTable } from '@/components/Table';
  import {
    exportWalletTransactions,
    getWalletList,
    getWalletStatistics,
    type WalletListParams,
    type WalletStatistics,
    type WalletTransactionItem,
  } from '@/api/wallet';
  import { formatAdminMoney } from '@/views/business/shared/formatters';
  import { normalizeDateRange } from '@/views/business/shared/formSchemaBuilders';
  import {
    buildWalletFilterOptions,
    buildWalletStatCards,
    buildWalletTransactionColumns,
  } from './transactions.builders';

  const actionRef = ref();
  const exporting = ref(false);
  const { typeOptions, statusOptions } = buildWalletFilterOptions();

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

  const statCards = computed(() => buildWalletStatCards(statistics));
  const columns = buildWalletTransactionColumns();
  const formatMoney = formatAdminMoney;

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
    return normalizeDateRange(params.dateRange);
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
