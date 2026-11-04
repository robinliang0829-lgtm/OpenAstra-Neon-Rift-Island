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
| `ANeonRiftPlayerState` | `Source/NeonRift/Public/NeonRiftPlayerState.h` | 一个客户端视角，再广播同一行。`BodyType`、`MatchFaction`、`ControllerKind` 只复制身体、阵营、操控者，不选边，不计分 |
| `ANeonRiftPhaseCore` | `Source/NeonRift/Public/NeonRiftPhaseCore.h` | 相位芯事件 |
| `UNeonRiftFactionSelect` | `Source/NeonRift/Public/NeonRiftFactionSelect.h` | 选边、岗位、锁队 |
| `ANeonRiftTerminalScore` | `Source/NeonRift/Public/NeonRiftTerminalScore.h` | 端子读条、倒地、结算 |
| `ANeonRiftBridgeWarn` | `Source/NeonRift/Public/NeonRiftBridgeWarn.h` | 桥预警、路线、移动 |
| `ANeonRiftBotPolicy` | `Source/NeonRift/Public/NeonRiftBotPolicy.h` | 转发 `BotDecision`。不选择，不计分 |
| `UNeonRiftResidentPort` | `Source/NeonRift/Public/NeonRiftResidentPort.h` | 薄策略。`SelectMatch` / `Decide` 只记合法座位和意图，不喂坐标，不计分 |
| `UNeonRiftReadabilityAsset` | `Source/NeonRift/Public/NeonRiftReadability.h` | NR-03 代理与 4 秒预警的数据。不记分 |
| `NeonRiftAudio` | `Source/NeonRift/Public/NeonRiftAudioCues.h` | NR-M2 音效 id。只列名字，不播放，不计分，无声音资产 |
| 参数 | `config/steel_tide_greybox.json` | 秒数和阵营。不要在编辑器里另填一套 |

复制以服务器为准。客户端发送意图。UI 读复制下来的 `holder_id`，不把本地预测的第二名持有者当成真的。

## 谁可以发什么

玩家客户端可以发：`request_move`、`use_ability`、`pick_core`、`pass_core`、`drop_core`、`begin_score`、`set_route`。

只有服务器可以发：`hit`、`leave_terminal`、`mark_core_overboard`、`mark_core_stuck`。玩家 RPC 自称「我被打了」或「芯掉海里了」会被拒绝（`server_only`）。原型里这四类命令的 `client_id` 固定为 `server`。

数字居民和本地机器人走同一套意图。回传里把 `local_bot` 和真正的 Resident 分开写。这批 bot 不是生产数字居民。

`BotDecision` 由 `sim/steel_tide` 在本地 bot 提交意图时写下，不是玩家 RPC，也不计分。`hit` 仍只有服务器能发。bot 决定打断读条时，模拟替服务器排队一次 `down` 为 false 的命中。`ResidentDecision` 是薄策略数字居民的同一类审计，`controller` 为 `digital_resident`。它不改持有者，不计分，也不写墙后坐标。NR-M1-bot 不构造 `UNeonRiftResidentPort`。NR-M2-resident 在 `sim/steel_tide` 里调用 `select_match` 和 `decide`。NR-M2-roles 让这两条决策在岗位上再选突进、支援或侦察；`reason` 写岗位 id。NR-M2-bridge 在桥接通或断开、路径用到的跨度边发生变化时，用同一个决策事件写 `reason=path_recompute`。这不是新事件名。GameMode / GameState / PlayerState 仍不构造端口，也不记分。

## 同一服务器帧的顺序

先处理该帧全部意图，再处理计时器。意图优先级与 `SteelTideMatch` 一致：

1. `request_move`
2. `use_ability`（同帧的定向护盾先于命中）
3. `hit`、`leave_terminal`、`drop_core`
4. `pass_core`
5. `mark_core_overboard`、`mark_core_stuck`
6. `pick_core`（这一帧所有拾取一起裁决，不按到达函数的先后抢两次）
7. `begin_score`
8. `set_route`

同帧拾取按 `(client_id, combatant_id)` 稳定排序。排序只为了和原型日志对齐，**通过条件是恰好一人成功**。两人同时站在芯上时，另一人收到 `CorePickRejected`，原因 `already_held`。

计时器在意图之后，顺序为：桥预警、灯带递进、桥预警结束、桥接通、桥断开、复活、芯超时复位、读条完成、比赛钟。因此读条结束的同一毫秒若有 `hit`，先打断，不计分。灯带和警报不改变持有者，也不加分。接通和断开会按当时的权威路线图重算还在走的路。断开时，已经排上的跨度步先被拒绝，站在 `center` 的人落到本方桥头。拒绝和落点都不计分，也不把人打倒。

## 事件

日志一行一条，时间用毫秒。格式与 `Event.format()` 相同：`t_s  EventName  {json}`。

