<template>
  <n-modal
    :show="show"
    preset="card"
    :title="`排课管理 - ${courseName}`"
    style="width: 900px; max-width: 95vw"
    :mask-closable="false"
    @update:show="(val) => emit('update:show', val)"
  >
    <n-flex vertical :size="16">
      <!-- 已有排课列表 -->
      <n-spin :show="listLoading">
        <n-data-table
          v-if="scheduleList.length > 0"
          :key="tableKey"
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
          </n-grid>

          <!-- 时间段选择器 -->
          <n-form-item label="上课时间段" path="time_slots">
            <div v-if="weekDates.length > 0" class="schedule-grid">
              <!-- 日期表头 -->
              <div class="schedule-header">
                <div class="header-cell"></div>
                <div
                  v-for="date in weekDates"
                  :key="date.dateStr"
                  class="header-cell date-header"
                >
                  <div class="weekday">{{ date.weekdayName }}</div>
                  <div class="date">{{ date.dateDisplay }}</div>
                </div>
              </div>
              <!-- 时间段网格 -->
              <div
                v-for="timeSlot in timeSlots"
                :key="timeSlot"
                class="schedule-row"
              >
                <div class="time-label">{{ timeSlot }}</div>
                <div
                  v-for="date in weekDates"
                  :key="`${date.dateStr}-${timeSlot}`"
                  class="slot-cell"
                  :class="{ selected: isSelected(date.dateStr, timeSlot) }"
                  @click="toggleSlot(date.dateStr, timeSlot)"
                >
                  {{ isSelected(date.dateStr, timeSlot) ? '✓' : '' }}
                </div>
              </div>
            </div>
            <n-empty v-else description="请先选择开始日期" />
          </n-form-item>

          <!-- 已选时间段显示 -->
          <n-form-item v-if="selectedSlotList.length > 0" label="已选时间段">
            <n-flex wrap>
              <n-tag
                v-for="slot in selectedSlotList"
                :key="slot.key"
                type="info"
                size="small"
                closable
                @close="removeSlot(slot.key)"
              >
                {{ slot.label }}
              </n-tag>
            </n-flex>
          </n-form-item>
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
  import { computed, h, ref, watch } from 'vue';
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

  // 时间段选项（2小时一个时间段）
  const timeSlots = [
    '08:00-10:00',
    '10:00-12:00',
    '12:00-14:00',
    '14:00-16:00',
    '16:00-18:00',
    '18:00-20:00',
    '20:00-22:00',
  ];

  const weekdayNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];

  // 状态
  const formRef = ref<FormInst | null>(null);
  const listLoading = ref(false);
  const teacherLoading = ref(false);
  const saving = ref(false);
  const scheduleList = ref<ScheduleRecord[]>([]);
  const tableKey = ref(0);
  const teacherOptions = ref<Array<{ label: string; value: number }>>([]);
  const editingId = ref<number | null>(null);

  const formValues = ref({
    teacher_id: null as number | null,
    start_date: null as string | null,
    price: 0 as number | null,
    full_package_price: null as number | null,
  });

  // 已选时间段（格式：dateStr|timeSlot）
  const selectedSlots = ref<Set<string>>(new Set());

  const formRules: FormRules = {
    price: { required: true, type: 'number', message: '请输入每课时价格', trigger: 'blur' },
  };

  // 计算一周的日期（从开始日期起7天）
  const weekDates = computed(() => {
    if (!formValues.value.start_date) return [];
    const startDate = new Date(formValues.value.start_date);
    if (isNaN(startDate.getTime())) return [];

    const dates = [];
    for (let i = 0; i < 7; i++) {
      const date = new Date(startDate);
      date.setDate(startDate.getDate() + i);
      const dateStr = formatDate(date);
      dates.push({
        dateStr,
        weekdayName: weekdayNames[date.getDay()],
        dateDisplay: `${date.getMonth() + 1}/${date.getDate()}`,
      });
    }
    return dates;
  });

  // 已选时间段列表（用于显示）
  const selectedSlotList = computed(() => {
    const list = [];
    selectedSlots.value.forEach((key) => {
      const [dateStr, timeSlot] = key.split('|');
      const date = new Date(dateStr);
      const weekdayName = weekdayNames[date.getDay()];
      list.push({
        key,
        label: `${weekdayName} ${timeSlot}`,
      });
    });
    return list.sort((a, b) => a.key.localeCompare(b.key));
  });

  // 表格列定义
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
      width: 250,
      render(row: ScheduleRecord) {
        if (!row.time_slots) return '-';
        try {
          const slots = JSON.parse(row.time_slots);
          if (!Array.isArray(slots)) return row.time_slots;
          return slots
            .map((s: { date: string; time_slot: string }) => {
              const date = new Date(s.date);
              const weekdayName = weekdayNames[date.getDay()];
              return `${weekdayName} ${s.time_slot}`;
            })
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
        label: t.name,
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
      const data = await getCourseSchedules(props.courseId);
      // 深拷贝生成新引用并递增 key，强制表格重新渲染，避免数据更新后视图不变
      scheduleList.value = data.map((item) => ({ ...item }));
      tableKey.value += 1;
    } catch {
      window['$message']?.error('加载排课记录失败');
    } finally {
      listLoading.value = false;
    }
  }

  function formatDate(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  function isSelected(dateStr: string, timeSlot: string): boolean {
    return selectedSlots.value.has(`${dateStr}|${timeSlot}`);
  }

  function toggleSlot(dateStr: string, timeSlot: string) {
    const key = `${dateStr}|${timeSlot}`;
    if (selectedSlots.value.has(key)) {
      selectedSlots.value.delete(key);
    } else {
      selectedSlots.value.add(key);
    }
    // 触发响应式更新
    selectedSlots.value = new Set(selectedSlots.value);
  }

  function removeSlot(key: string) {
    selectedSlots.value.delete(key);
    selectedSlots.value = new Set(selectedSlots.value);
  }

  function handleEdit(row: ScheduleRecord) {
    editingId.value = row.id;
    formValues.value.teacher_id = row.teacher_id;
    formValues.value.start_date = row.start_date;
    formValues.value.price = row.price;
    formValues.value.full_package_price = row.full_package_price;

    // 解析 time_slots
    selectedSlots.value = new Set();
    if (row.time_slots) {
      try {
        const slots = JSON.parse(row.time_slots);
        if (Array.isArray(slots)) {
          slots.forEach((s: { date: string; time_slot: string }) => {
            selectedSlots.value.add(`${s.date}|${s.time_slot}`);
          });
        }
      } catch {
        // ignore
      }
    }
    selectedSlots.value = new Set(selectedSlots.value);
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
    selectedSlots.value = new Set();
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
      const slotsArray = Array.from(selectedSlots.value).map((key) => {
        const [date, time_slot] = key.split('|');
        return { date, time_slot };
      });
      const timeSlotsJson = slotsArray.length > 0 ? JSON.stringify(slotsArray) : null;

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

<style scoped>
  .schedule-grid {
    width: 100%;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    overflow: hidden;
  }

  .schedule-header {
    display: flex;
    background: #f5f5f5;
    border-bottom: 1px solid #e0e0e0;
  }

  .header-cell {
    flex: 1;
    padding: 8px 4px;
    text-align: center;
    border-right: 1px solid #e0e0e0;
  }

  .header-cell:last-child {
    border-right: none;
  }

  .header-cell.date-header {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .weekday {
    font-size: 12px;
    color: #666;
  }

  .date {
    font-size: 14px;
    font-weight: 600;
    color: #333;
  }

  .schedule-row {
    display: flex;
    border-bottom: 1px solid #e0e0e0;
  }

  .schedule-row:last-child {
    border-bottom: none;
  }

  .time-label {
    flex: 1;
    padding: 8px 4px;
    text-align: center;
    font-size: 12px;
    color: #666;
    border-right: 1px solid #e0e0e0;
    background: #fafafa;
  }

  .slot-cell {
    flex: 1;
    padding: 8px 4px;
    text-align: center;
    cursor: pointer;
    border-right: 1px solid #e0e0e0;
    transition: all 0.2s;
    font-size: 14px;
  }

  .slot-cell:last-child {
    border-right: none;
  }

  .slot-cell:hover {
    background: #f0f0f0;
  }

  .slot-cell.selected {
    background: #e6f7ff;
    color: #1890ff;
    font-weight: 600;
  }
</style>
