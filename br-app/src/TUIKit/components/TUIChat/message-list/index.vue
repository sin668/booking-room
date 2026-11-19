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
        :scroll-anchoring="true"
        :scroll-top="scrollTop"
        @scroll="handelScrollListScroll"
      >
        <div id="messageScrollContent">
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
        </div>
      </scroll-view>
      <!-- 加载指示覆盖在消息区顶部，不占内容高度，避免干扰前插高度差核算 -->
      <div
        v-if="isLoadingMessage"
        class="message-loading-overlay"
      >
        <span class="message-loading-spinner" />
      </div>
      <!-- 离屏镜像：插入前预测量这批历史的高度，使「前插 + scroll-top 补偿」同一次 setData 生效，
           第一帧即定位正确，彻底消除先画错位帧再拉回的过渡。visibility:hidden 保留布局可测高。 -->
      <div
        id="measureMirror"
        class="measure-mirror"
        aria-hidden="true"
      >
        <li
          v-for="(item, index) in measureMessages"
          :key="'measure-' + item.ID"
          :class="'message-li ' + item.flow"
        >
          <MessageTimestamp
            :currTime="item.time"
            :prevTime="index > 0 ? measureMessages[index - 1].time : 0"
          />
          <div class="message-item">
            <MessageTip
              v-if="item.type === TYPES.MSG_GRP_TIP || isCreateGroupCustomMessage(item)"
              :content="item.getMessageContent()"
            />
            <div
              v-else-if="!item.isRevoked && !isPluginMessage(item)"
              class="message-bubble-container"
            >
              <MessageBubble
                :messageItem="deepCopy(item)"
                :content="item.getMessageContent()"
                :isAudioPlayed="true"
                :blinkMessageIDList="[]"
                :isMultipleSelectMode="false"
                :multipleSelectedMessageIDList="[]"
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
                  :isAudioPlayed="true"
                  :broadcastNewAudioSrc="''"
                />
                <MessageRecord
                  v-else-if="item.type === TYPES.MSG_MERGER"
                  :renderData="item.payload"
                  :messageItem="item"
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
            />
            <MessageRevoked
              v-else
              :isEdit="item.type === TYPES.MSG_TEXT"
              :messageItem="item"
            />
          </div>
        </li>
      </div>
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
// 离屏镜像批次：插入真实列表前先渲染到隐藏镜像量高，供原子前插补偿用
const measureMessages = ref<IMessageModel[]>([]);
const multipleSelectedMessageIDList = ref<string[]>([]);
const isCompleted = ref(false);
// SDK 漫游到头后是否还有更早的数据库历史可翻；取到空页即置 false，停止自动续拉
const dbHasMore = ref(true);
const currentConversationID = ref('');
const toggleID = ref('');
const scrollTop = ref(0);
const TYPES = ref(TUIChatEngine.TYPES);
const isLoadingMessage = ref(false);
const isLongpressing = ref(false);
const blinkMessageIDList = ref<string[]>([]);
const messageTarget = ref<IMessageModel>();
const scrollButtonInstanceRef = ref<InstanceType<typeof ScrollButton>>();
// 滚底统一用数值 scroll-top：原生 scroll-view 会把它 clamp 到最大滚动位置（即底部），
// 不会滚出内容外。不用 scroll-into-view 锚末条——它把末条「顶部」对齐视口顶部，
// 末条高度不足一屏时会滚过内容末尾，出现整屏白屏，再点一次才恢复。
// 递增哨兵保证每次设值都不同：手动滚动后 ref 不跟随原生位置，同值重设不会触发滚动。
let bottomScrollSeq = 0;
// 自动续拉防抖：上一轮续拉没有新增消息时停止，避免原地打转刷接口
let autoFillLastCount = -1;
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
  scrollTop.value = 1e9 + (++bottomScrollSeq);
};

