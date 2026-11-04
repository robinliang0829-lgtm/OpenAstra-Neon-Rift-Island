# 钢潮港事件接线

规则原型是 `sim/steel_tide`。UE 侧由 `UNeonRiftMatchSubsystem` 广播这些名字。`ANeonRiftGameMode`、`ANeonRiftGameState`、`ANeonRiftPlayerState` 只订阅并再广播，不另记一分。头文件在 `Source/NeonRift/Public/NeonRiftEventNames.h`，名字集合与 `sim/steel_tide/events.py` 一致。这些 C++ 存根只转发事件，不算分、不发第二名持有者。

不要在关卡蓝图里自己加分或按颜色分队。调用 `Emit*` 不是通过 NR-02。

## 模块

`NeonRift.uproject` 的 `EngineAssociation` 是 `5.4` 占位。真实小版本由 PM-钢潮岛按本机安装锁定。

| 类型 | 文件 | 职责 |
| --- | --- | --- |
| `UNeonRiftMatchSubsystem` | `Source/NeonRift/Public/NeonRiftMatchSubsystem.h` | 唯一广播口 |
| `ANeonRiftGameMode` | `Source/NeonRift/Public/NeonRiftGameMode.h` | 指定 GameState / PlayerState，转发总线，不计分 |
| `ANeonRiftGameState` | `Source/NeonRift/Public/NeonRiftGameState.h` | 订阅总线，复制事件行和权威载荷 |
| `ANeonRiftPlayerState` | `Source/NeonRift/Public/NeonRiftPlayerState.h` | 一个客户端视角，再广播同一行 |
| `ANeonRiftPhaseCore` | `Source/NeonRift/Public/NeonRiftPhaseCore.h` | 相位芯事件 |
| `UNeonRiftFactionSelect` | `Source/NeonRift/Public/NeonRiftFactionSelect.h` | 选边、岗位、锁队 |
| `ANeonRiftTerminalScore` | `Source/NeonRift/Public/NeonRiftTerminalScore.h` | 端子读条、倒地、结算 |
| `ANeonRiftBridgeWarn` | `Source/NeonRift/Public/NeonRiftBridgeWarn.h` | 桥预警、路线、移动 |
| 参数 | `config/steel_tide_greybox.json` | 秒数和阵营。不要在编辑器里另填一套 |

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
| `AbilityUsed` / `AbilityRejected` | 突进、支援、侦察的可调冷却。错岗位、冷却中、桥未通或目标在掩体后则拒绝。不是新里程碑。 | `UNeonRiftFactionSelect` |
| `CombatantJoined` | 进局，写明 body、controller、client | 玩家或 bot |
| `FactionChosen` / `FactionRejected` | 选边。非法身体、或已锁队 | 大厅 |
| `RoleChosen` / `RoleRejected` | 突进 `assault` / 支援 `support` / 侦察 `recon`。锁队后拒绝 | 大厅 |
| `FactionsLocked` `RolesLocked` `MatchStarted` | 开局。`role_select_open` 为 false | 子系统 |
| `RouteSelected` / `RouteRejected` | 选择 `elevated` 或 `repair_alley` | `ANeonRiftBridgeWarn` |
| `MoveCompleted` / `MoveRejected` | 沿配置边行走。桥未接通为 `bridge_blocked`；走得太快为 `too_soon` | `ANeonRiftBridgeWarn` |
| `CorePicked` / `CorePickRejected` | 芯状态是 `spawn` 或 `ground`，且人在芯的锚点上。同帧第二人原因 `already_held` | `ANeonRiftPhaseCore` |
| `CorePassed` / `CorePassRejected` | 同队、距离 ≤ `pass_range_m`、目标未倒地 | `ANeonRiftPhaseCore` |
| `CoreDropped` / `CoreDropRejected` | 主动丢、倒地、坠海、卡住 | `ANeonRiftPhaseCore` |
| `CoreMarkedUnpickable` / `CoreMarkRejected` | 芯进入 `sea` 或 `stuck`，拾取会得到 `not_pickable`。玩家伪造标记被拒绝 | `ANeonRiftPhaseCore` |
| `ScoreChannelStarted` / `ScoreChannelRejected` | 持芯者位于**对方**端子。A 在 `terminal_b`，B 在 `terminal_a`。重复调用不重置 3 秒 | `ANeonRiftTerminalScore` |
| `ScoreChannelInterrupted` | 受击、离开体积、丢芯、传芯、坠海/卡住、被桥挤出跨度 | `ANeonRiftTerminalScore` |
| `PointScored` | 连续满 `score_channel_seconds`（提案 3.0）且没有打断。只发一次 | `ANeonRiftTerminalScore` |
| `CoreReturnedToCenter` | 得分后芯回 `center`，这不是超时复位 | `ANeonRiftPhaseCore` |
| `CoreReset` | `stuck` 或 `overboard` 持续 `core_reset_timeout_seconds`（提案 8.0）。不计分 | `ANeonRiftPhaseCore` |
| `ActorDowned` | 命中且不在出生保护内。持芯者先掉芯 | `ANeonRiftTerminalScore` |
| `HitIgnored` / `HitRejected` | 出生保护内忽略。玩家客户端伪造命中被拒绝 | `ANeonRiftTerminalScore` |
| `ActorRespawned` | `down_seconds`（提案 5.0）后回本方出生点 | `ANeonRiftTerminalScore` |
| `BridgeWarningStarted` | 接通前 `bridge_warning_seconds`（提案 4.0）。载荷含 `readable_without_reflection: true` | `ANeonRiftBridgeWarn` |
| `BridgeStateChanged` | `connected` 或 `disconnected` | `ANeonRiftBridgeWarn` |
| `BridgeOccupantNudged` | 断开时把跨度上的人挪到本方桥头，不嵌进网格 | `ANeonRiftBridgeWarn` |
| `MatchClockExpired` | 提案 360 秒。`role_select_open` 仍为 false | `ANeonRiftTerminalScore` |
| `OvertimeStarted` | 平分才进入。提案 60 秒，先得分者结束。不重新选岗位 | `ANeonRiftTerminalScore` |
| `MatchSettled` | 只发一次。`kind` 为 `points`、`score` 或 `draw` | `ANeonRiftTerminalScore` |

