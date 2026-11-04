# NR-M2-roles

给游戏组-虚幻引擎操作。这张卡把三个岗位能力接进 `local_bot` 和 `digital_resident` 的决策。一局 3v3 的日志里，三种 `AbilityUsed` 都出现。`BotDecision` / `ResidentDecision` 在使用能力时，`reason` 写成该人的岗位 id。

**这不是生产数字居民。** `a2` 仍走 NR-M2-resident 的 `select_match` 和 `decide`。抢芯、近距传球、一次读条打断、常规先到 2 分，以及 NR-03 的 4 秒桥预警，都复用前面的口。不另写计分，不另写灯带。

**岗位和能力：**

| 岗位 id | 卡片叫法 | 能力 id | 这局里谁用 | 规则 |
| --- | --- | --- | --- | --- |
| `assault` | 突进 / rush | `dash` | `b2`，`local_bot` | 沿一条边短跳。距离 ≤ `range_m`（12）。更远的一跳 `AbilityRejected`，原因 `out_of_range`，人不挪。成功之后 `ready_ms` 加上冷却 8 秒；冷却内再跳，原因 `cooldown`，人仍不挪 |
| `support` | 支援 | `shield` | `a2`，`digital_resident`；`b3`，`local_bot` | 定向一发。`range_m` 是 0，所以只能给同一锚点的队友。载荷有 `directed_by`。同一毫秒的下一次命中是 `HitIgnored`，原因 `shield`。不罩另一队，也不把人打倒 |
| `recon` | 侦察 / scout | `mark` | `a3`，`local_bot` | 只标记看得见的目标。巷内另一锚点是 `AbilityRejected`，原因 `not_visible`。决策和拒绝都不写 `pos`、`x`、`y`、`x_m`、`y_m`。`scout` 不是第二个岗位 id |

决策的 `reason` 与岗位 id 相同：`assault`、`support`、`recon`。`role` 字段也是这个 id。能力 id 写在 `ability`。

**不喂墙后坐标。** 居民感知里，巷内另一锚点的敌人仍只有 `id`。队友信号可以有锚点名和 `distance_m`。下一跳只给锚点名和这条边的长度，不给坐标。

**UE 仍挂。** 本环境没有装 UE，没有 PIE，也没有实机录像。`EngineAssociation` 仍是 `5.4` 占位。不要改它，不要交 `.umap` / `.uasset`。

**验证动作：** 跑下面的 `--check`。它打一局 3v3：超距突进被拒绝，短突进落地并吃到冷却；两名支援各放一次定向护盾并挡住下一发；侦察先拒绝看不见的目标，再到看得见时标记同一个人。抢芯、传球、打断、先到 2 分、4 秒桥预警仍在这一局里。

**通过（仓内，本 PR HEAD）：** `PYTHONPATH=sim python3 -m steel_tide m2-roles --check` 退出码为 0。这不是实机通过。前面的 `m1-bot --check` 和 `m2-resident --check` 仍是 0。那两张卡不开岗位能力，样例日志不变。

**通过（上机）：** 仍做不到。UE 仍挂。装上本机引擎之前，不要用关卡蓝图写第二套计分来换一张「通过」。

## 输入