// 末条变化（初次加载/收到新消息）才滚底；前插历史末条不变，这里不触发，
// 前插后的视口复位由 anchorPrepend 用高度差补偿 scroll-top 完成。
watch(
  () => {
    const list = messageList.value;
    return list?.[list.length - 1]?.ID || '';
  },
  (newLast, oldLast) => {
    if (messageTarget.value) return;
    if (newLast && newLast !== oldLast) {
      const lastFlow = messageList.value?.[messageList.value.length - 1]?.flow;
      if (!(scrollButtonInstanceRef.value?.isScrollButtonVisible && lastFlow === 'in')) {
        scrollToBottom();
      }
    }
  },
);

interface ScrollMeasure { top: number; height: number; vp: number }

/** 测当前滚动位置、内容总高与视口高。小程序 scrollOffset 不返回 scrollHeight，内容高改测包裹层。 */
async function measureScroll(): Promise<ScrollMeasure | null> {
  try {
    const content = await getBoundingClientRect('#messageScrollContent', 'messageList');
    const view = await getBoundingClientRect('#messageScrollList', 'messageList');
    const { scrollTop } = await getScrollInfo('#messageScrollList', 'messageList');
    return { top: scrollTop || 0, height: content?.height || 0, vp: view?.height || 0 };
  } catch {
    return null;
  }
}

/** 前插渲染后只补测一次内容总高（单查询），把兜底补偿的过渡压到最短。 */
async function measureContentHeight(): Promise<number> {
  try {
    const rect = await getBoundingClientRect('#messageScrollContent', 'messageList');
    return rect?.height || 0;
  } catch {
    return 0;
  }
}

/**
 * 前插历史后复位视口：目标 scrollTop = 原 scrollTop + 内容高度差，使原首条停在原来的视觉位置。
 * 这是全平台一致的确定性兜底，不依赖 scroll-into-view 的渲染时序；iOS/Skyline 的原生
 * scroll-anchoring 与安卓 webview 的 overflow-anchor 若已原子补偿，本式算出的目标值与之相同，
 * 再设一次也幂等不会二次跳动。加载前内容不足一屏（初次加载/自动续拉）时改为滚到底看最新。
 */
function anchorPrepend(before: ScrollMeasure | null, afterHeight: number) {
  if (!before || !afterHeight) return;
  const delta = afterHeight - before.height;
  if (delta <= 0) return;
  const target = before.height <= before.vp + 10 ? afterHeight : before.top + delta;
  scrollTo(target);
}

/** 把批次渲染进离屏镜像量高（visibility:hidden 保留布局），得到前插后会增加的内容高度。 */
async function measureBatchHeight(batch: IMessageModel[]): Promise<number> {
  if (!batch.length) return 0;
  measureMessages.value = batch;
  await nextTick();
  try {
    const rect = await getBoundingClientRect('#measureMirror', 'messageList');
    return rect?.height || 0;
  } catch {
    return 0;
  }
}

/**
 * 原子前插：同一次 flush 内「设目标 scroll-top + 清镜像 + 前插真实列表 + 复位加载态」，
 * 渲染层在绘制前同时应用列表与滚动位置，第一帧即定位正确，没有先画错位再拉回的过渡帧。
 * delta 来自插入前的离屏镜像预测量；before 为插入前基准（spinner 已移出内容流，不占高度）。
 */
function commitPrepend(batch: IMessageModel[], before: ScrollMeasure | null, delta: number) {
  if (before && delta > 0) {
    scrollTop.value = before.height <= before.vp + 10
      ? before.height + delta
      : before.top + delta;
  }
  measureMessages.value = [];
  TUIChatService.updateMessageList(batch as any, 'unshift');
  isLoadingMessage.value = false;
}

