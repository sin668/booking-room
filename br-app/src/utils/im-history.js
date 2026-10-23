// 把本系统数据库里的 IM 消息镜像按 SDK 消息结构重建，用于补齐 IM 云端只漫游 7 天的深历史。
// 重建结果只用于渲染：没有 SDK 消息实例，撤回/删除/转发等需要内部标识的操作不会生效。
import TUIChatEngine from '@tencentcloud/chat-uikit-engine-lite'

const ELEMENT_TO_TYPE = {
  text: TUIChatEngine.TYPES.MSG_TEXT,
  image: TUIChatEngine.TYPES.MSG_IMAGE,
  sound: TUIChatEngine.TYPES.MSG_AUDIO,
  video: TUIChatEngine.TYPES.MSG_VIDEO,
  face: TUIChatEngine.TYPES.MSG_FACE,
  custom: TUIChatEngine.TYPES.MSG_CUSTOM,
}

// 只重建这几类：未知类型会被消息列表的 v-else 分支渲染成「撤回了一条消息」，宁可不显示
const REBUILDABLE = Object.keys(ELEMENT_TO_TYPE)

function firstElement(elements) {
  const list = elements || []
  return list.length ? list[0] : null
}

function imagePayload(row, content) {
  const info = (content.ImageInfoArray || []).find(i => i && i.URL)
  // 媒体优先用数据库转存的 OSS 地址：IM 的 COS 域名可能不在小程序白名单
  const url = row.oss_url || (info && info.URL) || row.media_url || ''
  const size = info || {}
  return {
    imageInfoArray: [
      {
        url,
        width: size.width || 0,
        height: size.height || 0,
        size: size.size || 0,
        type: size.Type || 1,
      },
    ],
  }
}

function buildPayload(elementType, row) {
  const element = firstElement(row.elements)
  const content = (element && element.MsgContent) || {}
  switch (elementType) {
    case 'text':
      return { text: content.Text || row.content || '' }
    case 'image':
      return imagePayload(row, content)
    case 'sound':
      return {
        url: row.oss_url || content.Url || row.media_url || '',
        second: content.Second || Number(row.content) || 0,
        size: content.Size || 0,
      }
    case 'video':
      return videoPayload(row, content)
    case 'face':
      return { data: content.Data || '', index: content.Index || 0, url: content.URL || '' }
    case 'custom':
      return {
        data: content.Data || '',
        description: content.Desc || '',
        extension: content.Extension || '',
      }
    default:
      return {}
  }
}

function videoPayload(row, content) {
  // 视频优先用数据库转存的 OSS 地址；缩略图保留腾讯云原地址（已在小程序域名白名单）
  const url = row.oss_url || content.VideoUrl || row.media_url || ''
  return {
    url,
    snapshotUrl: content.ThumbUrl || '',
    snapshotWidth: content.ThumbWidth || 0,
    snapshotHeight: content.ThumbHeight || 0,
  }
}

/**
 * 数据库行 → SDK 消息结构。ctx 提供本端视角：conversationID、myIMID、是否开启已读回执、用户资料。
 * 返回按时间正序的消息数组，交给 TUIChatService.updateMessageList(msgs, 'unshift') 合并。
 */
export function buildImHistoryMessages(rows, ctx = {}) {
  const conversationID = ctx.conversationID || ''
  const myIMID = ctx.myIMID || ''
  const userInfo = ctx.userInfo || {}
  const needReadReceipt = !!ctx.needReadReceipt

  const list = []
  for (let i = 0; i < (rows || []).length; i++) {
    const row = rows[i]
    if (!row || !row.msg_key) continue
    if (REBUILDABLE.indexOf(row.element_type) === -1) continue

    const from = row.im_from_account || ''
    const to = row.im_to_account || ''
    const profile = userInfo[from] || {}
    // 只对端发来的方向决定角标：本端消息看 is_read，对端消息自己不显示已读状态
    const peerRead = from === myIMID ? !!row.is_read : true
    const message = {
      ID: row.msg_key,
      conversationID,
      conversationType: 'C2C',
      type: ELEMENT_TO_TYPE[row.element_type],
      payload: buildPayload(row.element_type, row),
      time: row.msg_time,
      sequence: row.msg_seq,
      flow: from === myIMID ? 'out' : 'in',
      from,
      to,
      // 回调只落 SendMsgResult==0 的消息，历史里的消息一律是发送成功
      status: 'success',
      isRevoked: !!row.is_revoked,
      isModified: false,
      isRead: true,
      needReadReceipt,
      isPeerRead: peerRead,
      // read-status 组件直接解构 readReceiptInfo，缺对象就抛异常
      readReceiptInfo: {
        isPeerRead: peerRead,
        readCount: 0,
        unreadCount: 0,
        receiveReceiptInfoList: [],
      },
      cloudCustomData: row.cloud_custom_data || '',
      nick: profile.nick || profile.nameCard || '',
      avatar: profile.avatar || '',
    }
    list.push(message)
  }
  return list
}
