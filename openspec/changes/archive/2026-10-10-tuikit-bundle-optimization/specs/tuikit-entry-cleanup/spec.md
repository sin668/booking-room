## ADDED Requirements

### Requirement: TUIKit entry shall not bundle test UserSig generator

TUIKit entry (`src/TUIKit/index.ts`) SHALL NOT import or re-export `genTestUserSig`. The `debug/` directory SHALL NOT exist in the TUIKit source tree.

#### Scenario: No debug directory in source
- **GIVEN** TUIKit 源码目录
- **WHEN** 检查 `src/TUIKit/debug/` 是否存在
- **THEN** 该目录 SHALL NOT 存在

#### Scenario: No genTestUserSig in entry
- **GIVEN** `src/TUIKit/index.ts` 文件内容
- **WHEN** 检查是否包含 `genTestUserSig`
- **THEN** 文件 SHALL NOT 包含该标识符

### Requirement: TUIKit entry shall not contain stub files

TUIKit SHALL NOT contain `index.vue` (empty stub) or `vue.config.js` (unused webpack config).

#### Scenario: No stub index.vue
- **GIVEN** TUIKit 源码目录
- **WHEN** 检查 `src/TUIKit/index.vue` 是否存在
- **THEN** 该文件 SHALL NOT 存在

#### Scenario: No unused vue.config.js
- **GIVEN** TUIKit 源码目录
- **WHEN** 检查 `src/TUIKit/vue.config.js` 是否存在
- **THEN** 该文件 SHALL NOT 存在

### Requirement: TUIKit entry exports only TUIChatKit

TUIKit entry (`src/TUIKit/index.ts`) SHALL export only `TUIChatKit`.

#### Scenario: Single export
- **GIVEN** `src/TUIKit/index.ts` 文件内容
- **WHEN** 检查导出列表
- **THEN** 文件 SHALL 仅导出 `TUIChatKit`
- **AND** SHALL NOT 导出 `TUIKit`、`TUIComponents`、`TUIChat`、`TUIConversation`、`TUIContact`、`TUISearch`、`TUIGroup`、`hideTUIChatFeatures`、`genTestUserSig`
