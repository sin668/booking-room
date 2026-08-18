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
    <ScheduleModal
      v-model:show="showScheduleModal"
      :course-id="scheduleCourseId"
      :course-name="scheduleCourseName"
      @success="reloadTable"
    />
  </n-flex>
</template>

<script lang="ts" setup>
  import { h, ref } from 'vue';
  import { useRouter } from 'vue-router';
  import { PlusOutlined } from '@vicons/antd';
  import { BasicTable, TableAction } from '@/components/Table';
  import { BasicForm, useForm } from '@/components/Form/index';
  import { getCourseList, deleteCourse, toggleCourseStatus, type CourseItem } from '@/api/course';
  import { toBasicTableResult } from '@/api/contracts/admin';
  import { createTextColumn, createTagColumn, createDateTimeColumn } from '@/views/business/shared/tableBuilders';
  import { COURSE_STATUS_TAGS, COURSE_CATEGORY_OPTIONS, COURSE_CATEGORY_LABELS } from './options';
  import ScheduleModal from './ScheduleModal.vue';

  const router = useRouter();
  const actionRef = ref();

  const columns = [
    { title: 'ID', key: 'id', width: 60 },
    createTextColumn<CourseItem>('课程名称', 'name', 180),
    {
      title: '分类',
      key: 'category',
      width: 100,
      render(record: CourseItem) {
        return COURSE_CATEGORY_LABELS[record.category] || record.category;
      },
    },
    { title: '学员数', key: 'enrollment_count', width: 90 },
    { title: '评分', key: 'rating', width: 70 },
    createTagColumn<CourseItem>('状态', 'status', COURSE_STATUS_TAGS, 80),
    createDateTimeColumn<CourseItem>('创建时间', 'created_at'),
  ];

  const actionColumn = {
    width: 200,
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
            label: '排课',
            onClick: () => handleSchedule(record),
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
          options: COURSE_CATEGORY_OPTIONS,
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
    router.push({ name: 'training_course_edit' });
  }

  function editCourse(record: CourseItem) {
    router.push({ name: 'training_course_edit', params: { id: record.id } });
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

  // 排课弹窗
  const showScheduleModal = ref(false);
  const scheduleCourseId = ref<number | null>(null);
  const scheduleCourseName = ref('');

  function handleSchedule(record: CourseItem) {
    scheduleCourseId.value = record.id;
    scheduleCourseName.value = record.name;
    showScheduleModal.value = true;
  }
</script>
