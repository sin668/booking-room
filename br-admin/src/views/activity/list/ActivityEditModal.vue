<template>
  <n-modal
    :show="showModal"
    :show-icon="false"
    preset="dialog"
    :title="editData ? '编辑活动' : '新建活动'"
    @update:show="(val: boolean) => emit('update:show', val)"
  >
    <n-form
      :model="formValues"
      :rules="rules"
      ref="formRef"
      label-placement="left"
      :label-width="80"
      class="py-4"
    >
      <n-form-item label="标题" path="title">
        <n-input
          placeholder="请输入标题"
          v-model:value="formValues.title"
          :maxlength="100"
          show-count
        />
      </n-form-item>

      <n-form-item label="描述" path="description">
        <n-input
          type="textarea"
          placeholder="请输入描述"
          v-model:value="formValues.description"
          :maxlength="500"
          show-count
          :rows="3"
        />
      </n-form-item>

      <n-form-item label="封面图" path="cover_image">
        <n-space vertical>
          <n-upload
            :max="1"
            accept="image/*"
            :custom-request="handleUpload"
          >
            <n-button>上传图片</n-button>
          </n-upload>
          <n-image
            v-if="formValues.cover_image"
            :src="formValues.cover_image"
            width="80"
            height="80"
            object-fit="cover"
            preview-disabled
          />
        </n-space>
      </n-form-item>

      <n-form-item label="参与人数" path="participant_count">
        <n-input-number
          v-model:value="formValues.participant_count"
          :min="0"
          style="width: 100%"
        />
      </n-form-item>

      <n-form-item label="排序值" path="sort_order">
        <n-input-number
          v-model:value="formValues.sort_order"
          style="width: 100%"
        />
      </n-form-item>

      <n-form-item label="是否上架" path="is_active">
        <n-switch v-model:value="formValues.is_active" />
      </n-form-item>
    </n-form>

    <template #action>
      <n-space>
        <n-button @click="() => emit('update:show', false)">取消</n-button>
        <n-button type="info" :loading="formBtnLoading" @click="confirmForm">确定</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script lang="ts" setup>
  import { computed, reactive, ref, watch } from 'vue';
  import type { FormRules, FormInst, UploadFileInfo } from 'naive-ui';
  import {
    createActivity,
    updateActivity,
    uploadFile,
    type ActivityFormParams,
    type ActivityItem,
  } from '@/api/activity';

  const props = defineProps<{
    show: boolean;
    editData: ActivityItem | null;
  }>();

  const emit = defineEmits<{
    (e: 'update:show', value: boolean): void;
    (e: 'success'): void;
  }>();

  const showModal = computed({
    get: () => props.show,
    set: (val: boolean) => emit('update:show', val),
  });

  const formRef = ref<FormInst | null>(null);
  const formBtnLoading = ref(false);

  const defaultValues: ActivityFormParams = {
    title: '',
    description: '',
    cover_image: '',
    participant_count: 0,
    sort_order: 0,
    is_active: true,
  };

  const formValues = reactive<ActivityFormParams>({ ...defaultValues });

  const rules: FormRules = {
    title: {
      required: true,
      trigger: ['blur', 'input'],
      message: '请输入标题',
    },
  };

  watch(
    () => props.show,
    (val) => {
      if (!val) return;
      if (props.editData) {
        formValues.title = props.editData.title;
        formValues.description = props.editData.description ?? '';
        formValues.cover_image = props.editData.cover_image ?? '';
        formValues.participant_count = props.editData.participant_count;
        formValues.sort_order = props.editData.sort_order;
        formValues.is_active = props.editData.is_active;
      } else {
        Object.assign(formValues, { ...defaultValues });
      }
    },
  );

  async function handleUpload({ file, onFinish, onError }: { file: UploadFileInfo; onFinish: () => void; onError: () => void }) {
    try {
      const result = await uploadFile(file.file!);
      formValues.cover_image = result.url;
      onFinish();
    } catch {
      onError();
      window['$message'].error('上传失败');
    }
  }

  function confirmForm() {
    formBtnLoading.value = true;
    formRef.value?.validate(async (errors) => {
      if (!errors) {
        try {
          if (props.editData) {
            await updateActivity(props.editData.id, formValues);
          } else {
            await createActivity(formValues);
          }
          window['$message'].success('操作成功');
          emit('update:show', false);
          emit('success');
        } catch {
          window['$message'].error('操作失败');
        }
      }
      formBtnLoading.value = false;
    });
  }
</script>
