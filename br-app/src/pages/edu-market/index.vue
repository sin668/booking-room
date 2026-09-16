<template>
  <view class="page">
    <!-- 自定义导航栏 -->
    <view class="nav-bar">
      <text class="nav-title">教培供需</text>
      <view class="nav-publish" @tap="goPublish">
        <text class="nav-publish-text">+ 发布</text>
      </view>
    </view>

    <!-- 筛选区（固定） -->
    <view class="filters">
      <!-- 类型 TAB -->
      <view class="tab-bar">
        <view
          v-for="tab in typeTabs"
          :key="tab.key"
          :class="['tab-item', { 'tab-active': activeType === tab.key }]"
          @tap="switchType(tab.key)"
        >
          <text class="tab-text">{{ tab.label }}</text>
        </view>
      </view>

      <!-- 城市 + 科目 + 排序 -->
      <view class="sub-filter">
        <view class="city-pill" @tap="onTapCity">
          <view class="icon icon-location city-pill-icon" />
          <text class="city-pill-text">{{ currentCityName }}</text>
        </view>
        <scroll-view class="subject-scroll" scroll-x :show-scrollbar="false">
          <view class="subject-list">
            <text
              v-for="sub in subjectChips"
              :key="sub"
              :class="['subject-chip', { 'subject-chip-on': activeSubject === sub }]"
              @tap="switchSubject(sub)"
            >{{ sub }}</text>
          </view>
        </scroll-view>
        <view class="sort-pill" @tap="onTapSort">
          <text class="sort-pill-text">{{ sortLabel }}</text>
          <view class="icon icon-arrow-down sort-pill-arrow" />
        </view>
      </view>
    </view>

    <!-- 内容区域 -->
    <view class="content">
      <!-- 加载骨架 -->
      <view v-if="loading && listings.length === 0" class="skeleton-waterfall">
        <view class="skeleton-col">
          <view v-for="i in 2" :key="i" class="skeleton-card">
            <view class="skeleton-cover" :style="{ height: (i % 2 ? 240 : 190) + 'rpx' }" />
            <view class="skeleton-line long" />
            <view class="skeleton-line short" />
          </view>
        </view>
        <view class="skeleton-col">
          <view v-for="i in 2" :key="i" class="skeleton-card">
            <view class="skeleton-cover" :style="{ height: (i % 2 ? 190 : 240) + 'rpx' }" />
            <view class="skeleton-line long" />
            <view class="skeleton-line short" />
          </view>
        </view>
      </view>

      <!-- 空状态 -->
      <view v-else-if="!loading && listings.length === 0" class="empty-state">
        <view class="empty-icon-circle">
          <view class="icon icon-chalkboard-user empty-icon" />
        </view>
        <text class="empty-title">暂无供需信息</text>
        <text class="empty-subtitle">换个筛选条件，或成为第一个发布的人</text>
        <view class="empty-btn" @tap="goPublish">
          <text class="empty-btn-text">我要发布</text>
        </view>
      </view>

      <!-- 瀑布流（JS 拆左右两列） -->
      <view v-else class="waterfall">
        <view v-for="(col, ci) in columns" :key="ci" class="waterfall-col">
          <view
            v-for="(card, idx) in col"
            :key="card.id"
            :class="['card', 'animate-in', `delay-${Math.min(idx + 1, 3)}`]"
            @tap="goDetail(card.id)"
          >
            <!-- 封面 -->
            <view class="card-cover" :style="{ height: card._coverH + 'rpx' }">
              <image
                v-if="card.images && card.images.length"
                class="card-cover-img"
                :src="card.images[0]"
                mode="aspectFill"
              />
              <view v-else :class="['card-cover-ph', `ph-${card.listing_type}`]">
                <view class="icon card-ph-icon" :class="typeMeta(card.listing_type).icon" />
                <text v-if="card.subject" class="card-ph-subject">{{ card.subject }}</text>
              </view>
              <view :class="['card-type-badge', `badge-${card.listing_type}`]">
                <text class="card-type-text">{{ typeMeta(card.listing_type).label }}</text>
              </view>
            </view>

            <!-- 信息 -->
            <view class="card-body">
              <text class="card-title">{{ card.title }}</text>

              <view v-if="certBadges(card).length" class="card-certs">
                <view v-for="cb in certBadges(card)" :key="cb.text" class="card-cert">
                  <view class="icon icon-shield-check card-cert-icon" :class="cb.cls" />
                  <text class="card-cert-text">{{ cb.text }}</text>
                </view>
              </view>

              <view v-if="card.area" class="card-area">
                <view class="icon icon-location card-area-icon" />
                <text class="card-area-text">{{ card.area }}</text>
              </view>

              <view class="card-foot">
                <view class="card-publisher">
                  <image
                    v-if="card.publisher_avatar"
                    class="card-avatar"
                    :src="card.publisher_avatar"
                    mode="aspectFill"
                  />
                  <view v-else class="card-avatar-ph">
                    <view class="icon icon-user card-avatar-icon" />
                  </view>
                  <text class="card-nickname">{{ card.publisher_nickname || '匿名用户' }}</text>
                </view>
                <view v-if="card.price" class="card-price-wrap">
                  <text class="card-price-symbol">¥</text>
                  <text class="card-price">{{ formatPrice(card.price) }}</text>
                  <text v-if="card.price_unit" class="card-price-unit">{{ shortUnit(card.price_unit) }}</text>
                </view>
                <text v-else class="card-price-neg">面议</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 加载状态 -->
      <view v-if="listings.length" class="load-more">
        <text class="load-more-text">{{ loadMoreText }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onMounted } from 'vue'
