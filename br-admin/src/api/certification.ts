import { Alova } from '@/utils/http/alova/index';
import { ADMIN_NATIVE_META } from '@/api/contracts/admin';

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
  verification_type?: string;
  status?: string;
  keyword?: string;
}

export async function getCertifications(params?: CertificationListParams) {
  return Alova.Get('/v1/admin/certifications', {
    params: params || {},
    meta: ADMIN_NATIVE_META,
  });
}

export function reviewCertification(certId: string, data: { approved: boolean; rejection_reason?: string }) {
  return Alova.Patch(`/v1/admin/certifications/${certId}/review`, data, {
    meta: ADMIN_NATIVE_META,
  });
}
