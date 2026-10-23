<template>
  <div
    :class="{
      'tui-chat': true,
      'tui-chat-h5': isMobile,
    }"
    @click="onMessageListBackgroundClick"
  >
    <!-- <JoinGroupCard /> -->
    <div class="tui-chat-main">
      <div
        v-if="isOfficial"
        class="tui-chat-safe-tips"
      >
        <span>
          {{
            TUITranslateService.t(
              "TUIChat.【安全提示】本 APP 仅用于体验腾讯云即时通信 IM 产品功能，不可用于业务洽谈与拓展。请勿轻信汇款、中奖等涉及钱款的信息，勿轻易拨打陌生电话，谨防上当受骗。"
            )
          }}
        </span>
        <a @click="openComplaintLink(Link.complaint)">{{
          TUITranslateService.t("TUIChat.点此投诉")
        }}</a>
      </div>
      <MessageGroupApplication
        v-if="isGroup"
        :key="props.groupID"
        :groupID="props.groupID"
      />
      <scroll-view
        id="messageScrollList"
        class="tui-message-list"
        scroll-y="true"
        :scroll-top="scrollTop"
        :scroll-into-view="`tui-${historyFirstMessageID}`"
        @scroll="handelScrollListScroll"
      >
        <p
          v-if="!isCompleted || (!isGroup && dbHasMore)"
          class="message-more"
          @click="getHistoryMessageList"
        >
          {{ TUITranslateService.t("TUIChat.查看更多") }}
        </p>
        <li
          v-for="(item, index) in messageList"
          :id="`tui-${item.ID}`"
          :key="item.vueForRenderKey"
          :class="'message-li ' + item.flow"
        >
          <MessageTimestamp
            :currTime="item.time"
            :prevTime="index > 0 ? messageList[index - 1].time : 0"
          />
          <div
            class="message-item"
            @click="toggleID = ''"
          >
            <MessageTip
              v-if="item.type === TYPES.MSG_GRP_TIP ||
                isCreateGroupCustomMessage(item)
              "
              :content="item.getMessageContent()"
            />
            <div
              v-else-if="!item.isRevoked && !isPluginMessage(item)"
              :id="`msg-bubble-${item.ID}`"
              class="message-bubble-container"
              @longpress="handleToggleMessageItem($event, item, index, true)"
              @touchstart="handleH5LongPress($event, item, index, 'touchstart')"
              @touchend="handleH5LongPress($event, item, index, 'touchend')"
              @mouseover="handleH5LongPress($event, item, index, 'touchend')"
            >
              <MessageBubble
                :messageItem="deepCopy(item)"
                :content="item.getMessageContent()"
                :isAudioPlayed="audioPlayedMapping[item.ID]"
                :blinkMessageIDList="blinkMessageIDList"
                :isMultipleSelectMode="isMultipleSelectMode"
                :multipleSelectedMessageIDList="multipleSelectedMessageIDList"
                @resendMessage="resendMessage(item)"
                @blinkMessage="blinkMessage"
                @scrollTo="scrollTo"
                @changeSelectMessageIDList="changeSelectMessageIDList"
                @setReadReceiptPanelVisible="setReadReceiptPanelVisible"
              >
                <MessageText
                  v-if="item.type === TYPES.MSG_TEXT"
                  :content="item.getMessageContent()"
                  :messageItem="item"
                />
                <ProgressMessage
                  v-else-if="item.type === TYPES.MSG_IMAGE"
                  :content="item.getMessageContent()"
                  :messageItem="deepCopy(item)"
                >
                  <MessageImage
                    :content="item.getMessageContent()"
                    :messageItem="item"
                    @previewImage="handleImagePreview(index)"
                  />
                </ProgressMessage>
                <ProgressMessage
                  v-else-if="item.type === TYPES.MSG_VIDEO"
                  :content="item.getMessageContent()"
                  :messageItem="deepCopy(item)"
                >
                  <MessageVideo
                    :content="item.getMessageContent()"
                    :messageItem="item"
                  />
                </ProgressMessage>
                <MessageAudio
                  v-else-if="item.type === TYPES.MSG_AUDIO"
                  :content="item.getMessageContent()"
                  :messageItem="item"
                  :broadcastNewAudioSrc="broadcastNewAudioSrc"
                  @setAudioPlayed="setAudioPlayed"
                  @getGlobalAudioContext="getGlobalAudioContext"
                />
                <MessageRecord
                  v-else-if="item.type === TYPES.MSG_MERGER"
                  :renderData="item.payload"
                  :messageItem="item"
                  @assignMessageIDInUniapp="assignMessageIDInUniapp"
                />
                <MessageFile
                  v-else-if="item.type === TYPES.MSG_FILE"
                  :content="item.getMessageContent()"
                />
                <MessageFace
                  v-else-if="item.type === TYPES.MSG_FACE"
                  :content="item.getMessageContent()"
                />
                <MessageLocation
                  v-else-if="item.type === TYPES.MSG_LOCATION"
                  :content="item.getMessageContent()"
                />
                <MessageCustom
                  v-else-if="item.type === TYPES.MSG_CUSTOM"
                  :content="item.getMessageContent()"
                  :messageItem="item"
                />
              </MessageBubble>
            </div>
            <MessagePlugin
              v-else-if="!item.isRevoked && isPluginMessage(item)"
              :message="item"
              @resendMessage="resendMessage"
              @handleToggleMessageItem="handleToggleMessageItem"
              @handleH5LongPress="handleH5LongPress"
            />
            <MessageRevoked
              v-else
              :isEdit="item.type === TYPES.MSG_TEXT"
              :messageItem="item"
              @messageEdit="handleEdit(item)"
            />
            <!-- message tool -->
            <MessageTool
              v-if="item.ID === toggleID"
              :class="{
                'message-tool': true,
                'message-tool-out': item.flow === 'out',
                'message-tool-in': item.flow === 'in',
              }"
              :messageItem="item"
              :isMultipleSelectMode="isMultipleSelectMode"
              @toggleMultipleSelectMode="() => emits('toggleMultipleSelectMode')"
            />
          </div>
        </li>
      </scroll-view>
      <!-- scroll button -->
      <ScrollButton
        ref="scrollButtonInstanceRef"
        @scrollToLatestMessage="scrollToLatestMessage"
      />
      <Dialog
        v-if="reSendDialogShow"
        :show="reSendDialogShow"
        :isH5="!isPC"
        :center="true"
        :isHeaderShow="isPC"
        @submit="resendMessageConfirm()"
        @update:show="(e) => (reSendDialogShow = e)"
      >
        <p class="delDialog-title">
          {{ TUITranslateService.t("TUIChat.确认重发该消息？") }}
        </p>
      </Dialog>
      <!-- read receipt panel -->
      <ReadReceiptPanel
        v-if="isShowReadUserStatusPanel"
        :message="Object.assign({}, readStatusMessage)"
        @setReadReceiptPanelVisible="setReadReceiptPanelVisible"
      />
      <!-- simple message list -->
      <Drawer
        :visible="isShowSimpleMessageList"
        :overlayColor="'transparent'"
        :popDirection="'right'"
      >
        <SimpleMessageList
          :style="{height: '100%'}"
          :isMounted="isShowSimpleMessageList"
          :messageID="simpleMessageListRenderMessageID"
          @closeOverlay="isShowSimpleMessageList = false"
        />
      </Drawer>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {
  ref,
  watch,
  nextTick,
  onMounted,
  onUnmounted,
  getCurrentInstance,
} from '../../../adapter-vue';
import TUIChatEngine, {
  IMessageModel,
  TUIStore,
  StoreName,
  TUITranslateService,
  TUIChatService,
} from '@tencentcloud/chat-uikit-engine-lite';
import {
  setInstanceMapping,
  getBoundingClientRect,
  getScrollInfo,
} from '@tencentcloud/universal-api';
// import { JoinGroupCard } from '@trtc/calls-uikit-wx';
import Link from './link';
import SimpleMessageList from './message-elements/simple-message-list/index.vue';
import MessageGroupApplication from './message-group-application/index.vue';
import MessageText from './message-elements/message-text.vue';
import MessageImage from './message-elements/message-image.vue';
import MessageAudio from './message-elements/message-audio.vue';
import MessageRecord from './message-elements/message-record/index.vue';
import MessageFile from './message-elements/message-file.vue';
import MessageFace from './message-elements/message-face.vue';
import MessageCustom from './message-elements/message-custom.vue';
import MessageTip from './message-elements/message-tip.vue';
import MessageBubble from './message-elements/message-bubble.vue';
import MessageLocation from './message-elements/message-location.vue';
import MessageTimestamp from './message-elements/message-timestamp.vue';
import MessageVideo from './message-elements/message-video.vue';
import MessageTool from './message-tool/index.vue';
import MessageRevoked from './message-tool/message-revoked.vue';
import MessagePlugin from '../../../plugins/plugin-components/message-plugin.vue';
import ReadReceiptPanel from './read-receipt-panel/index.vue';
import ScrollButton from './scroll-button/index.vue';
import { isPluginMessage } from '../../../plugins/plugin-components/index';
import Dialog from '../../common/Dialog/index.vue';
import Drawer from '../../common/Drawer/index.vue';
import { Toast, TOAST_TYPE } from '../../common/Toast/index';
import ProgressMessage from '../../common/ProgressMessage/index.vue';
import { isCreateGroupCustomMessage } from '../utils/utils';
import { isEnabledMessageReadReceiptGlobal, deepCopy } from '../utils/utils';
import { throttle } from '../../../utils/lodash';
import { isPC, isH5, isMobile } from '../../../utils/env';
import chatStorage from '../utils/chatStorage';
import { fetchImHistoryPage } from '@/utils/im';
import { buildImHistoryMessages } from '@/utils/im-history';
import { IAudioContext } from '../../../interface';

