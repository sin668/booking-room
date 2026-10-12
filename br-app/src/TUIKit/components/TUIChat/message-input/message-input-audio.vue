<template>
  <div
    :class="{
      'message-input-audio': true,
      'message-input-audio-open': isAudioTouchBarShow,
    }"
  >
    <view class="audio-message-icon">
      <CommonIcon
        :file="audioIcon"
        :size="'23px'"
        :hotAreaSize="'0px'"
        @onClick="switchAudio"
      />
    </view>
    <view
      v-if="props.isEnableAudio"
      class="audio-input-touch-bar"
      @longpress="handleLongPress"
      @touchmove="handleTouchMove"
      @touchend="handleTouchEnd"
    >
      <span>{{ TUITranslateService.t(`TUIChat.${touchBarText}`) }}</span>
      <view
        v-if="isRecording"
        class="record-modal"
      >
        <div class="red-mask" />
        <view class="float-element moving-slider" />
        <view class="float-element modal-title">
          {{ TUITranslateService.t(`TUIChat.${modalText}`) }}
        </view>
      </view>
    </view>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from '../../../adapter-vue';
import {
  TUIStore,
  StoreName,
  TUIChatService,
  SendMessageParams,
  IConversationModel,
  TUITranslateService,
} from '@tencentcloud/chat-uikit-engine-lite';
import { TUIGlobal } from '@tencentcloud/universal-api';
import CommonIcon from '../../common/Icon.vue';
import audioIcon from '../../../assets/icon/audio.svg';
import { Toast, TOAST_TYPE } from '../../common/Toast/index';
import { throttle } from '../../../utils/lodash';
import { isEnabledMessageReadReceiptGlobal } from '../utils/utils';
import { InputDisplayType } from '../../../interface';
// #ifdef APP-PLUS
import {
	judgeIosPermissionRecord,
	requestAndroidPermission,
	gotoAppPermissionSetting,
	checkPermissionStatusInApp,
} from '../../../utils/permission.js';
// #endif

interface IProps {
  isEnableAudio: boolean;
}

interface IEmits {
  (e: 'changeDisplayType', type: InputDisplayType): void;
}

interface RecordResult {
  tempFilePath: string;
  duration?: number;
  fileSize?: number;
}

type TouchBarText = '按住说话' | '抬起发送' | '抬起取消';
type ModalText = '正在录音' | '继续上滑可取消' | '松开手指 取消发送';

// 麦克风权限状态枚举
enum MicPermissionStatus {
  UNKNOWN = 'unknown',          // 未知
  AUTHORIZED = 'authorized',    // 已授权
  NOT_DETERMINED = 'not_determined', // 未确定（首次）
  DENIED = 'denied',            // 已拒绝（可再次申请）
  DENIED_ALWAYS = 'denied_always', // 永久拒绝
}

const emits = defineEmits<IEmits>();
const props = withDefaults(defineProps<IProps>(), {
  isEnableAudio: false,
});

let recordTime: number = 0;
let isManualCancelBySlide = false;
let recordTimer: number | undefined;
let firstTouchPageY: number = -1;
let isFingerDown = false;
let recorderActive = false;
const recorderManager = TUIGlobal?.getRecorderManager();

const isRecording = ref(false);
const touchBarText = ref<TouchBarText>('按住说话');
const modalText = ref<ModalText>('正在录音');
const isAudioTouchBarShow = ref<boolean>(false);
const currentConversation = ref<IConversationModel>();

const recordConfig = {
  duration: 60000,
  sampleRate: 44100,
  numberOfChannels: 1,
  encodeBitRate: 192000,
  format: 'mp3',
};


/**
 * 处理权限检查结果并执行相应操作
 * @param {Function} onAuthorized 已授权时的回调
 */
