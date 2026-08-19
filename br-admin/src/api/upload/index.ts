import { Alova } from '@/utils/http/alova/index';

export type UploadScope =
  | 'avatar'
  | 'activity-cover'
  | 'room-cover'
  | 'room-environment'
  | 'common';

export interface UploadResult {
  url: string;
  object_key: string;
  size: number;
  content_type: string;
}

const adminMeta = {
  isReturnNativeResponse: true,
};

export function uploadImage(file: File, scope: UploadScope = 'common') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('scope', scope);

  return Alova.Post<UploadResult>('/v1/admin/upload', formData, {
    meta: adminMeta,
  });
}