interface IEmits {
  (e: 'closeInputToolBar'): void;
  (e: 'handleEditor', message: IMessageModel, type: string): void;
  (key: 'toggleMultipleSelectMode'): void;
}

interface IProps {
  isGroup: boolean;
  groupID: string;
  isNotInGroup: boolean;
  isMultipleSelectMode: boolean;
}

const emits = defineEmits<IEmits>();
const props = withDefaults(defineProps<IProps>(), {
  isGroup: false,
  groupID: '',
  isNotInGroup: false,
  isMultipleSelectMode: false,
});

let selfAddValue = 0;
let observer: any = null;
let groupType: string | undefined;
const sentReceiptMessageID = new Set<string>();
const isOfficial = TUIStore.getData(StoreName.APP, 'isOfficial');
const thisInstance = getCurrentInstance()?.proxy || getCurrentInstance();

const messageList = ref<IMessageModel[]>();
const multipleSelectedMessageIDList = ref<string[]>([]);
const isCompleted = ref(false);
// SDK 漫游到头后是否还有更早的数据库历史可翻；点过一次取到空页就收起「查看更多」
const dbHasMore = ref(true);
const currentConversationID = ref('');
const toggleID = ref('');
const scrollTop = ref(5000); // The initial number of messages is 15, and the maximum message height is 300.
const TYPES = ref(TUIChatEngine.TYPES);
const isLoadingMessage = ref(false);
const isLongpressing = ref(false);
const blinkMessageIDList = ref<string[]>([]);
const messageTarget = ref<IMessageModel>();
const scrollButtonInstanceRef = ref<InstanceType<typeof ScrollButton>>();
const historyFirstMessageID = ref<string>('');
const isShowSimpleMessageList = ref<boolean>(false);
const simpleMessageListRenderMessageID = ref<string>();
const audioPlayedMapping = ref<Record<string, boolean>>({});

