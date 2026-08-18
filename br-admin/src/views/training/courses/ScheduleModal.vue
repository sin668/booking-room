<template>
  <n-modal
    :show="show"
    preset="card"
    :title="`排课管理 - ${courseName}`"
    style="width: 800px; max-width: 95vw"
    :mask-closable="false"
    @update:show="(val) => emit('update:show', val)"
  >
    <n-flex vertical :size="16">
      <!-- 已有排课列表 -->
      <n-spin :show="listLoading">
        <n-data-table
          v-if="scheduleList.length > 0"
          :columns="tableColumns"
          :data="scheduleList"
          :bordered="false"
          size="small"
          :row-key="(row: ScheduleRecord) => row.id"
        />
        <n-empty v-else description="暂无排课记录" />
      </n-spin>

      <n-divider style="margin: 8px 0" />

      <!-- 新增/编辑排课表单 -->
      <n-card :bordered="false" class="bg-gray-50">
        <template #header>
          <n-text strong>{{ editingId ? '编辑排课' : '新增排课' }}</n-text>
        </template>
        <n-form
          ref="formRef"
          :model="formValues"
          :rules="formRules"
          label-placement="left"
          label-width="100"
        >
          <n-grid :cols="2" :x-gap="16">
            <n-gi>
              <n-form-item label="授课老师" path="teacher_id">
                <n-select
                  v-model:value="formValues.teacher_id"
                  placeholder="请选择老师"
                  :options="teacherOptions"
                  :loading="teacherLoading"
                  filterable
                  clearable
                />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="开始日期" path="start_date">
                <n-date-picker
                  v-model:formatted-value="formValues.start_date"
                  type="date"
                  value-format="yyyy-MM-dd"
                  style="width: 100%"
                  clearable
                />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="每课时价格" path="price">
                <n-input-number
                  v-model:value="formValues.price"
                  placeholder="请输入"
                  :min="0"
                  :precision="2"
                  style="width: 100%"
                />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="全套优惠价" path="full_package_price">
                <n-input-number
                  v-model:value="formValues.full_package_price"
                  placeholder="请输入"
                  :min="0"
                  :precision="2"
                  style="width: 100%"
                />
              </n-form-item>
            </n-gi>
            <n-gi :span="2">
              <n-form-item label="上课时间段" path="time_slots">
                <n-flex vertical :size="8" style="width: 100%">
                  <n-checkbox-group v-model:value="selectedSlots">
                    <n-flex wrap :size="8">
                      <n-checkbox
                        v-for="slot in availableSlots"
                        :key="slot.value"
                        :value="slot.value"
                        :label="slot.label"
                      />
                    </n-flex>
                  </n-checkbox-group>
                </n-flex>
              </n-form-item>
            </n-gi>
          </n-grid>
        </n-form>
        <template #footer>
          <n-flex justify="end" :size="12">
            <n-button v-if="editingId" @click="cancelEdit">取消编辑</n-button>
            <n-button type="primary" :loading="saving" @click="handleSave">
              {{ editingId ? '更新' : '保存' }}
            </n-button>
          </n-flex>
        </template>
      </n-card>
    </n-flex>
  </n-modal>
</template>

