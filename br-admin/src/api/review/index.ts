import { Alova } from '@/utils/http/alova/index';
import {
  ADMIN_NATIVE_META,
  normalizePageParams,
  toBasicTableResult,
  type AdminPageResponse,
  type BasicTableResult,
} from '@/api/contracts/admin';

/** 后台评价条目：后端永不脱敏，昵称头像始终是真实值 */
export interface AdminReviewItem {
  id: number;
  booking_id: number;
  user_nickname: string | null;
  user_avatar: string | null;
  rating: number;
  content: string;
  images: string[];
  tags: string[];
  is_anonymous: boolean;
  course_id: number | null;
  course_name: string | null;
  teacher_id: number | null;
  teacher_name: string | null;
  reply_content: string | null;
  reply_at: string | null;
  status: string;
  reject_reason: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface AdminReviewListParams {
  page?: number;
  pageSize?: number;
  page_size?: number;
  /** 审核状态：pending | approved | rejected，空串表示全部 */
  status?: string;
  /** 评分档位：good(4-5星) | mid(3星) | bad(1-2星)，空串表示全部 */
  rating_band?: string;
  /** 按评价内容或用户昵称模糊搜索 */
  keyword?: string;
  /** new(最新) | score(评分最高) */
  sort?: string;
}

/** 审核请求。目标状态只能是 approved / rejected，驳回时 reject_reason 必填 */
export interface ReviewStatusParams {
  status: 'approved' | 'rejected';
  reject_reason?: string | null;
}

// normalizePageParams 内部已做 compactQuery，空串筛选项会被自动剔除
export async function getAdminReviewList(
  params?: AdminReviewListParams
): Promise<BasicTableResult<AdminReviewItem>> {
  const result = await Alova.Get<AdminPageResponse<AdminReviewItem>>('/v1/admin/reviews', {
    params: normalizePageParams(params || {}),
    meta: ADMIN_NATIVE_META,
  });

  return toBasicTableResult(result);
}

export function updateAdminReviewStatus(id: number, data: ReviewStatusParams) {
  return Alova.Patch<AdminReviewItem>(`/v1/admin/reviews/${id}/status`, data, {
    meta: ADMIN_NATIVE_META,
  });
}

/** 机构回复。传空白内容表示清空既有回复 */
export function updateAdminReviewReply(id: number, reply_content: string) {
  return Alova.Patch<AdminReviewItem>(
    `/v1/admin/reviews/${id}/reply`,
    { reply_content },
    { meta: ADMIN_NATIVE_META }
  );
}