async function handlePermissionCheck(onAuthorized: () => void) {
  const status = await getRecordPermissionStatus();

  switch (status) {
    case MicPermissionStatus.AUTHORIZED:
      onAuthorized();
      break;

    case MicPermissionStatus.DENIED_ALWAYS:
      showDeniedAlwaysDialog();
      break;

    case MicPermissionStatus.NOT_DETERMINED:
      showAuthorizationDialog(async () => {
        const granted = await requestMicrophonePermission();
        if (granted) {
          // 授权成功，执行回调
          onAuthorized();
        } else {
          // 授权失败，再次检查状态
          const newStatus = await getRecordPermissionStatus();
          if (newStatus === MicPermissionStatus.DENIED_ALWAYS) {
            showDeniedAlwaysDialog();
          }
        }
      });
      break;
    default:
      Toast({
        message: TUITranslateService.t('TUIChat.获取麦克风权限状态失败，请重试'),
        type: TOAST_TYPE.ERROR,
      });
      break;
  }
}

/**
 * 获取录音权限状态（APP 端）
 * @returns {Promise<MicPermissionStatus>} 权限状态
 */
async function getRecordPermissionStatus(): Promise<MicPermissionStatus> {

  // #ifdef APP-PLUS
  const systemInfo = uni.getSystemInfoSync();

  if (systemInfo.platform === 'android') {
    // Android 端：使用 requestAndroidPermission 检查权限
    try {
      const checkResult = checkPermissionStatusInApp('RECORD');

      if (checkResult !== 1) {
        // 将 showModal 包装为 Promise，以便等待用户操作结果
        return await new Promise<MicPermissionStatus>((resolve) => {
          uni.showModal({
            title: TUITranslateService.t('TUIChat.权限申请'),
            content: TUITranslateService.t('TUIChat.请允许使用麦克风权限用于发送语音消息'),
            success: async function (res) {
              if (res.confirm) {
                const result = await requestAndroidPermission('android.permission.RECORD_AUDIO');
                if (result === 1) {
                  resolve(MicPermissionStatus.AUTHORIZED);
                } else if (result === -1) {
                  resolve(MicPermissionStatus.DENIED_ALWAYS);
                } else if (result === 0) {
                  resolve(MicPermissionStatus.NOT_DETERMINED);
                } else {
                  resolve(MicPermissionStatus.UNKNOWN);
                }
              } else if (res.cancel) {
                resolve(MicPermissionStatus.DENIED);
              }
            },
            fail: () => {
              resolve(MicPermissionStatus.UNKNOWN);
            }
          });
        });
      } else {
        return MicPermissionStatus.AUTHORIZED;
      }
    } catch (error) {
      console.error('[Audio] Android: 获取权限状态失败:', error);
      return MicPermissionStatus.UNKNOWN;
    }
  } else if (systemInfo.platform === 'ios') {
    try {
      const hasPermission = judgeIosPermissionRecord();

      if (hasPermission) {
        return MicPermissionStatus.AUTHORIZED;
      } else {
        // 需要进一步判断是首次还是已拒绝
        const AVAudioSession = plus.ios.importClass('AVAudioSession');
        const audioSession = AVAudioSession.sharedInstance();
        const permissionStatus = audioSession.recordPermission();
        plus.ios.deleteObject(audioSession);

        // 1684369017: denied, 1970168948: not determined
        if (permissionStatus === 1684369017) {
          return MicPermissionStatus.DENIED_ALWAYS;
        } else {
          return MicPermissionStatus.NOT_DETERMINED;
        }
      }
    } catch (error) {
      return MicPermissionStatus.UNKNOWN;
    }
  }
  // #endif

  // #ifdef MP
  return new Promise((resolve, reject) => {
    uni.getSetting({
      success(res) {
          if (res.authSetting['scope.record'] === false) {
            resolve(MicPermissionStatus.DENIED_ALWAYS);
          } else if (res.authSetting['scope.record'] === undefined) {
            resolve(MicPermissionStatus.NOT_DETERMINED);
          } else if (res.authSetting['scope.record'] === true) {
            resolve(MicPermissionStatus.AUTHORIZED);
          } else {
            resolve(MicPermissionStatus.UNKNOWN);
          }
        },
      fail() {
        reject();
      }
    });
  });
  // #endif

  return MicPermissionStatus.UNKNOWN;
}