import { onReachBottom, onShow } from '@dcloudio/uni-app'
import { getEduListings } from '@/api/eduMarket'
import { ensureLogin } from '@/utils/auth'
import { useCityStore } from '@/store/modules/city'

const TYPE_TABS = [
  { key: '', label: '全部' },
  { key: 'tutor', label: '家教' },
  { key: 'training', label: '培训班' },
  { key: 'demand', label: '求教' },
]
const SUBJECT_CHIPS = ['全部', '英语', '数学', '物理', '化学', '语文', '编程', '钢琴', '美术']
const TYPE_META = {
  tutor: { label: '家教', icon: 'icon-graduation-cap' },
  training: { label: '培训班', icon: 'icon-chalkboard-user' },
  demand: { label: '求教', icon: 'icon-user' },
}
const SORT_OPTIONS = [
  { key: 'new', label: '最新发布' },
  { key: 'price_asc', label: '价格从低到高' },
  { key: 'price_desc', label: '价格从高到低' },
]
// 封面高度循环，制造瀑布流错落感（无图时作为占位块高度）
const COVER_HEIGHTS = [280, 220, 320, 240, 300, 210]

const typeTabs = TYPE_TABS
const subjectChips = SUBJECT_CHIPS

const activeType = ref('')
const activeSubject = ref('全部')
const activeSort = ref('new')
const listings = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const PAGE_SIZE = 10
// 防竞态：仅接受最新一次请求的结果
let listRequestId = 0

const cityStore = useCityStore()
const currentCityName = computed(() => cityStore.currentCityName)
const currentCity = computed(() => cityStore.currentCity)
let lastCityId

const sortLabel = computed(() => {
  const opt = SORT_OPTIONS.find((o) => o.key === activeSort.value)
  return opt ? opt.label : '最新发布'
})

const hasMore = computed(() => listings.value.length < total.value)
const loadMoreText = computed(() => {
  if (loading.value) return '加载中…'
  return hasMore.value ? '上拉加载更多' : '没有更多了'
})

function typeMeta(type) {
  return TYPE_META[type] || TYPE_META.demand
}

function formatPrice(price) {
  const num = Number(price)
  if (!Number.isFinite(num)) return ''
  return Number.isInteger(num) ? String(num) : num.toFixed(2).replace(/\.?0+$/, '')
}

function shortUnit(unit) {
  return String(unit || '').replace(/^元/, '/')
}

