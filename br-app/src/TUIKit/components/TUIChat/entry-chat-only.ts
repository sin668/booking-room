import { TUILogin } from '@tencentcloud/tui-core-lite';
import { TUIConversationService, TUIStore, StoreName } from '@tencentcloud/chat-uikit-engine-lite';
import { ensureIM } from '@/utils/im';
// #ifdef MP-WEIXIN
import { TUIChatKit } from '../../index.ts';
// #endif

const SDK_READY_EVENT = 'sdkStateReady';
// 就绪预算与 ensureIM 的登录重试对齐（握手 15s + 等就绪 15s + 重试），不再 5s 就放弃——
// 旧上限短于登录预算，慢网络下登录还没成功 initChat 就报「初始化超时」，首次进入既慢又易失败。
const CHAT_READY_TIMEOUT = 35000;

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
  const conversationID = options.conversationID;

  const { chat } = TUILogin.getContext();
  if (chat?.isReady()) {
    await switchConversation(conversationID);
    return;
  }

  // 直接进会话页（未经 openCSChat 预热）时主动拉起登录；ensureIM 自带重试、晚到就绪复用、离线快失败
  ensureIM();

  // 事件驱动即时切会话 + 200ms 轮询兜底（实例可能尚未创建，轮询里再挂事件），预算与登录对齐
  let done = false;
  let attached: any = null;
  const cleanup = () => {
    clearInterval(timer);
    clearTimeout(deadline);
    attached?.off?.(SDK_READY_EVENT, onReady);
  };
  const finish = async () => {
    if (done) return;
    done = true;
    cleanup();
    await switchConversation(conversationID);
  };
  const onReady = () => { finish(); };
  const timer = setInterval(() => {
    const { chat } = TUILogin.getContext();
    if (chat?.isReady()) { finish(); return; }
    if (chat && chat !== attached) {
      attached?.off?.(SDK_READY_EVENT, onReady);
      attached = chat;
      chat.on?.(SDK_READY_EVENT, onReady);
    }
  }, 200);
  const deadline = setTimeout(() => {
    if (done) return;
    done = true;
    cleanup();
    console.error('[TUIChat] chat SDK not ready after 35s, conversation switch aborted');
    uni.showToast({ title: '消息服务初始化超时，请返回重试', icon: 'none' });
  }, CHAT_READY_TIMEOUT);
};

export const logout = (flag: boolean) => {
  if (flag) {
    return TUILogin.logout();
  }
  return Promise.resolve();
};
