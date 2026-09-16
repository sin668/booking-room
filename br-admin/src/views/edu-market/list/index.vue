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
        :row-key="(row: AdminEduListingItem) => row.id"
        :actionColumn="actionColumn"
        :scroll-x="1760"
        :striped="true"
      />
    </n-card>
    <EduListingAuditModal
      v-model:show="auditModalShow"
      :listing="currentListing"
      @success="reloadTable"
    />
  </n-flex>
</template>

<script lang="ts" setup>
  import { h, ref } from 'vue';
  import { NAvatar, NTag } from 'naive-ui';
  import { BasicTable, TableAction } from '@/components/Table';
  import { BasicForm, useForm } from '@/components/Form/index';
  import { getAdminEduListings, type AdminEduListingItem } from '@/api/eduMarket';
  import {
    createDateTimeColumn,
    createTagColumn,
    createTextColumn,
  } from '@/views/business/shared/tableBuilders';
  import {
    EDU_LISTING_STATUS_OPTIONS,
    EDU_LISTING_STATUS_TAGS,
    EDU_LISTING_TYPE_OPTIONS,
    EDU_LISTING_TYPE_TAGS,
  } from '@/views/business/shared/options';
  import {
    createKeywordSchema,
    createStatusSchema,
  } from '@/views/business/shared/formSchemaBuilders';
  import EduListingAuditModal from './EduListingAuditModal.vue';

  const actionRef = ref();
  const auditModalShow = ref(false);
  const currentListing = ref<AdminEduListingItem | null>(null);

  const columns = [
    { title: 'ID', key: 'id', width: 60 },
    createTagColumn<AdminEduListingItem>('类型', 'listing_type', EDU_LISTING_TYPE_TAGS, 100),
    createTextColumn<AdminEduListingItem>('标题', 'title', 240),
    createTextColumn<AdminEduListingItem>('科目', 'subject', 100),
    {
      title: '价格',
      key: 'price',
      width: 120,
      render(record: AdminEduListingItem) {
        if (record.price === null || record.price === undefined || record.price === '') {
          return '面议';
        }
        const unit = record.price_unit ? ` ${record.price_unit}` : '';
        return `¥${Number(record.price).toFixed(2)}${unit}`;
      },
    },
    createTextColumn<AdminEduListingItem>('地区', 'area', 120),
    {
      title: '发布者',
      key: 'publisher_nickname',
      width: 180,
      render(record: AdminEduListingItem) {
        return h('div', { class: 'flex items-center gap-2' }, [
          h(NAvatar, {
            src: record.publisher_avatar || undefined,
            round: true,
            size: 32,
            style: 'flex-shrink: 0',
          }),
          h('span', { class: 'text-sm' }, record.publisher_nickname || '未知用户'),
        ]);
      },
    },
    {
      title: '认证状态',
      key: 'certification',
      width: 160,
      render(record: AdminEduListingItem) {
        const tags = [];
        if (record.publisher_education_verified) {
          tags.push(
            h(NTag, { type: 'warning', size: 'small', bordered: false }, { default: () => '学历' })
          );
        }
        if (record.publisher_teacher_verified) {
          tags.push(
            h(NTag, { type: 'success', size: 'small', bordered: false }, { default: () => '教师资格' })
          );
        }
        if (!tags.length) return h('span', { style: 'color: #999' }, '-');
        return h('div', { class: 'flex flex-wrap gap-1' }, tags);
      },
    },
    { title: '浏览', key: 'view_count', width: 80 },
    createTagColumn<AdminEduListingItem>('状态', 'status', EDU_LISTING_STATUS_TAGS, 100),
    createDateTimeColumn<AdminEduListingItem>('发布时间', 'created_at'),
  ];

  const actionColumn = {
    width: 100,
    title: '操作',
    key: 'action',
    fixed: 'right' as const,
    render(record: AdminEduListingItem) {
      return h(TableAction, {
        actions: [
          {
            label: '审核',
            onClick: () => handleAudit(record),
          },
        ],
      });
    },
  };

  const [register, { getFieldsValue }] = useForm({
    gridProps: { cols: '1 s:1 m:2 l:3 xl:4 2xl:4' },
    labelWidth: 80,
    schemas: [
      createKeywordSchema('keyword', '搜索标题'),
      {
        field: 'type',
        component: 'NSelect',
        label: '类型',
        componentProps: {
          placeholder: '全部',
          options: EDU_LISTING_TYPE_OPTIONS,
        },
      },
      createStatusSchema('status', EDU_LISTING_STATUS_OPTIONS),
    ],
  });

  // 分页入参归一（pageSize -> page_size）与空值剔除都由 api 层的 normalizePageParams 负责，此处不重复
  const loadDataTable = async (res: any) => {
    return getAdminEduListings({ ...getFieldsValue(), ...res });
  };

  function handleAudit(record: AdminEduListingItem) {
    currentListing.value = record;
    auditModalShow.value = true;
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
