import { TUILogin } from '@tencentcloud/tui-core-lite';
import { TUIConversationService, TUIStore, StoreName } from '@tencentcloud/chat-uikit-engine-lite';
// #ifdef MP-WEIXIN
import { TUIChatKit } from '../../index.ts';
// #endif

async function switchConversation(conversationID: string) {
  if (!conversationID.startsWith('C2C') && !conversationID.startsWith('GROUP')) {
    console.warn('conversationID from options is invalid.');
    return false;
  }

  // 检查会话是否存在于 SDK 中（超过 7 天的历史会话可能不在 SDK 中）
  const conversationList = TUIStore.getData(StoreName.CONV, 'conversationList') || [];
  const exists = conversationList.some((conv: any) => conv.conversationID === conversationID);
  
  if (!exists) {
    // 会话不存在，需要先创建（用于超过 7 天的深历史会话）
    console.log('[TUIChat] Conversation not in SDK, creating:', conversationID);
    try {
      await TUIConversationService.createConversation({
        conversationID,
        type: conversationID.startsWith('C2C') ? 'C2C' : 'GROUP',
      });
    } catch (e) {
      console.warn('[TUIChat] createConversation failed, trying switch anyway:', e);
    }
  }

  TUIConversationService.switchConversation(conversationID);
  return true;
}

export const initChat = async (options: Record<string, string>) => {
  // #ifdef MP-WEIXIN
  TUIChatKit.init();
  // #endif

  if (!options?.conversationID) return;

  const { chat } = TUILogin.getContext();
  if (chat?.isReady()) {
    await switchConversation(options.conversationID);
    return;
  }

  let retries = 0;
  const maxRetries = 25;
  const timer = setInterval(async () => {
    retries++;
    const { chat } = TUILogin.getContext();
    if (chat?.isReady()) {
      clearInterval(timer);
      await switchConversation(options.conversationID);
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
