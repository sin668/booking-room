## ADDED Requirements

### Requirement: Conversation current-session release on chat exit
The TUIChat page SHALL release the IM current conversation when the page is unloaded on the mini program, so that messages arriving after the user leaves the chat window accumulate into the conversation's unread count and are displayed as the red badge number in the 会话 TAB.

#### Scenario: Peer reply after leaving the chat window
- **GIVEN** 用户已从「会话」TAB 打开与对方的聊天窗口并返回消息通知页
- **WHEN** 对方在该用户离开聊天窗口期间发送新消息
- **THEN** 该会话的 `unreadCount` SHALL 大于 0
- **AND** 「会话」TAB 该行右侧 SHALL 显示包含该数字的红点徽标

#### Scenario: Leaving the chat page clears the current conversation
- **GIVEN** 用户停留在与某会话的聊天窗口
- **WHEN** 用户返回上一页并触发该页面的卸载生命周期
- **THEN** 客户端 SHALL 调用会话切换接口把当前会话清空
- **AND** 引擎 SHALL NOT 再把属于该会话的新消息自动置为已读

#### Scenario: Next chat entry opens the requested conversation
- **GIVEN** 用户上一个聊天窗口已卸载
- **WHEN** 用户从「会话」TAB 点击另一条会话
- **THEN** 聊天窗口 SHALL 显示本次点击的会话
- **AND** SHALL NOT 复用上一个残留的当前会话

#### Scenario: Reading inside the chat window still clears unread
- **GIVEN** 用户正停留在某会话的聊天窗口
- **WHEN** 对方发送消息
- **THEN** 该会话未读数 SHALL 保持为 0
- **AND** 返回「会话」TAB 时该行 SHALL NOT 显示红点
