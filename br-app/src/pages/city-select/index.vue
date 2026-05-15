<template>
  <view class="page">
    <view class="search-header">
      <view class="search-box">
        <view class="icon icon-search search-icon" />
        <input
          class="search-input"
          v-model="keyword"
          placeholder="搜索城市或省份"
          placeholder-class="search-placeholder"
          confirm-type="search"
        />
      </view>
    </view>

    <scroll-view class="content" scroll-y>
      <view v-if="loading && cities.length === 0" class="loading-state">
        <text class="loading-text">正在加载城市</text>
      </view>

      <view v-else-if="filteredCities.length === 0" class="empty-state">
        <view class="icon icon-location empty-icon" />
        <text class="empty-title">未找到该城市</text>
      </view>

      <template v-else>
        <view v-if="!keyword && hotCities.length > 0" class="section">
          <text class="section-title">热门城市</text>
          <view class="hot-grid">
            <view
              v-for="city in hotCities"
              :key="city.id"
              :class="['hot-city', { active: isCurrentCity(city) }]"
              @tap="onSelectCity(city)"
            >
              <text class="hot-city-text">{{ city.name }}</text>
            </view>
          </view>
        </view>

        <view class="section">
          <text class="section-title">{{ keyword ? '搜索结果' : '全部城市' }}</text>
          <view
            v-for="group in groupedCities"
            :key="group.province"
            class="province-group"
          >
            <text class="province-title">{{ group.province }}</text>
            <view class="city-list">
              <view
                v-for="city in group.cities"
                :key="city.id"
                :class="['city-row', { active: isCurrentCity(city) }]"
                @tap="onSelectCity(city)"
              >
                <view class="city-row-main">
                  <view v-if="isCurrentCity(city)" class="icon icon-check city-check" />
                  <text class="city-name">{{ city.name }}</text>
                </view>
                <text class="city-province">{{ city.province }}</text>
              </view>
            </view>
          </view>
        </view>
      </template>

      <view style="height: 48rpx;" />
    </scroll-view>
  </view>
</template>

<script>
import { useCityStore } from '@/store/modules/city'

export default {
  data() {
    return {
      keyword: '',
      loading: false,
    }
  },

  computed: {
    cityStore() {
      return useCityStore()
    },

    cities() {
      return this.cityStore.cities || []
    },

    currentCity() {
      return this.cityStore.currentCity
    },

    hotCities() {
      return this.cities.slice(0, 6)
    },

    filteredCities() {
      const keyword = this.keyword.trim().toLowerCase()
      if (!keyword) return this.cities
      return this.cities.filter((city) => {
        const name = String(city.name || '').toLowerCase()
        const province = String(city.province || '').toLowerCase()
        return name.includes(keyword) || province.includes(keyword)
      })
    },

    groupedCities() {
      const groups = []
      const groupMap = {}
      this.filteredCities.forEach((city) => {
        const province = city.province || '其他'
        if (!groupMap[province]) {
          groupMap[province] = { province, cities: [] }
          groups.push(groupMap[province])
        }
        groupMap[province].cities.push(city)
      })
      return groups
    },
  },

  onLoad() {
    this.ensureCities()
  },

  methods: {
    async ensureCities() {
      if (this.cities.length > 0) return
      this.loading = true
      try {
        await this.cityStore.initCity()
      } finally {
        this.loading = false
      }
    },

    isCurrentCity(city) {
      return this.currentCity?.id === city.id
    },

    onSelectCity(city) {
      if (!this.isCurrentCity(city)) {
        this.cityStore.setCity(city)
      }
      uni.navigateBack()
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-color;
}

.search-header {
  position: sticky;
  top: 0;
  z-index: 10;
  padding: 20rpx 28rpx;
  background: #fff;
  box-shadow: 0 1rpx 0 rgba(0, 0, 0, 0.04);
}

.search-box {
  display: flex;
  align-items: center;
  height: 72rpx;
  padding: 0 24rpx;
  border-radius: 36rpx;
  background: $bg-color;
}

.search-icon {
  margin-right: 12rpx;
  font-size: 28rpx;
  color: $text-muted;
}

.search-input {
  flex: 1;
  min-width: 0;
  height: 72rpx;
  font-size: 28rpx;
  color: $text-primary;
}

.search-placeholder {
  color: $text-muted;
}

.content {
  height: calc(100vh - 112rpx);
}

.section {
  padding: 30rpx 28rpx 0;
}

.section-title {
  display: block;
  margin-bottom: 20rpx;
  font-size: 30rpx;
  font-weight: 700;
  color: $text-primary;
}

.hot-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16rpx;
}

.hot-city {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 72rpx;
  border-radius: 16rpx;
  background: #fff;
  border: 1rpx solid rgba(79, 110, 247, 0.08);
  box-shadow: $shadow-sm;
}

.hot-city.active {
  background: $primary-light;
  border-color: rgba(79, 110, 247, 0.22);
}

.hot-city:active,
.city-row:active {
  transform: scale(0.98);
}

.hot-city-text {
  font-size: 26rpx;
  font-weight: 600;
  color: $text-primary;
}

.hot-city.active .hot-city-text {
  color: $primary;
}

.province-group {
  margin-bottom: 24rpx;
}

.province-title {
  display: block;
  margin-bottom: 12rpx;
  font-size: 23rpx;
  color: $text-muted;
}

.city-list {
  overflow: hidden;
  border-radius: 20rpx;
  background: #fff;
  box-shadow: $shadow-sm;
}

.city-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 88rpx;
  padding: 0 24rpx;
  border-bottom: 1rpx solid rgba(99, 110, 114, 0.08);
}

.city-row:last-child {
  border-bottom: none;
}

.city-row.active {
  background: rgba(79, 110, 247, 0.06);
}

.city-row-main {
  display: flex;
  align-items: center;
  min-width: 0;
}

.city-check {
  margin-right: 10rpx;
  font-size: 24rpx;
  color: $success;
}

.city-name {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

.city-row.active .city-name {
  color: $primary;
}

.city-province {
  margin-left: 20rpx;
  font-size: 22rpx;
  color: $text-muted;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 420rpx;
}

.loading-text {
  font-size: 26rpx;
  color: $text-muted;
}

.empty-icon {
  font-size: 56rpx;
  color: $text-muted;
}

.empty-title {
  margin-top: 18rpx;
  font-size: 28rpx;
  color: $text-secondary;
}
</style>