| 事件 | 何时由子系统发出 | 场景物体 |
| --- | --- | --- |
| `AbilityUsed` / `AbilityRejected` | 突进、支援、侦察的可调冷却。错岗位、冷却中、桥未通、目标在掩体后，或突进时手里有芯（`holding_core`，不消耗冷却）则拒绝。传出或丢下芯之后可以再突进。不是新里程碑。 | `UNeonRiftFactionSelect` |
| `CombatantJoined` | 进局，写明 body、controller、client | 玩家或 bot |
| `BotDecision` | 本地 bot 提交一条意图。载荷有 `action`、`reason`、`target_id`，`controller` 为 `local_bot`。不改持有者，不计分。数字居民不产生这条。 | `ANeonRiftBotPolicy` |
| `ResidentDecision` | 薄策略数字居民提交一条意图。载荷有 `action`、`reason`、`target_id`，`controller` 为 `digital_resident`。`select_match` 只记录合法阵营。不改持有者，不计分，不含墙后坐标。 | `UNeonRiftResidentPort` |
| `FactionChosen` / `FactionRejected` | 选边。非法身体、或已锁队 | 大厅 |
| `RoleChosen` / `RoleRejected` | 突进 `assault` / 支援 `support` / 侦察 `recon`。锁队后拒绝 | 大厅 |
| `FactionsLocked` `RolesLocked` `MatchStarted` | 开局。`FactionsLocked.identities` 写下 body、faction、controller 三个字段。`role_select_open` 为 false | 子系统 |
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
| `HitIgnored` / `HitRejected` | 出生保护内忽略，并且先于护盾，不消耗护盾。护盾是定向的一发，载荷可带 `directed_by`。玩家客户端伪造命中被拒绝 | `ANeonRiftTerminalScore` |
| `ActorRespawned` | `down_seconds`（提案 5.0）后回本方出生点，载荷带 `protection_until_ms`（提案再保护 3.0 秒）。芯留在掉落处 | `ANeonRiftTerminalScore` |
| `BridgeLightStripAdvanced` | 预警开始后，灯带按剩余提前量逐盏点亮。不改持有者，不计分 | `ANeonRiftBridgeWarn` |
| `BridgeWarningStarted` | 接通前 `bridge_warning_seconds`（配置 4）。警报与灯带第一盏同一毫秒开始。载荷含配置里的 `readable_without_reflection` | `ANeonRiftBridgeWarn` |
| `BridgeWarningCompleted` | 灯带走完。与接通同一毫秒，提前量为 4 秒。不是记分 | `ANeonRiftBridgeWarn` |
| `BridgeStateChanged` | `connected` 或 `disconnected`。接通紧跟 `BridgeWarningCompleted`。断开把跨度边移出权威路线图 | `ANeonRiftBridgeWarn` |
| `BridgeOccupantNudged` | 断开时把跨度上的人挪到本方桥头，不嵌进网格。不计分，不击倒，不掉芯 | `ANeonRiftBridgeWarn` |
| `MatchClockExpired` | 提案 360 秒。`role_select_open` 仍为 false | `ANeonRiftTerminalScore` |
| `OvertimeStarted` | 平分才进入。提案 60 秒。打破平局的第一笔得分立即结束：未到 `points_to_win` 时 `kind=score`，到达时 `kind=points`。这一笔若把比分打回相同，立即 `kind=draw`。60 秒结束仍相同也是 `kind=draw`，不开启第二段，不重新选岗位 | `ANeonRiftTerminalScore` |
| `MatchSettled` | 只发一次。`kind` 为 `points`、`score` 或 `draw`。常规时间先到 `points_to_win` 立即 `kind=points`，不进入加时 | `ANeonRiftTerminalScore` |

`AudioCue` 不在上表，也不在 `sim/steel_tide/events.py` 的 `EVENT_NAMES`。模拟在权威事件的同一毫秒另写一行旁路日志，`rules_effect` 为 `none`，不改持有者，不加分，不打断。队标、桥和芯链的 id 在 `NeonRiftAudioCues.h`，与 `sim/steel_tide/audio.py` 一致。不提交声音文件。规格见 [../NR-M2-audio.md](../NR-M2-audio.md)。

持芯者速度用 `walk_speed_mps`（6，即 600 uu/s），不能冲刺，也不能突进。未持芯的原型移动用 `sprint_speed_mps`（8，即 800 uu/s）。1 米 = 100 UE 单位。坐标：模拟 x → UE X，模拟 y → UE Y，Z 向上，甲板 Z = 0。锚点表在 `config/steel_tide_greybox.json`。

## 和原型对日志

仓内一条验收是无头 Python 开发包，不是 UE 包，也不 cook：

```bash
PYTHONPATH=sim python3 -m steel_tide m2-pack --check
```

它串起下面每一条。规格见 [../NR-M2-pack.md](../NR-M2-pack.md)。

```bash
PYTHONPATH=sim python3 -m steel_tide repro
PYTHONPATH=sim python3 -m steel_tide nr02 --check
PYTHONPATH=sim python3 -m steel_tide nr03 --check
PYTHONPATH=sim python3 -m steel_tide m1 --check
PYTHONPATH=sim python3 -m steel_tide m1-pass --check
PYTHONPATH=sim python3 -m steel_tide m1-bot --check
PYTHONPATH=sim python3 -m steel_tide m2-resident --check
PYTHONPATH=sim python3 -m steel_tide m2-roles --check
PYTHONPATH=sim python3 -m steel_tide m2-bridge --check
```

双端对照用 [DUAL_END_EVENT_LOG.md](DUAL_END_EVENT_LOG.md)。`nr02` 是 3v3（两个客户端视角 + 四个本地 bot）的参照日志，样例在 `docs/evidence/nr02/`。`repro` 仍是四条脚本复现。

NR-02 的通过线是双端日志里出现与这三条相同的结果，而不是同一堆毫秒时间（灰盒手测对不齐样例里的 `place_for_test`）：

- 同帧两次拾取：一条 `CorePicked`，一条 `CorePickRejected` / `already_held`，全程审计不出第二个持有者。
- 读条中受击或离开：`ScoreChannelInterrupted`，没有 `PointScored`。倒地会 `CoreDropped`，满 5 秒 `ActorRespawned`，芯留在掉落处。
- 芯进海水或卡住体积：满 8 秒一条 `CoreReset` 回到 `center`，没有 `PointScored`。得分回中用的是 `CoreReturnedToCenter`，不要接成复位。

出现双持或一次读条记两次分，把两端日志退回 Codex，不要在编辑器里改胜负条件。