/**
 * 请求麦克风权限（弹出系统授权窗）
 * @returns {Promise<boolean>} 是否授权成功
 */
async function requestMicrophonePermission(): Promise<boolean> {

  // #ifdef APP-PLUS
  const systemInfo = uni.getSystemInfoSync();

  if (systemInfo.platform === 'android') {
    const result = await requestAndroidPermission('android.permission.RECORD_AUDIO');

    if (result === 1) {
      return true;
    } else if (result === -1) {
      return false;
    } else {
      return false;
    }
  } else if (systemInfo.platform === 'ios') {
    return new Promise((resolve) => {
      try {
        const AVAudioSession = plus.ios.importClass('AVAudioSession');
        const audioSession = AVAudioSession.sharedInstance();

        audioSession.requestRecordPermission((granted: boolean) => {
          plus.ios.deleteObject(audioSession);

          if (granted) {
            resolve(true);
          } else {
            resolve(false);
          }
        });
      } catch (error) {
        console.error('[Audio] iOS: 请求权限失败:', error);
        resolve(false);
      }
    });
  }
  // #endif

  // #ifdef MP
  return new Promise((resolve) => {
    uni.authorize({
      scope: 'scope.record',
      success: () => resolve(true),
      fail: () => resolve(false),
    });
  });
  // #endif
  return false;
}

/**
 * 打开应用权限设置页面
 */
function openAppPermissionSetting() {
  // #ifdef APP-PLUS
  gotoAppPermissionSetting();
  // #endif
}

/**
 * 显示永久拒绝提示弹窗
 */
function showDeniedAlwaysDialog() {
  let message = '';
  // #ifdef APP-PLUS
  const systemInfo = uni.getSystemInfoSync();
  if (systemInfo.platform === 'android') {
    message = TUITranslateService.t('TUIChat.麦克风权限已被拒绝，请前往"设置 → 应用信息 → 权限"中开启麦克风权限');
  } else if (systemInfo.platform === 'ios') {
    message = TUITranslateService.t('TUIChat.麦克风权限已被拒绝，请前往"设置 → 隐私 → 麦克风"中开启权限');
  }
  // #endif
  // #ifdef MP
  message = TUITranslateService.t('TUIChat.麦克风权限已被拒绝，请前往"右上角设置"中开启权限');
  // #endif
  uni.showModal({
    title: TUITranslateService.t('TUIChat.需要麦克风权限'),
    content: message,
    confirmText: TUITranslateService.t('TUIChat.去设置'),
    cancelText: TUITranslateService.t('TUIChat.取消'),
    success: (res: any) => {
      if (res.confirm) {
		// #ifdef APP-PLUS
        openAppPermissionSetting();
		// #endif
		// #ifdef MP
		uni.openSetting();
		// #endif
      } else {
        // 用户取消，切换回文本输入模式
        emits('changeDisplayType', 'editor');
      }
    },
  });

}

/**
 * 显示首次授权提示弹窗
 * @param {Function} onConfirm 用户点击授权后的回调
 */
function showAuthorizationDialog(onConfirm: () => void) {
  uni.showModal({
    title: TUITranslateService.t('TUIChat.需要麦克风权限'),
    content: TUITranslateService.t('TUIChat.需要您授权麦克风权限以使用语音功能'),
    confirmText: TUITranslateService.t('TUIChat.授权'),
    cancelText: TUITranslateService.t('TUIChat.取消'),
    success: (res: any) => {
      if (res.confirm) {
        onConfirm();
      } else {
        emits('changeDisplayType', 'editor');
      }
    },
  });
}


/**
 * 切换音频输入模式（点击麦克风图标）
 */
