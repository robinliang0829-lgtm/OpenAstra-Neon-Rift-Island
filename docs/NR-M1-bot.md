# NR-M1-bot

给游戏组-虚幻引擎操作。这张卡让四个 `local_bot` 用同一份策略走完一局 3v3。两个客户端视角在场，人留在出生点，不拿芯。抢芯、近距传球、打断一次读条、再把比分打到 2，都写在日志里。

**UE 仍挂。** 本环境没有装 UE，没有 PIE，也没有实机录像。`EngineAssociation` 仍是 `5.4` 占位。不要改它，不要交 `.umap` / `.uasset`。桥的 4 秒预警已经在 NR-03 落地，这张卡只调用 `schedule_bridge_connect`，不另写一套灯带。

**验证动作：** 跑下面的 `--check`。它打一局 3v3：四个本地 bot 沿机修巷走到中场，同帧抢芯；持有者把芯传给同一坐标的队友；突进在对方端子上让服务器打断一次读条，这一次没有分；之后两段完整读条把 A 打到 2 分，`MatchSettled` 的 `kind` 为 `points`，不进入加时。

**通过（仓内，本 PR HEAD）：** `PYTHONPATH=sim python3 -m steel_tide m1-bot --check` 退出码为 0。这不是实机通过。

**通过（上机）：** 仍做不到。UE 仍挂。装上本机引擎之前，不要用关卡蓝图写第二套计分来换一张「通过」。

## 输入

- 与 NR-01 / NR-02 / NR-03 / NR-M1 / NR-M1-pass 同一工程、同一关卡距离、同一份 `config/steel_tide_greybox.json`
- 事件名：`Source/NeonRift/Public/NeonRiftEventNames.h`，与 `sim/steel_tide/events.py` 同一集合。这张卡增加 `BotDecision`。它只记录本地 bot 的选择，不改持有者，不计分
- 双端格式：`docs/rules/DUAL_END_EVENT_LOG.md`。本卡 schema 是 `nr-m1-bot-dual-end-v1`，表头多一个 `identities`
- 近距：`pass_range_m`（4）。策略只在距离小于或等于这个值时传。样例里的 `distance_m` 是 `0.0`
- 读条：`score_channel_seconds`（3）。打断原因 `hit`，发生在读条开始后 1 秒，`down` 为 false，人不倒，芯不掉
- 先到：`points_to_win`（2）。常规时间里到达就 `kind=points`
- 桥预警：NR-03 已入库的 4 秒。样例在接通前 4.000 秒 `BridgeWarningStarted`（8.000 秒），12.000 秒 `BridgeWarningCompleted` 与 `BridgeStateChanged` 同时发生
- 路线：四人 `preferred_route` 都是 `repair_alley`。巷道走不到 `terminal_a`（出生点到本方端子那条边是高架），所以 B 的支援留在中场
- 这张卡不用 `place_for_test`。bot 自己沿边走
- 命令：

```bash
PYTHONPATH=sim python3 -m steel_tide m1-bot
PYTHONPATH=sim python3 -m steel_tide m1-bot --check
```

- 样例：`docs/evidence/nr-m1-bot/server.log`、`docs/evidence/nr-m1-bot/client-a.log`、`docs/evidence/nr-m1-bot/client-b.log`

上机自己走到体积里，毫秒不必和样例相同。`BotDecision` 的 `reason` 和 `target_id` 要对得上。

## 名单

| id | 视角 | 身体 `body` | 操控者 `controller` | 阵营 `faction` | 岗位 |
| --- | --- | --- | --- | --- | --- |
| a1 | `client-a` | `humanoid_robot` | `human` | A | 突进 `assault` |
| a2 | `bot-a2` | `humanoid_robot` | `local_bot` | A | 支援 `support` |
| a3 | `bot-a3` | `human` | `local_bot` | A | 侦察 `recon` |
| b1 | `client-b` | `humanoid_robot` | `human` | B | 侦察 `recon` |
| b2 | `bot-b2` | `humanoid_robot` | `local_bot` | B | 突进 `assault` |
| b3 | `bot-b3` | `beast` | `local_bot` | B | 支援 `support` |

四个 `local_bot` 不是生产数字居民。`digital_resident` 仍是第三种操控者。这张卡不构造它，策略也不调用它。可运行的薄策略在 [NR-M2-resident.md](NR-M2-resident.md)。

