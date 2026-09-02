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
                  :disabled="isCourseStarted"
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
                  :disabled="isCourseStarted"
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
              <n-form-item label="定制每课时价格" path="custom_price">
                <n-input-number
                  v-model:value="formValues.custom_price"
                  placeholder="选填"
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
            <n-gi>
              <n-form-item label="定制全套优惠价" path="full_custom_price">
                <n-input-number
                  v-model:value="formValues.full_custom_price"
                  placeholder="选填"
                  :min="0"
                  :precision="2"
                  style="width: 100%"
                />
              </n-form-item>
            </n-gi>
          </n-grid>

          <!-- 时间段选择器 -->
          <n-form-item label="上课时间段" path="time_slots">
            <div class="schedule-wrapper">
              <div v-if="weekDates.length > 0" :class="['schedule-grid', { 'schedule-locked': isCourseStarted }]">
                <!-- 日期表头 -->
                <div class="schedule-header">
                  <div class="header-cell time-header-cell">时间段</div>
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
                  <div class="time-label">
                    {{ timeSlot }}
                    <n-button
                      v-if="!isDefaultTimeSlot(timeSlot)"
                      text
                      type="error"
                      size="tiny"
                      class="delete-slot-btn"
                      @click.stop="removeCustomTimeSlot(timeSlot)"
                    >
                      <template #icon><n-icon size="12"><CloseOutline /></n-icon></template>
                    </n-button>
                  </div>
                  <div
                    v-for="date in weekDates"
                    :key="`${date.weekday}-${timeSlot}`"
                    class="slot-cell"
                    :class="{ selected: isSelected(date.weekday, timeSlot) }"
                    @click="toggleSlot(date.weekday, timeSlot)"
                  >
                    {{ isSelected(date.weekday, timeSlot) ? '✓' : '' }}
                  </div>
                </div>
              </div>
              <!-- 新增时间段（表格下方） -->
              <div v-if="weekDates.length > 0" class="add-slot-outside">
                <n-button
                  v-if="!showAddSlotInput"
                  text
                  type="primary"
                  size="small"
                  @click="showAddSlotInput = true"
                >
                  <template #icon><n-icon size="14"><AddOutline /></n-icon></template>
                  新增时间段
                </n-button>
                <div v-if="showAddSlotInput" class="add-slot-form">
                  <n-time-picker
                    v-model:formatted-value="newSlotStart"
                    format="HH:mm"
                    value-format="HH:mm"
                    placeholder="开始"
                    size="small"
                    style="width: 90px"
                    :show-icon="false"
                  />
                  <span class="add-slot-separator">-</span>
                  <n-time-picker
                    v-model:formatted-value="newSlotEnd"
                    format="HH:mm"
                    value-format="HH:mm"
                    placeholder="结束"
                    size="small"
                    style="width: 90px"
                    :show-icon="false"
                  />
                  <n-button
                    type="primary"
                    size="tiny"
                    :disabled="!newSlotStart || !newSlotEnd"
                    @click="confirmAddTimeSlot"
                  >
                    确定
                  </n-button>
                  <n-button
                    size="tiny"
                    @click="cancelAddTimeSlot"
                  >
                    取消
                  </n-button>
                </div>
              </div>
              <n-empty v-if="weekDates.length === 0" description="请先选择开始日期" />
            </div>
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

          <!-- 课程目录 -->
          <n-form-item label="课程目录">
            <div style="width: 100%">
              <n-list v-if="computedLessonSchedule.length > 0" bordered>
                <n-list-item 
                  v-for="(item, index) in computedLessonSchedule" 
                  :key="item.lessonId"
                  :class="{ 'lesson-locked': item.isLocked }"
                >
                  <div class="lesson-item-row">
                    <n-text class="lesson-title">{{ formatLessonTitle(item.title, index) }}</n-text>
                    <span class="lesson-right-group">
                      <n-text depth="3" class="lesson-time-text">于 {{ item.dateDisplay }} {{ item.timeSlotStart }} 上课</n-text>
                      <n-button
                        v-if="editingSchedule"
                        text
                        :type="item.canPostpone ? 'warning' : 'default'"
                        :disabled="!item.canPostpone"
                        class="postpone-btn"
                        @click="handlePostpone(item)"
                      >
                        <template #icon><n-icon><TimeOutline /></n-icon></template>
                        延期
                      </n-button>
                    </span>
                  </div>
                </n-list-item>
              </n-list>
              <n-empty v-else description="请先选择开始日期和上课时间段" />
            </div>
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
  import { computed, h, nextTick, ref, watch } from 'vue';
  import type { FormInst, FormRules } from 'naive-ui';
  import { NButton, NTag } from 'naive-ui';
  import { TimeOutline, AddOutline, CloseOutline } from '@vicons/ionicons5';
  import {
    getTeacherList,
    getCourseSchedules,
    createCourseSchedule,
    updateCourseSchedule,
    deleteCourseSchedule,
    getCourseLessons,
    postponeCourseLessonSchedule,
    type TeacherItem,
    type ScheduleRecord,
    type LessonItem,
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

  // 默认时间段（2小时一个时间段）
  const defaultTimeSlots = [
    '08:00-10:00',
    '10:00-12:00',
    '12:00-14:00',
    '14:00-16:00',
    '16:00-18:00',
    '18:00-20:00',
    '20:00-22:00',
  ];

  // 时间段列表（响应式，支持自定义新增）
  const timeSlots = ref<string[]>([...defaultTimeSlots]);

  // 新增时间段相关状态
  const showAddSlotInput = ref(false);
  const newSlotStart = ref<string | null>(null);
  const newSlotEnd = ref<string | null>(null);

  function isDefaultTimeSlot(slot: string): boolean {
    return defaultTimeSlots.includes(slot);
  }

  function formatTimeStr(val: string): string {
    // 确保格式为 HH:mm
    return val.length === 5 ? val : val.substring(0, 5);
  }

  function timeToMinutes(t: string): number {
    const [hh, mm] = t.split(':').map(Number);
    return hh * 60 + mm;
  }

  function confirmAddTimeSlot() {
    if (!newSlotStart.value || !newSlotEnd.value) return;
    const start = formatTimeStr(newSlotStart.value);
    const end = formatTimeStr(newSlotEnd.value);
    const label = `${start}-${end}`;

    // 校验：开始时间必须早于结束时间
    if (timeToMinutes(start) >= timeToMinutes(end)) {
      window['$message']?.warning('开始时间必须早于结束时间');
      return;
    }

    // 校验：不重复添加
    if (timeSlots.value.includes(label)) {
      window['$message']?.warning('该时间段已存在');
      return;
    }

    const newStart = timeToMinutes(start);
    // 按时间顺序插入
    const idx = timeSlots.value.findIndex((s) => timeToMinutes(s.split('-')[0]) > newStart);
    if (idx === -1) {
      timeSlots.value.push(label);
    } else {
      timeSlots.value.splice(idx, 0, label);
    }

    cancelAddTimeSlot();
    window['$message']?.success(`已添加时间段 ${label}`);
  }

  function cancelAddTimeSlot() {
    showAddSlotInput.value = false;
    newSlotStart.value = null;
    newSlotEnd.value = null;
  }

  function removeCustomTimeSlot(slot: string) {
    if (isDefaultTimeSlot(slot)) return;
    timeSlots.value = timeSlots.value.filter((s) => s !== slot);
    // 同时清除该时间段已选中的 slots
    const keysToRemove: string[] = [];
    selectedSlots.value.forEach((key) => {
      if (key.endsWith(`|${slot}`)) keysToRemove.push(key);
    });
    keysToRemove.forEach((k) => selectedSlots.value.delete(k));
    if (keysToRemove.length > 0) {
      selectedSlots.value = new Set(selectedSlots.value);
    }
    window['$message']?.success(`已删除时间段 ${slot}`);
  }

  const weekdayNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
  // 周几索引（1-7，周日为7），用于 time_slots 存储
  const weekdayIndexMap: Record<number, number> = { 0: 7, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6 };

  // 状态
  const formRef = ref<FormInst | null>(null);
  const listLoading = ref(false);
  const teacherLoading = ref(false);
  const saving = ref(false);
  const deleting = ref(false);
  const scheduleList = ref<ScheduleRecord[]>([]);
  const tableKey = ref(0);
  const teacherOptions = ref<Array<{ label: string; value: number }>>([]);
  const editingId = ref<number | null>(null);
  const lessons = ref<LessonItem[]>([]);
  const editingSchedule = ref<ScheduleRecord | null>(null);

  const formValues = ref({
    teacher_id: null as number | null,
    start_date: null as string | null,
    price: 0 as number | null,
    custom_price: null as number | null,
    full_package_price: null as number | null,
    full_custom_price: null as number | null,
  });

  // 已选时间段（格式：dateStr|timeSlot）
  const selectedSlots = ref<Set<string>>(new Set());

  const formRules: FormRules = {
    teacher_id: {
      required: true,
      type: 'number',
      message: '请选择授课老师',
      trigger: ['blur', 'change'],
    },
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
        weekday: weekdayIndexMap[date.getDay()],
        weekdayName: weekdayNames[date.getDay()],
        dateDisplay: `${date.getMonth() + 1}/${date.getDate()}`,
      });
    }
    return dates;
  });

  // 已选时间段列表（用于显示，按周几+时间排序）
  const selectedSlotList = computed(() => {
    const list = Array.from(selectedSlots.value).map((key) => {
      const [weekdayStr, timeSlot] = key.split('|');
      const weekday = Number(weekdayStr);
      return {
        key,
        weekday,
        label: `${weekdayNames[weekday % 7]} ${timeSlot}`,
      };
    });
    return list.sort((a, b) => a.key.localeCompare(b.key));
  });

  // 当前课时列表：优先使用排课记录中的 course_lessons，否则用 API 加载的 lessons
  const currentLessons = computed<LessonItem[]>(() => {
    if (editingSchedule.value?.course_lessons?.length) {
      return editingSchedule.value.course_lessons.sort((a, b) => a.sort_order - b.sort_order);
    }
    return lessons.value;
  });

  // 课程是否已经开始（用于禁用授课老师和开始日期字段）
  const isCourseStarted = computed(() => {
    if (!formValues.value.start_date) return false;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const startDate = new Date(formValues.value.start_date);
    startDate.setHours(0, 0, 0, 0);
    return today > startDate;
  });

  // 课程目录计算
  const computedLessonSchedule = computed(() => {
    const lessonList = currentLessons.value;
    if (!formValues.value.start_date || selectedSlots.value.size === 0 || !lessonList.length) return [];

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // 如果正在编辑且有 course_lessons 带 scheduled_date，使用后端数据
    if (editingSchedule.value?.course_lessons?.length) {
      const scheduledLessons = editingSchedule.value.course_lessons.filter(
        (l) => l.scheduled_date && l.scheduled_time_slot
      );
      if (scheduledLessons.length > 0) {
        return scheduledLessons
          .sort((a, b) => a.sort_order - b.sort_order)
          .map((l, idx) => {
            const lessonDate = new Date(l.scheduled_date as string);
            lessonDate.setHours(0, 0, 0, 0);
            const canPostpone = lessonDate > today; // 严格大于，当天不可延期
            return {
              lessonId: l.id,
              title: resolveLessonTitle(l.id, idx),
              dateDisplay: (l.scheduled_date as string).replace(/-/g, '/'),
              timeSlotStart: (l.scheduled_time_slot as string).split('-')[0],
              timeSlot: l.scheduled_time_slot as string,
              canPostpone,
              isLocked: !canPostpone, // 当天及之前的课时锁定
            };
          });
      }
    }

    // 新建模式或无后端数据：根据 start_date + selectedSlots 计算
    // 生成所有可用的 (date, timeSlot) 组合，按时间排序
    const availableSlots: { dateStr: string; weekday: number; timeSlot: string }[] = [];
    for (const wd of weekDates.value) {
      for (const slot of selectedSlotList.value) {
        if (slot.weekday === wd.weekday) {
          availableSlots.push({
            dateStr: wd.dateStr,
            weekday: wd.weekday,
            timeSlot: slot.label.split(' ').pop() || '',
          });
        }
      }
    }
    availableSlots.sort((a, b) => {
      const dateCompare = a.dateStr.localeCompare(b.dateStr);
      if (dateCompare !== 0) return dateCompare;
      return a.timeSlot.localeCompare(b.timeSlot);
    });

    if (availableSlots.length === 0) return [];

    // 遍历所有课时，可用槽位循环使用（取模方式）
    return lessonList.map((lesson, index) => {
      const slot = availableSlots[index % availableSlots.length];
      // 计算实际日期：基础日期 + (第几轮 × 7天)
      const weekOffset = Math.floor(index / availableSlots.length) * 7;
      const lessonDate = new Date(slot.dateStr);
      lessonDate.setDate(lessonDate.getDate() + weekOffset);
      lessonDate.setHours(0, 0, 0, 0);
      const canPostpone = lessonDate > today; // 严格大于，当天不可延期
      return {
        lessonId: lesson.id,
        title: resolveLessonTitle(lesson.id, index),
        dateDisplay: formatDate(lessonDate).replace(/-/g, '/'),
        timeSlotStart: slot.timeSlot.split('-')[0],
        timeSlot: slot.timeSlot,
        canPostpone,
        isLocked: !canPostpone, // 当天及之前的课时锁定
      };
    });
  });



  /**
   * 解析课时标题：优先从已加载的 lessons 中匹配真实标题，
   * 其次使用 l.title（如有），最后 fallback 为 "第N讲"（index+1 保证从1开始）
   */
  function resolveLessonTitle(lessonId: number, index: number): string {
    // 从已加载的 course lessons 中查找真实标题
    const lesson = lessons.value.find((l) => l.id === lessonId);
    const rawTitle = lesson?.title;
    if (rawTitle) {
      return formatLessonTitle(rawTitle, index);
    }
    return `第${index + 1}讲`;
  }

  /** 格式化课程目录标题，避免重复的"第N讲"前缀 */
  function formatLessonTitle(title: string, index: number): string {
    // 如果标题已经包含"第N讲"格式前缀（带或不带冒号），直接使用
    if (/^第\s*\d+\s*讲/.test(title)) {
      return title;
    }
    return `第${index + 1}讲：${title}`;
  }

  /** 课程状态：优先使用后端计算的 schedule_status（当前日期 > 结课日期 → completed），前端兼容回退计算 */
  function isScheduleCompleted(row: ScheduleRecord): boolean {
    if (row.schedule_status) return row.schedule_status === 'completed';
    if (!row.end_date) return false;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const endDate = new Date(row.end_date);
    endDate.setHours(0, 0, 0, 0);
    return today > endDate;
  }

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
    {
      title: '类型',
      key: 'schedule_type',
      width: 100,
      render(row: ScheduleRecord) {
        const isCustom = row.schedule_type === 'custom';
        return h(
          NTag,
          { type: isCustom ? 'warning' : 'info', size: 'small', bordered: false },
          () => (isCustom ? '定制课时' : '固定班课')
        );
      },
    },
    { title: '开始日期', key: 'start_date', width: 110 },
    { title: '结课日期', key: 'end_date', width: 110, render: (row: ScheduleRecord) => row.end_date || '-' },
    {
      title: '课程状态',
      key: 'schedule_status',
      width: 100,
      render(row: ScheduleRecord) {
        const completed = isScheduleCompleted(row);
        return h(
          NTag,
          { type: completed ? 'success' : 'warning', size: 'small', bordered: false },
          () => (completed ? '已完成' : '进行中')
        );
      },
    },
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
      title: '定制每课时价格',
      key: 'custom_price',
      width: 120,
      render(row: ScheduleRecord) {
        return row.custom_price
          ? h(NTag, { type: 'warning', size: 'small', bordered: false }, () => `¥${row.custom_price}`)
          : '-';
      },
    },
    {
      title: '定制全套优惠价',
      key: 'full_custom_price',
      width: 130,
      render(row: ScheduleRecord) {
        return row.full_custom_price
          ? h(NTag, { type: 'warning', size: 'small', bordered: false }, () => `¥${row.full_custom_price}`)
          : '-';
      },
    },
    {
      // 已支付金额：定制订单确认时由订单实付总额记入，与定制每课时价格区分
      title: '已支付金额',
      key: 'paid_amount',
      width: 120,
      render(row: ScheduleRecord) {
        return row.paid_amount
          ? h(NTag, { type: 'success', size: 'small', bordered: false }, () => `¥${row.paid_amount}`)
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
            .map((s: { weekday: number; time_slot: string }) => {
              const [start, end] = s.time_slot.split('-');
              return `${weekdayNames[s.weekday % 7]} ${start}-${end}`;
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
        // 已完成的排课（当前日期 > 结课日期）不显示编辑/删除按钮
        if (isScheduleCompleted(row)) {
          return null;
        }
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
    await Promise.all([loadTeachers(), loadSchedules(), loadLessons()]);
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

  async function loadLessons() {
    if (!props.courseId) return;
    try {
      const data = await getCourseLessons(props.courseId);
      lessons.value = data.sort((a, b) => a.sort_order - b.sort_order);
    } catch {
      // 静默失败，课时列表非关键数据
    }
  }

  async function loadSchedules() {
    if (!props.courseId) return;
    listLoading.value = true;
    try {
      const data = await getCourseSchedules(props.courseId);
      // 深拷贝 + 字段映射：后端返回 lesson_schedules(lesson_date/lesson_time_slot)，
      // 前端 computed 依赖 course_lessons(scheduled_date/scheduled_time_slot)
      scheduleList.value = data.map((item: any) => ({
        ...item,
        course_lessons: (item.lesson_schedules || []).map((ls: any) => ({
          id: ls.lesson_id,
          sort_order: ls.sort_order,
          scheduled_date: ls.lesson_date,
          scheduled_time_slot: ls.lesson_time_slot,
        })),
      }));
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

  function isSelected(weekday: number, timeSlot: string): boolean {
    return selectedSlots.value.has(`${weekday}|${timeSlot}`);
  }

  function toggleSlot(weekday: number, timeSlot: string) {
    const key = `${weekday}|${timeSlot}`;
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
    editingSchedule.value = row;
    // 确保 teacher_id 为 number 类型，避免表单验证 type:'number' 不匹配
    formValues.value.teacher_id = row.teacher_id ? Number(row.teacher_id) : null;
    formValues.value.start_date = row.start_date;
    formValues.value.price = row.price;
    formValues.value.custom_price = row.custom_price ?? null;
    formValues.value.full_package_price = row.full_package_price;
    formValues.value.full_custom_price = row.full_custom_price ?? null;

    // 重置表单验证状态，避免编辑时误报校验错误
    nextTick(() => {
      formRef.value?.restoreValidation();
    });

    // 解析 time_slots（周几 + 时间段格式，兼容旧的日期格式）
    selectedSlots.value = new Set();
    if (row.time_slots) {
      try {
        const slots = JSON.parse(row.time_slots);
        if (Array.isArray(slots)) {
          // 收集所有时间段，还原自定义时间段
          const restoredCustomSlots = new Set<string>();
          slots.forEach((s: { weekday?: number; date?: string; time_slot: string }) => {
            restoredCustomSlots.add(s.time_slot);
            if (s.weekday) {
              selectedSlots.value.add(`${s.weekday}|${s.time_slot}`);
            } else if (s.date) {
              // 兼容旧数据：由日期换算为周几
              const weekday = weekdayIndexMap[new Date(s.date).getDay()];
              selectedSlots.value.add(`${weekday}|${s.time_slot}`);
            }
          });
          // 将不在默认列表中的时间段添加到 timeSlots
          restoredCustomSlots.forEach((ts: string) => {
            if (!timeSlots.value.includes(ts)) {
              const idx = timeSlots.value.findIndex(
                (s) => timeToMinutes(s.split('-')[0]) > timeToMinutes(ts.split('-')[0])
              );
              if (idx === -1) {
                timeSlots.value.push(ts);
              } else {
                timeSlots.value.splice(idx, 0, ts);
              }
            }
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
    editingSchedule.value = null;
    resetForm();
  }

  function resetForm() {
    editingId.value = null;
    formValues.value = {
      teacher_id: null,
      start_date: null,
      price: 0,
      custom_price: null,
      full_package_price: null,
      full_custom_price: null,
    };
    selectedSlots.value = new Set();
    editingSchedule.value = null;
    // 重置时间段为默认值
    timeSlots.value = [...defaultTimeSlots];
    cancelAddTimeSlot();
  }

  function handlePostpone(item: { lessonId: number; title: string }) {
    if (!props.courseId || !editingSchedule.value) return;
    // 保存当前编辑的排课 ID，避免 loadSchedules 后引用失效
    const currentEditingId = editingSchedule.value.id;
    console.log('[postpone] 延期参数:', { courseId: props.courseId, scheduleId: currentEditingId, lessonId: item.lessonId, title: item.title });
    window['$dialog']?.warning({
      title: '确认延期',
      content: `是否确定延期课时"${item.title}"？`,
      positiveText: '确定',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          console.log('[postpone] 调用 API:', { courseId: props.courseId!, scheduleId: currentEditingId, lessonId: item.lessonId });
          const result = await postponeCourseLessonSchedule(
            props.courseId!,
            currentEditingId,
            item.lessonId
          );
          console.log('[postpone] API 返回结果:', result);
          window['$message']?.success('延期成功');
          // 刷新排课列表（force: true 绕过缓存）
          await loadSchedules();
          console.log('[postpone] 刷新后排课列表:', scheduleList.value.map(s => ({ id: s.id, end_date: s.end_date, lesson_count: s.course_lessons?.length || 0 })));
          // 从刷新后的列表中找到当前编辑的记录，用新数据更新 editingSchedule
          const updated = scheduleList.value.find((s) => s.id === currentEditingId);
          if (updated) {
            editingSchedule.value = { ...updated };
            console.log('[postpone] 更新 editingSchedule:', { id: updated.id, end_date: updated.end_date });
          }
        } catch (err) {
          console.error('延期失败:', err);
          window['$message']?.error('延期失败');
        }
      },
    });
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
      // 序列化时间段：保存周几（1-7）+ 时间段，表示每周循环上课
      const slotsArray = Array.from(selectedSlots.value).map((key) => {
        const [weekdayStr, time_slot] = key.split('|');
        return { weekday: Number(weekdayStr), time_slot };
      });
      const timeSlotsJson = slotsArray.length > 0 ? JSON.stringify(slotsArray) : null;

      const payload = {
        teacher_id: formValues.value.teacher_id,
        start_date: formValues.value.start_date,
        time_slots: timeSlotsJson,
        price: formValues.value.price || 0,
        custom_price: formValues.value.custom_price ?? 0,
        full_package_price: formValues.value.full_package_price,
        full_custom_price: formValues.value.full_custom_price,
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
        // 防重复触发：删除进行中时忽略后续点击
        if (deleting.value) return;
        deleting.value = true;
        try {
          await deleteCourseSchedule(props.courseId!, row.id);
          window['$message']?.success('删除成功');
        } catch (err) {
          // 404 表示记录已被删除（重复触发场景），静默刷新列表，不弹重复错误提示
          const msg = String((err as Error)?.message || '');
          if (!msg.includes('不存在')) {
            window['$message']?.error('删除失败');
            return;
          }
        } finally {
          deleting.value = false;
        }
        await loadSchedules();
        emit('success');
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
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 2px;
    position: relative;
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

  .time-header-cell {
    font-size: 12px;
    font-weight: 600;
    color: #666;
  }

  .delete-slot-btn {
    position: absolute;
    right: 2px;
    top: 50%;
    transform: translateY(-50%);
    opacity: 0.6;
  }

  .delete-slot-btn:hover {
    opacity: 1;
  }

  /* 时间段整体容器 */
  .schedule-wrapper {
    width: 100%;
    display: block;
  }

  /* 新增时间段（表格外） */
  .add-slot-outside {
    margin-top: 8px;
  }

  .add-slot-form {
    display: flex;
    align-items: center;
    gap: 4px;
    flex-wrap: nowrap;
  }

  .add-slot-separator {
    color: #999;
    font-size: 12px;
  }

  /* 课程目录布局 */
  .lesson-item-row {
    display: flex;
    align-items: center;
    width: 100%;
  }

  .lesson-title {
    flex-shrink: 0;
  }

  .lesson-right-group {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 32px;
    flex-shrink: 0;
  }

  .lesson-time-text {
    white-space: nowrap;
  }

  .postpone-btn {
    flex-shrink: 0;
  }

  /* 锁定的课时样式 */
  .lesson-locked {
    opacity: 0.5;
    background-color: #f5f5f5;
  }

  .lesson-locked :deep(.n-list-item__main) {
    color: #999;
  }

  .schedule-locked {
    opacity: 0.5;
    pointer-events: none;
  }
</style>
