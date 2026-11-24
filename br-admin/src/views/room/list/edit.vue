<template>
  <n-flex vertical>
    <!-- 顶部操作栏 -->
    <n-card :bordered="false">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <n-button text @click="goBack">
            <template #icon
              ><n-icon><ArrowLeftOutlined /></n-icon
            ></template>
          </n-button>
          <h2 class="text-lg font-semibold m-0">{{ isEdit ? '编辑学习室' : '新建学习室' }}</h2>
        </div>
        <n-space>
          <n-button @click="goBack">取消</n-button>
          <n-button type="primary" :loading="saving" @click="handleSave">
            <template #icon
              ><n-icon><SaveOutlined /></n-icon
            ></template>
            保存学习室
          </n-button>
        </n-space>
      </div>
    </n-card>

    <n-spin :show="loading">
      <div class="max-w-3xl mx-auto w-full space-y-4 py-4">
        <!-- 基本信息 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><InfoCircleOutlined /></n-icon>
              <span class="text-sm font-bold">基本信息</span>
            </div>
          </template>
          <n-form :model="formValues" :rules="rules" ref="formRef" label-placement="top">
            <n-grid :cols="2" :x-gap="16">
              <n-form-item-gi :span="2" label="名称" path="name">
                <n-input
                  v-model:value="formValues.name"
                  placeholder="请输入学习室名称"
                  :maxlength="100"
                  show-count
                />
              </n-form-item-gi>
              <n-form-item-gi :span="2" label="地址" path="address">
                <n-input
                  :value="formValues.address"
                  placeholder="请输入详细地址"
                  :maxlength="255"
                  show-count
                  @update:value="handleAddressChange"
                />
              </n-form-item-gi>
              <n-form-item-gi label="所在城市" path="city_id">
                <n-select
                  v-model:value="formValues.city_id"
                  :options="cityOptions"
                  placeholder="请选择所在城市"
                  clearable
                />
              </n-form-item-gi>
              <n-form-item-gi label="类型" path="room_type">
                <n-select v-model:value="formValues.room_type" :options="roomTypeOptions" />
              </n-form-item-gi>
              <n-form-item-gi label="营业时间" path="business_hours" :show-feedback="false">
                <n-input
                  v-model:value="formValues.business_hours"
                  placeholder="如 08:00-22:00"
                  :maxlength="50"
                />
              </n-form-item-gi>
              <n-form-item-gi label="最低价格" path="min_price" :show-feedback="false">
                <n-input-number
                  v-model:value="formValues.min_price"
                  :min="0"
                  :precision="2"
                  style="width: 100%"
                />
              </n-form-item-gi>
            </n-grid>
          </n-form>
        </n-card>

        <!-- 地址定位 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><EnvironmentOutlined /></n-icon>
              <span class="text-sm font-bold">地址定位</span>
            </div>
          </template>
          <n-space vertical :size="12">
            <div class="flex items-center gap-3 flex-wrap">
              <n-button v-if="mapKeyConfigured" secondary type="primary" @click="toggleMapPicker">
                {{ showMapPicker ? '收起地图' : '在地图上选点' }}
              </n-button>
              <n-text v-if="hasCoordinates" depth="3" class="text-xs">
                已选：{{ formValues.latitude?.toFixed(6) }},
                {{ formValues.longitude?.toFixed(6) }}
              </n-text>
              <n-text v-else depth="3" class="text-xs"> 未选点；保存时将按地址自动解析坐标 </n-text>
              <n-button
                v-if="hasCoordinates"
                text
                type="error"
                size="small"
                @click="clearCoordinates"
              >
                清除坐标
              </n-button>
            </div>
            <n-text v-if="!mapKeyConfigured" depth="3" class="text-xs">
              未配置 VITE_TENCENT_MAP_KEY，地图选点不可用；可只填写地址，由后端自动解析。
            </n-text>
            <div v-if="mapKeyConfigured && showMapPicker" class="map-picker">
              <div class="map-picker-search">
                <n-input
                  v-model:value="mapKeyword"
                  placeholder="搜索地点（可选）"
                  clearable
                  @keyup.enter="handleMapSearch"
                />
                <n-button secondary type="primary" :loading="mapSearching" @click="handleMapSearch">
                  搜索
                </n-button>
              </div>
              <div v-if="mapSearchResults.length" class="map-picker-results">
                <button
                  v-for="(item, index) in mapSearchResults"
                  :key="`${item.title}-${index}`"
                  type="button"
                  class="map-picker-result"
                  @click="selectSearchResult(item)"
                >
                  <span class="map-picker-result-title">{{ item.title }}</span>
                  <span class="map-picker-result-address">{{ item.address }}</span>
                </button>
              </div>
              <div ref="mapContainer" class="map-picker-canvas" />
              <n-text v-if="mapStatusText" depth="3" class="text-xs">
                {{ mapStatusText }}
              </n-text>
              <n-text v-if="searchHint" type="warning" class="text-xs">
                {{ searchHint }}
              </n-text>
            </div>
          </n-space>
        </n-card>

        <!-- 封面图片 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><PictureOutlined /></n-icon>
              <span class="text-sm font-bold">封面图片</span>
            </div>
          </template>
          <div class="flex items-start gap-4">
            <div
              class="w-40 h-28 rounded-lg overflow-hidden border border-gray-200 flex-shrink-0 flex items-center justify-center bg-gray-50"
            >
              <n-image
                v-if="formValues.cover_image"
                :src="formValues.cover_image"
                width="160"
                height="112"
                object-fit="cover"
                preview-disabled
              />
              <n-text v-else depth="3" class="text-xs">暂无封面</n-text>
            </div>
            <div class="flex-1">
              <n-upload
                :max="1"
                accept="image/*"
                :custom-request="handleCoverUpload"
                :show-file-list="false"
              >
                <n-button secondary type="info">上传图片</n-button>
              </n-upload>
              <n-text depth="3" class="text-xs mt-2 block"
                >建议尺寸 750×420px，支持 JPG/PNG 格式，最大 2MB</n-text
              >
            </div>
          </div>
        </n-card>

        <!-- 环境图片 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><FileImageOutlined /></n-icon>
              <span class="text-sm font-bold">环境图片</span>
            </div>
          </template>
          <div class="flex flex-wrap gap-3">
            <div v-for="(image, index) in environmentImages" :key="image" class="env-image-item">
              <n-image :src="image" width="120" height="90" object-fit="cover" preview-disabled />
              <n-button
                class="env-image-remove"
                size="tiny"
                quaternary
                circle
                @click="removeEnvironmentImage(index)"
              >
                <template #icon
                  ><n-icon><CloseOutlined /></n-icon
                ></template>
              </n-button>
            </div>
            <n-upload
              v-if="environmentImages.length < 5"
              :max="1"
              accept="image/*"
              :custom-request="handleEnvironmentUpload"
              :show-file-list="false"
            >
              <div class="env-image-add">
                <n-icon size="20"><PlusOutlined /></n-icon>
                <n-text depth="3" class="text-xs">上传图片</n-text>
              </div>
            </n-upload>
          </div>
          <n-text depth="3" class="text-xs mt-3 block"
            >最多上传 5 张环境图片，当前 {{ environmentImages.length }}/5</n-text
          >
        </n-card>

        <!-- 简介 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><AlignLeftOutlined /></n-icon>
              <span class="text-sm font-bold">简介</span>
            </div>
          </template>
          <n-input
            v-model:value="formValues.description"
            type="textarea"
            placeholder="请输入学习室简介"
            :maxlength="1000"
            show-count
            :rows="4"
          />
        </n-card>

        <!-- 发布设置 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><SettingOutlined /></n-icon>
              <span class="text-sm font-bold">发布设置</span>
            </div>
          </template>
          <div class="flex items-center gap-2">
            <n-switch :value="isPublished" @update:value="handlePublishChange" />
            <n-text depth="3" class="text-xs">{{ isPublished ? '已上架' : '已下架' }}</n-text>
          </div>
        </n-card>
      </div>
    </n-spin>
  </n-flex>
