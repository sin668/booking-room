<template>
  <n-modal
    :show="show"
    preset="card"
    :title="`可排课时间段 - ${teacherName}`"
    style="width: 900px; max-width: 95vw"
    :mask-closable="false"
    @update:show="(val) => emit('update:show', val)"
  >
    <n-flex vertical :size="16">
      <n-spin :show="loading">
        <!-- 时间段网格 -->
        <div class="schedule-wrapper">
          <div class="schedule-grid">
            <!-- 表头 -->
            <div class="schedule-header">
              <div class="header-cell time-header-cell">时间段</div>
              <div v-for="h in weekdayHeaders" :key="h.weekday" class="header-cell date-header">
                <div class="weekday">{{ h.name }}</div>
              </div>
            </div>
            <!-- 网格行 -->
            <div v-for="timeSlot in timeSlots" :key="timeSlot" class="schedule-row">
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
                  <template #icon>
                    <n-icon size="12"><CloseOutline /></n-icon>
                  </template>
                </n-button>
              </div>
              <div
                v-for="h in weekdayHeaders"
                :key="`${h.weekday}|${timeSlot}`"
                class="slot-cell"
                :class="{ selected: isSelected(h.weekday, timeSlot) }"
                @click="toggleSlot(h.weekday, timeSlot)"
              >
                {{ isSelected(h.weekday, timeSlot) ? '✓' : '' }}
              </div>
            </div>
          </div>
          <!-- 新增时间段 -->
          <div class="add-slot-outside">
            <n-button v-if="!showAddSlotInput" text type="primary" size="small" @click="showAddSlotInput = true">
              <template #icon>
                <n-icon size="14"><AddOutline /></n-icon>
              </template>
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
              <n-button type="primary" size="tiny" :disabled="!newSlotStart || !newSlotEnd" @click="confirmAddTimeSlot">
                确定
              </n-button>
              <n-button size="tiny" @click="cancelAddTimeSlot">取消</n-button>
            </div>
          </div>
        </div>

        <!-- 已选时间段 -->
        <n-form-item v-if="selectedSlotList.length > 0" label="已选时间段" style="margin-top: 16px">
          <n-flex wrap>
            <n-tag v-for="slot in selectedSlotList" :key="slot.key" type="info" size="small" closable @close="removeSlot(slot.key)">
              {{ slot.label }}
            </n-tag>
          </n-flex>
        </n-form-item>
      </n-spin>
    </n-flex>
    <template #footer>
      <n-flex justify="end" :size="12">
        <n-button @click="emit('update:show', false)">取消</n-button>
        <n-button type="primary" :loading="saving" @click="handleSave">保存</n-button>
      </n-flex>
    </template>
  </n-modal>
</template>

