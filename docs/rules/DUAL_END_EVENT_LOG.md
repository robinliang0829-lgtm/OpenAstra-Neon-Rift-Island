# 双端事件日志

NR-02 用三份文本对同一局。权威在 `sim/steel_tide`。两端视角各抄一份，不另记持有者，也不另加分。

样例（3v3，两个客户端视角 + 四个 `local_bot`）：

- `docs/evidence/nr02/server.log`
- `docs/evidence/nr02/client-a.log`
- `docs/evidence/nr02/client-b.log`

生成并核对：

```bash
PYTHONPATH=sim python3 -m steel_tide nr02
PYTHONPATH=sim python3 -m steel_tide nr02 --check
```

`place_for_test` 只表示「人已经站在体积里」。它不是事件。上机时自己走到体积里，毫秒不必和样例相同。

## 行

文件是 UTF-8。表头一行一条，以 `# ` 开头，键和值用一个空格分开：

| 键 | 含义 |
| --- | --- |
| `schema` | `nr02-dual-end-v1` |
| `authority` | `sim/steel_tide` |
| `end` | `server`、`client-a` 或 `client-b` |
| `viewpoint_client` | 服务器写 `-`。视角写自己的 `client_id` |
| `controlled` | 这一端操控的战斗员。服务器是全体；`client-a` 是 `a1`；`client-b` 是 `b1` |
| `local_bots` | 四个本地 bot 的 id。三端相同。他们不是生产数字居民 |
| `roster` | `id:controller:faction:client_id`，按 id 排序，三端相同 |
| `mirrored_holder` | 按下面的表重放后的持有者。没有则 `-` |
| `mirrored_score` | `A=<n> B=<n>`。只从 `PointScored` 的 `payload.score` 抄过来 |
| `event_lines` | 表头以下的事件行数 |
| `comparable` | `event_body_identical`。这一版三端的事件正文必须逐字相同 |

三端可以不同的表头只有 `end`、`viewpoint_client`、`controlled`。其余字段必须相同。

事件正文与 `Event.format()` 相同：

```text
   t_s  EventName  {"sorted":"json"}
```

`t_s` 宽 8、三位小数，时间是毫秒除以 1000。事件名和 JSON 之间是两个空格。JSON 键排序。

UE 存根还没有权威时钟时，行是：

```text
EventName  {json}
```

`ANeonRiftGameState::AuthoritativeEventLog` 和 `ANeonRiftPlayerState::ViewpointEventLog` 用这个短格式。输出日志同样两个空格。对照样例时认事件名和 JSON，不认本机世界时间。

## 怎么对

1. 丢掉以 `# ` 开头的行。
2. 这一版样例里，三端剩下的行必须相同。
3. 重放持有者：`CorePicked` 写入 `combatant_id`，`CorePassed` 改成 `to_id`，`CoreDropped` / `CoreReset` / `CoreReturnedToCenter` 清空。其它事件不改持有者。
4. 重放比分：看到 `PointScored` 就用它的 `payload.score` 覆盖镜像。`ScoreChannelInterrupted`、`ScoreChannelRejected`、`CoreReset` 不得记分。不要在本地 `+1`。
5. `mirrored_holder` 和 `mirrored_score` 三端相同，并且等于重放结果。服务器上的重放还要等于 `SteelTideMatch` 的 `core.holder_id` 和 `score`。
6. UE 实机日志的毫秒可以不同。事件名集合、同一条读条的打断、以及重放出来的持有者和比分必须和通过条件一致。

`PointScored` 本身不清持有者。紧跟着的 `CoreReturnedToCenter` 才清空。倒地先有 `CoreDropped`，然后才是 `ActorDowned`。芯被标记成不可拾取时，若当时有人拿着，会先有 `CoreDropped`；`CoreMarkedUnpickable` 自己不改持有者。

同帧抢芯只应有一条 `CorePicked`。另一人是 `CorePickRejected`，原因 `already_held`。打断那一毫秒没有 `PointScored`。`CoreReset` 的 `anchor` 为 `center` 时，关卡对象是 `NR_CoreSpawn`。`CoreReturnedToCenter` 也回到这个锚点，但它不是超时复位。

## 事件表

