import { TUILogin } from '@tencentcloud/tui-core-lite';
import { TUIConversationService, TUIStore, StoreName } from '@tencentcloud/chat-uikit-engine-lite';
// #ifdef MP-WEIXIN
import { TUIChatKit } from '../../index.ts';
// #endif

// 为超过 7 天的深历史会话创建最小会话对象，让聊天页面能正常渲染
function createMockConversation(conversationID: string): any {
  const peerID = conversationID.replace(/^C2C/, '').replace(/^GROUP/, '');
  return {
    conversationID,
    type: conversationID.startsWith('C2C') ? 'C2C' : 'GROUP',
    subType: '',
    unreadCount: 0,
    remark: '',
    isPinned: false,
    messageRemindType: '',
    markList: [],
    customData: '',
    conversationGroupList: [],
    draftText: '',
    isMuted: false,
    operationType: 0,
    _conversation: null,
    userProfile: { userID: peerID },
    groupProfile: null,
    updateProperties() {},
    updateOperationType() {},
    getConversation() { return this; },
    deleteConversation() { return Promise.resolve(); },
    pinConversation() { return Promise.resolve(); },
    muteConversation() { return Promise.resolve(); },
    setMessageRead() { return Promise.resolve(); },
    getAvatar() { return ''; },
    getShowName() { return peerID.slice(0, 8); },
    getGroupAtInfo() { return ''; },
    getLastMessage() { return null; },
  };
}

async function switchConversation(conversationID: string) {
  if (!conversationID.startsWith('C2C') && !conversationID.startsWith('GROUP')) {
    console.warn('conversationID from options is invalid.');
    return false;
  }

  // 检查会话是否存在于 SDK 中（超过 7 天的历史会话可能不在 SDK 中）
  const conversationList = TUIStore.getData(StoreName.CONV, 'conversationList') || [];
  const exists = conversationList.some((conv: any) => conv.conversationID === conversationID);

  if (exists) {
    // 会话存在于 SDK 中，直接切换
    TUIConversationService.switchConversation(conversationID);
    return true;
  }

  // 会话不存在（超过 7 天的深历史），尝试切换后捕获错误
  console.log('[TUIChat] Conversation not in SDK, attempting switch:', conversationID);
  try {
    await TUIConversationService.switchConversation(conversationID);
    // 切换成功，检查 currentConversation 是否已设置
    const currentConv = TUIStore.getData(StoreName.CONV, 'currentConversation');
    if (currentConv && currentConv.conversationID === conversationID) {
      return true;
    }
  } catch (e) {
    console.warn('[TUIChat] switchConversation failed:', e);
  }

  // 切换失败，创建模拟会话对象并直接设置到 Store
  console.log('[TUIChat] Creating mock conversation for deep history:', conversationID);
  const mockConv = createMockConversation(conversationID);
  TUIStore.update(StoreName.CONV, 'currentConversation', mockConv);
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
