import { Alova } from '@/utils/http/alova/index';
import {
  ADMIN_NATIVE_META,
  normalizePageParams,
  toBasicTableResult,
  type AdminPageResponse,
  type BasicTableResult,
} from '@/api/contracts/admin';

export interface CertificationItem {
  id: string;
  user_id: string;
  verification_type: string;
  status: string;
  real_name: string | null;
  id_card_masked: string | null;
  school: string | null;
  education_level: string | null;
  major: string | null;
  graduation_year: number | null;
  diploma_image_url: string | null;
  teacher_certificate_number: string | null;
  teaching_subject: string | null;
  certificate_image_url: string | null;
  rejection_reason: string | null;
  submitted_at: string;
  reviewed_at: string | null;
  reviewer_id: string | null;
  user_nickname?: string | null;
  user_phone?: string | null;
}

export interface CertificationListParams {
  page?: number;
  pageSize?: number;
  page_size?: number;
  /** 状态过滤：pending | approved | rejected，空串表示全部 */
  status_filter?: string;
  /** 类型过滤：real_name | education | teacher，空串表示全部 */
  type_filter?: string;
  /** 按昵称/手机号/学校模糊搜索 */
  keyword?: string;
}

// normalizePageParams 内部已做 compactQuery，空串筛选项会被自动剔除
export async function getCertifications(
  params?: CertificationListParams
): Promise<BasicTableResult<CertificationItem>> {
  const result = await Alova.Get<AdminPageResponse<CertificationItem>>(
    '/v1/admin/certifications',
    {
      params: normalizePageParams(params || {}),
      meta: ADMIN_NATIVE_META,
    }
  );

  return toBasicTableResult(result);
}

export function reviewCertification(
  certId: string,
  data: { approved: boolean; rejection_reason?: string }
) {
  return Alova.Patch(`/v1/admin/certifications/${certId}/review`, data, {
    meta: ADMIN_NATIVE_META,
  });
}
