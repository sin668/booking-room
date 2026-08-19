<template>
  <n-flex vertical>
    <!-- 顶部操作栏 -->
    <n-card :bordered="false">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <n-button text @click="goBack">
            <template #icon><n-icon><ArrowLeftOutlined /></n-icon></template>
          </n-button>
          <h2 class="text-lg font-semibold m-0">{{ isEdit ? '编辑老师' : '新增老师' }}</h2>
        </div>
        <n-space>
          <n-button @click="goBack">取消</n-button>
          <n-button type="primary" :loading="saving" @click="handleSave">
            <template #icon><n-icon><SaveOutlined /></n-icon></template>
            保存老师
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
              <n-form-item-gi label="老师姓名" path="name">
                <n-input v-model:value="formValues.name" placeholder="请输入老师姓名" :maxlength="50" show-count />
              </n-form-item-gi>
              <n-form-item-gi label="头衔称号" path="title">
                <n-input v-model:value="formValues.title" placeholder="如：金牌讲师" :maxlength="50" />
              </n-form-item-gi>
              <n-form-item-gi label="专业方向" path="specialty">
                <n-input v-model:value="formValues.specialty" placeholder="如：考研政治" :maxlength="50" />
              </n-form-item-gi>
              <n-form-item-gi label="教龄（年）" path="teaching_years">
                <n-input-number v-model:value="formValues.teaching_years" :min="0" :max="100" style="width: 100%" />
              </n-form-item-gi>
              <n-form-item-gi label="学历" path="education">
                <n-select
                  v-model:value="formValues.education"
                  placeholder="请选择学历"
                  :options="EDUCATION_OPTIONS"
                  clearable
                />
              </n-form-item-gi>
              <n-form-item-gi label="毕业院校" path="school">
                <n-input v-model:value="formValues.school" placeholder="请输入毕业院校" :maxlength="100" />
              </n-form-item-gi>
              <n-form-item-gi :span="2" label="所属房间（可多选培训室/综合室）" path="room_ids">
                <n-select
                  v-model:value="formValues.room_ids"
                  placeholder="请选择所属培训室或综合室"
                  :options="roomOptions"
                  :loading="roomLoading"
                  multiple
                  filterable
                  clearable
                />
              </n-form-item-gi>
            </n-grid>
          </n-form>
        </n-card>

        <!-- 老师头像 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><PictureOutlined /></n-icon>
              <span class="text-sm font-bold">老师头像</span>
            </div>
          </template>
          <div class="flex items-start gap-4">
            <div class="w-24 h-24 rounded-full overflow-hidden border border-gray-200 flex-shrink-0 flex items-center justify-center bg-gray-50">
              <n-image
                v-if="formValues.avatar"
                :src="formValues.avatar"
                width="96"
                height="96"
                object-fit="cover"
                preview-disabled
              />
              <n-text v-else depth="3" class="text-xs">暂无头像</n-text>
            </div>
            <div class="flex-1">
              <n-upload :max="1" accept="image/*" :custom-request="handleUpload" :show-file-list="false">
                <n-button secondary type="info">上传头像</n-button>
              </n-upload>
              <n-text depth="3" class="text-xs mt-2 block">建议尺寸 200×200px，支持 JPG/PNG 格式，最大 2MB</n-text>
            </div>
          </div>
        </n-card>

        <!-- 个人简介 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><AlignLeftOutlined /></n-icon>
              <span class="text-sm font-bold">个人简介</span>
            </div>
          </template>
          <n-form-item label="简介内容" :show-feedback="false">
            <n-input
              v-model:value="formValues.bio"
              type="textarea"
              placeholder="请输入老师个人简介..."
              :rows="4"
              :maxlength="1000"
              show-count
            />
          </n-form-item>
          <n-divider class="my-3" />
          <div>
            <n-text depth="3" class="text-xs">教学特色标签（最多5个）</n-text>
            <div class="flex flex-wrap gap-2 mt-2">
              <n-tag
                v-for="(tag, index) in tagList"
                :key="index"
                closable
                type="info"
                round
                size="small"
                @close="removeTag(index)"
              >
                {{ tag }}
              </n-tag>
              <n-tag
                v-if="tagList.length < 5"
                round
                size="small"
                class="cursor-pointer border-dashed"
                @click="showTagInput = true"
              >
                + 添加标签
              </n-tag>
            </div>
            <n-modal v-model:show="showTagInput" preset="dialog" title="添加标签" :show-icon="false" style="width: 360px">
              <n-input v-model:value="newTag" placeholder="请输入标签名称" :maxlength="20" @keyup.enter="addTag" />
              <template #action>
                <n-space>
                  <n-button @click="showTagInput = false">取消</n-button>
                  <n-button type="primary" @click="addTag">确定</n-button>
                </n-space>
              </template>
            </n-modal>
          </div>
        </n-card>

        <!-- 资质认证 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><SafetyCertificateOutlined /></n-icon>
              <span class="text-sm font-bold">资质认证</span>
            </div>
          </template>
          <div class="space-y-2">
            <div
              v-for="(item, index) in qualifications"
              :key="index"
              class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
            >
              <n-input
                v-model:value="item.name"
                placeholder="资质名称，如：高级中学教师资格证"
                class="flex-1"
                :maxlength="100"
              />
              <n-input
                v-model:value="item.sub"
                placeholder="补充说明（选填）"
                class="flex-1"
                :maxlength="100"
              />
              <n-button size="tiny" quaternary type="error" style="display: inline-flex" @click="removeQualification(index)">
                <template #icon><n-icon><DeleteOutlined /></n-icon></template>
              </n-button>
            </div>
            <n-button dashed block @click="addQualification">
              <template #icon><n-icon><PlusOutlined /></n-icon></template>
              添加资质认证
            </n-button>
          </div>
        </n-card>
      </div>
    </n-spin>
  </n-flex>