与 `sim/steel_tide/events.py` 的 `EVENT_NAMES` 逐条对齐。UE 名字在 `NeonRiftEventNames.h`。

<!-- nr02-event-schema -->
| 事件 | 持有者 | 比分 | 打断 |
| --- | --- | --- | --- |
| `AbilityRejected` | 不改变持有者 | 不改变比分 | 不是打断 |
| `AbilityUsed` | 不改变持有者 | 不改变比分 | 不是打断 |
| `ActorDowned` | 不改变持有者 | 不改变比分 | 不是打断 |
| `ActorRespawned` | 不改变持有者 | 不改变比分 | 不是打断 |
| `BridgeLightStripAdvanced` | 不改变持有者 | 不改变比分 | 不是打断 |
| `BridgeOccupantNudged` | 不改变持有者 | 不改变比分 | 不是打断 |
| `BridgeStateChanged` | 不改变持有者 | 不改变比分 | 不是打断 |
| `BridgeWarningCompleted` | 不改变持有者 | 不改变比分 | 不是打断 |
| `BridgeWarningStarted` | 不改变持有者 | 不改变比分 | 不是打断 |
| `BotDecision` | 不改变持有者 | 不改变比分 | 不是打断 |
| `CombatantJoined` | 不改变持有者 | 不改变比分 | 不是打断 |
| `CoreDropRejected` | 不改变持有者 | 不改变比分 | 不是打断 |
| `CoreDropped` | 清空持有者 | 不改变比分 | 不是打断 |
| `CoreMarkRejected` | 不改变持有者 | 不改变比分 | 不是打断 |
| `CoreMarkedUnpickable` | 不改变持有者 | 不改变比分 | 不是打断 |
| `CorePassRejected` | 不改变持有者 | 不改变比分 | 不是打断 |
| `CorePassed` | 持有者改为 `to_id` | 不改变比分 | 不是打断 |
| `CorePickRejected` | 不改变持有者 | 不改变比分 | 不是打断 |
| `CorePicked` | 写入持有者（`combatant_id`） | 不改变比分 | 不是打断 |
| `CoreReset` | 清空持有者 | 不得记分 | 不是打断 |
| `CoreReturnedToCenter` | 清空持有者 | 不改变比分 | 不是打断 |
| `FactionChosen` | 不改变持有者 | 不改变比分 | 不是打断 |
| `FactionRejected` | 不改变持有者 | 不改变比分 | 不是打断 |
| `FactionsLocked` | 不改变持有者 | 不改变比分 | 不是打断 |
| `HitIgnored` | 不改变持有者 | 不改变比分 | 不是打断 |
| `HitRejected` | 不改变持有者 | 不改变比分 | 不是打断 |
| `MatchClockExpired` | 不改变持有者 | 不改变比分 | 不是打断 |
| `MatchSettled` | 不改变持有者 | 不改变比分 | 不是打断 |
| `MatchStarted` | 不改变持有者 | 不改变比分 | 不是打断 |
| `MoveCompleted` | 不改变持有者 | 不改变比分 | 不是打断 |
| `MoveRejected` | 不改变持有者 | 不改变比分 | 不是打断 |
| `OvertimeStarted` | 不改变持有者 | 不改变比分 | 不是打断 |
| `PointScored` | 不改变持有者 | 用 `payload.score` 覆盖镜像比分 | 不是打断 |
| `ResidentDecision` | 不改变持有者 | 不改变比分 | 不是打断 |
| `RoleChosen` | 不改变持有者 | 不改变比分 | 不是打断 |
| `RoleRejected` | 不改变持有者 | 不改变比分 | 不是打断 |
| `RolesLocked` | 不改变持有者 | 不改变比分 | 不是打断 |
| `RouteRejected` | 不改变持有者 | 不改变比分 | 不是打断 |
| `RouteSelected` | 不改变持有者 | 不改变比分 | 不是打断 |
| `ScoreChannelInterrupted` | 不改变持有者 | 不得记分 | 是打断 |
| `ScoreChannelRejected` | 不改变持有者 | 不得记分 | 不是打断 |
| `ScoreChannelStarted` | 不改变持有者 | 不改变比分 | 不是打断 |
<!-- /nr02-event-schema -->

