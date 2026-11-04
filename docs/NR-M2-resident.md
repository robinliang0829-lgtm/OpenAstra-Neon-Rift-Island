# NR-M2-resident

给游戏组-虚幻引擎操作。这张卡把空的 `DigitalResidentPort` / `UNeonRiftResidentPort` 接成一份可跑的薄策略。一局 3v3 里至少有一名 `controller=digital_resident`。他用 `select_match` 选合法座位，再用 `decide` 出意图。另外三名驱动者仍是 `local_bot`。两个人类视角留在出生点。

**这不是生产数字居民。** 策略只接受合法座位，或在没有座位提议时取该身体的第一个合法阵营和第一个岗位。它复用 NR-M1-bot 的抢芯、近距传球、一次读条打断、常规先到 2 分，以及 NR-03 的 4 秒桥预警。不另写计分，不另写灯带。

**不喂墙后坐标。** 机修巷里不同锚点的敌人只以 `id` 进入感知。队友信号可以有锚点名和 `distance_m`。感知和 `ResidentDecision` 都不写 `pos`、`x`、`y`、`x_m`、`y_m`。公开的得分端子名不是敌人的实时坐标。

**UE 仍挂。** 本环境没有装 UE，没有 PIE，也没有实机录像。`EngineAssociation` 仍是 `5.4` 占位。不要改它，不要交 `.umap` / `.uasset`。

**验证动作：** 跑下面的 `--check`。它打一局 3v3：`a2` 先 `select_match` 加入 A 的支援；四个驱动者沿机修巷同帧抢芯；`a2` 把芯传给同一坐标的 `a3`；`b2` 在对方端子上让服务器打断一次读条，这一次没有分；之后两段完整读条把 A 打到 2 分，`MatchSettled` 的 `kind` 为 `points`，不进入加时。

**通过（仓内，本 PR HEAD）：** `PYTHONPATH=sim python3 -m steel_tide m2-resident --check` 退出码为 0。这不是实机通过。

**通过（上机）：** 仍做不到。UE 仍挂。装上本机引擎之前，不要用关卡蓝图写第二套计分来换一张「通过」。

## 输入

- 与 NR-01 / NR-02 / NR-03 / NR-M1 / NR-M1-pass / NR-M1-bot 同一工程、同一关卡距离、同一份 `config/steel_tide_greybox.json`
- 事件名：`Source/NeonRift/Public/NeonRiftEventNames.h`，与 `sim/steel_tide/events.py` 同一集合。这张卡增加 `ResidentDecision`。它只记录薄策略的选择，不改持有者，不计分
- 双端格式：`docs/rules/DUAL_END_EVENT_LOG.md`。本卡 schema 是 `nr-m2-resident-dual-end-v1`。表头有 `identities`，另有 `digital_residents`
- `BotDecision` 的 `controller` 只写 `local_bot`。`ResidentDecision` 的 `controller` 只写 `digital_resident`。人类视角没有这两条
- 近距：`pass_range_m`（4）。样例里的 `distance_m` 是 `0.0`
- 读条：`score_channel_seconds`（3）。打断原因 `hit`，发生在读条开始后 1 秒，`down` 为 false
- 先到：`points_to_win`（2）。常规时间里到达就 `kind=points`
- 桥预警：NR-03 已入库的 4 秒。样例在接通前 4.000 秒 `BridgeWarningStarted`（8.000 秒），12.000 秒 `BridgeWarningCompleted` 与 `BridgeStateChanged` 同时发生。这张卡只调用 `schedule_bridge_connect`
- 路线：四人 `preferred_route` 都是 `repair_alley`。巷道走不到 `terminal_a`，所以 B 的支援留在中场
- `a2` 的 `client_id` 仍是 `bot-a2`。这是同帧拾取的排序键，不是操控者。操控者看 `controller`
- 这张卡不用 `place_for_test`。驱动者自己沿边走
- 命令：

```bash
PYTHONPATH=sim python3 -m steel_tide m2-resident
PYTHONPATH=sim python3 -m steel_tide m2-resident --check
```

- 样例：`docs/evidence/nr-m2-resident/server.log`、`docs/evidence/nr-m2-resident/client-a.log`、`docs/evidence/nr-m2-resident/client-b.log`

上机自己走到体积里，毫秒不必和样例相同。`ResidentDecision` 与 `BotDecision` 的 `controller`、`reason`、`target_id` 要对得上。

## 名单

| id | 视角 | 身体 `body` | 操控者 `controller` | 阵营 `faction` | 岗位 |
| --- | --- | --- | --- | --- | --- |
| a1 | `client-a` | `humanoid_robot` | `human` | A | 突进 `assault` |
| a2 | `bot-a2` | `humanoid_robot` | `digital_resident` | A | 支援 `support` |
| a3 | `bot-a3` | `human` | `local_bot` | A | 侦察 `recon` |
| b1 | `client-b` | `humanoid_robot` | `human` | B | 侦察 `recon` |
| b2 | `bot-b2` | `humanoid_robot` | `local_bot` | B | 突进 `assault` |
| b3 | `bot-b3` | `beast` | `local_bot` | B | 支援 `support` |

`a2` 的阵营和岗位来自 `select_match`。人形机器人可以选 A 或 B；提议 A / `support` 合法，端口接受。兽被提议 A 时端口拒绝。没有提议时，端口取该身体的第一个合法阵营和第一个岗位，用来证明它会自己选，而不是把任何字符串都写下。

