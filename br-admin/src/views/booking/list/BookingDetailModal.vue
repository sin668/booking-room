<template>
  <n-modal
    v-model:show="visible"
    preset="card"
    title="订单详情"
    style="width: 720px"
    :bordered="false"
    :mask-closable="true"
  >
    <n-spin :show="loading">
      <template v-if="detail">
        <n-flex vertical :size="16">
          <!-- 订单基本信息 -->
          <n-card size="small" title="订单基本信息" :bordered="false">
            <n-descriptions :column="3" label-placement="left" bordered size="small">
              <n-descriptions-item label="订单ID">{{ detail.id }}</n-descriptions-item>
              <n-descriptions-item label="预约类型">{{ bookingTypeText }}</n-descriptions-item>
              <n-descriptions-item label="状态">
                <n-tag :type="statusTag.type" size="small">{{ statusTag.label }}</n-tag>
              </n-descriptions-item>
              <n-descriptions-item label="预约日期">{{ detail.date }}</n-descriptions-item>
              <n-descriptions-item label="时段" :span="2">{{
                formatBookingTimeRange(detail)
              }}</n-descriptions-item>
              <n-descriptions-item label="创建时间">{{ detail.created_at }}</n-descriptions-item>
              <n-descriptions-item label="更新时间" :span="2">{{
                detail.updated_at
              }}</n-descriptions-item>
            </n-descriptions>
          </n-card>

          <!-- 用户信息 -->
          <n-card size="small" title="用户信息" :bordered="false">
            <n-descriptions :column="3" label-placement="left" bordered size="small">
              <n-descriptions-item label="昵称">{{
                detail.user?.nickname || detail.user_nickname || '-'
              }}</n-descriptions-item>
              <n-descriptions-item label="手机号">{{ detail.user?.phone || '-' }}</n-descriptions-item>
              <n-descriptions-item label="用户ID">{{ detail.user_id }}</n-descriptions-item>
            </n-descriptions>
          </n-card>

          <!-- 自习室与座位（自习室订单展示） -->
          <n-card v-if="detail.booking_type !== 'course'" size="small" title="自习室与座位" :bordered="false">
            <n-descriptions :column="3" label-placement="left" bordered size="small">
              <n-descriptions-item label="自习室名称">{{ detail.room?.name || '-' }}</n-descriptions-item>
              <n-descriptions-item label="地址">{{ detail.room?.address || '-' }}</n-descriptions-item>
              <n-descriptions-item label="座位编号">{{ detail.seat?.seat_number || '-' }}</n-descriptions-item>
              <n-descriptions-item label="区域">{{ detail.seat?.zone || '-' }}</n-descriptions-item>
              <n-descriptions-item label="时价">
                {{ detail.seat?.price_per_hour != null ? `¥${detail.seat.price_per_hour}` : '-' }}
              </n-descriptions-item>
            </n-descriptions>
          </n-card>

          <!-- 课程与排课（课程订单展示） -->
          <template v-else>
            <n-card size="small" title="课程与排课" :bordered="false">
              <n-descriptions :column="3" label-placement="left" bordered size="small">
                <n-descriptions-item label="课程名称">{{ detail.course?.name || '-' }}</n-descriptions-item>
                <n-descriptions-item label="课程分类">{{ detail.course?.category || '-' }}</n-descriptions-item>
                <n-descriptions-item label="授课老师">{{ detail.teacher?.name || '-' }}</n-descriptions-item>
                <n-descriptions-item label="排课类型">{{ scheduleTypeText }}</n-descriptions-item>
                <n-descriptions-item label="排课状态">{{ detail.schedule?.schedule_status || '-' }}</n-descriptions-item>
                <n-descriptions-item label="排课ID">{{ detail.schedule_id ?? '-' }}</n-descriptions-item>
                <n-descriptions-item label="排课日期范围" :span="3">
                  {{ scheduleDateRange }}
                </n-descriptions-item>
              </n-descriptions>
            </n-card>

            <!-- 课时安排 -->
            <n-card size="small" title="课时安排" :bordered="false">
              <n-data-table
                v-if="(detail.lesson_schedules || []).length > 0"
                :columns="lessonColumns"
                :data="detail.lesson_schedules"
                :row-key="(row: BookingDetailLessonSchedule) => row.id"
                size="small"
                :bordered="true"
                :max-height="240"
              />
              <n-empty v-else description="暂无课时记录" />
            </n-card>
          </template>

          <!-- 价格与支付 -->
          <n-card size="small" title="价格与支付" :bordered="false">
            <n-descriptions :column="3" label-placement="left" bordered size="small">
              <n-descriptions-item label="原价">¥{{ detail.original_price ?? '-' }}</n-descriptions-item>
              <n-descriptions-item label="优惠金额">¥{{ detail.discount_amount ?? 0 }}</n-descriptions-item>
              <n-descriptions-item label="实付金额">¥{{ detail.total_price }}</n-descriptions-item>
              <n-descriptions-item label="支付方式">{{ detail.payment_method || '-' }}</n-descriptions-item>
              <n-descriptions-item label="支付状态">{{ paymentStatusText }}</n-descriptions-item>
              <n-descriptions-item label="支付时间">{{ detail.paid_at || '-' }}</n-descriptions-item>
              <n-descriptions-item label="优惠券">{{ couponText }}</n-descriptions-item>
              <n-descriptions-item label="交易单号">{{ detail.transaction_id || '-' }}</n-descriptions-item>
              <n-descriptions-item label="预支付单号">{{ detail.prepay_id || '-' }}</n-descriptions-item>
            </n-descriptions>
          </n-card>

          <!-- 取消与退款 -->
          <n-card
            v-if="detail.status === 'cancelled' || detail.cancelled_at || (detail.refund_amount ?? 0) > 0"
            size="small"
            title="取消与退款"
            :bordered="false"
          >
            <n-descriptions :column="3" label-placement="left" bordered size="small">
              <n-descriptions-item label="取消时间">{{ detail.cancelled_at || '-' }}</n-descriptions-item>
              <n-descriptions-item label="取消政策">{{ cancelPolicyText }}</n-descriptions-item>
              <n-descriptions-item label="违约金">¥{{ detail.penalty_amount ?? 0 }}</n-descriptions-item>
              <n-descriptions-item label="退款金额">¥{{ detail.refund_amount ?? 0 }}</n-descriptions-item>
              <n-descriptions-item label="退款后余额">
                {{
                  detail.refund_transaction?.balance_after != null
                    ? `¥${detail.refund_transaction.balance_after}`
                    : '-'
                }}
              </n-descriptions-item>
              <n-descriptions-item label="退款时间">
                {{ detail.refund_transaction?.created_at || '-' }}
              </n-descriptions-item>
            </n-descriptions>
          </n-card>
        </n-flex>
      </template>
      <n-empty v-else-if="!loading" description="暂无订单数据" />
    </n-spin>
    <template #footer>
      <n-flex justify="end">
        <n-button @click="visible = false">关闭</n-button>
      </n-flex>
    </template>
  </n-modal>
