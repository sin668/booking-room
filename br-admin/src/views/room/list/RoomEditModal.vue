<template>
  <n-modal
    :show="showModal"
    :show-icon="false"
    preset="dialog"
    :title="editData ? '编辑自习室' : '新建自习室'"
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
      <n-form-item label="名称" path="name">
        <n-input
          placeholder="请输入名称"
          v-model:value="formValues.name"
          :maxlength="100"
          show-count
        />
      </n-form-item>

      <n-form-item label="描述" path="description">
        <n-input
          type="textarea"
          placeholder="请输入描述"
          v-model:value="formValues.description"
          :maxlength="1000"
          show-count
          :rows="3"
        />
      </n-form-item>

      <n-form-item label="封面图片" path="cover_image">
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

      <n-form-item label="地址" path="address">
        <n-input
          placeholder="请输入地址"
          v-model:value="formValues.address"
          :maxlength="255"
          show-count
        />
      </n-form-item>

      <n-form-item label="营业时间" path="business_hours">
        <n-input
          placeholder="如 08:00-22:00"
          v-model:value="formValues.business_hours"
          :maxlength="50"
          show-count
        />
      </n-form-item>

      <n-form-item label="最低价格" path="min_price">
        <n-input-number
          v-model:value="formValues.min_price"
          :min="0"
          style="width: 100%"
        />
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
    createRoom,
    updateRoom,
    type RoomFormParams,
    type RoomItem,
  } from '@/api/room';
  import { uploadFile as uploadActivityFile } from '@/api/activity';

  const props = defineProps<{
    show: boolean;
    editData: RoomItem | null;
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

  const defaultValues: RoomFormParams = {
    name: '',
    description: '',
    cover_image: '',
    address: '',
    business_hours: '',
    min_price: 0,
  };

  const formValues = reactive<RoomFormParams>({ ...defaultValues });

  const rules: FormRules = {
    name: {
      required: true,
      trigger: ['blur', 'input'],
      message: '请输入名称',
    },
    address: {
      required: true,
      trigger: ['blur', 'input'],
      message: '请输入地址',
    },
  };

  watch(
    () => props.show,
    (val) => {
      if (!val) return;
      if (props.editData) {
        formValues.name = props.editData.name;
        formValues.description = props.editData.description ?? '';
        formValues.cover_image = props.editData.cover_image ?? '';
        formValues.address = props.editData.address;
        formValues.business_hours = props.editData.business_hours ?? '';
        formValues.min_price = props.editData.min_price;
      } else {
        Object.assign(formValues, { ...defaultValues });
      }
    },
  );

  async function handleUpload({ file, onFinish, onError }: { file: UploadFileInfo; onFinish: () => void; onError: () => void }) {
    if (!file.file) {
      onError();
      return;
    }
    try {
      const result = await uploadActivityFile(file.file);
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
            await updateRoom(props.editData.id, formValues);
          } else {
            await createRoom(formValues);
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
