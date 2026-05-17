<template>
  <view class="page">
    <scroll-view
      class="content-scroll"
      scroll-y
      refresher-enabled
      :refresher-triggered="refreshing"
      @refresherrefresh="onPullDownRefresh"
      @scrolltolower="loadMore"
    >
      <view class="summary-card">
        <view class="summary-top">
          <view>
            <text class="summary-label">账户余额</text>
            <view v-if="balanceLoading" class="summary-skeleton main" />
            <text v-else class="summary-value">¥{{ formatMoney(balance) }}</text>
          </view>
          <view class="summary-action" @tap="goRecharge">
            <text class="summary-action-text">充值</text>
          </view>
        </view>
        <view v-if="balanceError" class="summary-error">
          <text class="summary-error-text">余额加载失败</text>
        </view>
        <view v-else class="summary-stats">
          <view class="summary-stat">
            <text class="summary-stat-value">¥{{ formatMoney(totalRecharged) }}</text>
            <text class="summary-stat-label">累计充值</text>
          </view>
          <view class="summary-divider" />
          <view class="summary-stat">
            <text class="summary-stat-value income">¥{{ formatMoney(pageIncome) }}</text>
            <text class="summary-stat-label">本页收入</text>
          </view>
          <view class="summary-divider" />
          <view class="summary-stat">
            <text class="summary-stat-value expense">¥{{ formatMoney(pageExpense) }}</text>
            <text class="summary-stat-label">本页支出</text>
          </view>
        </view>
      </view>

      <view class="filter-card">
        <view
          v-for="item in filters"
          :key="item.value"
          :class="['filter-item', { active: currentType === item.value }]"
          @tap="changeFilter(item.value)"
        >
          <text class="filter-text">{{ item.label }}</text>
        </view>
      </view>

      <view class="list-section">
        <view v-if="initialLoading" class="loading-list">
          <view v-for="index in 4" :key="index" class="transaction-skeleton">
            <view class="skeleton-icon" />
            <view class="skeleton-main">
              <view class="skeleton-line title" />
              <view class="skeleton-line sub" />
            </view>
            <view class="skeleton-amount" />
          </view>
        </view>

        <view v-else-if="loadError" class="state-card">
          <view class="state-icon error">!</view>
          <text class="state-title">流水加载失败，请重试</text>
          <view class="state-btn" @tap="retryLoad">
            <text class="state-btn-text">重新加载</text>
          </view>
        </view>

        <view v-else-if="transactions.length === 0" class="state-card">
          <view class="state-icon empty">¥</view>
          <text class="state-title">暂无钱包流水</text>
          <text class="state-desc">充值后可在这里查看交易明细</text>
          <view class="state-btn" @tap="goRecharge">
            <text class="state-btn-text">去钱包充值</text>
          </view>
        </view>

        <view v-else class="transaction-list">
          <view v-for="item in transactions" :key="item.id" class="transaction-item">
            <view :class="['type-icon', transactionIconClass(item)]">
              <text class="type-icon-text">{{ transactionIconText(item) }}</text>
            </view>
            <view class="transaction-main">
              <view class="transaction-title-row">
                <text class="transaction-title">{{ getTransactionTitle(item) }}</text>
                <text :class="['status-tag', item.status]">{{ statusText(item.status) }}</text>
              </view>
              <text class="transaction-meta">{{ formatTime(item.created_at) }}</text>
              <text class="transaction-meta">{{ paymentText(item.payment_method) }}</text>
              <view class="transaction-extra">
                <text class="extra-text">{{ balanceAfterText(item.balance_after) }}</text>
                <text v-if="hasBonus(item)" class="bonus-text">赠送 ¥{{ formatMoney(item.bonus_amount) }}</text>
              </view>
            </view>
            <view class="amount-block">
              <text :class="['amount-text', amountClass(item)]">{{ amountPrefix(item) }}¥{{ formatMoney(item.amount) }}</text>
            </view>
          </view>
        </view>

        <view v-if="transactions.length > 0" class="load-footer">
          <text v-if="loadingMore" class="footer-text">加载中...</text>
          <text v-else-if="!hasMore" class="footer-text">没有更多流水了</text>
        </view>
      </view>

      <view class="bottom-safe" />
    </scroll-view>
  </view>