async function switchAudio() {
  if (props.isEnableAudio) {
    // 当前是音频模式，切换回文本模式
    emits('changeDisplayType', 'editor');
  } else {
    // 切换到音频模式前，先检查权限
    await handlePermissionCheck(() => {
      // 权限通过，切换到音频模式
      emits('changeDisplayType', 'audio');
    });
  }
}

/**
 * 长按开始录音（作为兜底检查）
 */
async function handleLongPress() {
  isFingerDown = true;
  // 检查权限（作为兜底）
  await handlePermissionCheck(() => {
    // 权限通过，开始录音
    startRecording();
  });
}

/**
 * 开始录音
 */
function startRecording() {
  // 权限检查是异步的，回调可能在松手后才到达
  if (!isFingerDown || recorderActive) {
    return;
  }
  recorderActive = true;
  recorderManager.start(recordConfig);
}

onMounted(() => {
  // 注册录音管理器事件
  recorderManager.onStart(onRecorderStart);
  recorderManager.onStop(onRecorderStop);
  recorderManager.onError(onRecorderError);

  TUIStore.watch(StoreName.CONV, {
    currentConversation: onCurrentConverstaionUpdated,
  });
});

onUnmounted(() => {
  TUIStore.unwatch(StoreName.CONV, {
    currentConversation: onCurrentConverstaionUpdated,
  });
});

function onCurrentConverstaionUpdated(conversation: IConversationModel) {
  currentConversation.value = conversation;
}

function initRecorder() {
  initRecorderData();
  initRecorderView();
}

function initRecorderView() {
  isRecording.value = false;
  touchBarText.value = TUITranslateService.t('TUIChat.按住说话');
  modalText.value = TUITranslateService.t('TUIChat.正在录音');
}

function initRecorderData(options?: { hasError: boolean }) {
  clearInterval(recordTimer);
  recordTimer = undefined;
  recordTime = 0;
  firstTouchPageY = -1;
  isManualCancelBySlide = false;
  isFingerDown = false;
  const wasActive = recorderActive;
  recorderActive = false;
  if (!options?.hasError && wasActive) {
    recorderManager.stop();
  }
}

const handleTouchMove = throttle(function (e: any) {
  if (isRecording.value) {
    const pageY = e.changedTouches[e.changedTouches.length - 1].pageY;
    if (firstTouchPageY < 0) {
      firstTouchPageY = pageY;
    }
    const offset = (firstTouchPageY as number) - pageY;
    if (offset > 150) {
      touchBarText.value = TUITranslateService.t('TUIChat.抬起取消');
      modalText.value = TUITranslateService.t('TUIChat.松开手指 取消发送');
      isManualCancelBySlide = true;
    } else if (offset > 50) {
      touchBarText.value = TUITranslateService.t('TUIChat.抬起发送');
      modalText.value = TUITranslateService.t('TUIChat.继续上滑可取消');
      isManualCancelBySlide = false;
    } else {
      touchBarText.value = TUITranslateService.t('TUIChat.抬起发送');
      modalText.value = TUITranslateService.t('TUIChat.正在录音');
      isManualCancelBySlide = false;
    }
  }
}, 100);

function handleTouchEnd() {
  isFingerDown = false;
  if (recorderActive) {
    recorderActive = false;
    recorderManager.stop();
  }
}

function onRecorderStart() {
  recordTimer = setInterval(() => {
    recordTime += 1;
  }, 1000);
  touchBarText.value = TUITranslateService.t('TUIChat.抬起发送');
  isRecording.value = true;
}

