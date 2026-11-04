# NR-M2-bridge

给游戏组-虚幻引擎操作。这张卡让桥的接通和断开改权威路线图。跨度边只在桥合上（`connected`）时可以走。桥张开（`disconnected`）时，这两条边不在图里。机修巷不靠跨度，断开时仍能走到对方端子并得分。

**预警仍是 NR-03。** 4 秒提前量、`BridgeWarningStarted`、`BridgeLightStripAdvanced`、`BridgeWarningCompleted` 都调用已经入库的 `schedule_bridge_connect`。不另写灯带。断开调用已经入库的 `schedule_bridge_disconnect`。

**不新造计分，也不新造事件名。** 抢芯、近距传球、一次读条打断、常规先到 2 分，以及突进 / 支援 / 侦察，都走 NR-M1-bot、NR-M2-resident、NR-M2-roles 的口。路径重算写在已有的 `BotDecision` / `ResidentDecision` 上，`reason` 为 `path_recompute`。

**UE 仍挂。** 本环境没有装 UE，没有 PIE，也没有实机录像。`EngineAssociation` 仍是 `5.4` 占位。不要改它，不要交 `.umap` / `.uasset`。

**验证动作：** 跑下面的 `--check`。它打一局 3v3：预警、接通、有人走过跨度、再断开。断开时跨度上的人落到本方桥头，已经排上的跨度步被拒绝。落点和拒绝都不记分，也不把人打倒。机修巷在断开之后仍走出一分，并先到 2 分。

**通过（仓内，本 PR HEAD）：** `PYTHONPATH=sim python3 -m steel_tide m2-bridge --check` 退出码为 0。这不是实机通过。`m1-bot --check`、`m2-resident --check`、`m2-roles --check` 仍是 0。那三张卡不改路线偏好，样例日志不变。

**通过（上机）：** 仍做不到。UE 仍挂。装上本机引擎之前，不要用关卡蓝图写第二套计分来换一张「通过」。

## 输入

- 与 NR-01 / NR-02 / NR-03 / NR-M1 / NR-M1-pass / NR-M1-bot / NR-M2-resident / NR-M2-roles 同一工程、同一关卡距离、同一份 `config/steel_tide_greybox.json`
- 事件名不新增。`BridgeStateChanged` 的 `state` 仍是 `connected` 或 `disconnected`
- 双端格式：`docs/rules/DUAL_END_EVENT_LOG.md`。本卡 schema 是 `nr-m2-bridge-dual-end-v1`。表头有 `identities`，另有 `digital_residents`
- 权威路线图：非跨度边一直在。跨度边是 `bridgehead_a-center` 和 `bridgehead_b-center`，只在 `connected` 时进入图。`span_edges` 在断开时是空字符串
- 偏好：`b2` 的 `preferred_route` 是 `elevated`。其余五人是 `repair_alley`。巷道偏好在跨度合上时也不改走桥；跨度偏好在桥张开时先沿固定甲板走到桥头，不踏上空的跨度
- 桥头是安全甲板。`center` 在跨度上。断开时站在 `center` 的人落到本方桥头（`bridgehead_a` / `bridgehead_b`）。人在桥头再请求 `center`，得到 `MoveRejected`，原因 `bridge_blocked`，人留在桥头
- 持芯者被挪走时芯跟着人走。不写 `CoreDropped`，不写 `PointScored`，不写 `ActorDowned`
- 抢芯、传球、打断、先到 2 分、岗位能力与前面的卡同一套函数。决策 `reason` 仍是 `contest_core`、`close_range_pass`、`contest_channel`、`score_path`，外加桥图变化时的 `path_recompute`。常规时间到达 `points_to_win` 就 `kind=points`
- 这张卡不用 `place_for_test`。驱动者自己沿边走
- 命令：

```bash
PYTHONPATH=sim python3 -m steel_tide m2-bridge
PYTHONPATH=sim python3 -m steel_tide m2-bridge --check
```

- 样例：`docs/evidence/nr-m2-bridge/server.log`、`docs/evidence/nr-m2-bridge/client-a.log`、`docs/evidence/nr-m2-bridge/client-b.log`

上机自己走到体积里，毫秒不必和样例相同。三端都要看见一次 `connected` 和一次 `disconnected`。断开之后的得分路径不能再踏跨度边。

## 名单

| id | 视角 | 身体 `body` | 操控者 `controller` | 阵营 `faction` | 岗位 | 路线 |
| --- | --- | --- | --- | --- | --- | --- |
| a1 | `client-a` | `humanoid_robot` | `human` | A | 突进 `assault` | `repair_alley` |
| a2 | `bot-a2` | `humanoid_robot` | `digital_resident` | A | 支援 `support` | `repair_alley` |
| a3 | `bot-a3` | `human` | `local_bot` | A | 侦察 `recon` | `repair_alley` |
| b1 | `client-b` | `humanoid_robot` | `human` | B | 侦察 `recon` | `repair_alley` |
| b2 | `bot-b2` | `humanoid_robot` | `local_bot` | B | 突进 `assault` | `elevated` |
| b3 | `bot-b3` | `beast` | `local_bot` | B | 支援 `support` | `repair_alley` |

`a2` 的阵营和岗位仍来自 `select_match`。两个人类视角留在出生点。

