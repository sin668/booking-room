## 方案概述

坐标只计算一次（管理端录入时），用户端只消费坐标：详情页导航与距离计算不再调用任何地理编码接口，避免用户访问量消耗地图配额。

## 关键决策

1. **坐标系统一 GCJ-02**
   腾讯位置服务、微信小程序 `uni.openLocation`、高德都使用 GCJ-02，选点与导航可直接互通，不做坐标转换。数据库同时只存一套坐标，不引入 `coord_type`。

2. **坐标字段**
   `study_rooms.latitude/longitude` 使用 `NUMERIC(10,7)`、可空。响应 schema 使用 `float`，保证 JSON 输出为数字，前端无需转换。

3. **管理端选点**
   br-admin 使用腾讯位置服务「地图选点组件」（iframe + `postMessage`），不引入 npm 依赖。选点回填 `latitude/longitude` 和规范化地址；key 通过 `VITE_TENCENT_MAP_KEY` 注入，未配置时隐藏选点入口并提示。

4. **服务端地理编码兜底**
   管理员只改文本地址时，`admin_study_room` 服务在「地址有值且未传坐标」的情况下调用腾讯 WebService 地理编码，成功则写回坐标；`TENCENT_MAP_KEY` 未配置、超时或返回异常时仅记录日志，保存流程照常成功。存量数据由一次性脚本补录。

5. **App 真实距离与降级**
   - 有坐标时进入页面尝试 `uni.getLocation({ type: 'gcj02' })`，成功后用 Haversine 计算直线距离：`<1km` 显示「距您约 xxxm」，否则「距您约 x.xkm」。
   - 用户拒绝授权、定位失败、无坐标时**不显示距离**，显示「点击查看地图 / 导航」。
   - 点击地址：有坐标时 `uni.openLocation`（H5 走高德 URI）；无坐标时复制地址到剪贴板并提示「位置暂未配置，已复制地址」。
   - 删除现有硬编码「距您约1.2km」。

6. **小程序定位权限**
   `manifest.json` 补充 `scope.userLocation` 描述与 `requiredPrivateInfos: ["getLocation"]`。微信后台未开通接口权限时 `getLocation` 会失败，按第 5 条降级，不影响导航。

## 数据流

```
br-admin 选点 ──> PUT/POST 房间(latitude, longitude) ──> study_rooms
        └─ 未选点且地址有值 ──> 腾讯地理编码 ──> 写回坐标（失败则留空）

br-app 详情页 GET /api/v1/rooms/{id} ──> room.latitude/longitude
        ├─ 有坐标 ──> openLocation 导航
        └─ 有坐标 + getLocation 成功 ──> Haversine 距离
```

## 影响与兼容

- 新列可空，旧数据与旧客户端行为不变。
- 腾讯 key 缺失时功能降级为纯文本地址，不报错。
- 回滚：删除 UI 调用与两个配置项，再执行 `alembic downgrade` 删除两列。

## 验证方式

- br-server：pytest 覆盖创建/更新带坐标、缺坐标触发地理编码（mock httpx）、编码失败仍保存、响应包含坐标。
- br-admin：`pnpm build` 通过；无 key 时选点入口隐藏。
- br-app：`npm run build:h5` 与 `npm run build:mp-weixin` 通过；距离计算函数跑 node 自检脚本（命中/未命中/边界）。
