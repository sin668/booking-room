## Why

学习室详情页的地址目前只是纯文本，无法导航；页面上的「距您约1.2km」是硬编码假数据，且 `study_rooms` 表没有经纬度字段，导致无法计算真实距离或跳转地图。用户到店最需要的就是「一键导航」，这是当前转化链路上的明确断点。

## What Changes

- **数据库**：`study_rooms` 新增 `latitude`、`longitude`（`NUMERIC(10,7)`，可空，统一存储 GCJ-02 火星坐标），提供 alembic 迁移与存量房间补录脚本。
- **br-server**：
  - 房间创建/更新/详情响应 schema 增加 `latitude`、`longitude`。
  - 管理员保存房间时，若地址有值但未提供坐标，调用腾讯位置服务地理编码兜底并写回；编码失败不阻塞保存。
  - 新增配置项 `TENCENT_MAP_KEY`（服务端地理编码用）。
- **br-admin**：新建/编辑自习室表单增加「在地图上选点」，使用腾讯位置服务地图选点组件回填 GCJ-02 坐标；前端 key 通过 `VITE_TENCENT_MAP_KEY` 注入。
- **br-app**：学习室详情页地址行可点击，调用 `uni.openLocation` 打开地图导航（H5 走高德 URI）；进入页面尝试 `uni.getLocation` 计算直线距离并显示，取不到定位或无坐标时回退为「点击查看地图」或复制地址提示，移除硬编码距离。
- **br-app 小程序配置**：补充 `scope.userLocation` 说明与 `requiredPrivateInfos: ["getLocation"]`，仅用于距离展示，失败可降级。
- **回滚方案**：回滚代码与三处 UI 改动即可恢复纯文本地址；新增列为可空，回滚时执行 alembic downgrade 删除两列，不影响既有数据；腾讯 key 可随时停用，仅影响选点/地理编码与距离展示，不阻塞房间保存与浏览。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `study-room-booking-api`：详情响应 schema 增加经纬度字段。
- `study-room-admin-api`：创建/更新房间接受经纬度，并在缺坐标时做地理编码兜底；详情响应返回经纬度。
- `study-room-admin-ui`：新建/编辑表单增加腾讯地图选点。
- `study-room-booking-ui`：详情页地址可点击导航，显示真实距离并有降级文案。

## Impact

- 代码模块：`br-server`（models/schemas/services/routes/alembic/scripts）、`br-admin`（room edit 表单、env）、`br-app`（booking/detail、manifest、utils）。
- 数据库：`study_rooms` 表新增两列（可空，向后兼容）。
- 外部依赖：腾讯位置服务（免费配额，服务端地理编码 + 管理端选点组件）。
- 配置：`br-server/.env` 的 `TENCENT_MAP_KEY`、`br-admin/.env.*` 的 `VITE_TENCENT_MAP_KEY`。
- 不受影响：房间列表、座位预约、订单与支付链路；经纬度为空时行为与现状一致。