/**
 * 原子前插后的安全网：仅当真实位置与理想位置偏差明显（>40px，如同帧 scroll-top 被旧高度钳制、
 * 缺尺寸图片加载后大幅撑高）才用 +1px 微 nudging 强制重设复位；阈值内的小残差（原首条时间戳显隐等）
 * 忽略，避免再产生一次可见滚动。原子前插已到位时本函数不动，无额外绘制。
 */
async function verifyPrepend(before: ScrollMeasure | null, delta: number) {
  if (!before) return;
  await nextTick();
  try {
    const actualHeight = await measureContentHeight();
    const { scrollTop: actualTop } = await getScrollInfo('#messageScrollList', 'messageList');
    if (!actualHeight) return;
    const actualDelta = actualHeight - before.height;
    const ideal = before.height <= before.vp + 10 ? actualHeight : before.top + actualDelta;
    if (Math.abs((actualTop || 0) - ideal) > 40) {
      scrollTop.value = ideal + 1;
    }
  } catch {
    // 测量失败不强行复位
  }
}

const onCurrentConversationIDUpdated = (conversationID: string) => {
  currentConversationID.value = conversationID;
  // 切会话时引擎会清空 CHAT store 的消息列表，数据库翻页状态一并重置
  dbHasMore.value = true;
  autoFillLastCount = -1;
  measureMessages.value = [];
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
  // 会话可能在本组件挂载前就已切换，watcher 补不上这一次
  currentConversationID.value = TUIStore.getData(StoreName.CONV, 'currentConversationID') || '';

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
    // 滚动到顶部时自动加载更多历史消息
    const detail = (e as any).detail || {};
    const scrollTop = detail.scrollTop || 0;
    const canLoadMore = !isCompleted.value || (!props.isGroup && dbHasMore.value);
    if (scrollTop < 50 && canLoadMore && !isLoadingMessage.value) {
      getHistoryMessageList();
    }
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
  if (messageTarget.value) {
    // scroll to target message
    scrollAndBlinkMessage(messageTarget.value);
  }
  if (isEnabledMessageReadReceiptGlobal()) {
    nextTick(() => bindIntersectionObserver());
  }
  // 内容不足一屏时自动续拉历史，避免消息很少就停在顶部
  nextTick(() => autoFillViewport());
}

function scrollToLatestMessage() {
  scrollToBottom();
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
  // 全部消息都超出 SDK 漫游窗口（免费版 7 天）时，引擎只会给回空列表，此时直接从数据库取最近一页
  if (flag && !props.isGroup && !TUIStore.getData(StoreName.CHAT, 'messageList')?.length) {
    loadDatabaseHistoryPage();
  }
}

const getHistoryMessageList = async () => {
  if (isLoadingMessage.value) return;
  if (isCompleted.value && !props.isGroup) {
    // SDK 漫游窗口到头（免费版只有 7 天），更早的历史改读本系统数据库落库的消息镜像
    loadDatabaseHistoryPage();
    return;
  }
  isLoadingMessage.value = true;
  // 前插前先量一次（含加载态 spinner），前插渲染后再量一次，高度差即本批历史占位
  const before = await measureScroll();
  try {
    await TUIChatService.getMessageList();
    await nextTick();
    const afterHeight = await measureContentHeight();
    anchorPrepend(before, afterHeight);
    isLoadingMessage.value = false;
    autoFillViewport();
  } catch {
    // SDK 不可用时若不复位，自动加载就永久卡住了
    isLoadingMessage.value = false;
  }
};

/** 内容不足一屏时自动往前续拉，直到铺满视口或没有更多历史，免去手点「查看更多」。 */
async function autoFillViewport() {
  if (isLoadingMessage.value) return;
  const canLoadMore = !isCompleted.value || (!props.isGroup && dbHasMore.value);
  if (!canLoadMore) return;
  const count = messageList.value?.length || 0;
  if (count === autoFillLastCount) return;
  try {
    // 小程序 scrollOffset 不返回 scrollHeight，改测内容包裹层高度
    const { height: contentHeight } = await getBoundingClientRect('#messageScrollContent', 'messageList');
    const { height } = await getBoundingClientRect('#messageScrollList', 'messageList');
    if (contentHeight && height && contentHeight <= height + 10) {
      autoFillLastCount = count;
      getHistoryMessageList();
    }
  } catch {
    // 测量失败时不强行续拉
  }
}