function onRecorderStop(res: RecordResult) {
  if (isManualCancelBySlide || !isRecording.value) {
    initRecorder();
    return;
  }
  clearInterval(recordTimer);

  const tempFilePath = res.tempFilePath;
  const duration = res.duration ? res.duration : recordTime * 1000;
  const fileSize = res.fileSize ? res.fileSize : ((48 * recordTime) / 8) * 1024;

  if (duration < 1000) {
    Toast({
      message: TUITranslateService.t('TUIChat.录音时间太短'),
      type: TOAST_TYPE.NORMAL,
      duration: 1500,
    });
  } else {
    const options = {
      to:
        currentConversation?.value?.groupProfile?.groupID
        || currentConversation?.value?.userProfile?.userID,
      conversationType: currentConversation?.value?.type,
      payload: { file: { duration, tempFilePath, fileSize } },
      needReadReceipt: isEnabledMessageReadReceiptGlobal(),
    } as SendMessageParams;
    TUIChatService?.sendAudioMessage(options)
      ?.then(onSendAudioFailure)
      ?.catch(onSendAudioFailure);
  }
  initRecorder();
}

// 富媒体上传域名由服务端下发，不在小程序 uploadFile 白名单内时只会静默失败，
// 不暴露 code/message 就无法定位到底是哪个域名被拦截。
function onSendAudioFailure(err: any): void {
  if (!err) return;
  console.error('[Audio] sendAudioMessage failed:', err);
  const code = err?.code;
  const raw = String(
    err?.message
    || err?.msg
    || err?.errMsg
    || (typeof err === 'object' ? JSON.stringify(err) : String(err))
  );
  // 小程序 Toast 只显示两行，完整对象看 console
  const text = raw.length > 60 ? `${raw.slice(0, 60)}…` : raw;
  Toast({
    message: `语音发送失败 ${code ?? ''} ${text}`,
    type: TOAST_TYPE.ERROR,
    duration: 5000,
  });
}

function onRecorderError(err: any) {
  console.error('[Audio] Recorder error:', err);

  initRecorderData({ hasError: true });
  initRecorderView();

  // 根据错误码判断是否是权限问题
  if (err?.errMsg?.includes('auth') || err?.errMsg?.includes('permission')) {
    showDeniedAlwaysDialog();
  } else {
    Toast({
      message: err?.errMsg || TUITranslateService.t('TUIChat.录音失败，请重试'),
      type: TOAST_TYPE.ERROR,
    });
  }
}
</script>

<style lang="scss" scoped>
@use "../../../assets/styles/common";

.message-input-audio {
  display: flex;
  flex-direction: row;
  align-items: center;
  position: relative;

  .audio-message-icon {
    flex: 0 0 23px;
    width: 23px;
    height: 30px;
    margin-right: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .audio-input-touch-bar {
    min-height: 38px;
    flex: 1;
    padding: 8px 12px;
    border: 1px solid #e5e8ee;
    border-radius: 20px;
    box-sizing: border-box;
    font-size: 15px;
    display: flex;
    flex-direction: row;
    justify-content: center;
    align-items: center;
    background-color: #fff;

    .record-modal {
      height: 300rpx;
      width: 60vw;
      background-color: rgba(0, 0, 0, 0.8);
      position: fixed;
      left: 50%;
      top: 50%;
      transform: translate(-50%, -50%);
      z-index: 9999;
      border-radius: 24rpx;
      display: flex;
      flex-direction: column;
      overflow: hidden;

      .red-mask {
        position: absolute;
        inset: 0;
        background-color: rgba(#ff3e48, 0.5);
        opacity: 0;
        transition: opacity 10ms linear;
        z-index: 1;
      }

      .moving-slider {
        margin: 10vw;
        width: 40rpx;
        height: 16rpx;
        border-radius: 4rpx;
        background-color: #006fff;
        animation: loading 1s ease-in-out infinite alternate;
        z-index: 2;
      }

      .float-element {
        position: relative;
        z-index: 2;
      }
    }

    @keyframes loading {
      0% {
        transform: translate(0, 0);
      }

      100% {
        transform: translate(30vw, 0);
        background-color: #f5634a;
        width: 40px;
      }
    }

    .modal-title {
      text-align: center;
      color: #fff;
    }
  }

  &-open {
    flex: 1;
  }
}
</style>