## 这局要发生的事

1. 0.000 秒 `a2` 写下 `ResidentDecision`，`action` 为 `select_match`。随后才锁队。四人出发。`a2`、`a3`、`b3` 进机修巷。`b2` 沿高架甲板走向桥头，不进巷。
2. 2.250 秒 `a3` 在 `alley_a`，看不见 `b1`。`AbilityRejected`，能力 `mark`，原因 `not_visible`。没有坐标。
3. 3.000 秒 `b2` 到 `bridgehead_b`。同一毫秒请求踏上 `center`，`MoveRejected`，原因 `bridge_blocked`。人留在桥头。这一毫秒没有 `PointScored`，也没有 `ActorDowned`。
4. 3.500 秒 `BridgeWarningStarted`，`lead_ms` 为 4000，`readable_without_reflection` 为 true。灯带在这一毫秒和 7.500 秒之间递进。预警不加分。
5. 7.500 秒 `BridgeWarningCompleted` 与 `BridgeStateChanged` 同一毫秒。`state` 为 `connected`。`b2` 的 `BotDecision` 是 `path_recompute`：`anchor` 为 `bridgehead_b`，`path` 为 `center`，`span_walkable` 为 true，`span_edges` 为 `bridgehead_a-center,bridgehead_b-center`。同一毫秒突进想跳上 `center`（24 米），`AbilityRejected`，原因 `out_of_range`。人仍在桥头。
6. 10.500 秒 `b2` 的 `MoveCompleted` 从 `bridgehead_b` 到 `center`，`route` 为 `elevated`。这是跨度边，只在接通之后发生。同一毫秒巷道三人到 `center`。`CorePicked` 给 `a2`。`a3`、`b2`、`b3` 是 `already_held`。`a2` 把芯传给同一坐标的 `a3`。`a3` 标记看得见的 `b1`。`a2` 和 `b3` 各放一次定向护盾，下一发是 `HitIgnored`，原因 `shield`。没有 `ActorDowned`。
7. 12.000 秒桥再张开。`b2` 已经排好的跨度步（去 `bridgehead_b`）先是 `MoveRejected`，原因 `bridge_blocked`。站在 `center` 的 `a2`、`a3`、`b2`、`b3` 各有一条 `BridgeOccupantNudged`，原因 `span_not_embedded`，落到本方桥头。`a3` 当时持芯，芯跟着到 `bridgehead_a`，没有 `CoreDropped`。随后 `BridgeStateChanged`，`state` 为 `disconnected`。四条 `path_recompute` 的 `span_walkable` 都是 false，`span_edges` 是空字符串，路径里没有跨度边。`a3` 的路径是 `terminal_a>spawn_a>alley_a>alley_mid>alley_b>spawn_b>terminal_b`。这一毫秒没有 `PointScored`，也没有 `ActorDowned`。`b2` 沿固定甲板突进到 `terminal_b`（12 米，不是跨度），再跳一次吃到 `cooldown`。
8. 40.000 秒 `a3` 沿上面这条不跨桥的路走到 `terminal_b`，开始读条。41.000 秒 `ScoreChannelInterrupted`，原因 `hit`，`elapsed_ms` 为 1000。这一毫秒没有 `PointScored`。护盾已在 10.500 秒用掉。
9. 44.000 秒 `PointScored` 使比分变成 A=1 B=0。读条从 41.000 秒重新开始，这一分是读条走完，不是桥头拒绝记的分。同一毫秒 `b2` 又到 `bridgehead_b`，请求 `center` 再次 `bridge_blocked`。人留在桥头。桥仍是 `disconnected`。
10. 54.500 秒芯在 `center`，`a3` 从机修巷回来 `CorePicked`。之后仍走 `repair_alley` 到 `terminal_b`，不踏跨度。
11. 73.500 秒 `PointScored` 使比分变成 A=2 B=0，同一毫秒 `CoreReturnedToCenter` 与 `MatchSettled`。`kind` 为 `points`，胜者 A。没有 `OvertimeStarted`，也没有 `MatchClockExpired`。两个视角仍在出生点。桥停在 `disconnected`，路线图里没有跨度边。

## 上机以后

UE 仍挂。装上本机引擎之后才做这些，做不到就停，把安装路径回给 PM-钢潮岛：

1. `--check` 先通过。不过就不要上机。`m1-bot`、`m2-resident`、`m2-roles` 的 `--check` 也要仍是 0。
2. 打开 `NeonRift.uproject`。`EngineAssociation` 仍是 `5.4` 占位。不要改。
3. 不要交回 `.umap` / `.uasset`。
4. PIE 两个独立输入的客户端。导航网格跟权威路线图：桥张开时跨度不可走，机修巷可走。不要在关卡蓝图里另写一套可走边。
5. 断开时人不能留在跨度碰撞里。落到桥头，或在桥头被拒绝。不要因此记分或击倒。
6. 日志按 `docs/rules/DUAL_END_EVENT_LOG.md` 落三份。两端都要有 `connected` 和 `disconnected`。事件名和 JSON 对得上即可，毫秒可以和样例不同。
7. 双持、断开记了分、人被桥夹死、或巷道在桥张开时走不通：三份日志原样退回。不要改胜负条件。