/** 向数据库取比当前最早一条更早的一页消息，按 SDK 消息结构前插到消息列表。 */
async function loadDatabaseHistoryPage(cursor?: number, before?: ScrollMeasure | null) {
  // 游标取列表最早一条；SDK 一条都没给时（深历史会话）没有游标可用，用当前时间取最近一页
  const earliestTime =
    cursor ||
    TUIStore.getData(StoreName.CHAT, 'messageList')?.[0]?.time ||
    Math.floor(Date.now() / 1000);
  isLoadingMessage.value = true;
  // 递归续取时沿用首次量到的基准，保证高度差补偿对齐用户触发加载那一刻的视口
  if (before === undefined) before = await measureScroll();
  try {
    const page = await fetchImHistoryPage(currentConversationID.value, earliestTime);
    dbHasMore.value = page.hasMore;
    if (!page.messages.length) {
      isLoadingMessage.value = false;
      return;
    }
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
      // 整页都是不支持重建的类型：带上本页最早时间继续往前取，否则游标不变会原地打转
      if (page.hasMore) {
        loadDatabaseHistoryPage(Math.min(...page.messages.map(row => row.msg_time)), before);
        return;
      }
      isLoadingMessage.value = false;
      return;
    }
    // 插入前先用离屏镜像量出这批历史的高度，再原子前插：前插与 scroll-top 补偿同一次 setData，
    // 第一帧即定位正确，彻底消除「先画错位帧再拉回」的过渡（unshift 按 ID 去重、不上报已读）
    const delta = await measureBatchHeight(messages);
    commitPrepend(messages, before, delta);
    // 安全网：仅在真实位置明显偏离时微调，原子前插已到位则不动
    await verifyPrepend(before, delta);
    autoFillViewport();
  } catch (e: any) {
    isLoadingMessage.value = false;
    Toast({
      message: e?.message || '加载更早消息失败',
      type: TOAST_TYPE.ERROR,
    });
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
  // 原生图片预览会触发页面 onHide/onShow，先标记预览中，避免会话被 reset 后重新拉到最新消息
  uni.$emit('media-preview-start');
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
<style lang="scss" scoped>
// 让浏览器原生滚动锚定接管前插：微信 scroll-view 内部滚动容器默认关闭 overflow-anchor，
// 安卓 webview 下前插历史会先画一帧错位再被补偿拉回。开启后浏览器在同一次渲染内原子保持视口，
// 不闪不跳；iOS/Skyline 由 scroll-anchoring 属性负责，二者与高度差兜底补偿幂等共存。
.tui-message-list {
  :deep(.wx-scroll-view),
  :deep(.uni-scroll-view) {
    overflow-anchor: auto !important;
  }
}

// 覆盖层与离屏镜像都以消息区为定位上下文
.tui-chat-main {
  position: relative;
}

// 加载指示：浮在消息区顶部中央的圆形 pill，不占内容高度，前插高度差核算不受其干扰
.message-loading-overlay {
  position: absolute;
  top: 8px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  pointer-events: none;
}

.message-loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(153, 153, 153, 0.25);
  border-top-color: #999;
  border-radius: 50%;
  animation: tui-message-loading-spin 0.8s linear infinite;
}

// 离屏镜像：与真实列表同宽（left/right:0 撑满消息区），visibility:hidden 保留布局以便测高，
// 绝对定位脱离文档流、z-index:-1 沉底，不影响真实列表布局与可见渲染
.measure-mirror {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  visibility: hidden;
  pointer-events: none;
  z-index: -1;
}

@keyframes tui-message-loading-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