- 与 NR-01 / NR-02 / NR-03 / NR-M1 / NR-M1-pass / NR-M1-bot / NR-M2-resident 同一工程、同一关卡距离、同一份 `config/steel_tide_greybox.json`
- 事件名不新增。`AbilityUsed` / `AbilityRejected` 已在 `Source/NeonRift/Public/NeonRiftEventNames.h` 和 `sim/steel_tide/events.py`
- 双端格式：`docs/rules/DUAL_END_EVENT_LOG.md`。本卡 schema 是 `nr-m2-roles-dual-end-v1`。表头有 `identities`，另有 `digital_residents`
- `BotDecision` 的 `controller` 只写 `local_bot`。`ResidentDecision` 的 `controller` 只写 `digital_resident`
- 突进：`role_abilities.assault`，`range_m` 12，`cooldown_seconds` 8
- 支援：`role_abilities.support`，`range_m` 0，`cooldown_seconds` 12
- 侦察：`role_abilities.recon`，`cooldown_seconds` 10。看不见时不消耗冷却
- 近距、读条、先到 2 分、4 秒桥预警与 NR-M2-resident 相同。常规时间到达 `points_to_win` 就 `kind=points`
- 路线：四人 `preferred_route` 都是 `repair_alley`。巷道边都长于 12 米，所以超距拒绝发生在 `spawn_b` → `alley_b`（18 米）。短跳是共用边 `spawn_b` → `terminal_b`（12 米）
- 这张卡不用 `place_for_test`。驱动者自己沿边走
- 命令：

```bash
PYTHONPATH=sim python3 -m steel_tide m2-roles
PYTHONPATH=sim python3 -m steel_tide m2-roles --check
```

- 样例：`docs/evidence/nr-m2-roles/server.log`、`docs/evidence/nr-m2-roles/client-a.log`、`docs/evidence/nr-m2-roles/client-b.log`

上机自己走到体积里，毫秒不必和样例相同。`reason` 必须是岗位 id。三种 `AbilityUsed` 的 `ability` 必须是 `dash`、`shield`、`mark`。

## 名单

| id | 视角 | 身体 `body` | 操控者 `controller` | 阵营 `faction` | 岗位 |
| --- | --- | --- | --- | --- | --- |
| a1 | `client-a` | `humanoid_robot` | `human` | A | 突进 `assault` |
| a2 | `bot-a2` | `humanoid_robot` | `digital_resident` | A | 支援 `support` |
| a3 | `bot-a3` | `human` | `local_bot` | A | 侦察 `recon` |
| b1 | `client-b` | `humanoid_robot` | `human` | B | 侦察 `recon` |
| b2 | `bot-b2` | `humanoid_robot` | `local_bot` | B | 突进 `assault` |
| b3 | `bot-b3` | `beast` | `local_bot` | B | 支援 `support` |

`a2` 的阵营和岗位仍来自 `select_match`。两个人类视角留在出生点。C++ 的 `UNeonRiftResidentPort` 仍不计分，也不吃坐标。这张卡的通过线跑的是 Python 端口。GameMode / GameState / PlayerState 不构造它。

## 这局要发生的事