## NR-M1

同一套三端正文，schema 换成 `nr-m1-dual-end-v1`。多一个表头 `identities`，格式 `id:body:faction:controller`。它不参加计分。样例在 `docs/evidence/nr-m1/`。平局加时的服务器日志是 `retie.log`，schema `nr-m1-retie-v1`。

```bash
PYTHONPATH=sim python3 -m steel_tide m1 --check
```

## NR-M1-pass

同一套三端正文，schema 换成 `nr-m1-pass-dual-end-v1`。表头同样有 `identities`。样例在 `docs/evidence/nr-m1-pass/`。这一局在常规时间先到 2 分结束，日志里没有 `OvertimeStarted`。

```bash
PYTHONPATH=sim python3 -m steel_tide m1-pass --check
```

## NR-M1-bot

同一套三端正文，schema 换成 `nr-m1-bot-dual-end-v1`。表头同样有 `identities`。样例在 `docs/evidence/nr-m1-bot/`。四个 `local_bot` 的 `BotDecision` 带 `reason` 和 `target_id`。这一局在常规时间先到 2 分结束，日志里没有 `OvertimeStarted`。`digital_resident` 不进这局。

```bash
PYTHONPATH=sim python3 -m steel_tide m1-bot --check
```

## NR-M2-resident

同一套三端正文，schema 换成 `nr-m2-resident-dual-end-v1`。表头有 `identities`，另有 `digital_residents`。样例在 `docs/evidence/nr-m2-resident/`。`a2` 的 `controller` 是 `digital_resident`，决策事件是 `ResidentDecision`。其余三个驱动者仍是 `local_bot`，决策事件是 `BotDecision`。这一局在常规时间先到 2 分结束，日志里没有 `OvertimeStarted`。`ResidentDecision` 不写墙后坐标。

```bash
PYTHONPATH=sim python3 -m steel_tide m2-resident --check
```

## NR-M2-roles

同一套三端正文，schema 换成 `nr-m2-roles-dual-end-v1`。表头有 `identities`，另有 `digital_residents`。样例在 `docs/evidence/nr-m2-roles/`。`a2` 仍是 `digital_resident`，其余三个驱动者仍是 `local_bot`。这一局在常规时间先到 2 分结束，日志里没有 `OvertimeStarted`。三种 `AbilityUsed` 都在：`dash`、`shield`、`mark`。使用能力时，`BotDecision` / `ResidentDecision` 的 `reason` 等于该人的岗位 id。侦察拒绝看不见的目标时，决策和 `AbilityRejected` 都不写坐标。

```bash
PYTHONPATH=sim python3 -m steel_tide m2-roles --check
```

## NR-M2-bridge

同一套三端正文，schema 换成 `nr-m2-bridge-dual-end-v1`。表头有 `identities`，另有 `digital_residents`。样例在 `docs/evidence/nr-m2-bridge/`。`a2` 仍是 `digital_resident`，其余三个驱动者仍是 `local_bot`。这一局在常规时间先到 2 分结束，日志里没有 `OvertimeStarted`。`BridgeStateChanged` 先 `connected`，后 `disconnected`，三端正文都有。`reason` 为 `path_recompute` 的决策在接通和断开各出现。断开时的 `BridgeOccupantNudged` 和 `MoveRejected` / `bridge_blocked` 不记分，也不击倒。

```bash
PYTHONPATH=sim python3 -m steel_tide m2-bridge --check
```

## NR-M2-pack

这条不新加双端 schema，也不新加事件名。它把 `repro`、上面各张 `--check` 和 `unittest` 串成一条无头 Python 验收。不是 UE 包。命令和退出码在 `docs/evidence/nr-m2-pack/`。

```bash
PYTHONPATH=sim python3 -m steel_tide m2-pack --check
```

## NR-M2-audio

`AudioCue` 不进上面的事件表，也不进三端正文。它是权威事件同一毫秒的旁路日志，不改持有者，不加分，不是打断。样例在 `docs/evidence/nr-m2-audio/audio.log`。这条不进 `m2-pack` 的步骤表。

```bash
PYTHONPATH=sim python3 -m steel_tide m2-audio --check
```
