## ADDED Requirements

### Requirement: IM sign-in follows system sign-in and sign-out

The client SHALL keep the Tencent IM sign-in aligned with the system (br-app) session: signing into the system SHALL (re)establish IM sign-in for that user when the message center is opened, and signing out of the system SHALL sign out of IM and reset the IM module state so the next system sign-in cannot reuse the previous user's IM session.

#### Scenario: Sign out of system also signs out of IM
- **GIVEN** 用户 A 已登录系统且已完成 IM 登录（进入过「会话」TAB）
- **WHEN** 用户 A 退出系统登录
- **THEN** 客户端 SHALL 调用 IM 登出（`TUILogin.logout`）
- **AND** IM 模块的已初始化标记 SHALL 被重置为未初始化

#### Scenario: Next user signs in gets their own IM session
- **GIVEN** 用户 A 已退出系统登录，IM 已随退出登出并被重置
- **WHEN** 用户 B 登录系统并打开「会话」TAB
- **THEN** 客户端 SHALL 以 B 的身份重新登录 IM
- **AND** 「会话」TAB SHALL 显示 B 的会话列表，而不是 A 残留的会话

#### Scenario: Receiver sees sender profile and unread badge after switching account
- **GIVEN** 发送者 A 给接收者 B 发送消息后退出，B 随后登录系统
- **WHEN** B 打开「会话」TAB
- **THEN** 该会话行 SHALL 显示发送者 A 在本系统设置的头像与昵称
- **AND** 未读消息条数 SHALL 以带数字的红点展示
- **AND** 点击该会话 SHALL 进入与 A 的会话窗口