- Python：`sim/steel_tide/resident_port.py` 的 `DigitalResidentPort`。本卡的 `bot_policy` 与 `nr_m1_bot` 不调用 `select_match` / `decide`
- UE：`UNeonRiftResidentPort` 的薄策略由 NR-M2 写下。GameMode / GameState / PlayerState 不构造它

身体、本局阵营、操控者仍是三个字段。`BotDecision` 的 `controller` 只写 `local_bot`。人类视角没有这条事件。UE 侧只订阅。`ANeonRiftGameState` 听见 `BotDecision`，不把它记成持有者或比分。GameMode / GameState / PlayerState 不加分，也不选第二个持有者。胜负仍只在 `sim/steel_tide`。

## 这局要发生的事

1. 开局四个 bot 沿机修巷走向 `center`。每一步都有 `BotDecision`，`reason` 为 `contest_core`，`target_id` 为 `core`。a1、b1 留在 `spawn_a`、`spawn_b`。
2. 10.500 秒四人同时 `pick_core`。`CorePicked` 给 a2，a3、b2、b3 是 `CorePickRejected`，原因 `already_held`。同帧只有一个持有者。
3. 10.500 秒 a2 把芯传给站在同一坐标的 a3。`BotDecision` 的 `action` 为 `pass_core`，`reason` 为 `close_range_pass`，`target_id` 为 `a3`，`distance_m` 为 `0.0`。同一毫秒 `CorePassed`。没有 `CorePassRejected`。
4. b2 前往 A 的得分端子 `terminal_b`，准备打断。传球落地前，这一步的 `target_id` 还是当时的持有者 a2；传出之后改成 a3。
5. 桥在 12.000 秒接通。预警仍是 NR-03 的 4 秒，警报和灯带一起开始。预警不加分。bot 继续走巷，不改道。
6. 26.500 秒 a3 在 `terminal_b` 开始读条。`BotDecision` 的 `reason` 为 `score_path`，`target_id` 为 `terminal_b`。同一毫秒 b2 决定 `interrupt_channel`，`reason` 为 `contest_channel`，`target_id` 为 `a3`。命中不是 bot 客户端发的：模拟替服务器在 27.500 秒排队一次 `hit`，`down` 为 false。`ScoreChannelInterrupted` 原因 `hit`，`elapsed_ms` 为 1000。这一毫秒没有 `PointScored`，没有 `ActorDowned`，也没有 `CoreDropped`。芯还在 a3 手上。
7. 27.500 秒 a3 再次读条，这次没有人再打断。30.500 秒 `PointScored` 使比分变成 A=1 B=0，同一毫秒 `CoreReturnedToCenter`。这一分不到 2，比赛不结束。
8. 芯回到 `center`。a2 还站在那里，b3 也还在（巷道走不到 `terminal_a`）。30.500 秒第二次同帧抢芯：a2 `CorePicked`，b3 `already_held`。两条 `BotDecision` 的 `reason` 仍是 `contest_core`。
9. a2 沿巷把芯送到 `terminal_b`，43.500 秒读条。46.500 秒 `PointScored` 使比分变成 A=2 B=0，同一毫秒 `CoreReturnedToCenter` 与 `MatchSettled`。`kind` 为 `points`，胜者 A。没有 `OvertimeStarted`，也没有 `MatchClockExpired`。时刻仍在 360 秒常规时间之内。两个视角仍在出生点。

`hit` 仍是服务器命令。日志里用 b2 的 `BotDecision` 对上那一次打断，不要在 PlayerState 里自己减一条读条。

## 上机以后

UE 仍挂。装上本机引擎之后才做这些，做不到就停，把安装路径回给 PM-钢潮岛：

1. `--check` 先通过。不过就不要上机。
2. 打开 `NeonRift.uproject`。`EngineAssociation` 仍是 `5.4` 占位。不要改。
3. 不要交回 `.umap` / `.uasset`。
4. PIE 两个独立输入的客户端。四个本地 bot 不要写成数字居民，也不要构造 `UNeonRiftResidentPort` 来充数。
5. 不要在 PlayerState 里加分。持有者、`BotDecision` 的 `reason` / `target_id`，以及 `kind=points` 都从服务器日志抄。
6. 日志按 `docs/rules/DUAL_END_EVENT_LOG.md` 落三份。事件名和 JSON 对得上即可，毫秒可以和样例不同。
7. 双持、打断那一次记了分、或先到 2 分却进入加时：三份日志原样退回。不要改胜负条件。