持芯者速度用 `walk_speed_mps`（6，即 600 uu/s），不能冲刺。未持芯的原型移动用 `sprint_speed_mps`（8，即 800 uu/s）。1 米 = 100 UE 单位。坐标：模拟 x → UE X，模拟 y → UE Y，Z 向上，甲板 Z = 0。锚点表在 `config/steel_tide_greybox.json`。

## 和原型对日志

```bash
PYTHONPATH=sim python3 -m steel_tide repro
PYTHONPATH=sim python3 -m steel_tide nr02 --check
```

双端对照用 [DUAL_END_EVENT_LOG.md](DUAL_END_EVENT_LOG.md)。`nr02` 是 3v3（两个客户端视角 + 四个本地 bot）的参照日志，样例在 `docs/evidence/nr02/`。`repro` 仍是四条脚本复现。

NR-02 的通过线是双端日志里出现与这三条相同的结果，而不是同一堆毫秒时间（灰盒手测对不齐样例里的 `place_for_test`）：

- 同帧两次拾取：一条 `CorePicked`，一条 `CorePickRejected` / `already_held`，全程审计不出第二个持有者。
- 读条中受击或离开：`ScoreChannelInterrupted`，没有 `PointScored`。倒地会 `CoreDropped`，满 5 秒 `ActorRespawned`，芯留在掉落处。
- 芯进海水或卡住体积：满 8 秒一条 `CoreReset` 回到 `center`，没有 `PointScored`。得分回中用的是 `CoreReturnedToCenter`，不要接成复位。

出现双持或一次读条记两次分，把两端日志退回 Codex，不要在编辑器里改胜负条件。
