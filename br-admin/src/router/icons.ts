import { renderIcon } from '@/utils/index';
import {
  AppstoreOutlined,
  CalendarOutlined,
  DashboardOutlined,
  GiftOutlined,
  HomeOutlined,
  MenuOutlined,
  SettingOutlined,
  TeamOutlined,
  ToolOutlined,
  UserOutlined,
  WalletOutlined,
} from '@vicons/antd';

//前端路由图标映射表
export const constantRouterIcon = {
  HomeOutlined: renderIcon(HomeOutlined),
  DashboardOutlined: renderIcon(DashboardOutlined),
  SettingOutlined: renderIcon(SettingOutlined),
  MenuOutlined: renderIcon(MenuOutlined),
  TeamOutlined: renderIcon(TeamOutlined),
  UserOutlined: renderIcon(UserOutlined),
  ToolOutlined: renderIcon(ToolOutlined),
  AppstoreOutlined: renderIcon(AppstoreOutlined),
  GiftOutlined: renderIcon(GiftOutlined),
  CalendarOutlined: renderIcon(CalendarOutlined),
  WalletOutlined: renderIcon(WalletOutlined),
};