</template>

<script lang="ts" setup>
  import { computed, ref } from 'vue';
  import { getBookingDetail, type BookingDetail, type BookingDetailLessonSchedule } from '@/api/booking';
  import { BOOKING_STATUS_TAGS } from '@/views/business/shared/options';
  import { formatBookingTimeRange } from './builders';

  const visible = ref(false);
  const loading = ref(false);
  const detail = ref<BookingDetail | null>(null);

  const bookingTypeText = computed(() =>
    detail.value?.booking_type === 'course' ? '课程预约' : '自习室预约'
  );

  const statusTag = computed(() => {
    const status = detail.value?.status || '';
    return BOOKING_STATUS_TAGS[status] || { label: status, type: 'default' as const };
  });

  const scheduleTypeText = computed(() => {
    const type = detail.value?.schedule?.schedule_type || detail.value?.schedule_type;
    if (type === 'fixed') return '固定班课';
    if (type === 'custom') return '私人定制';
    return type || '-';
  });

  const scheduleDateRange = computed(() => {
    const schedule = detail.value?.schedule;
    if (!schedule?.start_date && !schedule?.end_date) return '-';
    return `${schedule?.start_date || '-'} ~ ${schedule?.end_date || '不限'}`;
  });

  const paymentStatusText = computed(() => {
    const map: Record<string, string> = {
      unpaid: '未支付',
      paid: '已支付',
      refunded: '已退款',
    };
    const status = detail.value?.payment_status || '';
    return map[status] || status || '-';
  });

  const couponText = computed(() => {
    const coupon = detail.value?.coupon;
    if (!coupon) return '-';
    const discount =
      coupon.discount_amount != null
        ? `¥${coupon.discount_amount}`
        : coupon.discount_percent != null
          ? `${coupon.discount_percent}%`
          : '-';
    return `${coupon.name || coupon.coupon_id}（${discount}）`;
  });

  const cancelPolicyText = computed(() => {
    const map: Record<string, string> = {
      full_refund: '全额退款',
      over_48h: '提前48小时以上',
      h24_48: '24-48小时内',
      h2_24: '2-24小时内',
      within_2h: '2小时内',
    };
    const policy = detail.value?.cancel_policy;
    return (policy && map[policy]) || policy || '-';
  });

  const lessonColumns = [
    { title: '序号', key: 'sort_order', width: 60 },
    { title: '课时', key: 'lesson_title', render: (row: BookingDetailLessonSchedule) => row.lesson_title || `课时 ${row.lesson_id}` },
    { title: '上课日期', key: 'lesson_date', render: (row: BookingDetailLessonSchedule) => row.lesson_date || '-' },
    { title: '时段', key: 'lesson_time_slot' },
  ];

  async function showModal(bookingId: number) {
    visible.value = true;
    detail.value = null;
    loading.value = true;
    try {
      detail.value = await getBookingDetail(bookingId);
    } catch {
      window['$message'].error('订单详情加载失败');
    } finally {
      loading.value = false;
    }
  }

  defineExpose({ showModal });
</script>