身体、本局阵营、操控者仍是三个字段。UE 侧只订阅。`ANeonRiftGameState` 听见 `ResidentDecision` 和 `BotDecision`，不把它们记成持有者或比分。GameMode / GameState / PlayerState 不构造 `UNeonRiftResidentPort`，不加分，也不选第二个持有者。胜负仍只在 `sim/steel_tide`。

C++ 的 `SelectMatch` / `Decide` 是同一份薄策略的旗标入口：身体与阵营是否合法、是否持芯、是否在芯上、队友是否在近距。参数里没有坐标，函数里不计分。仓内通过线跑的是 Python 端口。

## 感知

`decide` 只读 `perceive` 交出来的字典。

- 自己的锚点名、岗位、是否持芯、芯是否可拾取
- 芯在公开出生点 `center`。当前锚点只有观察者看得见时才写入
- 队友：`id`、岗位、锚点名、`distance_m`。这是队友信号
- 看得见的敌人：`id`、阵营、锚点名。同一锚点，或双方都不在机修巷
- 巷内另一锚点的敌人：只有 `id`。没有锚点，没有坐标
- 持有者在掩体后时不写他的锚点。他的阵营对应的得分端子名仍可写，那是规则表，不是他站的位置

## 这局要发生的事

1. 0.000 秒 `a2` 写下 `ResidentDecision`，`action` 为 `select_match`，`reason` 为 `legal_faction`，`target_id` 为 `A`，`role` 为 `support`，`join` 为 true。随后才 `FactionChosen` / `RoleChosen`。这一条在 `MatchStarted` 之前。
2. 开局 `a2` 的移动是 `ResidentDecision`，`a3`、`b2`、`b3` 的移动是 `BotDecision`。走向 `center` 时 `reason` 为 `contest_core`，`target_id` 为 `core`。a1、b1 留在 `spawn_a`、`spawn_b`。巷内错开的敌人不会把坐标写进 `ResidentDecision`。
3. 10.500 秒四人同时抢芯。`CorePicked` 给 a2，a3、b2、b3 是 `CorePickRejected`，原因 `already_held`。a2 的那条是 `ResidentDecision`，`controller` 为 `digital_resident`。另外三条是 `BotDecision`，`controller` 为 `local_bot`。
4. 10.500 秒 a2 把芯传给站在同一坐标的 a3。`ResidentDecision` 的 `action` 为 `pass_core`，`reason` 为 `close_range_pass`，`target_id` 为 `a3`，`distance_m` 为 `0.0`。同一毫秒 `CorePassed`。没有 `CorePassRejected`，也没有本地 bot 的传球决策。
5. b2 前往 A 的得分端子 `terminal_b`。这条是 `BotDecision`，`reason` 为 `interrupt_channel`。传球落地前 `target_id` 还是 a2；传出之后改成 a3。
6. 桥在 12.000 秒接通。预警仍是 NR-03 的 4 秒。预警不加分。
7. 26.500 秒 a3 在 `terminal_b` 开始读条。`BotDecision` 的 `reason` 为 `score_path`。同一毫秒 b2 决定 `interrupt_channel`，`reason` 为 `contest_channel`，`target_id` 为 `a3`。模拟替服务器在 27.500 秒排队一次 `hit`，`down` 为 false。`ScoreChannelInterrupted` 原因 `hit`，`elapsed_ms` 为 1000。这一毫秒没有 `PointScored`，没有 `ActorDowned`，也没有 `CoreDropped`。
8. 27.500 秒 a3 再次读条。30.500 秒 `PointScored` 使比分变成 A=1 B=0，同一毫秒 `CoreReturnedToCenter`。这一分不到 2，比赛不结束。
9. 30.500 秒第二次同帧抢芯：a2 `CorePicked`，b3 `already_held`。a2 是 `ResidentDecision`，b3 是 `BotDecision`，`reason` 都是 `contest_core`。
10. a2 沿巷把芯送到 `terminal_b`。43.500 秒 `ResidentDecision` 的 `action` 为 `begin_score`。46.500 秒 `PointScored` 使比分变成 A=2 B=0，同一毫秒 `CoreReturnedToCenter` 与 `MatchSettled`。`kind` 为 `points`，胜者 A。没有 `OvertimeStarted`，也没有 `MatchClockExpired`。两个视角仍在出生点。

`hit` 仍是服务器命令。日志里用 b2 的 `BotDecision` 对上那一次打断。

## 上机以后

UE 仍挂。装上本机引擎之后才做这些，做不到就停，把安装路径回给 PM-钢潮岛：

1. `--check` 先通过。不过就不要上机。
2. 打开 `NeonRift.uproject`。`EngineAssociation` 仍是 `5.4` 占位。不要改。
3. 不要交回 `.umap` / `.uasset`。
4. PIE 两个独立输入的客户端。不要把三个 `local_bot` 写成数字居民。不要在 PlayerState 里构造端口来充数，也不要在 PlayerState 里加分。
5. 薄策略不是生产 Resident。不要给它墙后坐标。`ResidentDecision` 和 `BotDecision` 的 `controller` 必须分开。
6. 持有者、`reason` / `target_id`，以及 `kind=points` 都从服务器日志抄。
7. 日志按 `docs/rules/DUAL_END_EVENT_LOG.md` 落三份。事件名和 JSON 对得上即可，毫秒可以和样例不同。
8. 双持、打断那一次记了分、或先到 2 分却进入加时：三份日志原样退回。不要改胜负条件。