</template>

<script lang="ts" setup>
  import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import type { FormInst, FormRules, UploadFileInfo } from 'naive-ui';
  import {
    ArrowLeftOutlined,
    SaveOutlined,
    InfoCircleOutlined,
    PictureOutlined,
    FileImageOutlined,
    AlignLeftOutlined,
    SettingOutlined,
    CloseOutlined,
    PlusOutlined,
    EnvironmentOutlined,
  } from '@vicons/antd';
  import {
    createRoom,
    getCityList,
    getRoomById,
    reverseRoomGeocode,
    suggestRoomLocations,
    updateRoom,
    type CityItem,
    type RoomMapSuggestion,
    type RoomType,
  } from '@/api/room';
  import { uploadImage } from '@/api/upload';
  import { useTabsViewStore } from '@/store/modules/tabsView';

  interface RoomFormValues {
    name: string;
    address: string;
    latitude: number | null;
    longitude: number | null;
    description: string;
    cover_image: string;
    business_hours: string;
    city_id: number | null;
    room_type: RoomType;
    min_price: number;
  }

  const route = useRoute();
  const router = useRouter();
  const tabsViewStore = useTabsViewStore();
  const roomId = computed(() => {
    const id = route.params.id;
    return id ? Number(id) : null;
  });
  const isEdit = computed(() => roomId.value !== null);

  const formRef = ref<FormInst | null>(null);
  const loading = ref(false);
  const saving = ref(false);

  const cityOptions = ref<{ label: string; value: number }[]>([]);
  const roomTypeOptions = [
    { label: '学习室', value: 'study' },
    { label: '培训室', value: 'training' },
    { label: '综合室', value: 'comprehensive' },
  ];

  const formValues = reactive<RoomFormValues>({
    name: '',
    address: '',
    latitude: null,
    longitude: null,
    description: '',
    cover_image: '',
    business_hours: '',
    city_id: null,
    room_type: 'study',
    min_price: 0,
  });
  const environmentImages = ref<string[]>([]);
  const isPublished = ref(true);

  const TENCENT_MAP_KEY = String(import.meta.env.VITE_TENCENT_MAP_KEY || '').trim();
  const mapKeyConfigured = computed(() => Boolean(TENCENT_MAP_KEY));
  const showMapPicker = ref(false);
  const hasCoordinates = computed(
    () => formValues.latitude !== null && formValues.longitude !== null
  );
  const DEFAULT_MAP_CENTER = { latitude: 23.1291, longitude: 113.2644 };
  const MARKER_SRC =
    'data:image/svg+xml;charset=UTF-8,' +
    encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" width="25" height="35" viewBox="0 0 25 35"><path fill="#4F6EF7" d="M12.5 0C5.6 0 0 5.6 0 12.5 0 21.9 12.5 35 12.5 35S25 21.9 25 12.5C25 5.6 19.4 0 12.5 0z"/><circle cx="12.5" cy="12.5" r="4.5" fill="#fff"/></svg>'
    );
  const mapContainer = ref<HTMLDivElement | null>(null);
  const mapKeyword = ref('');
  const mapSearchResults = ref<RoomMapSuggestion[]>([]);
  const mapSearching = ref(false);
  const mapStatusText = ref('');
  const searchHint = ref('');
  let mapSdkPromise: Promise<any> | null = null;
  let mapInstance: any = null;
  let markerInstance: any = null;

  const rules: FormRules = {
    name: { required: true, message: '请输入名称', trigger: ['blur', 'input'] },
    address: { required: true, message: '请输入地址', trigger: ['blur', 'input'] },
  };

  onMounted(async () => {
    // 进入编辑页时移除列表 tab，让编辑页接管标签位置
    removeTab((t) => t.name === 'room_list');
    await loadCityOptions();
    if (roomId.value) {
      await loadRoom(roomId.value);
    }
  });

  onBeforeUnmount(() => {
    destroyMap();
  });

  // 安全移除匹配的标签页（仅 splice，不影响导航主流程）
  function removeTab(matcher: (t: any) => boolean) {
    try {
      const idx = tabsViewStore.tabsList.findIndex(matcher);
      if (idx > -1) {
        tabsViewStore.tabsList.splice(idx, 1);
      }
    } catch {
      // 标签清理失败不阻断页面逻辑
    }
  }

  // 返回列表页（参考座位管理 router.back 实现）
  function backToList() {
    // 关闭当前编辑页 tab，返回后标签栏恢复为列表页
    removeTab((t) => t.fullPath === route.fullPath);
    if (window.history.state && window.history.state.back) {
      router.back();
    } else {
      router.push({ name: 'room_list' });
    }
  }

  async function loadCityOptions() {
    try {
      const cities: CityItem[] = await getCityList();
      cityOptions.value = cities.map((city) => ({ label: city.name, value: city.id }));
    } catch {
      // 城市加载失败不阻断编辑
    }
  }

  async function loadRoom(id: number) {
    loading.value = true;
    try {
      const detail = await getRoomById(id);
      formValues.name = detail.name;
      formValues.address = detail.address;
      formValues.latitude = detail.latitude ?? null;
      formValues.longitude = detail.longitude ?? null;
      formValues.description = detail.description ?? '';
      formValues.cover_image = detail.cover_image ?? '';
      formValues.business_hours = detail.business_hours ?? '';
      formValues.city_id = detail.city_id;
      formValues.room_type = detail.room_type;
      formValues.min_price = Number(detail.min_price ?? 0);
      environmentImages.value = [...(detail.environment_images ?? [])];
      isPublished.value = detail.status === 'open';
    } catch (error) {
      window['$message']?.error(getReadableError(error, '学习室详情加载失败，请稍后重试'));
    } finally {
      loading.value = false;
    }
  }

  // 封面上传
  async function handleCoverUpload({
    file,
    onFinish,
    onError,
  }: {
    file: UploadFileInfo;
    onFinish: () => void;
    onError: () => void;
  }) {
    if (!file.file) {
      onError();
      return;
    }
    try {
      const result = await uploadImage(file.file, 'room-cover');
      formValues.cover_image = result.url;
      onFinish();
    } catch {
      onError();
      window['$message']?.error('上传失败');
    }
  }

  // 环境图片上传
  async function handleEnvironmentUpload({
    file,
    onFinish,
    onError,
  }: {
    file: UploadFileInfo;
    onFinish: () => void;
    onError: () => void;
  }) {
    if (!file.file) {
      onError();
      return;
    }
    if (environmentImages.value.length >= 5) {
      onError();
      window['$message']?.warning('最多上传 5 张环境图片');
      return;
    }
    try {
      const result = await uploadImage(file.file, 'room-environment');
      environmentImages.value.push(result.url);
      onFinish();
    } catch {
      onError();
      window['$message']?.error('上传失败');
    }
  }

  function removeEnvironmentImage(index: number) {
    environmentImages.value.splice(index, 1);
  }

  // 手动修改地址后旧坐标失效，交由保存时的地理编码重新解析
  function handleAddressChange(value: string) {
    formValues.address = value;
    formValues.latitude = null;
    formValues.longitude = null;
  }

  function clearCoordinates() {
    formValues.latitude = null;
    formValues.longitude = null;
    markerInstance?.setGeometries?.([]);
  }

  function loadMapSdk(): Promise<any> {
    const existing = (window as any).TMap;
    if (existing) {
      return Promise.resolve(existing);
    }
    if (!mapSdkPromise) {
      mapSdkPromise = new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = `https://map.qq.com/api/gljs?v=1.exp&libraries=service&key=${encodeURIComponent(
          TENCENT_MAP_KEY
        )}`;
        script.async = true;
        script.onload = () => {
          const sdk = (window as any).TMap;
          if (sdk) {
            resolve(sdk);
          } else {
            reject(new Error('腾讯地图 SDK 加载异常'));
          }
        };
        script.onerror = () => reject(new Error('腾讯地图 SDK 加载失败'));
        document.head.appendChild(script);
      }).catch((error) => {
        mapSdkPromise = null;
        throw error;
      });
    }
    return mapSdkPromise;
  }

  function toggleMapPicker() {
    showMapPicker.value = !showMapPicker.value;
    if (showMapPicker.value) {
      nextTick(() => initMap());
    } else {
      destroyMap();
    }
  }

  async function initMap() {
    if (!mapContainer.value || mapInstance) {
      return;
    }
    mapStatusText.value = '地图加载中…';
    try {
      const sdk = await loadMapSdk();
      const el = mapContainer.value;
      // 等一帧再建图，确保 v-if 插入的容器已完成布局
      await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));
      if (!el || !el.clientWidth || !el.clientHeight) {
        mapStatusText.value = '地图容器尺寸异常，请收起后重新展开地图';
        return;
      }
      const center = hasCoordinates.value
        ? new sdk.LatLng(Number(formValues.latitude), Number(formValues.longitude))
        : new sdk.LatLng(DEFAULT_MAP_CENTER.latitude, DEFAULT_MAP_CENTER.longitude);
      mapInstance = new sdk.Map(el, {
        center,
        zoom: hasCoordinates.value ? 16 : 12,
        viewMode: '2D',
      });
      try {
        markerInstance = new sdk.MultiMarker({
          map: mapInstance,
          styles: {
            marker: new sdk.MarkerStyle({
              width: 25,
              height: 35,
              anchor: { x: 16, y: 32 },
              src: MARKER_SRC,
            }),
          },
          geometries: hasCoordinates.value
            ? [
                {
                  id: 'target',
                  styleId: 'marker',
                  position: new sdk.LatLng(
                    Number(formValues.latitude),
                    Number(formValues.longitude)
                  ),
                },
              ]
            : [],
        });
      } catch {
        // 标记失败不影响选点，坐标仍可正常回填
      }
      mapInstance.on('click', (event: any) => {
        const latitude = Number(event?.latLng?.getLat?.() ?? event?.latLng?.lat);
        const longitude = Number(event?.latLng?.getLng?.() ?? event?.latLng?.lng);
        if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
          return;
        }
        applyMapCoordinates(latitude, longitude);
        mapStatusText.value = '已选坐标，可继续点击地图微调';
        void reverseGeocode(latitude, longitude);
      });
      mapStatusText.value = hasCoordinates.value
        ? '点击地图可重新选点'
        : '点击地图任意位置即可选点';
      window.setTimeout(() => {
        if (mapInstance && mapContainer.value && !mapContainer.value.querySelector('canvas')) {
          mapStatusText.value =
            '地图未能渲染，请确认该 Key 已开通「Web端(JS API)」并配置正确的域名白名单';
        }
      }, 3000);
    } catch (error) {
      const detail = error instanceof Error ? error.message : '';
      destroyMap();
      mapStatusText.value = `地图加载失败：${detail || '请检查 VITE_TENCENT_MAP_KEY 与网络'}`;
    }
  }

  function applyMapCoordinates(latitude: number, longitude: number) {
    formValues.latitude = latitude;
    formValues.longitude = longitude;
    const sdk = (window as any).TMap;
    if (sdk && markerInstance) {
      markerInstance.updateGeometries([
        { id: 'target', styleId: 'marker', position: new sdk.LatLng(latitude, longitude) },
      ]);
    }
  }

  // 逆地址解析走服务端，避免浏览器端 WebServiceAPI 鉴权受限
  // key 按域名白名单鉴权时浏览器直连可用；按授权 IP 鉴权时只有服务端请求可用
  async function resolveAddress(latitude: number, longitude: number): Promise<string | null> {
    const sdk = (window as any).TMap;
    if (sdk?.service?.Geocoder) {
      try {
        const result = await new sdk.service.Geocoder().getAddress({
          location: new sdk.LatLng(latitude, longitude),
        });
        if (result?.status === 0) {
          const address =
            result?.result?.formatted_addresses?.recommend || result?.result?.address;
          if (address) {
            return String(address);
          }
        }
      } catch {
        // 浏览器直连被拒绝时退回服务端转发
      }
    }
    try {
      const result = await reverseRoomGeocode(latitude, longitude);
      return result?.address || null;
    } catch {
      return null;
    }
  }

  async function reverseGeocode(latitude: number, longitude: number) {
    const address = await resolveAddress(latitude, longitude);
    if (address) {
      formValues.address = address;
    } else {
      mapStatusText.value = '已选坐标；未能解析地址，可手动填写';
    }
  }

  function describeMapError(status?: number, message?: string) {
    if (status === 120 || status === 121) {
      return '该 Key 今日调用量已达上限，可点击地图选点或稍后再试';
    }
    if (status === 199) {
      return '该 Key 未开启 WebServiceAPI';
    }
    if (status === 110 || status === 111 || status === 112 || status === 113) {
      return '该 Key 未授权此服务或来源，请检查腾讯位置服务的服务勾选与鉴权方式';
    }
    return message || '';
  }

  async function searchPlaces(
    keyword: string
  ): Promise<{ items: RoomMapSuggestion[]; error: string }> {
    const sdk = (window as any).TMap;
    let sdkError = '';
    if (sdk?.service?.Suggestion) {
      try {
        const result = await new sdk.service.Suggestion({ pageSize: 10 }).getSuggestions({
          keyword,
        });
        if (result?.status === 0) {
          const items = (result?.data || [])
            .map((item: any) => ({
              title: String(item.title || ''),
              address: String(item.address || ''),
              latitude: Number(item.location?.lat),
              longitude: Number(item.location?.lng),
            }))
            .filter(
              (item: RoomMapSuggestion) =>
                item.title && Number.isFinite(item.latitude) && Number.isFinite(item.longitude)
            );
          return { items, error: '' };
        }
        sdkError = describeMapError(result?.status, result?.message);
      } catch (error: any) {
        // 浏览器直连被拒绝时退回服务端转发
        sdkError = describeMapError(error?.status, error?.message);
      }
    }
    try {
      const result = await suggestRoomLocations(keyword);
      const items = result?.items || [];
      return { items, error: items.length ? '' : sdkError };
    } catch {
      return { items: [], error: sdkError || '搜索服务暂不可用' };
    }
  }

  async function handleMapSearch() {
    const keyword = mapKeyword.value.trim();
    if (!keyword) {
      return;
    }
    mapSearching.value = true;
    mapSearchResults.value = [];
    searchHint.value = '';
    try {
      const { items, error } = await searchPlaces(keyword);
      mapSearchResults.value = items;
      if (!items.length) {
        searchHint.value = error ? `搜索失败：${error}` : '未找到匹配地点，可直接点击地图选点';
      }
    } finally {
      mapSearching.value = false;
    }
  }

  function selectSearchResult(item: RoomMapSuggestion) {
    const sdk = (window as any).TMap;
    mapSearchResults.value = [];
    mapKeyword.value = item.title;
    applyMapCoordinates(item.latitude, item.longitude);
    if (sdk) {
      mapInstance?.setCenter?.(new sdk.LatLng(item.latitude, item.longitude));
      mapInstance?.setZoom?.(16);
    }
    if (item.address || item.title) {
      formValues.address = item.address || item.title;
    }
    mapStatusText.value = '已选择搜索结果，可继续点击地图微调';
  }

  function destroyMap() {
    try {
      markerInstance?.setMap?.(null);
      markerInstance?.destroy?.();
      mapInstance?.destroy?.();
    } catch {
      // 忽略地图销毁异常
    }
    mapInstance = null;
    markerInstance = null;
    mapSearchResults.value = [];
    mapStatusText.value = '';
    searchHint.value = '';
  }

  function handlePublishChange(value: boolean) {
    isPublished.value = value;
  }

  // 保存学习室
  async function handleSave() {
    try {
      await formRef.value?.validate();
    } catch {
      window['$message']?.warning('请检查必填项');
      return;
    }

    saving.value = true;
    let saved = false;
    try {
      const payload = {
        name: formValues.name,
        address: formValues.address,
        latitude: formValues.latitude,
        longitude: formValues.longitude,
        description: formValues.description || '',
        cover_image: formValues.cover_image || '',
        environment_images: environmentImages.value,
        business_hours: formValues.business_hours || '',
        city_id: formValues.city_id,
        room_type: formValues.room_type,
        min_price: formValues.min_price,
        status: isPublished.value ? 'open' : 'closed',
      };
      if (roomId.value) {
        await updateRoom(roomId.value, payload);
        window['$message']?.success('学习室更新成功');
        saved = true;
      } else {
        await createRoom(payload);
        window['$message']?.success('学习室创建成功');
        saved = true;
      }
    } catch (error) {
      window['$message']?.error(getReadableError(error, '保存失败，请检查填写内容'));
    } finally {
      saving.value = false;
    }
    // 保存成功后返回列表页
    if (saved) {
      backToList();
    }
  }

  function getReadableError(error: unknown, fallback: string) {
    if (error instanceof Error && error.message) {
      return error.message;
    }
    return fallback;
  }

  function goBack() {
    backToList();
  }
