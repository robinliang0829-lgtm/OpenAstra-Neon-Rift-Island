# 钢潮港事件接线

规则原型是 `sim/steel_tide`。UE 里将来由 **一个** 权威比赛对象接收这些事件。本仓还没有这个 C++ 模块，下面的类名是留给下一份 Codex 代码的名字，不是已经能编译的类型。

不要在关卡蓝图、关卡脚本或第二个子系统里自己加分、改持有者或按颜色分队。模块还没进工程时，体积只打印「将要发送的事件名」，并把结果标成 `BLOCKED native rules module not in this build`。

## 预留类型

| 名字 | 以后放在 | 职责 |
| --- | --- | --- |
| `UNeonRiftMatchSubsystem` | `Source/NeonRift`，GameInstanceSubsystem | 权威状态、同帧裁决、计时器 |
| `UNeonRiftRulesConfig` | 由 `config/steel_tide_greybox.json` 生成的数据资产 | 只读参数，操作员不在编辑器里另填一套秒数 |
| `ANeonRiftCore` | 场景里只有一个 | 相位芯 |
| `ANeonRiftTerminal` | `NR_Terminal_A`、`NR_Terminal_B` | 对方在此读条 |
| `ANeonRiftBridgeSpan` | `NR_BridgeSpan` | 高架跨度，断开时不能走，不断开把人嵌进碰撞体 |

复制以服务器为准。客户端发送意图。UI 读复制下来的 `holder_id`，不把本地预测的第二名持有者当成真的。

## 谁可以发什么

玩家客户端可以发：`request_move`、`pick_core`、`pass_core`、`drop_core`、`begin_score`、`set_route`。

只有服务器可以发：`hit`、`leave_terminal`、`mark_core_overboard`、`mark_core_stuck`。玩家 RPC 自称「我被打了」或「芯掉海里了」会被拒绝（`server_only`）。原型里这四类命令的 `client_id` 固定为 `server`。

数字居民和本地机器人走同一套意图。回传里把 `local_bot` 和真正的 Resident 分开写。这批 bot 不是生产数字居民。

## 同一服务器帧的顺序

先处理该帧全部意图，再处理计时器。意图优先级与 `SteelTideMatch` 一致：

1. `request_move`
2. `hit`、`leave_terminal`、`drop_core`
3. `pass_core`
4. `mark_core_overboard`、`mark_core_stuck`
5. `pick_core`（这一帧所有拾取一起裁决，不按到达函数的先后抢两次）
6. `begin_score`
7. `set_route`

同帧拾取按 `(client_id, combatant_id)` 稳定排序。排序只为了和原型日志对齐，**通过条件是恰好一人成功**。两人同时站在芯上时，另一人收到 `CorePickRejected`，原因 `already_held`。

计时器在意图之后，顺序为：桥预警、桥接通、桥断开、复活、芯超时复位、读条完成、比赛钟。因此读条结束的同一毫秒若有 `hit`，先打断，不计分。

## 事件

日志一行一条，时间用毫秒。格式与 `Event.format()` 相同：`t_s  EventName  {json}`。