// audio control
const broadcastNewAudioSrc = ref<string>('');

const readStatusMessage = ref<IMessageModel>();
const isShowReadUserStatusPanel = ref<boolean>(false);

// Resend Message Dialog
const reSendDialogShow = ref(false);
const resendMessageData = ref();

const scrollToBottom = () => {
  scrollTop.value += 1;
};

const onCurrentConversationIDUpdated = (conversationID: string) => {
  currentConversationID.value = conversationID;
  // 切会话时引擎会清空 CHAT store 的消息列表，数据库翻页状态一并重置
  dbHasMore.value = true;
  if (isEnabledMessageReadReceiptGlobal()) {
    const { groupProfile }
      = TUIStore.getConversationModel(conversationID) || {};
    groupType = groupProfile?.type;
  }

  if (Object.keys(audioPlayedMapping.value).length > 0) {
    // Synchronize storage about whether the audio has been played when converstaion switched
    chatStorage.setChatStorage('audioPlayedMapping', audioPlayedMapping.value);
  }
};

onMounted(() => {
  // Retrieve the information about whether the audio has been played from localStorage
  audioPlayedMapping.value = chatStorage.getChatStorage('audioPlayedMapping') || {};

  TUIStore.watch(StoreName.CHAT, {
    messageList: onMessageListUpdated,
    messageSource: onMessageSourceUpdated,
    isCompleted: onChatCompletedUpdated,
  });

  TUIStore.watch(StoreName.CONV, {
    currentConversationID: onCurrentConversationIDUpdated,
  });

  setInstanceMapping('messageList', thisInstance);

  uni.$on('scroll-to-bottom', scrollToLatestMessage);
});