function certBadges(card) {
  const badges = []
  if (card.publisher_education_verified) badges.push({ text: '学历认证', cls: 'cert-edu' })
  if (card.publisher_teacher_verified) badges.push({ text: '教师资格', cls: 'cert-tea' })
  return badges
}

// JS 拆两列：按累计估算高度放入较矮的一列
const columns = computed(() => {
  const cols = [[], []]
  const heights = [0, 0]
  listings.value.forEach((item, idx) => {
    const coverH = COVER_HEIGHTS[idx % COVER_HEIGHTS.length]
    const titleLines = (item.title || '').length > 13 ? 2 : 1
    const est = coverH + 140 + titleLines * 32
    const target = heights[0] <= heights[1] ? 0 : 1
    cols[target].push({ ...item, _coverH: coverH })
    heights[target] += est
  })
  return cols
})

function switchType(key) {
  if (activeType.value === key) return
  activeType.value = key
  fetchListings(true)
}

function switchSubject(sub) {
  if (activeSubject.value === sub) return
  activeSubject.value = sub
  fetchListings(true)
}

function onTapCity() {
  uni.navigateTo({ url: '/pages/city-select/index' })
}

function onTapSort() {
  uni.showActionSheet({
    itemList: SORT_OPTIONS.map((o) => o.label),
    success: (res) => {
      const opt = SORT_OPTIONS[res.tapIndex]
      if (opt && opt.key !== activeSort.value) {
        activeSort.value = opt.key
        fetchListings(true)
      }
    },
  })
}

function goPublish() {
  if (!ensureLogin()) return
  uni.navigateTo({ url: '/pages/edu-market/publish' })
}

function goDetail(id) {
  uni.navigateTo({ url: `/pages/edu-market/detail?id=${id}` })
}

async function fetchListings(reset = false) {
  if (loading.value) return
  if (reset) {
    page.value = 1
  }
  const requestId = ++listRequestId
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: PAGE_SIZE,
      sort: activeSort.value,
    }
    if (activeType.value) params.listing_type = activeType.value
    if (activeSubject.value && activeSubject.value !== '全部') params.subject = activeSubject.value
    if (currentCity.value?.name) params.city = currentCity.value.name
    const data = await getEduListings(params)
    if (requestId !== listRequestId) return
    const items = data.items || []
    listings.value = reset ? items : listings.value.concat(items)
    total.value = data.total || 0
    if (!reset) page.value++
  } catch {
    if (requestId !== listRequestId) return
    if (reset) {
      listings.value = []
      total.value = 0
    }
  } finally {
    if (requestId === listRequestId) loading.value = false
  }
}

onMounted(async () => {
  await cityStore.initCity()
  lastCityId = currentCity.value?.id
  fetchListings(true)
})

onShow(() => {
  if (lastCityId !== undefined && currentCity.value?.id !== lastCityId) {
    lastCityId = currentCity.value?.id
    fetchListings(true)
  }
})

onReachBottom(() => {
  if (hasMore.value && !loading.value) {
    fetchListings(false)
  }
})
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-color;
  padding-bottom: 40rpx;
}

/* ── 导航栏 ── */
.nav-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: 88rpx;
  background: $surface;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1rpx 0 rgba(0, 0, 0, 0.03);
}

.nav-title {
  font-size: 34rpx;
  font-weight: 600;
  color: $text-primary;
  letter-spacing: 0.5rpx;
}

.nav-publish {
  position: absolute;
  right: 28rpx;
  top: 50%;
  transform: translateY(-50%);
  padding: 10rpx 24rpx;
  background: $gradient-primary;
  border-radius: 999rpx;
  box-shadow: $shadow-md;
}

.nav-publish-text {
  font-size: 24rpx;
  font-weight: 600;
  color: $white;
}

/* ── 筛选区 ── */
.filters {
  position: fixed;
  top: 88rpx;
  left: 0;
  right: 0;
  z-index: 90;
  background: $surface;
  border-bottom: 1rpx solid $border-soft;
}

.tab-bar {
  display: flex;
}

.tab-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 22rpx 0;
  position: relative;
}

