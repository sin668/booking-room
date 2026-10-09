import { TUIGlobal } from '@tencentcloud/universal-api';
import TUIChatEngine from '@tencentcloud/chat-uikit-engine-lite';

export type ButtonType = 'primary' | 'default' | 'text';
export type Action = 'cancel' | 'confirm' | 'close' | 'mask';
export type ModalType = 'info' | 'warning' | 'error' | 'success';

export interface UIKitModalEvents {
  onConfirm?: () => void;
  onCancel?: () => void;
}

export interface UIKitModalOptions extends UIKitModalEvents {
  id: number;
  title: string;
  content: string;
  type: ModalType;
}

export interface IUIKitModalBtn {
  type?: ButtonType;
  text?: string;
  customClasses?: string[];
  action?: () => void;
  disabled?: boolean;
}

const isLocalEnvironment = (): boolean => {
  if (typeof window === 'undefined') return false;
  const host = window.location.hostname;
  return host === 'localhost' || host === '127.0.0.1' || host.startsWith('192.168.');
};

const reportModalView = (options: UIKitModalOptions): void => {
  const chat = (TUIChatEngine as any).chat;
  if (chat && typeof chat.callExperimentalAPI === 'function') {
    const reportData = {
      id: options.id,
      title: options.title,
      type: options.type,
      content: options.content,
    };
    chat.callExperimentalAPI('reportModalView', JSON.stringify(reportData));
  }
};

const openModal = (options: UIKitModalOptions): Promise<{ action: string }> => {
  return new Promise((resolve) => {
    reportModalView(options);
    if (!isLocalEnvironment()) {
      resolve({ action: 'confirm' });
      return;
    }
    TUIGlobal.showModal({
      title: options.title || '',
      content: options.content || '',
      showCancel: true,
      success: (res: { confirm: boolean; cancel: boolean }) => {
        if (res.confirm) {
          options.onConfirm?.();
          resolve({ action: 'confirm' });
        } else if (res.cancel) {
          options.onCancel?.();
          resolve({ action: 'cancel' });
        }
      },
      fail: () => {
        resolve({ action: 'cancel' });
      },
    });
  });
};

export const UIKitModal = {
  openModal,
};
