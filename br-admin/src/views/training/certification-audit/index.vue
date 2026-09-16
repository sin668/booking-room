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
        :row-key="(row: CertificationItem) => row.id"
        :actionColumn="actionColumn"
        :scroll-x="1200"
        :striped="true"
      />
    </n-card>
    <CertificationReviewModal
      v-model:show="reviewModalShow"
      :cert="currentCert"
      @success="reloadTable"
    />
  </n-flex>
</template>

<script lang="ts" setup>
  import { h, ref } from 'vue';
  import { NImage, NTag } from 'naive-ui';
  import { BasicTable, TableAction } from '@/components/Table';
  import { BasicForm, useForm } from '@/components/Form/index';
  import { getCertifications, type CertificationItem } from '@/api/certification';
  import { createDateTimeColumn } from '@/views/business/shared/tableBuilders';
  import {
    createKeywordSchema,
    createStatusSchema,
  } from '@/views/business/shared/formSchemaBuilders';
  import type { BusinessOption, BusinessTagConfig } from '@/views/business/shared/options';
  import CertificationReviewModal from './CertificationReviewModal.vue';

  const CERT_TYPE_OPTIONS: BusinessOption[] = [
    { label: '全部', value: '' },
    { label: '实名认证', value: 'real_name' },
    { label: '学历认证', value: 'education' },
    { label: '教师资格', value: 'teacher' },
  ];

  const CERT_STATUS_OPTIONS: BusinessOption[] = [
    { label: '全部', value: '' },
    { label: '待审核', value: 'pending' },
    { label: '已通过', value: 'approved' },
    { label: '已拒绝', value: 'rejected' },
  ];

  const CERT_TYPE_TAGS: Record<string, BusinessTagConfig> = {
    real_name: { label: '实名认证', type: 'info' },
    education: { label: '学历认证', type: 'warning' },
    teacher: { label: '教师资格', type: 'success' },
  };

  const CERT_STATUS_TAGS: Record<string, BusinessTagConfig> = {
    pending: { label: '待审核', type: 'warning' },
    approved: { label: '已通过', type: 'success' },
    rejected: { label: '已拒绝', type: 'error' },
  };

  const actionRef = ref();
  const reviewModalShow = ref(false);
  const currentCert = ref<CertificationItem | null>(null);

  function certInfoText(record: CertificationItem) {
    if (record.verification_type === 'real_name') return record.real_name || '-';
    if (record.verification_type === 'education') {
      return `${record.school || '-'} / ${record.education_level || '-'}`;
    }
    if (record.verification_type === 'teacher') {
      return record.teacher_certificate_number || '-';
    }
    return '-';
  }

  function certImageUrl(record: CertificationItem) {
    if (record.verification_type === 'education') return record.diploma_image_url;
    if (record.verification_type === 'teacher') return record.certificate_image_url;
    return null;
  }

  const columns = [
    {
      title: '用户',
      key: 'user_nickname',
      width: 200,
      render(record: CertificationItem) {
        return h('div', { class: 'flex flex-col' }, [
          h('span', { class: 'text-sm' }, record.user_nickname || '-'),
          h('span', { class: 'text-xs', style: 'color: #999' }, record.user_phone || ''),
        ]);
      },
    },
    {
      title: '认证类型',
      key: 'verification_type',
      width: 120,
      render(record: CertificationItem) {
        const config = CERT_TYPE_TAGS[record.verification_type];
        return config
          ? h(NTag, { type: config.type, size: 'small' }, { default: () => config.label })
          : record.verification_type;
      },
    },
    {
      title: '认证信息',
      key: 'info',
      width: 240,
      ellipsis: { tooltip: true },
      render(record: CertificationItem) {
        return certInfoText(record);
      },
    },
    {
      title: '证书照片',
      key: 'cert_images',
      width: 120,
      render(record: CertificationItem) {
        const url = certImageUrl(record);
        if (!url) return h('span', { style: 'color: #999' }, '-');
        return h(NImage, {
          src: url,
          width: 48,
          height: 48,
          objectFit: 'cover',
          style: 'border-radius: 4px; cursor: pointer',
        });
      },
    },
    {
      title: '状态',
      key: 'status',
      width: 100,
      render(record: CertificationItem) {
        const config = CERT_STATUS_TAGS[record.status] || {
          label: record.status || '未知',
          type: 'default' as const,
        };
        return h(NTag, { type: config.type, size: 'small' }, { default: () => config.label });
      },
    },
    createDateTimeColumn<CertificationItem>('提交时间', 'submitted_at'),
  ];

  const actionColumn = {
    width: 100,
    title: '操作',
    key: 'action',
    fixed: 'right' as const,
    render(record: CertificationItem) {
      return h(TableAction, {
        actions: [
          {
            label: record.status === 'pending' ? '审核' : '查看',
            onClick: () => handleReview(record),
          },
        ],
      });
    },
  };

  const [register, { getFieldsValue }] = useForm({
    gridProps: { cols: '1 s:1 m:2 l:3 xl:4 2xl:4' },
    labelWidth: 80,
    schemas: [
      createStatusSchema('status_filter', CERT_STATUS_OPTIONS),
      {
        field: 'type_filter',
        component: 'NSelect',
        label: '认证类型',
        componentProps: {
          placeholder: '全部',
          options: CERT_TYPE_OPTIONS,
        },
      },
      createKeywordSchema('keyword', '搜索昵称/手机号/学校'),
    ],
  });

  // 分页入参归一（pageSize -> page_size）与空值剔除都由 api 层的 normalizePageParams 负责，此处不重复
  const loadDataTable = async (res: any) => {
    return getCertifications({ ...getFieldsValue(), ...res });
  };

  function handleReview(record: CertificationItem) {
    currentCert.value = record;
    reviewModalShow.value = true;
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
