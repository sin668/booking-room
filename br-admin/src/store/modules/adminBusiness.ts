import { defineStore } from 'pinia';
import { store } from '@/store';
import { getRoomList } from '@/api/room';

export interface BusinessSelectOption {
  label: string;
  value: number;
}

export const useAdminBusinessStore = defineStore({
  id: 'admin-business',
  state: () => ({
    roomOptions: [] as BusinessSelectOption[],
    roomOptionsLoaded: false,
  }),
  actions: {
    async loadRoomOptions(force = false) {
      if (this.roomOptionsLoaded && !force) return this.roomOptions;
      const result = await getRoomList({ page_size: 999 });
      this.roomOptions = result.items.map((room) => ({ label: room.name, value: room.id }));
      this.roomOptionsLoaded = true;
      return this.roomOptions;
    },
  },
});

export function useAdminBusiness() {
  return useAdminBusinessStore(store);
}
