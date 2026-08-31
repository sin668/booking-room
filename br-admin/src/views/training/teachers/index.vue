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
        :row-key="(row: AdminTeacherItem) => row.id"
        :actionColumn="actionColumn"
        :scroll-x="1200"
        :striped="true"
      >
        <template #tableTitle>
          <n-button type="primary" @click="addTeacher">
            <template #icon>
              <n-icon><PlusOutlined /></n-icon>
            </template>
            新增老师
          </n-button>
        </template>
      </BasicTable>
    </n-card>
    <TeacherScheduleModal
      v-model:show="scheduleModalShow"
      :teacher-id="currentTeacherId"
      :teacher-name="currentTeacherName"
      @success="reloadTable"
    />
  </n-flex>
</template>

<script lang="ts" setup>
  import { h, ref } from 'vue';
  import TeacherScheduleModal from './TeacherScheduleModal.vue';
  import { useRouter } from 'vue-router';
  import { NAvatar } from 'naive-ui';
  import { PlusOutlined } from '@vicons/antd';
  import { BasicTable, TableAction } from '@/components/Table';
  import { BasicForm, useForm } from '@/components/Form/index';
  import {
    getAdminTeacherList,
    deleteAdminTeacher,
    toggleAdminTeacherStatus,
    type AdminTeacherItem,
  } from '@/api/teacher';
  import { toBasicTableResult } from '@/api/contracts/admin';
  import { createTagColumn } from '@/views/business/shared/tableBuilders';
  import { TEACHER_STATUS_TAGS } from './options';

  const router = useRouter();
  const actionRef = ref();
  const scheduleModalShow = ref(false);
  const currentTeacherId = ref<number | null>(null);
  const currentTeacherName = ref('');

  const columns = [
    { title: 'ID', key: 'id', width: 60 },
    {
      title: '老师',
      key: 'name',
      width: 220,
      render(record: AdminTeacherItem) {
        const subtitle = [record.education, record.school].filter(Boolean).join(' · ');
        return h('div', { class: 'flex items-center gap-2' }, [
          h(NAvatar, {
            src: record.avatar || undefined,
            round: true,
            size: 36,
            style: 'flex-shrink: 0',
          }),
          h('div', { class: 'flex flex-col' }, [
            h('span', { class: 'text-sm font-medium' }, record.name),
            subtitle
              ? h('span', { class: 'text-xs', style: 'color: #999' }, subtitle)
              : null,
          ]),
        ]);
      },
    },
    { title: '专业方向', key: 'specialty', width: 120 },
    {
      title: '教龄',
      key: 'teaching_years',
      width: 80,
      render(record: AdminTeacherItem) {
        return record.teaching_years ? `${record.teaching_years}年` : '-';
      },
    },
    { title: '授课数', key: 'course_count', width: 90 },
    { title: '学员数', key: 'student_count', width: 90 },
    { title: '评分', key: 'rating', width: 70 },
    createTagColumn<AdminTeacherItem>('状态', 'status', TEACHER_STATUS_TAGS, 80),
  ];

  const actionColumn = {
    width: 260,
    title: '操作',
    key: 'action',
    fixed: 'right' as const,
    render(record: AdminTeacherItem) {
      return h(TableAction, {
        actions: [
          {
            label: '编辑',
            onClick: () => editTeacher(record),
          },
          {
            label: '可排课',
            onClick: () => {
              currentTeacherId.value = record.id;
              currentTeacherName.value = record.name;
              scheduleModalShow.value = true;
            },
          },
          {
            label: record.status === 'active' ? '停用' : '启用',
            onClick: () => handleToggleStatus(record),
          },
          {
            label: '删除',
            type: 'error',
            onClick: () => handleDelete(record),
          },
        ],
      });
    },
  };

  const [register, { getFieldsValue }] = useForm({
    gridProps: { cols: '1 s:1 m:2 l:3 xl:4 2xl:4' },
    labelWidth: 80,
    schemas: [
      {
        field: 'keyword',
        component: 'NInput',
        label: '关键词',
        componentProps: { placeholder: '搜索老师姓名' },
      },
      {
        field: 'status',
        component: 'NSelect',
        label: '状态',
        componentProps: {
          placeholder: '全部',
          options: [
            { label: '在职', value: 'active' },
            { label: '停用', value: 'inactive' },
          ],
        },
      },
    ],
  });

  const loadDataTable = async (res: any) => {
    const formValues = getFieldsValue();
    const queryParams: Record<string, any> = { ...formValues, ...res };
    queryParams.page_size = queryParams.pageSize;
    delete queryParams.pageSize;
    if (!queryParams.status) delete queryParams.status;
    if (!queryParams.keyword) delete queryParams.keyword;

    const result = await getAdminTeacherList(queryParams);
    return toBasicTableResult(result);
  };

  function handleSubmit() {
    reloadTable();
  }

  function handleReset() {
    reloadTable();
  }

  function reloadTable() {
    actionRef.value?.reload();
  }

  function addTeacher() {
    router.push({ name: 'training_teacher_edit' });
  }

  function editTeacher(record: AdminTeacherItem) {
    router.push({ name: 'training_teacher_edit', params: { id: record.id } });
  }

  async function handleToggleStatus(record: AdminTeacherItem) {
    const newStatus = record.status === 'active' ? 'inactive' : 'active';
    try {
      await toggleAdminTeacherStatus(record.id, newStatus);
      window.$message?.success(newStatus === 'active' ? '启用成功' : '停用成功');
      reloadTable();
    } catch (e) {
      window.$message?.error('操作失败');
    }
  }

  async function handleDelete(record: AdminTeacherItem) {
    window.$dialog?.warning({
      title: '确认删除',
      content: `确定要删除老师「${record.name}」吗？`,
      positiveText: '确定',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await deleteAdminTeacher(record.id);
          window.$message?.success('删除成功');
          reloadTable();
        } catch (e) {
          window.$message?.error('删除失败，该老师可能存在关联排课');
        }
      },
    });
  }
</script>
