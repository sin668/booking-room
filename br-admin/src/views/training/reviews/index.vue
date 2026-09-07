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
        :row-key="(row: AdminReviewItem) => row.id"
        :actionColumn="actionColumn"
        :scroll-x="1600"
        :striped="true"
      />
    </n-card>
    <ReviewAuditModal
      v-model:show="auditModalShow"
      :review="currentReview"
      @success="reloadTable"
    />
  </n-flex>
</template>

<script lang="ts" setup>
  import { h, ref } from 'vue';
  import { NAvatar, NRate, NTag } from 'naive-ui';
  import { BasicTable, TableAction } from '@/components/Table';
  import { BasicForm, useForm } from '@/components/Form/index';
  import { getAdminReviewList, type AdminReviewItem } from '@/api/review';
  import {
    createDateTimeColumn,
    createTagColumn,
    createTextColumn,
  } from '@/views/business/shared/tableBuilders';
  import {
    REVIEW_RATING_BAND_OPTIONS,
    REVIEW_STATUS_OPTIONS,
    REVIEW_STATUS_TAGS,
  } from '@/views/business/shared/options';
  import {
    createKeywordSchema,
    createStatusSchema,
  } from '@/views/business/shared/formSchemaBuilders';
  import ReviewAuditModal from './ReviewAuditModal.vue';

  const actionRef = ref();
  const auditModalShow = ref(false);
  const currentReview = ref<AdminReviewItem | null>(null);

  const columns = [
    { title: 'ID', key: 'id', width: 60 },
    {
      title: '发表者',
      key: 'user_nickname',
      width: 200,
      render(record: AdminReviewItem) {
        return h('div', { class: 'flex items-center gap-2' }, [
          h(NAvatar, {
            src: record.user_avatar || undefined,
            round: true,
            size: 32,
            style: 'flex-shrink: 0',
          }),
          h('span', { class: 'text-sm' }, record.user_nickname || '匿名用户'),
          record.is_anonymous
            ? h(NTag, { type: 'info', size: 'small', bordered: false }, { default: () => '匿名' })
            : null,
        ]);
      },
    },
    {
      title: '星级',
      key: 'rating',
      width: 130,
      render(record: AdminReviewItem) {
        return h(NRate, { value: record.rating, readonly: true, size: 'small' });
      },
    },
    createTextColumn<AdminReviewItem>('评价内容', 'content', 260),
    {
      title: '图片',
      key: 'images',
      width: 70,
      render(record: AdminReviewItem) {
        return record.images?.length ? `${record.images.length}张` : '-';
      },
    },
    createTextColumn<AdminReviewItem>('所属课程', 'course_name', 150),
    createTextColumn<AdminReviewItem>('所属老师', 'teacher_name', 110),
    { title: '订单号', key: 'booking_id', width: 90 },
    createDateTimeColumn<AdminReviewItem>('发表时间', 'created_at'),
    createTagColumn<AdminReviewItem>('审核状态', 'status', REVIEW_STATUS_TAGS, 100),
    {
      title: '机构回复',
      key: 'reply_content',
      width: 100,
      render(record: AdminReviewItem) {
        const replied = Boolean(record.reply_content);
        return h(
          NTag,
          { type: replied ? 'success' : 'default', size: 'small' },
          { default: () => (replied ? '已回复' : '未回复') }
        );
      },
    },
  ];

  const actionColumn = {
    width: 100,
    title: '操作',
    key: 'action',
    fixed: 'right' as const,
    render(record: AdminReviewItem) {
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
      createKeywordSchema('keyword', '搜索评价内容或用户昵称'),
      createStatusSchema('status', REVIEW_STATUS_OPTIONS),
      {
        field: 'rating_band',
        component: 'NSelect',
        label: '评分档位',
        componentProps: {
          placeholder: '全部',
          options: REVIEW_RATING_BAND_OPTIONS,
        },
      },
    ],
  });

  // 分页入参归一（pageSize -> page_size）与空值剔除都由 api 层的 normalizePageParams 负责，此处不重复
  const loadDataTable = async (res: any) => {
    return getAdminReviewList({ ...getFieldsValue(), ...res });
  };

  function handleAudit(record: AdminReviewItem) {
    currentReview.value = record;
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
