<template>
  <basicModal @register="modalRegister" ref="modalRef" @on-ok="okModal">
    <div class="pt-8">
      <n-spin :show="loading">
        <n-checkbox-group v-model:value="selectedRoleIds">
          <n-space vertical>
            <n-checkbox
              v-for="role in allRoles"
              :key="role.id"
              :value="role.id"
              :label="role.name"
            />
          </n-space>
        </n-checkbox-group>
        <n-empty v-if="!loading && allRoles.length === 0" description="暂无角色" />
      </n-spin>
    </div>
  </basicModal>
</template>

<script lang="ts" setup>
  import { ref, nextTick } from 'vue';
  import { basicModal, useModal } from '@/components/Modal';
  import { getRoleList } from '@/api/system/role';
  import { updateUser } from '@/api/system/user';

  const emit = defineEmits(['success']);

  const loading = ref(false);
  const allRoles = ref<any[]>([]);
  const selectedRoleIds = ref<number[]>([]);
  let currentId: string | number | undefined;

  const [modalRegister, { openModal, closeModal, setSubLoading }] = useModal({
    title: '分配角色',
    subBtuText: '保存',
  });

  async function showModal(record: any) {
    currentId = record?.id;
    selectedRoleIds.value = (record?.roles || []).map((r: any) => r.id);
    openModal();

    loading.value = true;
    try {
      const result = await getRoleList({ page_size: 999 });
      allRoles.value = result.list;
    } catch {
      allRoles.value = [];
    } finally {
      loading.value = false;
    }
  }

  async function okModal() {
    if (currentId == null) return;
    try {
      await updateUser(currentId, { role_ids: selectedRoleIds.value });
      closeModal();
      emit('success');
    } catch {
      setSubLoading(false);
    }
  }

  defineExpose({
    showModal,
  });
</script>
