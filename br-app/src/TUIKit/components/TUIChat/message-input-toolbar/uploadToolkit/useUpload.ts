import { ref, computed } from '../../../../adapter-vue';
import { TUIStore, StoreName, IConversationModel } from '@tencentcloud/chat-uikit-engine-lite';
import { TUIGlobal } from '@tencentcloud/universal-api';
import { Toast, TOAST_TYPE } from '../../../common/Toast/index';
import { isPC, isUniFrameWork } from '../../../../utils/env';
import TUIChatConfig from '../../config';
import {
  TOOLBAR_DISPLAY_CONFIG,
  ICON_SIZE_CONFIG,
  MEDIA_CHOOSE_CONFIG,
  UploadType,
  SourceType,
  PlatformType,
} from './constants';
import {
  sendImageMessage,
  sendVideoMessage,
  sendFileMessage,
  handleWebFileSelect,
} from './utils';

export function genSourceType(uploadType: UploadType): SourceType {
  if (uploadType === UploadType.CAMERA) {
    return SourceType.CAMERA;
  }
  return SourceType.ALBUM;
}

// chooseImage/chooseVideo 原本只写 success，真机上相机权限被拒（`fail user denied`）或选择器
// 报错时点了完全没反应，也分不清是没弹框还是发送失败。取消属于正常操作，不提示。
function genChooseFailHandler(label: string) {
  return (err: any): void => {
    const errMsg = String(err?.errMsg || err || '');
    console.error(`[TUIChat] ${label}选择失败:`, err);
    if (errMsg.includes('cancel')) {
      return;
    }
    Toast({
      message: `${label}选择失败 ${errMsg.slice(0, 60)}`,
      type: TOAST_TYPE.ERROR,
      duration: 5000,
    });
  };
}