| 事件 | 何时由子系统发出 | 场景物体 |
| --- | --- | --- |
| `CombatantJoined` | 进局，写明 body、controller、client | 玩家或 bot |
| `FactionChosen` / `FactionRejected` | 选边。非法身体、或已锁队 | 大厅 |
| `RoleChosen` / `RoleRejected` | 突进 `assault` / 支援 `support` / 侦察 `recon`。锁队后拒绝 | 大厅 |
| `FactionsLocked` `RolesLocked` `MatchStarted` | 开局。`role_select_open` 为 false | 子系统 |
| `RouteSelected` | 选择 `elevated` 或 `repair_alley` | 玩家 |
| `MoveCompleted` / `MoveRejected` | 沿配置边行走。桥未接通为 `bridge_blocked`；走得太快为 `too_soon` | 导航 |
| `CorePicked` | 芯状态是 `spawn` 或 `ground`，且人在芯的锚点上 | `NR_Core` 与 `NR_CoreSpawn` |
| `CorePickRejected` | 同帧第二人、已有持有者、人不在芯上、芯在海里或卡住 | 同上 |
| `CorePassed` | 同队、距离 ≤ `pass_range_m`、目标未倒地 | 两名Pawn |
| `CoreDropped` | 主动丢、倒地、坠海、卡住 | `NR_Core` |
| `CoreMarkedUnpickable` | 芯进入 `sea` 或 `stuck`，拾取会得到 `not_pickable` | `NR_SeaVolume` / `NR_StuckVolume` |
| `ScoreChannelStarted` | 持芯者位于**对方**端子。A 在 `terminal_b`，B 在 `terminal_a`。重复调用不重置 3 秒 | `NR_Terminal_*` |
| `ScoreChannelInterrupted` | 受击、离开体积、丢芯、传芯、坠海/卡住、被桥挤出跨度 | 端子体积的 End Overlap，或服务器伤害 |
| `PointScored` | 连续满 `score_channel_seconds`（提案 3.0）且没有打断。只发一次 | 子系统 |
| `CoreReturnedToCenter` | 得分后芯回 `center`，这不是超时复位 | `NR_CoreSpawn` |
| `CoreReset` | `stuck` 或 `overboard` 持续 `core_reset_timeout_seconds`（提案 8.0）。不计分 | `NR_CoreSpawn` |
| `ActorDowned` | 命中且不在出生保护内。持芯者先掉芯 | 伤害 |
| `HitIgnored` | 出生保护内 | 出生点 |
| `ActorRespawned` | `down_seconds`（提案 5.0）后回本方出生点 | `NR_Spawn_A` / `NR_Spawn_B` |
| `BridgeWarningStarted` | 接通前 `bridge_warning_seconds`（提案 4.0）。载荷含 `readable_without_reflection: true` | 倒影、灯带、警报。倒影关了也要能读 |
| `BridgeStateChanged` | `connected` 或 `disconnected` | `NR_BridgeSpan` |
| `BridgeOccupantNudged` | 断开时把跨度上的人挪到本方桥头，不嵌进网格 | `NR_BridgeHead_A` / `B` |
| `MatchClockExpired` | 提案 360 秒。`role_select_open` 仍为 false | 子系统 |
| `OvertimeStarted` | 平分才进入。提案 60 秒，先得分者结束。不重新选岗位 | 子系统 |
| `MatchSettled` | 只发一次。`kind` 为 `points`、`score` 或 `draw` | 子系统 |

持芯者速度用 `walk_speed_mps`（6，即 600 uu/s），不能冲刺。未持芯的原型移动用 `sprint_speed_mps`（8，即 800 uu/s）。1 米 = 100 UE 单位。坐标：模拟 x → UE X，模拟 y → UE Y，Z 向上，甲板 Z = 0。锚点表在 `config/steel_tide_greybox.json`。

## 和原型对日志

```bash
PYTHONPATH=sim python3 -m steel_tide repro
```

NR-02 的通过线是双端日志里出现与这三条相同的结果，而不是同一堆毫秒时间（灰盒手测对不齐 bot 的 29.5 秒）：

- 同帧两次拾取：一条 `CorePicked`，一条 `CorePickRejected` / `already_held`，全程审计不出第二个持有者。
- 读条中受击或离开：`ScoreChannelInterrupted`，没有 `PointScored`。倒地会 `CoreDropped`，满 5 秒 `ActorRespawned`，芯留在掉落处。
- 芯进海水或卡住体积：满 8 秒一条 `CoreReset` 回到 `center`，没有 `PointScored`。得分回中用的是 `CoreReturnedToCenter`，不要接成复位。

出现双持或一次读条记两次分，把两端日志退回 Codex，不要在编辑器里改胜负条件。
