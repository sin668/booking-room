# Tasks: 学习室详情地址定位与导航

## 1. 数据层

- [x] 1.1 新增 alembic 迁移：`study_rooms` 增加可空 `latitude`、`longitude`（`NUMERIC(10,7)`），包含 downgrade
- [x] 1.2 `StudyRoom` 模型、`StudyRoomResponse`、`RoomAdminResponse`、`RoomCreate`、`RoomUpdate` 增加经纬度字段与范围校验（lat -90~90，lng -180~180）
- [x] 1.3 新增存量房间坐标补录脚本，按地址调用地理编码，失败跳过并汇总结果

## 2. 后端服务

- [x] 2.1 `Settings` 增加 `TENCENT_MAP_KEY`、`TENCENT_MAP_GEOCODE_TIMEOUT_SECONDS`；新增腾讯地理编码客户端（超时/异常返回 None）
- [x] 2.2 管理员创建/更新房间时：未传坐标且地址非空则调用地理编码写回；编码失败不阻塞保存
- [x] 2.3 补充后端单测：带坐标直接保存、缺坐标成功编码、编码失败仍保存、坐标越界返回 422、响应包含坐标

## 3. 管理端

- [x] 3.1 br-admin 增加 `VITE_TENCENT_MAP_KEY` 配置；新建/编辑表单展示「在地图上选点」，未配置 key 时隐藏并提示
- [x] 3.2 接入腾讯地图选点 iframe，监听 `postMessage` 回填坐标与地址，提交时携带 `latitude/longitude`
- [x] 3.3 表单回显已有坐标，并支持清除坐标

## 4. App 详情页

- [x] 4.1 `manifest.json` 补充 `scope.userLocation` 描述与 `requiredPrivateInfos: ["getLocation"]`
- [x] 4.2 新增距离计算工具（Haversine），提供 node 自检脚本
- [x] 4.3 详情页地址行可点击：有坐标走 `uni.openLocation`（H5 走高德 URI），无坐标复制地址并提示
- [x] 4.4 进入页面尝试 `getLocation` 计算真实距离；拒绝/失败/无坐标时不显示距离，移除硬编码「距您约1.2km」

## 5. 验证

- [x] 5.1 运行后端相关 pytest 全部通过
- [x] 5.2 `br-admin` 构建通过；`br-app` 的 `build:h5` 与 `build:mp-weixin` 通过
- [x] 5.3 运行距离工具自检脚本并记录结果
