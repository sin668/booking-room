import { TUILogin } from '@tencentcloud/tui-core-lite';
import { TUIConversationService } from '@tencentcloud/chat-uikit-engine-lite';
// #ifdef MP-WEIXIN
import { TUIChatKit } from '../../index.ts';
// #endif

function switchConversation(conversationID: string) {
  if (!conversationID.startsWith('C2C') && !conversationID.startsWith('GROUP')) {
    console.warn('conversationID from options is invalid.');
    return false;
  }
  TUIConversationService.switchConversation(conversationID);
  return true;
}

export const initChat = (options: Record<string, string>) => {
  // #ifdef MP-WEIXIN
  TUIChatKit.init();
  // #endif

  if (!options?.conversationID) return;

  const { chat } = TUILogin.getContext();
  if (chat?.isReady()) {
    switchConversation(options.conversationID);
    return;
  }

  let retries = 0;
  const maxRetries = 25;
  const timer = setInterval(() => {
    retries++;
    const { chat } = TUILogin.getContext();
    if (chat?.isReady()) {
      clearInterval(timer);
      switchConversation(options.conversationID);
    } else if (retries >= maxRetries) {
      clearInterval(timer);
      console.error('[TUIChat] chat SDK not ready after 5s, conversation switch aborted');
      uni.showToast({ title: '消息服务初始化超时，请返回重试', icon: 'none' });
    }
  }, 200);
};

export const logout = (flag: boolean) => {
  if (flag) {
    return TUILogin.logout();
  }
  return Promise.resolve();
};