onUnmounted(() => {
  TUIStore.unwatch(StoreName.CHAT, {
    messageList: onMessageListUpdated,
    isCompleted: onChatCompletedUpdated,
  });

  TUIStore.unwatch(StoreName.CONV, {
    currentConversationID: onCurrentConversationIDUpdated,
  });

  observer?.disconnect();
  observer = null;

  uni.$off('scroll-to-bottom');

  if (Object.keys(audioPlayedMapping.value).length > 0) {
    // Synchronize storage about whether the audio has been played when the component is unmounted
    chatStorage.setChatStorage('audioPlayedMapping', audioPlayedMapping.value);
  }
});

const handelScrollListScroll = throttle(
  function (e: Event) {
    scrollButtonInstanceRef.value?.judgeScrollOverOneScreen(e);
  },
  500,
  { leading: true },
);

function getGlobalAudioContext(
  audioMap: Map<string, IAudioContext>,
  options?: { newAudioSrc: string },
) {
  if (options?.newAudioSrc) {
    broadcastNewAudioSrc.value = options.newAudioSrc;
  }
}

async function onMessageListUpdated(list: IMessageModel[]) {
  observer?.disconnect();
  messageList.value = list
    .filter(message => !message.isDeleted)
    .map((message) => {
      message.vueForRenderKey = `${message.ID}`;
      return message;
    });
  const newLastMessage = messageList.value?.[messageList.value?.length - 1];
  if (messageTarget.value) {
    // scroll to target message
    scrollAndBlinkMessage(messageTarget.value);
  } else if (!isLoadingMessage.value && !(scrollButtonInstanceRef.value?.isScrollButtonVisible && newLastMessage?.flow === 'in')) {
    // scroll to bottom
    nextTick(() => {
      scrollToLatestMessage();
    });
  }
  if (isEnabledMessageReadReceiptGlobal()) {
    nextTick(() => bindIntersectionObserver());
  }
}

async function scrollToLatestMessage() {
  try {
    const { scrollHeight } = await getScrollInfo(
      '#messageScrollList',
      'messageList',
    );
    if (scrollHeight) {
      scrollTop.value = scrollHeight + 1;
    } else {
      scrollToBottom();
    }
  } catch (error) {
    scrollToBottom();
  }
}

async function onMessageSourceUpdated(message: IMessageModel) {
  messageTarget.value = message;
  scrollAndBlinkMessage(messageTarget.value);
}

function scrollAndBlinkMessage(message: IMessageModel) {
  if (
    messageList.value?.some(
      messageListItem => messageListItem?.ID === message?.ID,
    )
  ) {
    nextTick(async () => {
      await scrollToTargetMessage(message);
      await blinkMessage(message?.ID);
      messageTarget.value = undefined;
    });
  }
}

function onChatCompletedUpdated(flag: boolean) {
  isCompleted.value = flag;
}

const getHistoryMessageList = () => {
  if (isLoadingMessage.value) return;
  if (isCompleted.value && !props.isGroup) {
    // SDK 漫游窗口到头（免费版只有 7 天），更早的历史改读本系统数据库落库的消息镜像
    loadDatabaseHistoryPage();
    return;
  }
  isLoadingMessage.value = true;
  const currentFirstMessageID = messageList.value?.[0]?.ID || '';
  TUIChatService.getMessageList().then(() => {
    nextTick(() => {
      historyFirstMessageID.value = currentFirstMessageID;
      const timer = setTimeout(() => {
        historyFirstMessageID.value = '';
        isLoadingMessage.value = false;
        clearTimeout(timer);
      }, 500);
    });
  });
};