<script lang="ts" setup>
  import { computed, h, onMounted, ref, watch } from 'vue';
  import type { FormInst, FormRules } from 'naive-ui';
  import { NButton, NTag } from 'naive-ui';
  import {
    getTeacherList,
    getCourseSchedules,
    createCourseSchedule,
    updateCourseSchedule,
    deleteCourseSchedule,
    type TeacherItem,
    type ScheduleRecord,
  } from '@/api/course';

  const props = defineProps<{
    show: boolean;
    courseId: number | null;
    courseName: string;
  }>();

  const emit = defineEmits<{
    (e: 'update:show', val: boolean): void;
    (e: 'success'): void;
  }>();

  // 预设时间段选项
  const availableSlots = [
    { label: '周一 09:00-11:00', value: JSON.stringify({ weekday: 1, start: '09:00', end: '11:00' }) },
    { label: '周一 14:00-16:00', value: JSON.stringify({ weekday: 1, start: '14:00', end: '16:00' }) },
    { label: '周一 19:00-21:00', value: JSON.stringify({ weekday: 1, start: '19:00', end: '21:00' }) },
    { label: '周二 09:00-11:00', value: JSON.stringify({ weekday: 2, start: '09:00', end: '11:00' }) },
    { label: '周二 14:00-16:00', value: JSON.stringify({ weekday: 2, start: '14:00', end: '16:00' }) },
    { label: '周二 19:00-21:00', value: JSON.stringify({ weekday: 2, start: '19:00', end: '21:00' }) },
    { label: '周三 09:00-11:00', value: JSON.stringify({ weekday: 3, start: '09:00', end: '11:00' }) },
    { label: '周三 14:00-16:00', value: JSON.stringify({ weekday: 3, start: '14:00', end: '16:00' }) },
    { label: '周三 19:00-21:00', value: JSON.stringify({ weekday: 3, start: '19:00', end: '21:00' }) },
    { label: '周四 09:00-11:00', value: JSON.stringify({ weekday: 4, start: '09:00', end: '11:00' }) },
    { label: '周四 14:00-16:00', value: JSON.stringify({ weekday: 4, start: '14:00', end: '16:00' }) },
    { label: '周四 19:00-21:00', value: JSON.stringify({ weekday: 4, start: '19:00', end: '21:00' }) },
    { label: '周五 09:00-11:00', value: JSON.stringify({ weekday: 5, start: '09:00', end: '11:00' }) },
    { label: '周五 14:00-16:00', value: JSON.stringify({ weekday: 5, start: '14:00', end: '16:00' }) },
    { label: '周五 19:00-21:00', value: JSON.stringify({ weekday: 5, start: '19:00', end: '21:00' }) },
    { label: '周六 09:00-11:00', value: JSON.stringify({ weekday: 6, start: '09:00', end: '11:00' }) },
    { label: '周六 14:00-16:00', value: JSON.stringify({ weekday: 6, start: '14:00', end: '16:00' }) },
    { label: '周日 09:00-11:00', value: JSON.stringify({ weekday: 7, start: '09:00', end: '11:00' }) },
    { label: '周日 14:00-16:00', value: JSON.stringify({ weekday: 7, start: '14:00', end: '16:00' }) },
  ];

  // 状态
  const formRef = ref<FormInst | null>(null);
  const listLoading = ref(false);
  const teacherLoading = ref(false);
  const saving = ref(false);
  const scheduleList = ref<ScheduleRecord[]>([]);
  const teacherOptions = ref<Array<{ label: string; value: number }>>([]);
  const selectedSlots = ref<string[]>([]);
  const editingId = ref<number | null>(null);

  const formValues = ref({
    teacher_id: null as number | null,
    start_date: null as string | null,
    price: 0 as number | null,
    full_package_price: null as number | null,
  });

  const formRules: FormRules = {
    price: { required: true, type: 'number', message: '请输入每课时价格', trigger: 'blur' },
  };

  // 表格列定义
  const weekdayNames: Record<number, string> = {
    1: '周一', 2: '周二', 3: '周三', 4: '周四', 5: '周五', 6: '周六', 7: '周日',
  };

  const tableColumns = [
    {
      title: '授课老师',
      key: 'teacher_id',
      width: 100,
      render(row: ScheduleRecord) {
        const teacher = teacherOptions.value.find((t) => t.value === row.teacher_id);
        return teacher ? teacher.label : '-';
      },
    },
    { title: '开始日期', key: 'start_date', width: 110 },
    {
      title: '每课时价格',
      key: 'price',
      width: 100,
      render(row: ScheduleRecord) {
        return h(NTag, { type: 'info', size: 'small', bordered: false }, () => `¥${row.price}`);
      },
    },
    {
      title: '全套优惠价',
      key: 'full_package_price',
      width: 110,
      render(row: ScheduleRecord) {
        return row.full_package_price
          ? h(NTag, { type: 'success', size: 'small', bordered: false }, () => `¥${row.full_package_price}`)
          : '-';
      },
    },
    {
      title: '上课时间',
      key: 'time_slots',
      width: 200,
      render(row: ScheduleRecord) {
        if (!row.time_slots) return '-';
        try {
          const slots = JSON.parse(row.time_slots);
          if (!Array.isArray(slots)) return row.time_slots;
          return slots
            .map((s: { weekday: number; start: string; end: string }) =>
              `${weekdayNames[s.weekday] || s.weekday} ${s.start}-${s.end}`
            )
            .join('、');
        } catch {
          return row.time_slots;
        }
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      fixed: 'right' as const,
      render(row: ScheduleRecord) {
        return h('div', { style: 'display: flex; gap: 8px;' }, [
          h(
            NButton,
            { text: true, type: 'primary', size: 'small', onClick: () => handleEdit(row) },
            () => '编辑'
          ),
          h(
            NButton,
            {
              text: true,
              type: 'error',
              size: 'small',
              onClick: () => handleDeleteSchedule(row),
            },
            () => '删除'
          ),
        ]);
      },
    },
  ];

  // 弹窗打开时加载数据
  watch(
    () => props.show,
    (val) => {
      if (val && props.courseId) {
        loadData();
      } else {
        resetForm();
      }
    }
  );

  async function loadData() {
    await Promise.all([loadTeachers(), loadSchedules()]);
  }

  async function loadTeachers() {
    teacherLoading.value = true;
    try {
      const result = await getTeacherList();
      teacherOptions.value = result.items.map((t: TeacherItem) => ({
        label: t.title ? `${t.name}（${t.title}）` : t.name,
        value: t.id,
      }));
    } catch {
      window['$message']?.error('加载教师列表失败');
    } finally {
      teacherLoading.value = false;
    }
  }

  async function loadSchedules() {
    if (!props.courseId) return;
    listLoading.value = true;
    try {
      scheduleList.value = await getCourseSchedules(props.courseId);
    } catch {
      window['$message']?.error('加载排课记录失败');
    } finally {
      listLoading.value = false;
    }
  }

  function handleEdit(row: ScheduleRecord) {
    editingId.value = row.id;
    formValues.value.teacher_id = row.teacher_id;
    formValues.value.start_date = row.start_date;
    formValues.value.price = row.price;
    formValues.value.full_package_price = row.full_package_price;

    // 解析 time_slots
    if (row.time_slots) {
      try {
        const slots = JSON.parse(row.time_slots);
        selectedSlots.value = slots.map((s: { weekday: number; start: string; end: string }) =>
          JSON.stringify({ weekday: s.weekday, start: s.start, end: s.end })
        );
      } catch {
        selectedSlots.value = [];
      }
    } else {
      selectedSlots.value = [];
    }
  }

  function cancelEdit() {
    editingId.value = null;
    resetForm();
  }

  function resetForm() {
    editingId.value = null;
    formValues.value = {
      teacher_id: null,
      start_date: null,
      price: 0,
      full_package_price: null,
    };
    selectedSlots.value = [];
  }

  async function handleSave() {
    if (!props.courseId) return;
    try {
      await formRef.value?.validate();
    } catch {
      window['$message']?.warning('请检查必填项');
      return;
    }

    saving.value = true;
    try {
      // 序列化时间段
      const timeSlotsJson = selectedSlots.value.length > 0
        ? JSON.stringify(selectedSlots.value.map((v) => JSON.parse(v)))
        : null;

      const payload = {
        teacher_id: formValues.value.teacher_id,
        start_date: formValues.value.start_date,
        time_slots: timeSlotsJson,
        price: formValues.value.price || 0,
        custom_price: 0,
        full_package_price: formValues.value.full_package_price,
      };

      if (editingId.value) {
        await updateCourseSchedule(props.courseId, editingId.value, payload);
        window['$message']?.success('排课更新成功');
      } else {
        await createCourseSchedule(props.courseId, payload);
        window['$message']?.success('排课添加成功');
      }

      resetForm();
      await loadSchedules();
      emit('success');
    } catch {
      window['$message']?.error('保存失败');
    } finally {
      saving.value = false;
    }
  }

  function handleDeleteSchedule(row: ScheduleRecord) {
    if (!props.courseId) return;
    window['$dialog']?.warning({
      title: '确认删除',
      content: '确定要删除这条排课记录吗？',
      positiveText: '确定',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await deleteCourseSchedule(props.courseId!, row.id);
          window['$message']?.success('删除成功');
          await loadSchedules();
          emit('success');
        } catch {
          window['$message']?.error('删除失败');
        }
      },
    });
  }
</script>
