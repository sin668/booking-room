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
  const currentConversation = ref<IConversationModel>();
  const theme = TUIChatConfig.getTheme();

  TUIStore.watch(StoreName.CONV, {
    currentConversation: (conversation: IConversationModel) => {
      currentConversation.value = conversation;
    },
  });

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
        if (currentConversation.value) {
          sendImageMessage(currentConversation.value, res);
        }
      },
    });
  };

  const chooseVideoInUniApp = () => {
    TUIGlobal?.chooseVideo({
      count: MEDIA_CHOOSE_CONFIG.VIDEO.COUNT,
      sourceType: [sourceType],
      compressed: MEDIA_CHOOSE_CONFIG.VIDEO.COMPRESSED,
      fail: genChooseFailHandler('视频'),
      success: function (res: Record<string, any>) {
        if (currentConversation.value) {
          sendVideoMessage(currentConversation.value, res);
        }
      },
    });
  };

  const chooseMediaInUniApp = () => {
    TUIGlobal?.chooseImage({
      count: MEDIA_CHOOSE_CONFIG.IMAGE.COUNT,
      sourceType: [SourceType.ALBUM, SourceType.CAMERA],
      fail: genChooseFailHandler('图片'),
      success: function (res: Record<string, any>) {
        if (currentConversation.value) {
          sendImageMessage(currentConversation.value, res);
        }
      },
    });
  };

  const chooseCameraInUniApp = () => {
    TUIGlobal?.chooseVideo({
      count: MEDIA_CHOOSE_CONFIG.VIDEO.COUNT,
      sourceType: [SourceType.ALBUM, SourceType.CAMERA],
      compressed: MEDIA_CHOOSE_CONFIG.VIDEO.COMPRESSED,
      fail: genChooseFailHandler('视频'),
      success: function (res: Record<string, any>) {
        if (currentConversation.value) {
          sendVideoMessage(currentConversation.value, res);
        }
      },
    });
  };

  const handleWebFileChange = (event: Event) => {
    switch (uploadType) {
      case UploadType.IMAGE:
        handleWebFileSelect(event, (file) => {
          if (currentConversation.value) {
            sendImageMessage(currentConversation.value, file);
          }
        });
        break;
      case UploadType.VIDEO:
        handleWebFileSelect(event, (file) => {
          if (currentConversation.value) {
            sendVideoMessage(currentConversation.value, file);
          }
        });
        break;
      case UploadType.FILE:
        handleWebFileSelect(event, (file) => {
          if (currentConversation.value) {
            sendFileMessage(currentConversation.value, file);
          }
        });
        break;
    }
  };

  return {
    inputRef,
    currentConversation,
    toolbarConfig,
    isPC,
    isUniFrameWork,
    handleIconClick,
    handleWebFileChange,
  };
}
