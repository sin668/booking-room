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
        :row-key="(row: CourseItem) => row.id"
        :actionColumn="actionColumn"
        :scroll-x="1200"
        :striped="true"
      >
        <template #tableTitle>
          <n-button type="primary" @click="addCourse">
            <template #icon>
              <n-icon><PlusOutlined /></n-icon>
            </template>
            新增课程
          </n-button>
        </template>
      </BasicTable>
    </n-card>
  </n-flex>
</template>

<script lang="ts" setup>
  import { h, ref } from 'vue';
  import { PlusOutlined } from '@vicons/antd';
  import { BasicTable, TableAction } from '@/components/Table';
  import { BasicForm, useForm } from '@/components/Form/index';
  import { getCourseList, deleteCourse, toggleCourseStatus, type CourseItem } from '@/api/course';
  import { toBasicTableResult } from '@/api/contracts/admin';
  import { createTextColumn, createTagColumn, createDateTimeColumn } from '@/views/business/shared/tableBuilders';
  import { COURSE_STATUS_TAGS } from './options';

  const actionRef = ref();

  const columns = [
    { title: 'ID', key: 'id', width: 60 },
    createTextColumn<CourseItem>('课程名称', 'name', 180),
    createTextColumn<CourseItem>('分类', 'category', 100),
    { title: '学员数', key: 'enrollment_count', width: 90 },
    { title: '评分', key: 'rating', width: 70 },
    createTagColumn<CourseItem>('状态', 'status', COURSE_STATUS_TAGS, 80),
    createDateTimeColumn<CourseItem>('创建时间', 'created_at'),
  ];

  const actionColumn = {
    width: 150,
    title: '操作',
    key: 'action',
    fixed: 'right' as const,
    render(record: CourseItem) {
      return h(TableAction, {
        actions: [
          {
            label: '编辑',
            onClick: () => editCourse(record),
          },
          {
            label: record.status === 'active' ? '下架' : '上架',
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
        componentProps: { placeholder: '搜索课程名称' },
      },
      {
        field: 'category',
        component: 'NSelect',
        label: '分类',
        componentProps: {
          placeholder: '全部',
          options: [
            { label: '考研辅导', value: 'postgraduate' },
            { label: '公考备考', value: 'civil_service' },
            { label: '语言培训', value: 'language' },
            { label: '技能提升', value: 'skills' },
            { label: '职业资格', value: 'professional' },
            { label: '小学辅导', value: 'primaryschool' },
            { label: '中学辅导', value: 'middleschool' },
          ],
        },
      },
      {
        field: 'status',
        component: 'NSelect',
        label: '状态',
        componentProps: {
          placeholder: '全部',
          options: [
            { label: '已上架', value: 'active' },
            { label: '已下架', value: 'inactive' },
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
    if (!queryParams.category) delete queryParams.category;
    if (!queryParams.status) delete queryParams.status;
    if (!queryParams.keyword) delete queryParams.keyword;

    const result = await getCourseList(queryParams);
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

  function addCourse() {
    // TODO: 打开新增课程弹窗或跳转到编辑页
    console.log('Add course');
  }

  function editCourse(record: CourseItem) {
    // TODO: 打开编辑课程弹窗或跳转到编辑页
    console.log('Edit course', record.id);
  }

  async function handleToggleStatus(record: CourseItem) {
    const newStatus = record.status === 'active' ? 'inactive' : 'active';
    try {
      await toggleCourseStatus(record.id, newStatus);
      window.$message?.success(newStatus === 'active' ? '上架成功' : '下架成功');
      reloadTable();
    } catch (e) {
      window.$message?.error('操作失败');
    }
  }

  async function handleDelete(record: CourseItem) {
    window.$dialog?.warning({
      title: '确认删除',
      content: `确定要删除课程「${record.name}」吗？`,
      positiveText: '确定',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await deleteCourse(record.id);
          window.$message?.success('删除成功');
          reloadTable();
        } catch (e) {
          window.$message?.error('删除失败');
        }
      },
    });
  }
</script>
