import { Alova } from '@/utils/http/alova/index';
import {
  ADMIN_NATIVE_META,
  normalizePageParams,
  toBasicTableResult,
  type AdminPageResponse,
  type BasicTableResult,
} from '@/api/contracts/admin';

/** 后台教培供需条目：与 br-app 广场共用数据模型，额外携带审核元数据 */
export interface AdminEduListingItem {
  id: number;
  listing_type: string;
  title: string;
  subject: string | null;
  teaching_mode: string | null;
  price: string | number | null;
  price_unit: string | null;
  area: string | null;
  description: string | null;
  images: string[];
  available_times: string[];
  status: string;
  reject_reason: string | null;
  view_count: number;
  publisher_id: string | null;
  publisher_nickname: string | null;
  publisher_avatar: string | null;
  publisher_education_verified: boolean | null;
  publisher_teacher_verified: boolean | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface AdminEduListingListParams {
  page?: number;
  pageSize?: number;
  page_size?: number;
  /** 标题模糊搜索 */
  keyword?: string;
  /** 供需类型：tutor | training | demand，空串表示全部（后端 query 名为 type） */
  type?: string;
  /** 审核状态：pending | approved | rejected | offline，空串表示全部 */
  status?: string;
}

/** 审核请求。目标状态只能是 approved / rejected / offline，rejected 时 reject_reason 必填 */
export interface EduListingStatusParams {
  status: 'approved' | 'rejected' | 'offline';
  reject_reason?: string | null;
}

// normalizePageParams 内部已做 compactQuery，空串筛选项会被自动剔除
export async function getAdminEduListings(
  params?: AdminEduListingListParams
): Promise<BasicTableResult<AdminEduListingItem>> {
  const result = await Alova.Get<AdminPageResponse<AdminEduListingItem>>(
    '/v1/admin/edu-listings',
    {
      params: normalizePageParams(params || {}),
      meta: ADMIN_NATIVE_META,
    }
  );

  return toBasicTableResult(result);
}

export function reviewEduListing(id: number, data: EduListingStatusParams) {
  return Alova.Patch<AdminEduListingItem>(`/v1/admin/edu-listings/${id}/status`, data, {
    meta: ADMIN_NATIVE_META,
  });
}