.tab-text {
  font-size: 27rpx;
  color: $text-secondary;
  letter-spacing: 1rpx;
}

.tab-active .tab-text {
  color: $primary;
  font-weight: 600;
}

.tab-active::after {
  content: '';
  position: absolute;
  bottom: 2rpx;
  left: 50%;
  transform: translateX(-50%);
  width: 36rpx;
  height: 4rpx;
  background: $primary;
  border-radius: 2rpx;
}

.sub-filter {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 12rpx 24rpx 16rpx;
}

.city-pill {
  display: flex;
  align-items: center;
  gap: 6rpx;
  padding: 10rpx 16rpx;
  background: $primary-soft;
  border-radius: 999rpx;
  flex-shrink: 0;
}

.city-pill-icon {
  font-size: 22rpx;
  color: $primary;
}

.city-pill-text {
  font-size: 23rpx;
  font-weight: 500;
  color: $primary;
  max-width: 110rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.subject-scroll {
  flex: 1;
  min-width: 0;
  white-space: nowrap;
}

.subject-list {
  display: inline-flex;
  align-items: center;
  gap: 12rpx;
}

.subject-chip {
  padding: 8rpx 20rpx;
  background: $surface-soft;
  border: 1rpx solid $border-soft;
  border-radius: 999rpx;
  font-size: 22rpx;
  color: $text-secondary;
  white-space: nowrap;
}

.subject-chip-on {
  background: $primary-light;
  border-color: rgba(79, 110, 247, 0.3);
  color: $primary;
  font-weight: 500;
}

.sort-pill {
  display: flex;
  align-items: center;
  gap: 4rpx;
  flex-shrink: 0;
}

.sort-pill-text {
  font-size: 22rpx;
  color: $text-secondary;
}

.sort-pill-arrow {
  font-size: 18rpx;
  color: $text-muted;
}

/* ── 内容 ── */
.content {
  padding-top: 268rpx;
}

/* ── 瀑布流 ── */
.waterfall {
  display: flex;
  align-items: flex-start;
  gap: 18rpx;
  padding: 20rpx 24rpx 0;
}

.waterfall-col {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.card {
  background: $surface;
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
  transition: transform 0.18s $ease-out;
}

.card:active {
  transform: scale(0.98);
}

.card-cover {
  position: relative;
  width: 100%;
  overflow: hidden;
  background: #eef1fb;
}

.card-cover-img {
  width: 100%;
  height: 100%;
}

.card-cover-ph {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
}

.ph-tutor {
  background: linear-gradient(135deg, #E8EDFF 0%, #DCE4FF 100%);
}

.ph-training {
  background: linear-gradient(135deg, #EFEAFF 0%, #E4DCFF 100%);
}

.ph-demand {
  background: linear-gradient(135deg, #FFF3E0 0%, #FFE8CC 100%);
}

.card-ph-icon {
  font-size: 64rpx;
  opacity: 0.55;
}

.ph-tutor .card-ph-icon {
  color: $primary;
}

.ph-training .card-ph-icon {
  color: $purple;
}

.ph-demand .card-ph-icon {
  color: $orange;
}

.card-ph-subject {
  font-size: 24rpx;
  font-weight: 600;
  color: $text-secondary;
  opacity: 0.8;
}

.card-type-badge {
  position: absolute;
  top: 14rpx;
  left: 14rpx;
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
}

.badge-tutor {
  background: rgba(79, 110, 247, 0.92);
}

.badge-training {
  background: rgba(108, 92, 231, 0.92);
}

.badge-demand {
  background: rgba(255, 140, 0, 0.92);
}

.card-type-text {
  font-size: 19rpx;
  font-weight: 600;
  color: $white;
}

.card-body {
  padding: 16rpx 18rpx 18rpx;
}

.card-title {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: 26rpx;
  font-weight: 600;
  color: $text-primary;
  line-height: 1.35;
}

.card-certs {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
  margin-top: 10rpx;
}

.card-cert {
  display: flex;
  align-items: center;
  gap: 4rpx;
}

.card-cert-icon {
  font-size: 18rpx;
}

.cert-edu {
  color: $orange;
}

.cert-tea {
  color: $success;
}

.card-cert-text {
  font-size: 18rpx;
  color: $text-muted;
}

.card-area {
  display: flex;
  align-items: center;
  gap: 4rpx;
  margin-top: 10rpx;
  min-width: 0;
}

.card-area-icon {
  font-size: 18rpx;
  color: $text-muted;
  flex-shrink: 0;
}

.card-area-text {
  font-size: 19rpx;
  color: $text-muted;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8rpx;
  margin-top: 14rpx;
}

.card-publisher {
  display: flex;
  align-items: center;
  gap: 8rpx;
  min-width: 0;
  flex: 1;
}

.card-avatar {
  width: 34rpx;
  height: 34rpx;
  border-radius: 50%;
  flex-shrink: 0;
}

.card-avatar-ph {
  width: 34rpx;
  height: 34rpx;
  border-radius: 50%;
  background: $surface-soft;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.card-avatar-icon {
  font-size: 20rpx;
  color: $text-muted;
}

.card-nickname {
  font-size: 20rpx;
  color: $text-secondary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-price-wrap {
  display: flex;
  align-items: baseline;
  gap: 1rpx;
  flex-shrink: 0;
}

.card-price-symbol {
  font-size: 20rpx;
  font-weight: 700;
  color: $danger;
}

.card-price {
  font-size: 30rpx;
  font-weight: 800;
  color: $danger;
  line-height: 1;
}

.card-price-unit {
  font-size: 17rpx;
  color: $text-muted;
}

.card-price-neg {
  font-size: 24rpx;
  font-weight: 600;
  color: $danger;
  flex-shrink: 0;
}

/* ── 加载更多 ── */
.load-more {
  display: flex;
  justify-content: center;
  padding: 28rpx 0 12rpx;
}

.load-more-text {
  font-size: 22rpx;
  color: $text-muted;
}

/* ── 骨架 ── */
.skeleton-waterfall {
  display: flex;
  align-items: flex-start;
  gap: 18rpx;
  padding: 20rpx 24rpx 0;
}

.skeleton-col {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.skeleton-card {
  background: $surface;
  border-radius: 24rpx;
  overflow: hidden;
  padding-bottom: 18rpx;
  border: 1rpx solid $border-soft;
}

.skeleton-cover {
  width: 100%;
  background: linear-gradient(90deg, #F0F1F5 25%, #F7F8FA 50%, #F0F1F5 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.4s ease-in-out infinite;
}

.skeleton-line {
  height: 22rpx;
  margin: 16rpx 18rpx 0;
  border-radius: 8rpx;
  background: linear-gradient(90deg, #F0F1F5 25%, #F7F8FA 50%, #F0F1F5 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.4s ease-in-out infinite;
}

.skeleton-line.long {
  width: 80%;
}

.skeleton-line.short {
  width: 45%;
}

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── 空状态 ── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 24rpx;
  padding: 120rpx 0;
  border-radius: 24rpx;
  background: $surface;
  border: 1rpx solid $border-soft;
  box-shadow: $shadow-card;
}

.empty-icon-circle {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: $primary-soft;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 28rpx;
}

.empty-icon {
  font-size: 52rpx;
  color: $text-muted;
}

.empty-title {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-secondary;
}

.empty-subtitle {
  font-size: 23rpx;
  color: $text-muted;
  margin-top: 8rpx;
}

.empty-btn {
  margin-top: 32rpx;
  padding: 16rpx 48rpx;
  background: $gradient-primary;
  border-radius: 999rpx;
  box-shadow: $shadow-md;
}

.empty-btn-text {
  font-size: 26rpx;
  font-weight: 600;
  color: $white;
}

/* ── 动画 ── */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(16rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-in {
  animation: fadeInUp 0.42s $ease-out backwards;
}

.delay-1 { animation-delay: 0.06s; }
.delay-2 { animation-delay: 0.13s; }
.delay-3 { animation-delay: 0.2s; }
</style>
