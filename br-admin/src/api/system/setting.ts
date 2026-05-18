import { Alova } from '@/utils/http/alova/index';

export interface BasicSettings {
  site_name: string;
  icp_code?: string;
  contact_phone?: string;
  contact_address?: string;
  login_captcha?: boolean;
  system_open?: boolean;
  close_text?: string;
  login_desc?: string;
}

export interface EmailSettings {
  smtp_host?: string;
  smtp_port?: number;
  smtp_username?: string;
  smtp_password?: string;
  smtp_sender?: string;
  smtp_tls?: boolean;
  smtp_password_set?: boolean;
}

export interface SystemSettings {
  basic: BasicSettings;
  email: EmailSettings;
}

const nativeMeta = {
  isReturnNativeResponse: true,
};

export function getSystemSettings() {
  return Alova.Get<SystemSettings>('/v1/admin/settings', {
    meta: nativeMeta,
  });
}

export function updateBasicSettings(data: BasicSettings) {
  return Alova.Put<BasicSettings>('/v1/admin/settings/basic', data, {
    meta: nativeMeta,
  });
}

export function updateEmailSettings(data: EmailSettings) {
  const payload = { ...data };
  if (!payload.smtp_password) {
    delete payload.smtp_password;
  }
  return Alova.Put<EmailSettings>('/v1/admin/settings/email', payload, {
    meta: nativeMeta,
  });
}

export function testEmailSettings(to_email: string) {
  return Alova.Post(
    '/v1/admin/settings/email/test',
    { to_email },
    {
      meta: nativeMeta,
    }
  );
}