/** 向数据库取比当前最早一条更早的一页消息，按 SDK 消息结构前插到消息列表。 */
async function loadDatabaseHistoryPage() {
  const earliestTime = messageList.value?.[0]?.time;
  if (!earliestTime) return;
  isLoadingMessage.value = true;
  const currentFirstMessageID = messageList.value?.[0]?.ID || '';
  try {
    const page = await fetchImHistoryPage(currentConversationID.value, earliestTime);
    dbHasMore.value = page.hasMore;
    if (!page.messages.length) return;
    const conversationModel: any =
      TUIStore.getConversationModel(currentConversationID.value) || {};
    const selfProfile: any = TUIStore.getData(StoreName.USER, 'userProfile') || {};
    const peerProfile: any = conversationModel.userProfile || {};
    const userInfo: Record<string, any> = {};
    if (conversationModel.conversationID) {
      userInfo[String(conversationModel.conversationID).replace(/^C2C/, '')] = {
        nick: peerProfile.nick || '',
        avatar: peerProfile.avatar || '',
      };
    }
    if (selfProfile.userID) {
      userInfo[selfProfile.userID] = {
        nick: selfProfile.nick || '',
        avatar: selfProfile.avatar || '',
      };
    }
    const messages = buildImHistoryMessages(page.messages, {
      conversationID: currentConversationID.value,
      myIMID: selfProfile.userID || '',
      needReadReceipt: isEnabledMessageReadReceiptGlobal(),
      userInfo,
    });
    if (!messages.length) {
      // 整页都是不支持重建的类型：继续往前取，否则按钮点下去没反应
      if (page.hasMore) loadDatabaseHistoryPage();
      return;
    }
    // unshift 合并：按 ID 去重、前插、重排，且不会触发已读上报
    TUIChatService.updateMessageList(messages as any, 'unshift');
    nextTick(() => {
      historyFirstMessageID.value = currentFirstMessageID;
      const timer = setTimeout(() => {
        historyFirstMessageID.value = '';
        clearTimeout(timer);
      }, 500);
    });
  } catch (e: any) {
    Toast({
      message: e?.message || '加载更早消息失败',
      type: TOAST_TYPE.ERROR,
    });
  } finally {
    isLoadingMessage.value = false;
  }
}

const openComplaintLink = () => { };

// toggle message
const handleToggleMessageItem = (
  e: any,
  message: IMessageModel,
  index: number,
  isLongpress = false,
) => {
  if (props.isMultipleSelectMode || props.isNotInGroup) {
    return;
  }
  if (isLongpress) {
    isLongpressing.value = true;
  }
  toggleID.value = message.ID;
};

// h5 long press
let timer: number;
const handleH5LongPress = (
  e: any,
  message: IMessageModel,
  index: number,
  type: string,
) => {
  if (props.isMultipleSelectMode || props.isNotInGroup) {
    return;
  }
  if (!isH5) return;
  function longPressHandler() {
    clearTimeout(timer);
    handleToggleMessageItem(e, message, index, true);
  }
  function touchStartHandler() {
    timer = setTimeout(longPressHandler, 500);
  }
  function touchEndHandler() {
    clearTimeout(timer);
  }
  switch (type) {
    case 'touchstart':
      touchStartHandler();
      break;
    case 'touchend':
      touchEndHandler();
      setTimeout(() => {
        isLongpressing.value = false;
      }, 200);
      break;
  }
};

// reedit message
const handleEdit = (message: IMessageModel) => {
  emits('handleEditor', message, 'reedit');
};

const resendMessage = (message: IMessageModel) => {
  reSendDialogShow.value = true;
  resendMessageData.value = message;
};

const handleImagePreview = (index: number) => {
  if (!messageList.value) {
    return;
  }
  const imageMessageIndex: number[] = [];
  const imageMessageList: IMessageModel[] = messageList.value.filter((item, index) => {
    if (
      !item.isRevoked
      && !item.hasRiskContent
      && item.type === TYPES.value.MSG_IMAGE
    ) {
      imageMessageIndex.push(index);
      return true;
    }
    return false;
  });
  uni.previewImage({
    current: imageMessageIndex.indexOf(index),
    urls: imageMessageList.map(message => message.payload.imageInfoArray?.[2].url),
    // #ifdef APP-PLUS
    indicator: 'number',
    // #endif
  });
};

const resendMessageConfirm = () => {
  reSendDialogShow.value = !reSendDialogShow.value;
  const messageModel = resendMessageData.value;
  messageModel.resendMessage();
};

function blinkMessage(messageID: string): Promise<void> {
  return new Promise((resolve) => {
    const index = blinkMessageIDList.value.indexOf(messageID);
    if (index < 0) {
      blinkMessageIDList.value.push(messageID);
      const timer = setTimeout(() => {
        blinkMessageIDList.value.splice(
          blinkMessageIDList.value.indexOf(messageID),
          1,
        );
        clearTimeout(timer);
        resolve();
      }, 3000);
    }
  });
}

function scrollTo(scrollHeight: number) {
  scrollTop.value = scrollHeight;
}