</template>

<script lang="ts" setup>
  import { computed, onMounted, reactive, ref } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import type { FormInst, FormRules, UploadFileInfo } from 'naive-ui';
  import {
    ArrowLeftOutlined,
    SaveOutlined,
    InfoCircleOutlined,
    PictureOutlined,
    AlignLeftOutlined,
    PlusOutlined,
    DeleteOutlined,
    SafetyCertificateOutlined,
  } from '@vicons/antd';
  import {
    getAdminTeacherById,
    createAdminTeacher,
    updateAdminTeacher,
    type QualificationItem,
  } from '@/api/teacher';
  import { getRoomList, type RoomItem } from '@/api/room';
  import { uploadImage } from '@/api/upload';
  import { EDUCATION_OPTIONS, ROOM_TYPE_LABELS } from './options';
  import { useTabsViewStore } from '@/store/modules/tabsView';

  interface QualificationDraft {
    name: string;
    sub: string;
  }

  const route = useRoute();
  const router = useRouter();
  const tabsViewStore = useTabsViewStore();
  const teacherId = computed(() => {
    const id = route.params.id;
    return id ? Number(id) : null;
  });
  const isEdit = computed(() => teacherId.value !== null);

  const formRef = ref<FormInst | null>(null);
  const loading = ref(false);
  const saving = ref(false);

  const formValues = reactive({
    name: '',
    title: '',
    specialty: '',
    teaching_years: 0,
    education: null as string | null,
    school: '',
    avatar: '',
    bio: '',
    room_ids: [] as number[],
  });

  const rules: FormRules = {
    name: { required: true, message: '请输入老师姓名', trigger: 'blur' },
  };

  // 所属房间选项（仅培训室/综合室）
  const roomOptions = ref<{ label: string; value: number }[]>([]);
  const roomLoading = ref(false);

  // 教学特色标签
  const tagList = ref<string[]>([]);
  const showTagInput = ref(false);
  const newTag = ref('');

  // 资质认证
  const qualifications = ref<QualificationDraft[]>([]);

  onMounted(async () => {
    // 进入编辑页时移除列表 tab，让编辑页接管标签位置
    removeTab((t) => t.name === 'training_teachers');
    await loadRooms();
    if (teacherId.value) {
      await loadTeacher(teacherId.value);
    }
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

  // 返回列表页（参考课程编辑页实现）
  function backToList() {
    removeTab((t) => t.fullPath === route.fullPath);
    if (window.history.state && window.history.state.back) {
      router.back();
    } else {
      router.push({ name: 'training_teachers' });
    }
  }

  async function loadRooms() {
    roomLoading.value = true;
    try {
      const result = await getRoomList({ page: 1, page_size: 100 });
      roomOptions.value = result.items
        .filter((r: RoomItem) => r.room_type === 'training' || r.room_type === 'comprehensive')
        .map((r: RoomItem) => ({
          label: `${r.name}（${ROOM_TYPE_LABELS[r.room_type] || r.room_type}）`,
          value: r.id,
        }));
    } catch {
      window['$message']?.error('加载房间列表失败');
    } finally {
      roomLoading.value = false;
    }
  }

  async function loadTeacher(id: number) {
    loading.value = true;
    try {
      const detail = await getAdminTeacherById(id);
      formValues.name = detail.name;
      formValues.title = detail.title || '';
      formValues.specialty = detail.specialty || '';
      formValues.teaching_years = detail.teaching_years || 0;
      formValues.education = detail.education || null;
      formValues.school = detail.school || '';
      formValues.avatar = detail.avatar || '';
      formValues.bio = detail.bio || '';
      formValues.room_ids = detail.room_ids || [];

      tagList.value = detail.teaching_tags || [];
      qualifications.value = (detail.qualifications || []).map((q: QualificationItem) => ({
        name: q.name,
        sub: q.sub || '',
      }));
    } catch {
      window['$message']?.error('加载老师信息失败');
    } finally {
      loading.value = false;
    }
  }

  // 标签操作
  function addTag() {
    const tag = newTag.value.trim();
    if (tag && tagList.value.length < 5 && !tagList.value.includes(tag)) {
      tagList.value.push(tag);
      newTag.value = '';
      showTagInput.value = false;
    }
  }

  function removeTag(index: number) {
    tagList.value.splice(index, 1);
  }

  // 资质认证操作
  function addQualification() {
    qualifications.value.push({ name: '', sub: '' });
  }

  function removeQualification(index: number) {
    qualifications.value.splice(index, 1);
  }

  // 头像上传
  async function handleUpload({
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
      const result = await uploadImage(file.file, 'teacher-avatar');
      formValues.avatar = result.url;
      onFinish();
    } catch {
      onError();
      window['$message']?.error('上传失败');
    }
  }

  // 保存老师
  async function handleSave() {
    try {
      await formRef.value?.validate();
    } catch {
      window['$message']?.warning('请检查必填项');
      return;
    }

    const validQualifications = qualifications.value
      .filter((q) => q.name.trim())
      .map((q) => ({ name: q.name.trim(), sub: q.sub.trim() || null }));

    const payload = {
      name: formValues.name,
      title: formValues.title || null,
      specialty: formValues.specialty || null,
      teaching_years: formValues.teaching_years || 0,
      education: formValues.education || null,
      school: formValues.school || null,
      avatar: formValues.avatar || null,
      bio: formValues.bio || null,
      teaching_tags: tagList.value,
      qualifications: validQualifications,
      room_ids: formValues.room_ids,
    };

    saving.value = true;
    let saved = false;
    try {
      if (teacherId.value) {
        await updateAdminTeacher(teacherId.value, payload);
        window['$message']?.success('老师信息更新成功');
        saved = true;
      } else {
        await createAdminTeacher(payload);
        window['$message']?.success('老师创建成功');
        saved = true;
      }
    } catch {
      window['$message']?.error('保存失败');
    } finally {
      saving.value = false;
    }
    // 保存成功后返回列表页
    if (saved) {
      backToList();
    }
  }

  function goBack() {
    backToList();
  }
</script>

<style scoped>
  .flex { display: flex; }
  .items-center { align-items: center; }
  .items-start { align-items: flex-start; }
  .justify-center { justify-content: center; }
  .justify-between { justify-content: space-between; }
  .flex-col { flex-direction: column; }
  .gap-2 { gap: 0.5rem; }
  .gap-3 { gap: 0.75rem; }
  .gap-4 { gap: 1rem; }
  .space-y-2 > * + * { margin-top: 0.5rem; }
  .space-y-4 > * + * { margin-top: 1rem; }
  .w-full { width: 100%; }
  .w-24 { width: 6rem; }
  .h-24 { height: 6rem; }
  .max-w-3xl { max-width: 48rem; }
  .mx-auto { margin-left: auto; margin-right: auto; }
  .py-4 { padding-top: 1rem; padding-bottom: 1rem; }
  .p-3 { padding: 0.75rem; }
  .mt-2 { margin-top: 0.5rem; }
  .m-0 { margin: 0; }
  .my-3 { margin-top: 0.75rem; margin-bottom: 0.75rem; }
  .block { display: block; }
  .text-xs { font-size: 0.75rem; }
  .text-sm { font-size: 0.875rem; }
  .text-lg { font-size: 1.125rem; }
  .font-medium { font-weight: 500; }
  .font-semibold { font-weight: 600; }
  .font-bold { font-weight: 700; }
  .rounded-full { border-radius: 9999px; }
  .rounded-lg { border-radius: 0.5rem; }
  .overflow-hidden { overflow: hidden; }
  .flex-shrink-0 { flex-shrink: 0; }
  .flex-1 { flex: 1 1 0%; }
  .cursor-pointer { cursor: pointer; }
  .border { border-width: 1px; border-style: solid; }
  .border-gray-200 { border-color: #e5e7eb; }
  .border-dashed { border-style: dashed; }
  .bg-gray-50 { background-color: #f9fafb; }
  .shadow-sm { box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05); }
  .flex-wrap { flex-wrap: wrap; }
</style>