</template>

<script>
import { getBalance, getWalletTransactions } from '@/api/wallet'

const PAGE_SIZE = 20

export default {
  data() {
    return {
      balance: 0,
      totalRecharged: 0,
      balanceLoading: false,
      balanceError: false,
      currentType: 'all',
      filters: [
        { label: '全部', value: 'all' },
        { label: '充值', value: 'recharge' },
        { label: '消费', value: 'consume' },
      ],
      transactions: [],
      page: 1,
      hasMore: true,
      initialLoading: false,
      loadingMore: false,
      refreshing: false,
      loadError: false,
      requestVersion: 0,
    }
  },

  computed: {
    pageIncome() {
      return this.transactions.reduce((sum, item) => {
        if (item.direction === 'income' && item.status === 'completed') {
          return sum + this.toNumber(item.amount)
        }
        return sum
      }, 0)
    },

    pageExpense() {
      return this.transactions.reduce((sum, item) => {
        if (item.direction === 'expense') {
          return sum + this.toNumber(item.amount)
        }
        return sum
      }, 0)
    },
  },

  onLoad() {
    this.loadBalance()
    this.loadTransactions({ reset: true })
  },

  methods: {
    async loadBalance() {
      this.balanceLoading = true
      this.balanceError = false
      try {
        const data = await getBalance()
        this.balance = data.balance || 0
        this.totalRecharged = data.total_recharged || data.totalRecharged || 0
      } catch {
        this.balanceError = true
      } finally {
        this.balanceLoading = false
      }
    },

    async loadTransactions({ reset = false } = {}) {
      if (!reset && (this.initialLoading || this.loadingMore)) return
      if (!reset && !this.hasMore) return

      const requestVersion = this.requestVersion + 1
      this.requestVersion = requestVersion
      const requestType = this.currentType
      const nextPage = reset ? 1 : this.page + 1
      if (reset) {
        this.initialLoading = true
        this.loadingMore = false
        this.loadError = false
      } else {
        this.loadingMore = true
      }

      try {
        const data = await getWalletTransactions({
          page: nextPage,
          page_size: PAGE_SIZE,
          type: requestType,
        })
        if (requestVersion !== this.requestVersion || requestType !== this.currentType) {
          return
        }
        const items = Array.isArray(data.items) ? data.items : []
        this.transactions = reset ? items : this.transactions.concat(items)
        this.page = data.page || nextPage
        this.hasMore = Boolean(data.has_more || data.hasMore)
        this.loadError = false
      } catch {
        if (requestVersion !== this.requestVersion || requestType !== this.currentType) {
          return
        }
        if (reset) {
          this.transactions = []
          this.loadError = true
        } else {
          uni.showToast({ title: '加载更多失败，请重试', icon: 'none' })
        }
      } finally {
        if (requestVersion === this.requestVersion) {
          this.initialLoading = false
          this.loadingMore = false
          this.refreshing = false
          uni.stopPullDownRefresh()
        }
      }
    },

    changeFilter(type) {
      if (this.currentType === type) return
      this.currentType = type
      this.transactions = []
      this.page = 1
      this.hasMore = true
      this.loadTransactions({ reset: true })
    },

    onPullDownRefresh() {
      this.refreshing = true
      this.loadBalance()
      this.loadTransactions({ reset: true })
    },

    loadMore() {
      this.loadTransactions()
    },

    retryLoad() {
      this.loadTransactions({ reset: true })
    },

    goRecharge() {
      uni.navigateTo({ url: '/pages/recharge/index' })
    },

    getTransactionTitle(item) {
      if (item.title) return item.title
      if (item.type === 'recharge') {
        if (item.status === 'pending') return '充值待支付'
        if (item.status === 'failed') return '充值失败'
        return '充值到账'
      }
      return '钱包流水'
    },

    statusText(status) {
      const statusMap = {
        completed: '完成',
        pending: '待处理',
        failed: '失败',
        cancelled: '已取消',
      }
      return statusMap[status] || '处理中'
    },

    paymentText(method) {
      const methodMap = {
        wechat: '微信支付',
        alipay: '支付宝',
        wallet: '钱包余额',
      }
      return methodMap[method] || '支付方式 -'
    },

    balanceAfterText(value) {
      if (value === null || value === undefined || value === '') {
        return '交易后余额 -'
      }
      return `交易后余额 ¥${this.formatMoney(value)}`
    },

    transactionIconText(item) {
      if (item.type === 'recharge') return '充'
      if (item.direction === 'expense') return '支'
      return '收'
    },

    transactionIconClass(item) {
      if (item.status === 'failed') return 'failed'
      if (item.status === 'pending') return 'pending'
      return item.direction === 'expense' ? 'expense' : 'income'
    },

    amountClass(item) {
      if (item.status !== 'completed') return 'muted'
      return item.direction === 'expense' ? 'expense' : 'income'
    },

    amountPrefix(item) {
      if (item.status !== 'completed') return ''
      return item.direction === 'expense' ? '-' : '+'
    },

    hasBonus(item) {
      return this.toNumber(item.bonus_amount) > 0
    },

    toNumber(value) {
      const amount = Number(value)
      return Number.isFinite(amount) ? amount : 0
    },

    formatMoney(value) {
      return this.toNumber(value).toFixed(2)
    },

    formatTime(value) {
      if (!value) return '时间 -'
      const date = new Date(value)
      if (Number.isNaN(date.getTime())) return String(value)
      const pad = (num) => String(num).padStart(2, '0')
      return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-color;
}

.content-scroll {
  height: 100vh;
}

.summary-card {
  margin: 32rpx 32rpx 0;
  padding: 36rpx;
  border-radius: $radius-xl;
  background: linear-gradient(135deg, $primary 0%, $purple 100%);
  color: $white;
  box-shadow: 0 18rpx 42rpx rgba(79, 110, 247, 0.2);
}

.summary-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24rpx;
}

.summary-label,
.summary-error-text {
  font-size: 24rpx;
  line-height: 34rpx;
  color: rgba(255, 255, 255, 0.72);
}

.summary-value {
  display: block;
  margin-top: 10rpx;
  font-size: 56rpx;
  line-height: 70rpx;
  font-weight: 700;
  color: $white;
  word-break: break-all;
}

.summary-action {
  flex-shrink: 0;
  height: 56rpx;
  padding: 0 28rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
}

.summary-action-text {
  font-size: 24rpx;
  font-weight: 600;
  color: $white;
}

.summary-stats {
  margin-top: 30rpx;
  padding-top: 26rpx;
  border-top: 1rpx solid rgba(255, 255, 255, 0.16);
  display: flex;
  align-items: center;
}

.summary-stat {
  flex: 1;
  min-width: 0;
}

.summary-stat-value {
  display: block;
  font-size: 26rpx;
  line-height: 36rpx;
  font-weight: 700;
  color: $white;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.summary-stat-value.income {
  color: #d9fff0;
}

.summary-stat-value.expense {
  color: #fff0d9;
}

.summary-stat-label {
  display: block;
  margin-top: 6rpx;
  font-size: 22rpx;
  line-height: 30rpx;
  color: rgba(255, 255, 255, 0.64);
}

.summary-divider {
  width: 1rpx;
  height: 48rpx;
  margin: 0 22rpx;
  background: rgba(255, 255, 255, 0.14);
}

.summary-error {
  margin-top: 28rpx;
  padding: 18rpx 22rpx;
  border-radius: $radius-md;
  background: rgba(255, 255, 255, 0.12);
}

.summary-skeleton {
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.22);
}

.summary-skeleton.main {
  width: 260rpx;
  height: 60rpx;
  margin-top: 18rpx;
}

.filter-card {
  margin: 28rpx 32rpx 0;
  padding: 8rpx;
  border-radius: 999rpx;
  background: $white;
  display: flex;
  box-shadow: $shadow-sm;
}

.filter-item {
  flex: 1;
  height: 64rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.filter-item.active {
  background: $primary;
  box-shadow: 0 8rpx 18rpx rgba(79, 110, 247, 0.2);
}

.filter-text {
  font-size: 26rpx;
  line-height: 36rpx;
  font-weight: 600;
  color: $text-secondary;
}

.filter-item.active .filter-text {
  color: $white;
}

.list-section {
  margin: 28rpx 32rpx 0;
}

.transaction-list,
.loading-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.transaction-item,
.transaction-skeleton {
  min-height: 150rpx;
  padding: 28rpx;
  border-radius: $radius-lg;
  background: $white;
  box-shadow: $shadow-sm;
  display: flex;
  gap: 20rpx;
}

.type-icon,
.skeleton-icon {
  width: 64rpx;
  height: 64rpx;
  border-radius: 18rpx;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.type-icon.income {
  background: rgba(7, 193, 96, 0.1);
}

.type-icon.expense {
  background: rgba(255, 149, 0, 0.12);
}

.type-icon.pending {
  background: $primary-light;
}

.type-icon.failed {
  background: rgba(255, 107, 107, 0.1);
}

.type-icon-text {
  font-size: 24rpx;
  font-weight: 700;
  color: $primary;
}

.type-icon.income .type-icon-text {
  color: $success;
}

.type-icon.expense .type-icon-text {
  color: #e67900;
}

.type-icon.failed .type-icon-text {
  color: $danger;
}

.transaction-main {
  flex: 1;
  min-width: 0;
}

.transaction-title-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.transaction-title {
  flex: 1;
  min-width: 0;
  font-size: 28rpx;
  line-height: 38rpx;
  font-weight: 700;
  color: $text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-tag {
  flex-shrink: 0;
  padding: 4rpx 12rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  line-height: 28rpx;
  color: $text-secondary;
  background: rgba(99, 110, 114, 0.1);
}

.status-tag.completed {
  color: $success;
  background: rgba(7, 193, 96, 0.1);
}

.status-tag.pending {
  color: $primary;
  background: $primary-light;
}

.status-tag.failed {
  color: $danger;
  background: rgba(255, 107, 107, 0.1);
}

.transaction-meta {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 30rpx;
  color: $text-muted;
}

.transaction-extra {
  margin-top: 14rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx 16rpx;
}

.extra-text,
.bonus-text {
  font-size: 22rpx;
  line-height: 30rpx;
  color: $text-secondary;
}

.bonus-text {
  color: #e67900;
}

.amount-block {
  width: 150rpx;
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
}

.amount-text {
  display: block;
  max-width: 150rpx;
  font-size: 28rpx;
  line-height: 38rpx;
  font-weight: 700;
  text-align: right;
  word-break: break-all;
}

.amount-text.income {
  color: $success;
}

.amount-text.expense {
  color: #e67900;
}

.amount-text.muted {
  color: $text-secondary;
}

.state-card {
  min-height: 420rpx;
  border-radius: $radius-lg;
  background: $white;
  box-shadow: $shadow-sm;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48rpx 32rpx;
  text-align: center;
}

.state-icon {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 42rpx;
  font-weight: 700;
}

.state-icon.empty {
  color: $primary;
  background: $primary-light;
}

.state-icon.error {
  color: $danger;
  background: rgba(255, 107, 107, 0.1);
}

.state-title {
  display: block;
  margin-top: 24rpx;
  font-size: 30rpx;
  line-height: 42rpx;
  font-weight: 700;
  color: $text-primary;
}

.state-desc {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  line-height: 34rpx;
  color: $text-muted;
}

.state-btn {
  margin-top: 30rpx;
  height: 64rpx;
  padding: 0 32rpx;
  border-radius: 999rpx;
  background: $primary;
  display: flex;
  align-items: center;
  justify-content: center;
}

.state-btn-text {
  font-size: 24rpx;
  font-weight: 600;
  color: $white;
}

.load-footer {
  height: 82rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.footer-text {
  font-size: 22rpx;
  color: $text-muted;
}

.skeleton-icon,
.skeleton-line,
.skeleton-amount {
  background: #eef1f6;
  border-radius: 999rpx;
}

.skeleton-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.skeleton-line.title {
  width: 70%;
  height: 30rpx;
}

.skeleton-line.sub {
  width: 52%;
  height: 24rpx;
}

.skeleton-amount {
  width: 110rpx;
  height: 34rpx;
}

.bottom-safe {
  height: calc(40rpx + env(safe-area-inset-bottom));
}
</style>