async function bindIntersectionObserver() {
  if (!messageList.value || messageList.value.length === 0) {
    return;
  }

  if (
    groupType === TYPES.value.GRP_AVCHATROOM
    || groupType === TYPES.value.GRP_COMMUNITY
  ) {
    // AVCHATROOM and COMMUNITY chats do not monitor read receipts for messages.
    return;
  }

  observer?.disconnect();
  observer = uni
    .createIntersectionObserver(thisInstance, {
      threshold: [0.7],
      observeAll: true,
      // In Uni-app, the `safetip` is also included, so a negative margin is needed to exclude it.
    })
    .relativeTo('#messageScrollList', { top: -70 });

  observer?.observe('.message-li.in .message-bubble-container', (res: any) => {
    if (sentReceiptMessageID.has(res.id)) {
      return;
    }
    const matchingMessage = messageList.value.find((message: IMessageModel) => {
      return res.id.indexOf(message.ID) > -1;
    });
    if (
      matchingMessage
      && matchingMessage.needReadReceipt
      && matchingMessage.flow === 'in'
      && !matchingMessage.readReceiptInfo?.isPeerRead
    ) {
      TUIChatService.sendMessageReadReceipt([matchingMessage]);
      sentReceiptMessageID.add(res.id);
    }
  });
}

function setReadReceiptPanelVisible(visible: boolean, message?: IMessageModel) {
  if (visible && props.isNotInGroup) {
    return;
  }
  if (!visible) {
    readStatusMessage.value = undefined;
  } else {
    readStatusMessage.value = message;
  }
  isShowReadUserStatusPanel.value = visible;
}

async function scrollToTargetMessage(message: IMessageModel) {
  const targetMessageID = message.ID;
  const isTargetMessageInScreen
    = messageList.value
    && messageList.value.some(msg => msg.ID === targetMessageID);
  if (targetMessageID && isTargetMessageInScreen) {
    const timer = setTimeout(async () => {
      try {
        const scrollViewRect = await getBoundingClientRect(
          '#messageScrollList',
          'messageList',
        );
        const originalMessageRect = await getBoundingClientRect(
          '#tui-' + targetMessageID,
          'messageList',
        );
        const { scrollTop } = await getScrollInfo(
          '#messageScrollList',
          'messageList',
        );
        const finalScrollTop
          = originalMessageRect.top
          + scrollTop
          - scrollViewRect.top
          - (selfAddValue++ % 2);
        scrollTo(finalScrollTop);
        clearTimeout(timer);
      } catch (error) {
        // todo
      }
    }, 500);
  } else {
    Toast({
      message: TUITranslateService.t('TUIChat.无法定位到原消息'),
      type: TOAST_TYPE.WARNING,
    });
  }
}

function onMessageListBackgroundClick() {
  emits('closeInputToolBar');
}

watch(() => props.isMultipleSelectMode, (newValue) => {
  if (!newValue) {
    changeSelectMessageIDList({
      type: 'clearAll',
      messageID: '',
    });
  }
});

function changeSelectMessageIDList({ type, messageID }: { type: 'add' | 'remove' | 'clearAll'; messageID: string }) {
  // TODO need to delete this
  if (type === 'clearAll') {
    multipleSelectedMessageIDList.value = [];
  } else if (type === 'add' && !multipleSelectedMessageIDList.value.includes(messageID)) {
    multipleSelectedMessageIDList.value.push(messageID);
  } else if (type === 'remove') {
    multipleSelectedMessageIDList.value = multipleSelectedMessageIDList.value.filter(id => id !== messageID);
  }
}

function mergeForwardMessage() {
  TUIStore.update(StoreName.CUSTOM, 'multipleForwardMessageID', {
    isMergeForward: true,
    messageIDList: multipleSelectedMessageIDList.value,
  });
}

function oneByOneForwardMessage() {
  TUIStore.update(StoreName.CUSTOM, 'multipleForwardMessageID', {
    isMergeForward: false,
    messageIDList: multipleSelectedMessageIDList.value,
  });
}

function assignMessageIDInUniapp(messageID: string) {
  simpleMessageListRenderMessageID.value = messageID;
  isShowSimpleMessageList.value = true;
}

function setAudioPlayed(messageID: string) {
  audioPlayedMapping.value[messageID] = true;
}

defineExpose({
  oneByOneForwardMessage,
  mergeForwardMessage,
  scrollToLatestMessage,
});
</script>
<style lang="scss" scoped src="./style/index.scss"></style>
