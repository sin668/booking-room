<template>
  <n-flex vertical>
    <!-- 顶部操作栏 -->
    <n-card :bordered="false">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <n-button text @click="goBack">
            <template #icon><n-icon><ArrowLeftOutlined /></n-icon></template>
          </n-button>
          <h2 class="text-lg font-semibold m-0">{{ isEdit ? '编辑课程' : '新增课程' }}</h2>
        </div>
        <n-space>
          <n-button @click="goBack">取消</n-button>
          <n-button type="primary" :loading="saving" @click="handleSave">
            <template #icon><n-icon><SaveOutlined /></n-icon></template>
            保存课程
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
              <n-form-item-gi :span="2" label="课程名称" path="name">
                <n-input v-model:value="formValues.name" placeholder="请输入课程名称" :maxlength="100" show-count />
              </n-form-item-gi>
              <n-form-item-gi label="课程分类" path="category">
                <n-select
                  v-model:value="formValues.category"
                  placeholder="请选择分类"
                  :options="categoryOptions"
                />
              </n-form-item-gi>
              <n-form-item-gi label="所属教室" path="room_id">
                <n-select
                  v-model:value="formValues.room_id"
                  placeholder="请选择教室"
                  :options="roomOptions"
                  :loading="roomLoading"
                  filterable
                />
              </n-form-item-gi>
              <n-form-item-gi label="热门课程" :show-feedback="false">
                <n-switch v-model:value="formValues.is_hot" />
              </n-form-item-gi>
              <n-form-item-gi label="排序值" :show-feedback="false">
                <n-input-number v-model:value="formValues.sort_order" :min="0" style="width: 100%" />
              </n-form-item-gi>
            </n-grid>
          </n-form>
        </n-card>

        <!-- 课程封面 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><PictureOutlined /></n-icon>
              <span class="text-sm font-bold">课程封面</span>
            </div>
          </template>
          <div class="flex items-start gap-4">
            <div class="w-40 h-28 rounded-lg overflow-hidden border border-gray-200 flex-shrink-0 flex items-center justify-center bg-gray-50">
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
              <n-upload :max="1" accept="image/*" :custom-request="handleUpload" :show-file-list="false">
                <n-button secondary type="info">上传图片</n-button>
              </n-upload>
              <n-text depth="3" class="text-xs mt-2 block">建议尺寸 750×420px，支持 JPG/PNG 格式，最大 2MB</n-text>
            </div>
          </div>
        </n-card>

        <!-- 课程介绍 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><AlignLeftOutlined /></n-icon>
              <span class="text-sm font-bold">课程介绍</span>
            </div>
          </template>
          <n-form-item label="课程描述" :show-feedback="false">
            <n-input
              v-model:value="formValues.description"
              type="textarea"
              placeholder="请输入课程介绍..."
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

        <!-- 课程目录（课时） -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><OrderedListOutlined /></n-icon>
              <span class="text-sm font-bold">课程目录</span>
            </div>
          </template>
          <div class="space-y-2">
            <div
              v-for="(lesson, index) in lessons"
              :key="lesson.id || `new-${index}`"
              class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
            >
              <n-tag type="info" round size="small" :bordered="false" style="min-width: 28px; justify-content: center">
                {{ index + 1 }}
              </n-tag>
              <n-input
                v-model:value="lesson.title"
                placeholder="课时标题"
                class="flex-1"
                :disabled="!lesson._editable"
              />
              <div v-if="lesson._editable" class="flex items-center gap-1" style="width: 140px; flex-shrink: 0">
                <n-input-number
                  v-model:value="lesson.duration_minutes"
                  placeholder="分钟"
                  :min="0"
                  style="width: 100px"
                  size="small"
                />
                <n-text depth="3" class="text-xs">分钟</n-text>
              </div>
              <n-text v-else depth="3" class="text-xs flex-shrink-0" style="width: 140px; text-align: center">
                {{ lesson.duration_minutes ? `${lesson.duration_minutes}分钟` : '-' }}
              </n-text>
              <n-space v-if="lesson._editable" :size="4">
                <n-button size="tiny" type="primary" @click="saveLesson(lesson, index)">保存</n-button>
                <n-button size="tiny" @click="cancelEditLesson(lesson, index)">取消</n-button>
              </n-space>
              <n-space v-else :size="4">
                <n-button size="tiny" quaternary type="info" @click="editLesson(lesson)">
                  <template #icon><n-icon><EditOutlined /></n-icon></template>
                </n-button>
                <n-popconfirm @positive-click="handleDeleteLesson(lesson, index)">
                  <template #trigger>
                    <n-button size="tiny" quaternary type="error" style="display: inline-flex">
                      <template #icon><n-icon><DeleteOutlined /></n-icon></template>
                    </n-button>
                  </template>
                  确定删除该课时？
                </n-popconfirm>
              </n-space>
            </div>
            <n-button dashed block @click="addLesson" :loading="lessonSaving">
              <template #icon><n-icon><PlusOutlined /></n-icon></template>
              添加课时
            </n-button>
          </div>
        </n-card>

        <!-- 发布设置 -->
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex items-center gap-2">
              <n-icon color="#4F6EF7"><SettingOutlined /></n-icon>
              <span class="text-sm font-bold">发布设置</span>
            </div>
          </template>
          <n-radio-group v-model:value="formValues.status">
            <n-space>
              <n-radio value="active">立即上架</n-radio>
              <n-radio value="inactive">存为草稿</n-radio>
            </n-space>
          </n-radio-group>
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
    OrderedListOutlined,
    SettingOutlined,
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
  } from '@vicons/antd';
  import {
    getCourseById,
    createCourse,
    updateCourse,
    createLesson,
    updateLesson,
    deleteLesson,
    type CourseDetail,
    type LessonItem,
  } from '@/api/course';
  import { getRoomList, type RoomItem } from '@/api/room';
  import { uploadImage } from '@/api/upload';
  import { COURSE_CATEGORY_OPTIONS } from './options';
  import { useTabsViewStore } from '@/store/modules/tabsView';

  interface LessonDraft extends Partial<LessonItem> {
    _editable: boolean;
    _isNew: boolean;
  }

  const route = useRoute();
  const router = useRouter();
  const tabsViewStore = useTabsViewStore();
  const courseId = computed(() => {
    const id = route.params.id;
    return id ? Number(id) : null;
  });
  const isEdit = computed(() => courseId.value !== null);

  const formRef = ref<FormInst | null>(null);
  const loading = ref(false);
  const saving = ref(false);
  const lessonSaving = ref(false);

  const formValues = reactive({
    name: '',
    category: null as string | null,
    room_id: null as number | null,
    cover_image: '',
    description: '',
    status: 'active',
    is_hot: false,
    sort_order: 0,
  });

  const rules: FormRules = {
    name: { required: true, message: '请输入课程名称', trigger: 'blur' },
    category: { required: true, type: 'string', message: '请选择课程分类', trigger: 'change' },
    room_id: { required: true, type: 'number', message: '请选择所属教室', trigger: 'change' },
  };

  const categoryOptions = COURSE_CATEGORY_OPTIONS;

  // 教室选项
  const roomOptions = ref<{ label: string; value: number }[]>([]);
  const roomLoading = ref(false);

  // 标签
  const tagList = ref<string[]>([]);
  const showTagInput = ref(false);
  const newTag = ref('');

  // 课时
  const lessons = ref<LessonDraft[]>([]);

  onMounted(async () => {
    // 移除课程列表 tab，实现原 tab 内跳转到编辑页的效果
    removeListTab();
    await loadRooms();
    if (courseId.value) {
      await loadCourse(courseId.value);
    }
  });

  // 移除课程列表标签页
  function removeListTab() {
    const idx = tabsViewStore.tabsList.findIndex((t) => t.name === 'training_courses');
    if (idx > -1) {
      tabsViewStore.tabsList.splice(idx, 1);
    }
  }

  // 返回列表页：将当前编辑页 tab 原地替换为列表 tab，保持标签位置不变
  function backToList() {
    const listTab = {
      fullPath: '/training/courses',
      path: '/training/courses',
      name: 'training_courses',
      hash: '',
      meta: { title: '培训课程' },
      params: {},
      query: {},
    };
    const idx = tabsViewStore.tabsList.findIndex((t) => t.fullPath === route.fullPath);
    if (idx > -1) {
      tabsViewStore.tabsList[idx] = listTab as any;
    }
    router.push({ name: 'training_courses' });
  }

  async function loadRooms() {
    roomLoading.value = true;
    try {
      const result = await getRoomList({ page: 1, page_size: 100 });
      roomOptions.value = result.items.map((r: RoomItem) => ({ label: r.name, value: r.id }));
    } catch {
      window['$message']?.error('加载教室列表失败');
    } finally {
      roomLoading.value = false;
    }
  }

  async function loadCourse(id: number) {
    loading.value = true;
    try {
      const detail: CourseDetail = await getCourseById(id);
      formValues.name = detail.name;
      formValues.category = detail.category;
      formValues.room_id = detail.room_id;
      formValues.cover_image = detail.cover_image || '';
      formValues.description = detail.description || '';
      formValues.status = detail.status;
      formValues.is_hot = detail.is_hot;
      formValues.sort_order = detail.sort_order;

      // 解析标签
      if (detail.tags && detail.tags.length > 0) {
        tagList.value = Array.isArray(detail.tags) ? detail.tags : detail.tags.split(',').filter(Boolean);
      }

      // 加载课时
      if (detail.lessons && detail.lessons.length > 0) {
        lessons.value = detail.lessons.map((l) => ({
          ...l,
          _editable: false,
          _isNew: false,
        }));
      }
    } catch {
      window['$message']?.error('加载课程信息失败');
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

  // 封面上传
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
      const result = await uploadImage(file.file, 'room-cover');
      formValues.cover_image = result.url;
      onFinish();
    } catch {
      onError();
      window['$message']?.error('上传失败');
    }
  }

  // 课时操作
  function addLesson() {
    lessons.value.push({
      title: '',
      duration_minutes: 120,
      sort_order: lessons.value.length + 1,
      is_free_preview: false,
      _editable: true,
      _isNew: true,
    });
  }

  function editLesson(lesson: LessonDraft) {
    lesson._editable = true;
  }

  function cancelEditLesson(lesson: LessonDraft, index: number) {
    if (lesson._isNew) {
      lessons.value.splice(index, 1);
    } else {
      lesson._editable = false;
      // 恢复原始数据
      if (courseId.value && lesson.id) {
        loadCourse(courseId.value);
      }
    }
  }

  async function saveLesson(lesson: LessonDraft, index: number) {
    if (!lesson.title?.trim()) {
      window['$message']?.warning('请输入课时标题');
      return;
    }
    if (!courseId.value) {
      // 课程未保存时，仅本地保存
      lesson._editable = false;
      lesson._isNew = false;
      return;
    }

    lessonSaving.value = true;
    try {
      if (lesson._isNew || !lesson.id) {
        const created = await createLesson(courseId.value, {
          title: lesson.title,
          duration_minutes: lesson.duration_minutes,
          sort_order: index + 1,
          is_free_preview: lesson.is_free_preview,
        });
        lessons.value[index] = { ...created, _editable: false, _isNew: false };
        window['$message']?.success('课时添加成功');
      } else {
        await updateLesson(courseId.value, lesson.id, {
          title: lesson.title,
          duration_minutes: lesson.duration_minutes,
          sort_order: index + 1,
          is_free_preview: lesson.is_free_preview,
        });
        lesson._editable = false;
        window['$message']?.success('课时更新成功');
      }
    } catch {
      window['$message']?.error('保存课时失败');
    } finally {
      lessonSaving.value = false;
    }
  }

  async function handleDeleteLesson(lesson: LessonDraft, index: number) {
    if (!courseId.value || !lesson.id) {
      lessons.value.splice(index, 1);
      return;
    }
    try {
      await deleteLesson(courseId.value, lesson.id);
      lessons.value.splice(index, 1);
      window['$message']?.success('课时已删除');
    } catch {
      window['$message']?.error('删除课时失败');
    }
  }

  // 保存课程
  async function handleSave() {
    try {
      await formRef.value?.validate();
    } catch {
      window['$message']?.warning('请检查必填项');
      return;
    }

    saving.value = true;
    try {
      const payload = {
        name: formValues.name,
        category: formValues.category!,
        room_id: formValues.room_id!,
        cover_image: formValues.cover_image || null,
        description: formValues.description || null,
        tags: tagList.value.join(','),
        status: formValues.status,
        is_hot: formValues.is_hot,
        sort_order: formValues.sort_order,
      };

      if (courseId.value) {
        await updateCourse(courseId.value, payload);
        window['$message']?.success('课程更新成功');
      } else {
        await createCourse(payload);
        window['$message']?.success('课程创建成功');
      }
      // 保存成功后返回列表页（原 tab 内跳转）
      backToList();
    } catch {
      window['$message']?.error('保存失败');
    } finally {
      saving.value = false;
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
  .gap-2 { gap: 0.5rem; }
  .gap-3 { gap: 0.75rem; }
  .gap-4 { gap: 1rem; }
  .space-y-2 > * + * { margin-top: 0.5rem; }
  .space-y-4 > * + * { margin-top: 1rem; }
  .w-full { width: 100%; }
  .w-40 { width: 10rem; }
  .h-28 { height: 7rem; }
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
  .font-semibold { font-weight: 600; }
  .font-bold { font-weight: 700; }
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
