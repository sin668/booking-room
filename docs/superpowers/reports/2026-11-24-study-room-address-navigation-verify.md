# 验证报告：study-room-address-navigation

- 日期：2026-11-24
- Workflow：tweak（verify_mode: full）
- 分支：main
- 变更范围：学习室地址定位与导航（管理端腾讯地图选点 + 服务端地理编码兜底 + App 导航与真实距离）

## 结论

**通过。** 无 CRITICAL、无 IMPORTANT 问题；1 项 SUGGESTION 已记录（不影响归档）。

## 1. 任务完成度（Completeness）

| 检查项 | 结果 | 证据 |
| --- | --- | --- |
| tasks.md 全部完成 | PASS | `openspec instructions apply` 返回 16/16 complete，remaining 0 |
| 产物严格校验 | PASS | `comet classic openspec -- validate <change> --strict` → valid |
| Delta spec 能力覆盖 | PASS | 4 个能力：study-room-admin-api、study-room-admin-ui、study-room-booking-api、study-room-booking-ui |

## 2. 正确性（Correctness）

| 验收点数 | 结果 | 证据 |
| --- | --- | --- |
| 后端响应包含坐标（列表/详情，可为 null） | PASS | `StudyRoomResponse`/`RoomAdminResponse` 增加 `latitude/longitude: float \| None`；`test_public_room_detail_includes_null_coordinates` |
| 创建时显式坐标直接保存且不触发地理编码 | PASS | `test_admin_create_room_with_coordinates`（monkeypatch 断言不调用） |
| 创建时缺坐标按地址地理编码补全 | PASS | `test_admin_create_room_geocode_fallback` |
| 地理编码失败不阻塞创建，坐标保持 null | PASS | `test_admin_create_room_geocode_failure_keeps_null` |
| 坐标越界返回 422 | PASS | `RoomCreate/RoomUpdate` Field ge/le 校验；`test_admin_create_room_rejects_invalid_coordinates` |
| 更新坐标 | PASS | `test_admin_update_room_coordinates` |
| 更新地址后地理编码补全 | PASS | `test_admin_update_address_geocode_fallback` |
| 显式 null 清除坐标 | PASS | `update_room` 对 `latitude/longitude` 不过滤 None；`test_admin_update_room_clears_coordinates` |
| 腾讯地理编码客户端降级 | PASS | 无 key / API 非 0 / 缺 location 均返回 None：`test_tencent_map_service.py` 4 项 |
| 管理端选点与 key 降级 | PASS | `edit.vue`：`VITE_TENCENT_MAP_KEY` 空时隐藏入口并提示；选点监听 `postMessage(module=locationPicker)`；清除坐标；编辑回显 |
| App 地址点击导航 | PASS | `detail.vue` `handleAddressTap`：有坐标走 `uni.openLocation`，H5 走高德 URI；无坐标复制并提示「位置暂未配置，已复制地址」 |
| App 真实距离与降级 | PASS | `distance.js` Haversine + `formatDistance`；`loadRealDistance` 失败/拒绝/无坐标时清空，展示「点击查看地图 / 导航」；硬编码 1.2km 已删除 |
| 小程序定位权限声明 | PASS | `manifest.json` mp-weixin 增加 `scope.userLocation.desc` 与 `requiredPrivateInfos: ["getLocation"]` |
| 距离工具边界 | PASS | `npm run test:distance` → `distance self-check passed`（同点 0、京沪 1030~1100km、空/非法返回 null、格式化边界） |

## 3. 一致性（Coherence）

| 检查项 | 结果 | 说明 |
| --- | --- | --- |
| 实现符合 design.md 关键决策 | PASS | GCJ-02 单坐标体系；`NUMERIC(10,7)` 可空；iframe + postMessage 零依赖；服务端兜底不阻塞；端上零地图配额 |
| Design Doc 一致性 | 跳过 | tweak 流程未创建 Design Doc（`design_doc: null`） |
| delta spec 与 design doc 矛盾 | 跳过 | 同上 |
| 集成代码审查 | 跳过（已记录原因） | `review_mode: off`（tweak 默认）；已人工复核最终 diff：模型/迁移/服务/schema/路由/管理端/App/测试，未发现正确性、安全或边界问题 |
| 安全 | PASS | 无硬编码密钥；key 仅通过 `VITE_TENCENT_MAP_KEY` / `TENCENT_MAP_KEY` 环境变量注入；`.env.example` 仅占位 |
| 数据库迁移链 | PASS | `n9p5q1r7s3t9` 的 `down_revision = m8n4p0q6r2s7`，后者为当前 head，无分叉 |

## 4. 构建与测试证据

通过 Runtime 记录的验证命令（cwd=项目根）：

1. `br-server`：`pytest tests/test_admin_room_routes.py tests/test_tencent_map_service.py tests/test_study_room_admin_service.py -q` → 36 passed
2. `br-admin`：`pnpm build` → 成功
3. `br-app`：`npm run test:distance` → `distance self-check passed`；`npm run build:mp-weixin`、`npm run build:h5` → 成功

Runtime 记录：`comet check run study-room-address-navigation verify --local -- sh -c '...'` → `exit=0; reused=false`；
日志：`openspec/changes/study-room-address-navigation/.comet/checks/6c631a57-5c5a-4ee0-b39b-c6add626e177.log`。

## 5. 问题清单

### CRITICAL

无。

### WARNING

无。

### SUGGESTION

1. **距离为 0 时文案显示「距您约1m」**（`br-app/src/utils/distance.js:49`）
   - 说明：`Math.max(1, ...)` 保证不出现「0m」，同点定位时略有偏差。
   - 建议：如需精确可改为「就在附近」，非必要不调整。

## 6. 环境依赖提示（非阻塞）

- 腾讯地图 key 未在本环境配置，用户将在 `br-server/.env` 与 `br-admin/.env` 自行填入；未配置时地理编码与选点均自动降级，不影响已有功能。
- 微信小程序 `getLocation` 仍需在微信后台开通「地理位置」接口权限，未开通时按设计降级为不显示距离。
