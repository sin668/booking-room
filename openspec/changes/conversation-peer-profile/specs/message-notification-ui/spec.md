## ADDED Requirements

### Requirement: Conversation peer profile
消息通知页「会话」TAB SHALL display the peer's avatar and nickname from the peer's profile in this system, carried by the Tencent IM user portrait that each client writes after IM sign-in, and SHALL fall back to the first-character placeholder when the peer has no avatar.

#### Scenario: Sender sees receiver avatar
- **GIVEN** 接收者已在本系统设置头像并完成过一次 IM 登录
- **WHEN** 发送者打开消息通知页「会话」TAB
- **THEN** 该会话行 SHALL 显示接收者的本系统头像，而不是首字母占位

#### Scenario: Receiver sees sender nickname and avatar
- **GIVEN** 发送者已在本系统设置昵称与头像并完成过一次 IM 登录
- **WHEN** 接收者打开消息通知页「会话」TAB
- **THEN** 该会话行 SHALL 显示发送者的本系统昵称作为名称，并显示其头像
- **AND** 名称 SHALL NOT 回显 IM 账号名（平台 `username`）

#### Scenario: Profile change propagates
- **GIVEN** 用户已登录且 IM 就绪
- **WHEN** 用户修改本系统的昵称或头像
- **THEN** 客户端 SHALL 立即把新的昵称与头像写入 IM 用户画像
- **AND** 对方下次拉取会话列表时 SHALL 看到更新后的资料

#### Scenario: Peer without avatar falls back
- **GIVEN** 对方从未在本系统设置头像
- **WHEN** 用户打开「会话」TAB
- **THEN** 该会话行 SHALL 显示昵称（缺失时显示账号名）与名称首字母占位头像
- **AND** 页面 SHALL NOT 因头像为空而报错或空白