</script>

<style scoped lang="less">
  .map-picker {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .map-picker-search {
    display: flex;
    gap: 8px;
  }

  .map-picker-results {
    max-height: 180px;
    overflow-y: auto;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
  }

  .map-picker-result {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
    width: 100%;
    padding: 8px 12px;
    border: 0;
    border-bottom: 1px solid #f3f4f6;
    background: #fff;
    text-align: left;
    cursor: pointer;

    &:last-child {
      border-bottom: 0;
    }

    &:hover {
      background: #f5f7ff;
    }
  }

  .map-picker-result-title {
    font-size: 13px;
    color: #111827;
  }

  .map-picker-result-address {
    font-size: 12px;
    color: #9ca3af;
  }

  .map-picker-canvas {
    width: 100%;
    height: 420px;
    border-radius: 0.5rem;
    overflow: hidden;
  }

  .env-image-item {
    position: relative;
    width: 120px;
    height: 90px;
    border-radius: 0.5rem;
    overflow: hidden;
    border: 1px solid #e5e7eb;
  }

  .env-image-remove {
    position: absolute;
    top: 2px;
    right: 2px;
    background: rgba(0, 0, 0, 0.45);
    color: #fff;
  }

  .env-image-add {
    width: 120px;
    height: 90px;
    border: 1px dashed #d1d5db;
    border-radius: 0.5rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
    cursor: pointer;

    &:hover {
      border-color: #4f6ef7;
    }
  }

  .flex {
    display: flex;
  }
  .flex-wrap {
    flex-wrap: wrap;
  }
  .items-center {
    align-items: center;
  }
  .items-start {
    align-items: flex-start;
  }
  .justify-center {
    justify-content: center;
  }
  .justify-between {
    justify-content: space-between;
  }
  .gap-2 {
    gap: 0.5rem;
  }
  .gap-3 {
    gap: 0.75rem;
  }
  .gap-4 {
    gap: 1rem;
  }
  .space-y-4 > * + * {
    margin-top: 1rem;
  }
  .w-full {
    width: 100%;
  }
  .w-40 {
    width: 10rem;
  }
  .h-28 {
    height: 7rem;
  }
  .max-w-3xl {
    max-width: 48rem;
  }
  .mx-auto {
    margin-left: auto;
    margin-right: auto;
  }
  .py-4 {
    padding-top: 1rem;
    padding-bottom: 1rem;
  }
  .mt-3 {
    margin-top: 0.75rem;
  }
  .mt-2 {
    margin-top: 0.5rem;
  }
  .m-0 {
    margin: 0;
  }
  .block {
    display: block;
  }
  .text-xs {
    font-size: 0.75rem;
  }
  .text-sm {
    font-size: 0.875rem;
  }
  .text-lg {
    font-size: 1.125rem;
  }
  .font-semibold {
    font-weight: 600;
  }
  .font-bold {
    font-weight: 700;
  }
  .rounded-lg {
    border-radius: 0.5rem;
  }
  .overflow-hidden {
    overflow: hidden;
  }
  .flex-shrink-0 {
    flex-shrink: 0;
  }
  .flex-1 {
    flex: 1 1 0%;
  }
  .border {
    border-width: 1px;
    border-style: solid;
  }
  .border-gray-200 {
    border-color: #e5e7eb;
  }
  .bg-gray-50 {
    background-color: #f9fafb;
  }
  .shadow-sm {
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  }
</style>