1. 0.000 秒 `a2` 写下 `ResidentDecision`，`action` 为 `select_match`，`reason` 为 `legal_faction`，`target_id` 为 `A`，`role` 为 `support`。随后才锁队。
2. 0.000 秒 `b2` 的 `BotDecision` 是 `use_ability`，`ability` 为 `dash`，`reason` 为 `assault`，`target_id` 为 `alley_b`，`distance_m` 为 `18.0`。同一毫秒 `AbilityRejected`，原因 `out_of_range`。`b2` 仍在 `spawn_b`。下一笔移动仍是走向 `alley_b` 的 `contest_core`。超距不消耗冷却。
3. 2.250 秒 `a3` 已在 `alley_a`，`b1` 在 `spawn_b`。巷里看不见另一锚点。`BotDecision` 的 `ability` 为 `mark`，`reason` 为 `recon`，`target_id` 为 `b1`。没有 `distance_m`，也没有坐标。`AbilityRejected` 原因 `not_visible`，载荷同样只有 id。
4. 10.500 秒四人同时抢芯。`CorePicked` 给 a2。a3、b2、b3 是 `already_held`。a2 是 `ResidentDecision`，另外三人是 `BotDecision`，`reason` 都是 `contest_core`。
5. 10.500 秒 a2 把芯传给同一坐标的 a3。`reason` 为 `close_range_pass`，`distance_m` 为 `0.0`。同一毫秒 `CorePassed`。
6. 10.500 秒 `a3` 在 `center`，看得见仍在 `spawn_b` 的 `b1`。`AbilityUsed` 的 `ability` 为 `mark`，`target_id` 为 `b1`，`role` 为 `recon`。这是同一个人，上一笔还是 `not_visible`。
7. 10.500 秒 `b3` 与 `b2` 同在 `center`。`BotDecision` 的 `ability` 为 `shield`，`reason` 为 `support`，`target_id` 为 `b2`，`distance_m` 为 `0.0`。`AbilityUsed` 带 `directed_by` `b3`。同一毫秒 `HitIgnored`，原因 `shield`，`target_id` 为 `b2`。没有 `ActorDowned`。
8. 10.500 秒 `a2` 与持芯的 `a3` 同在 `center`。`ResidentDecision` 的 `ability` 为 `shield`，`reason` 为 `support`，`target_id` 为 `a3`，`controller` 为 `digital_resident`。`AbilityUsed` 的 `directed_by` 是 `a2`。同一毫秒 `HitIgnored` 挡住打在 `a3` 身上的下一发。护盾先于命中。两人同阵营。
9. 桥在 12.000 秒接通。预警从 8.000 秒开始，仍是 4 秒。预警不加分。
10. 21.000 秒 `b2` 站在 `spawn_b`，下一跳是 `terminal_b`，正好 12 米。`BotDecision` 的 `distance_m` 为 `12.0`，`reason` 为 `assault`。`AbilityUsed` 的 `from` 是 `spawn_b`，`dest` 是 `terminal_b`，`range_m` 是 12，`ready_ms` 是 29000。没有这段路的 `MoveCompleted`。同一毫秒再跳一次，`AbilityRejected` 原因 `cooldown`，`ready_ms` 仍是 29000。人留在 `terminal_b`。
11. 26.500 秒 a3 在 `terminal_b` 开始读条。`BotDecision` 的 `reason` 为 `score_path`。b2 的 `BotDecision` 是 `interrupt_channel`，`reason` 为 `contest_channel`。27.500 秒 `ScoreChannelInterrupted`，原因 `hit`，`elapsed_ms` 为 1000。这一毫秒没有 `PointScored`。护盾已经在 10.500 秒用掉，所以这一发不被护盾吃掉。
12. 30.500 秒 `PointScored` 使比分变成 A=1 B=0。芯回 `center`。a2 再次 `CorePicked`，b3 `already_held`。
13. 46.500 秒 `PointScored` 使比分变成 A=2 B=0，同一毫秒 `CoreReturnedToCenter` 与 `MatchSettled`。`kind` 为 `points`，胜者 A。没有 `OvertimeStarted`，也没有 `MatchClockExpired`。两个视角仍在出生点。

`hit` 仍是服务器命令。打断那一发 `down` 为 false。护盾的证明命中也是服务器发的，`down` 为 false。

## 上机以后

UE 仍挂。装上本机引擎之后才做这些，做不到就停，把安装路径回给 PM-钢潮岛：

1. `--check` 先通过。不过就不要上机。`m1-bot` 和 `m2-resident` 的 `--check` 也要仍是 0。
2. 打开 `NeonRift.uproject`。`EngineAssociation` 仍是 `5.4` 占位。不要改。
3. 不要交回 `.umap` / `.uasset`。
4. PIE 两个独立输入的客户端。不要把三个 `local_bot` 写成数字居民。不要在 PlayerState 里构造端口来充数，也不要在 PlayerState 里加分。
5. 薄策略不是生产 Resident。不要给它墙后坐标。侦察看不见时，日志里不要出现坐标。
6. `reason` 对得上岗位。三种 `AbilityUsed` 都要从服务器日志里抄到。
7. 日志按 `docs/rules/DUAL_END_EVENT_LOG.md` 落三份。事件名和 JSON 对得上即可，毫秒可以和样例不同。
8. 双持、打断那一次记了分、超距突进却挪了人、护盾挡住了另一队、或先到 2 分却进入加时：三份日志原样退回。不要改胜负条件。
