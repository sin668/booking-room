import { defineStore } from 'pinia';
import { store } from '@/store';
import { ACCESS_TOKEN, CURRENT_USER, IS_SCREENLOCKED } from '@/store/mutation-types';
import { ResultEnum } from '@/enums/httpEnum';

import { getUserInfo as getUserInfoApi, login, type AdminUserInfo } from '@/api/system/user';
import { storage } from '@/utils/Storage';

// 会话有效期兜底默认值（秒）：优先读后端 login 响应的 expires_in（单一事实源，§7.2），缺失时退回 7 天
const DEFAULT_SESSION_TTL_SECONDS = 7 * 24 * 60 * 60;

export type UserInfoType = AdminUserInfo & {
  username: string;
};

export interface IUserState {
  token: string;
  username: string;
  welcome: string;
  avatar: string;
  permissions: any[];
  info: UserInfoType;
}

export const useUserStore = defineStore({
  id: 'app-user',
  state: (): IUserState => ({
    token: storage.get(ACCESS_TOKEN, ''),
    username: '',
    welcome: '',
    avatar: '',
    permissions: [],
    info: storage.get(CURRENT_USER, {}),
  }),
  getters: {
    getToken(): string {
      return this.token;
    },
    getAvatar(): string {
      return this.avatar;
    },
    getNickname(): string {
      return this.username;
    },
    getPermissions(): [any][] {
      return this.permissions;
    },
    getUserInfo(): UserInfoType {
      return this.info;
    },
  },
  actions: {
    setToken(token: string) {
      this.token = token;
    },
    setNickname(nickname: string) {
      this.username = nickname;
    },
    setAvatar(avatar: string) {
      this.avatar = avatar;
    },
    setPermissions(permissions) {
      this.permissions = permissions;
    },
    setUserInfo(info: UserInfoType) {
      this.info = info;
    },
    // 登录
    async login(params: any) {
      const result = await login(params);
      const token = result.access_token;
      const ex = result.expires_in ?? DEFAULT_SESSION_TTL_SECONDS;
      storage.set(ACCESS_TOKEN, token, ex);
      storage.set(CURRENT_USER, result, ex);
      storage.set(IS_SCREENLOCKED, false);
      this.setToken(token);
      this.setUserInfo({ username: params.username, ...result });
      return {
        code: ResultEnum.SUCCESS,
        message: '登录成功',
        result: {
          ...result,
          token,
        },
      };
    },

    // 获取用户信息
    async getInfo() {
      const result = await getUserInfoApi();
      const permissionsList = Array.isArray(result.permissions) ? result.permissions : [];
      const nickname = result.nickname || result.username || '';
      this.setPermissions(permissionsList);
      this.setUserInfo(result as UserInfoType);
      this.setNickname(nickname);
      this.setAvatar(result.avatar || '');
      storage.set(CURRENT_USER, result, DEFAULT_SESSION_TTL_SECONDS);
      return result;
    },

    // 登出
    async logout() {
      this.setPermissions([]);
      this.setUserInfo({ username: '', email: '' });
      storage.remove(ACCESS_TOKEN);
      storage.remove(CURRENT_USER);
    },
  },
});

// Need to be used outside the setup
export function useUser() {
  return useUserStore(store);
}
