## Purpose

扩展 room_follows 关注系统支持 teacher 关注类型，使用户可以关注/取消关注教师，与现有的 room 和 course 关注类型并存。

## ADDED Requirements

### Requirement: follow_type 参数支持 teacher

room_follows API 的 `follow_type` 查询参数 SHALL 从 `^(room|course)$` 扩展为 `^(room|course|teacher)$`，支持教师关注/取消关注/列表查询。

#### Scenario: 关注教师

- **GIVEN** 用户未关注教师 id=1
- **WHEN** 客户端发送 `POST /api/v1/room-follows/1?follow_type=teacher`
- **THEN** 返回 HTTP 201，创建 `follow_type=teacher` 的关注记录

#### Scenario: 取消关注教师

- **GIVEN** 用户已关注教师 id=1（`follow_type=teacher`）
- **WHEN** 客户端发送 `DELETE /api/v1/room-follows/1?follow_type=teacher`
- **THEN** 返回 HTTP 204，仅删除 `follow_type=teacher` 的记录，不影响同一 room_id 的其他 follow_type 记录

#### Scenario: 查询教师关注列表

- **GIVEN** 用户关注了 2 位教师
- **WHEN** 客户端发送 `GET /api/v1/room-follows?follow_type=teacher`
- **THEN** 返回 HTTP 200，`total` 为 2

#### Scenario: 重复关注教师（幂等）

- **GIVEN** 用户已关注教师 id=1（`follow_type=teacher`）
- **WHEN** 客户端再次发送 `POST /api/v1/room-follows/1?follow_type=teacher`
- **THEN** 返回 HTTP 200，不创建重复记录

#### Scenario: teacher 类型与 room/course 类型互不干扰

- **GIVEN** 用户对同一 id=1 分别有 `follow_type=room` 和 `follow_type=teacher` 的关注记录
- **WHEN** 客户端发送 `DELETE /api/v1/room-follows/1?follow_type=teacher`
- **THEN** 仅删除 `follow_type=teacher` 的记录，`follow_type=room` 的记录保留