export function useUpload(uploadType: UploadType) {
  const inputRef = ref();
  const theme = TUIChatConfig.getTheme();

  // 直接从 SDK 获取当前会话，不依赖 watch（watch 在多个组件实例间可能有时序问题）
  const getCurrentConversation = (): IConversationModel | undefined => {
    return TUIStore.getData(StoreName.CONV, 'currentConversation');
  };

  const sourceType = genSourceType(uploadType);

  const toolbarConfig = computed(() => {
    const config = TOOLBAR_DISPLAY_CONFIG[uploadType];

    if (isUniFrameWork) {
      const displayConfig = (config as any)[PlatformType.UNI];

      return {
        icon: displayConfig.icon,
        title: displayConfig.title,
        iconWidth: ICON_SIZE_CONFIG.UNI.WIDTH,
        iconHeight: ICON_SIZE_CONFIG.UNI.HEIGHT,
      };
    } else {
      const displayConfig = (config as any)[PlatformType.WEB];

      return {
        icon: displayConfig.getIcon ? displayConfig.getIcon(theme) : displayConfig.icon,
        title: displayConfig.title,
        iconWidth: ICON_SIZE_CONFIG.WEB.WIDTH,
        iconHeight: ICON_SIZE_CONFIG.WEB.HEIGHT,
      };
    }
  });

  const handleIconClick = () => {
    if (isUniFrameWork) {
      handleUniAppClick();
    } else {
      handleWebClick();
    }
  };

  const handleUniAppClick = () => {
    switch (uploadType) {
      case UploadType.IMAGE:
        chooseImageInUniApp();
        break;
      case UploadType.VIDEO:
        chooseVideoInUniApp();
        break;
      case UploadType.ALBUM:
        chooseMediaInUniApp();
        break;
      case UploadType.CAMERA:
        chooseCameraInUniApp();
        break;
      default:
        break;
    }
  };

  const handleWebClick = () => {
    if (inputRef.value?.click) {
      inputRef.value.click();
    }
  };

  const chooseImageInUniApp = () => {
    TUIGlobal?.chooseImage({
      count: MEDIA_CHOOSE_CONFIG.IMAGE.COUNT,
      sourceType: [sourceType],
      fail: genChooseFailHandler('图片'),
      success: function (res: Record<string, any>) {
        const conversation = getCurrentConversation();
        if (conversation) {
          sendImageMessage(conversation, res);
        }
      },
    });
  };

  const chooseVideoInUniApp = () => {
    if (!TUIGlobal?.chooseVideo) {
      Toast({ message: '当前环境不支持视频选择', type: TOAST_TYPE.ERROR, duration: 3000 });
      return;
    }
    try {
      TUIGlobal.chooseVideo({
        count: MEDIA_CHOOSE_CONFIG.VIDEO.COUNT,
        sourceType: [sourceType],
        compressed: MEDIA_CHOOSE_CONFIG.VIDEO.COMPRESSED,
        fail: genChooseFailHandler('视频'),
        success: function (res: Record<string, any>) {
          const conversation = getCurrentConversation();
          if (!conversation) {
            Toast({ message: '会话未加载，请稍后重试', type: TOAST_TYPE.ERROR, duration: 3000 });
            return;
          }
          sendVideoMessage(conversation, res);
        },
      });
    } catch (err) {
      console.error('[TUIChat] chooseVideo 调用异常:', err);
      Toast({
        message: `视频选择异常 ${String(err?.errMsg || err?.message || err).slice(0, 60)}`,
        type: TOAST_TYPE.ERROR,
        duration: 5000,
      });
    }
  };

  const chooseMediaInUniApp = () => {
    TUIGlobal?.chooseImage({
      count: MEDIA_CHOOSE_CONFIG.IMAGE.COUNT,
      sourceType: [SourceType.ALBUM, SourceType.CAMERA],
      fail: genChooseFailHandler('图片'),
      success: function (res: Record<string, any>) {
        const conversation = getCurrentConversation();
        if (conversation) {
          sendImageMessage(conversation, res);
        }
      },
    });
  };

  const chooseCameraInUniApp = () => {
    if (!TUIGlobal?.chooseVideo) {
      Toast({ message: '当前环境不支持视频拍摄', type: TOAST_TYPE.ERROR, duration: 3000 });
      return;
    }
    try {
      TUIGlobal.chooseVideo({
        count: MEDIA_CHOOSE_CONFIG.VIDEO.COUNT,
        sourceType: [SourceType.ALBUM, SourceType.CAMERA],
        compressed: MEDIA_CHOOSE_CONFIG.VIDEO.COMPRESSED,
        fail: genChooseFailHandler('视频'),
        success: function (res: Record<string, any>) {
          const conversation = getCurrentConversation();
          if (!conversation) {
            Toast({ message: '会话未加载，请稍后重试', type: TOAST_TYPE.ERROR, duration: 3000 });
            return;
          }
          sendVideoMessage(conversation, res);
        },
      });
    } catch (err) {
      console.error('[TUIChat] chooseVideo 调用异常:', err);
      Toast({
        message: `视频选择异常 ${String(err?.errMsg || err?.message || err).slice(0, 60)}`,
        type: TOAST_TYPE.ERROR,
        duration: 5000,
      });
    }
  };

  const handleWebFileChange = (event: Event) => {
    const conversation = getCurrentConversation();
    if (!conversation) {
      return;
    }
    switch (uploadType) {
      case UploadType.IMAGE:
        handleWebFileSelect(event, (file) => {
          sendImageMessage(conversation, file);
        });
        break;
      case UploadType.VIDEO:
        handleWebFileSelect(event, (file) => {
          sendVideoMessage(conversation, file);
        });
        break;
      case UploadType.FILE:
        handleWebFileSelect(event, (file) => {
          sendFileMessage(conversation, file);
        });
        break;
    }
  };

  return {
    inputRef,
    toolbarConfig,
    isPC,
    isUniFrameWork,
    handleIconClick,
    handleWebFileChange,
  };
}