<script lang="ts" setup>
  import { computed, ref, watch } from 'vue';
  import { AddOutline, CloseOutline } from '@vicons/ionicons5';
  import { getTeacherAvailableTimeSlots, updateTeacherAvailableTimeSlots } from '@/api/teacher';

  const props = defineProps<{
    show: boolean;
    teacherId: number | null;
    teacherName: string;
  }>();

  const emit = defineEmits<{
    (e: 'update:show', val: boolean): void;
    (e: 'success'): void;
  }>();

  const defaultTimeSlots = [
    '08:00-10:00',
    '10:00-12:00',
    '12:00-14:00',
    '14:00-16:00',
    '16:00-18:00',
    '18:00-20:00',
    '20:00-22:00',
  ];

  const weekdayHeaders = [
    { weekday: 1, name: '周一' },
    { weekday: 2, name: '周二' },
    { weekday: 3, name: '周三' },
    { weekday: 4, name: '周四' },
    { weekday: 5, name: '周五' },
    { weekday: 6, name: '周六' },
    { weekday: 7, name: '周日' },
  ];

  const weekdayNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];

  const timeSlots = ref<string[]>([...defaultTimeSlots]);
  const selectedSlots = ref<Set<string>>(new Set());
  const loading = ref(false);
  const saving = ref(false);
  const showAddSlotInput = ref(false);
  const newSlotStart = ref<string | null>(null);
  const newSlotEnd = ref<string | null>(null);

  function isDefaultTimeSlot(slot: string) {
    return defaultTimeSlots.includes(slot);
  }

  function isSelected(weekday: number, timeSlot: string) {
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

  function removeCustomTimeSlot(slot: string) {
    // 删除该时间段对应的所有选中项
    const newSelected = new Set<string>();
    selectedSlots.value.forEach((key) => {
      if (!key.endsWith(`|${slot}`)) {
        newSelected.add(key);
      }
    });
    selectedSlots.value = newSelected;
    timeSlots.value = timeSlots.value.filter((s) => s !== slot);
  }

  function confirmAddTimeSlot() {
    if (!newSlotStart.value || !newSlotEnd.value) return;
    const slot = `${newSlotStart.value}-${newSlotEnd.value}`;
    if (!timeSlots.value.includes(slot)) {
      timeSlots.value.push(slot);
    }
    showAddSlotInput.value = false;
    newSlotStart.value = null;
    newSlotEnd.value = null;
  }

  function cancelAddTimeSlot() {
    showAddSlotInput.value = false;
    newSlotStart.value = null;
    newSlotEnd.value = null;
  }

  const selectedSlotList = computed(() => {
    return Array.from(selectedSlots.value)
      .map((key) => {
        const [weekdayStr, timeSlot] = key.split('|');
        const weekday = Number(weekdayStr);
        return {
          key,
          label: `${weekdayNames[weekday]} ${timeSlot}`,
        };
      })
      .sort((a, b) => {
        const [aWeekday] = a.key.split('|');
        const [bWeekday] = b.key.split('|');
        return Number(aWeekday) - Number(bWeekday) || a.label.localeCompare(b.label);
      });
  });

  function serializeSlots(): any[] {
    return Array.from(selectedSlots.value)
      .map((key) => {
        const [weekdayStr, timeSlot] = key.split('|');
        return { weekday: Number(weekdayStr), time_slot: timeSlot };
      })
      .sort((a, b) => a.weekday - b.weekday || a.time_slot.localeCompare(b.time_slot));
  }

  function deserializeSlots(data: any[]) {
    selectedSlots.value = new Set();
    const customSlots = new Set<string>();
    // 收集默认时间段
    defaultTimeSlots.forEach((s) => customSlots.add(s));

    data.forEach((s: any) => {
      if (s.weekday && s.time_slot) {
        selectedSlots.value.add(`${s.weekday}|${s.time_slot}`);
        if (!defaultTimeSlots.includes(s.time_slot)) {
          customSlots.add(s.time_slot);
        }
      }
    });

    // 还原自定义时间段
    const newCustom = Array.from(customSlots).filter((s) => !defaultTimeSlots.includes(s));
    newCustom.sort((a, b) => {
      const [aStart] = a.split('-');
      const [bStart] = b.split('-');
      return aStart.localeCompare(bStart);
    });
    timeSlots.value = [...defaultTimeSlots, ...newCustom];
  }

  async function loadData() {
    if (!props.teacherId) return;
    loading.value = true;
    try {
      const res = await getTeacherAvailableTimeSlots(props.teacherId);
      const slots = res.available_time_slots || [];
      deserializeSlots(slots);
    } catch (e) {
      window.$message?.error('加载可排课时间段失败');
      // 重置为默认
      timeSlots.value = [...defaultTimeSlots];
      selectedSlots.value = new Set();
    } finally {
      loading.value = false;
    }
  }

  async function handleSave() {
    if (!props.teacherId) return;
    saving.value = true;
    try {
      const data = serializeSlots();
      await updateTeacherAvailableTimeSlots(props.teacherId, {
        available_time_slots: data.length > 0 ? data : null,
      });
      window.$message?.success('保存成功');
      emit('success');
      emit('update:show', false);
    } catch (e) {
      window.$message?.error('保存失败');
    } finally {
      saving.value = false;
    }
  }

  watch(
    () => props.show,
    (val) => {
      if (val) {
        loadData();
      }
    }
  );
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
</style>
