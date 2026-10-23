import TUIChatEngine, {
  TUIChatService,
  IConversationModel,
  SendMessageParams,
  SendMessageOptions,
} from '@tencentcloud/chat-uikit-engine-lite';
import { isEnabledMessageReadReceiptGlobal } from '../../utils/utils';
import OfflinePushInfoManager, { IOfflinePushInfoCreateParams } from '../../offlinePushInfoManager/index';
import { Toast, TOAST_TYPE } from '../../../common/Toast/index';
import { getIMLastUploadError } from '@/utils/im';

export function createSendMessageOptions(
  currentConversation: IConversationModel | undefined,
  file: any,
): SendMessageParams {
  return {
    to:
      currentConversation?.groupProfile?.groupID
      || currentConversation?.userProfile?.userID,
    conversationType: currentConversation?.type,
    payload: {
      file,
    },
    needReadReceipt: isEnabledMessageReadReceiptGlobal(),
  } as SendMessageParams;
}

export function genOfflinePushInfo(
  currentConversation: IConversationModel,
  payload: any,
  messageType: any,
): SendMessageOptions {
  const offlinePushInfoCreateParams: IOfflinePushInfoCreateParams = {
    conversation: currentConversation,
    payload,
    messageType,
  };

  return {
    offlinePushInfo: OfflinePushInfoManager.create(offlinePushInfoCreateParams),
  };
}

// 富媒体上传地址由服务端下发，不在小程序 uploadFile 白名单内时只会静默失败；
// 真机看不出是域名被拦、超大小还是格式不支持，必须把 host + errMsg + SDK 错误码打到屏幕上。
function reportSendFailure(label: string) {
  return (err: any): void => {
    if (!err) {
      return;
    }
    console.error(`[TUIChat] ${label}发送失败:`, err);
    const upload = getIMLastUploadError();
    const raw = String(
      upload?.errMsg
      || err?.message
      || err?.msg
      || err?.errMsg
      || (typeof err === 'object' ? JSON.stringify(err) : String(err)),
    );
    const host = upload?.url ? `${upload.url.split('/')[2] || upload.url} ` : '';
    const text = raw.length > 60 ? `${raw.slice(0, 60)}…` : raw;
    Toast({
      message: `${label}发送失败 ${err?.code ?? ''} ${host}${text}`,
      type: TOAST_TYPE.ERROR,
      duration: 5000,
    });
  };
}

export function sendImageMessage(
  currentConversation: IConversationModel,
  files: any,
): void {
  if (!files) {
    return;
  }

  const options = createSendMessageOptions(currentConversation, files);
  const sendMessageOptions = genOfflinePushInfo(
    currentConversation,
    options.payload,
    TUIChatEngine.TYPES.MSG_IMAGE,
  );

  TUIChatService.sendImageMessage(options, sendMessageOptions);
}

export function sendVideoMessage(
  currentConversation: IConversationModel,
  file: any,
): void {
  if (!file) {
    return;
  }

  // 诊断日志：真机上视频发送失败时看这里，确认 chooseVideo 返回的数据结构
  console.log('[TUIChat] 视频发送入参:', {
    tempFilePath: file.tempFilePath,
    fileType: file.fileType,
    size: file.size,
    duration: file.duration,
    width: file.width,
    height: file.height,
    hasTempFiles: Array.isArray(file.tempFiles),
    tempFilesLength: file.tempFiles?.length,
    tempFiles0: file.tempFiles?.[0] ? Object.keys(file.tempFiles[0]) : null,
  });

  const options = createSendMessageOptions(currentConversation, file);
  const sendMessageOptions = genOfflinePushInfo(
    currentConversation,
    options.payload,
    TUIChatEngine.TYPES.MSG_VIDEO,
  );

  // createVideoMessage 内部会同步校验视频格式/大小，失败时直接 throw 而不是返回 rejected Promise，
  // 错误会冒泡到 wx.chooseVideo 的 success 回调里被框架吞掉，所以必须在这里 try-catch。
  try {
    const result = TUIChatService.sendVideoMessage(options, sendMessageOptions);
    if (result && typeof result.catch === 'function') {
      result.catch(reportSendFailure('视频'));
    }
  } catch (err) {
    reportSendFailure('视频')(err);
  }
}

export function sendFileMessage(
  currentConversation: IConversationModel,
  file: any,
): void {
  if (!file) {
    return;
  }

  const options = createSendMessageOptions(currentConversation, file);
  const sendMessageOptions = genOfflinePushInfo(
    currentConversation,
    options.payload,
    TUIChatEngine.TYPES.MSG_FILE,
  );

  TUIChatService.sendFileMessage(options, sendMessageOptions);
}

export function handleWebFileSelect(
  event: any,
  sendCallback: (file: any) => void,
): void {
  if (event?.target?.files?.length <= 0) {
    return;
  }

  sendCallback(event.target);
  event.target.value = '';
}

export function isValidFile(file: any): boolean {
  return !!file;
}

export function clearFileInput(inputRef: any): void {
  if (inputRef.value) {
    inputRef.value.value = '';
  }
}
