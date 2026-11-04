# NR-M2-fail

给游戏组-虚幻引擎操作。这张卡把三条失败路径收进一条无头 `--check`：两端同时抢芯只有一人持有，读条被击中不计分，超时结算不重新打开三选一岗位。

**这是和 `m2-pack` 并行的刀口。它不进 `m2-pack` 的步骤表。** `wired_into_m2_pack` 为 `false`。`sim/steel_tide/nr_m2_pack.py` 的 `STEPS` 没有 `m2-fail`。`docs/evidence/nr-m2-pack/` 不改。开发包的 `unittest` 仍会跑 `sim/tests/test_nr_m2_fail.py`。单独的 `--check` 才对照这三份样例。

**不新造计分，也不新造事件名。** 胜负仍只在 `SteelTideMatch`。`EVENT_NAMES` 不增加。`RoleRejected` 在大厅关闭时仍只有 `combatant_id` 和 `reason=locked`，不把岗位名写成新字段。`EngineAssociation` 仍是 `5.4` 占位。

**UE 仍挂。** 本环境没有装 UE，没有 PIE，也没有实机录像。不要改 `EngineAssociation`，不要交 `.umap` / `.uasset`。

**验证动作：** 跑下面的 `--check`。它打一局两人：`client-a` / a1 与 `client-b` / b1 同时站在芯上拾取；a1 在对方端子读条，未满 3 秒被服务器击倒；比分停在 0 比 0，常规时间结束进入加时，加时结束 `kind=draw`。加时开始和结算之后，两端各再请求一次 `assault`、`support`、`recon`，全部 `RoleRejected`。结算后再改阵营，也是 `FactionRejected`。岗位和阵营保持开局锁定的那一套。

**通过（仓内，本 PR HEAD）：** `PYTHONPATH=sim python3 -m steel_tide m2-fail --check` 退出码为 0，并且输出里有 `wired_into_m2_pack=false`。这不是实机通过。

**通过（上机）：** 仍做不到。UE 仍挂。装上本机引擎之前，不要用关卡蓝图写第二套计分来换一张「通过」。

## 输入

- 与 NR-02 同一套拾取、读条和结算函数。不改 `config/steel_tide_greybox.json`
- 样例只在内存里把 `match_seconds` 缩到 12、`overtime_seconds` 缩到 5，好让平局落在短日志里。磁盘上的提案仍是 360 秒和 60 秒。读条仍是 `score_channel_seconds`（3）。倒地仍是 `down_seconds`（5）
- 岗位菜单仍是配置里的三个：`assault`、`support`、`recon`
- 事件名：`Source/NeonRift/Public/NeonRiftEventNames.h`，与 `sim/steel_tide/events.py` 同一集合
- 双端格式：`docs/rules/DUAL_END_EVENT_LOG.md`。本卡 schema 是 `nr-m2-fail-dual-end-v1`。表头多 `identities`、`fail_paths`、`role_menu`、`wired_into_m2_pack`
- 命令：

```bash
PYTHONPATH=sim python3 -m steel_tide m2-fail
PYTHONPATH=sim python3 -m steel_tide m2-fail --check
```

- 样例：`docs/evidence/nr-m2-fail/server.log`、`docs/evidence/nr-m2-fail/client-a.log`、`docs/evidence/nr-m2-fail/client-b.log`

`place_for_test` 只表示「人已经站在体积里」。它不是事件。上机自己走到体积里，毫秒不必和样例相同。

## 名单

| id | 视角 | 身体 `body` | 操控者 `controller` | 阵营 `faction` | 岗位 |
| --- | --- | --- | --- | --- | --- |
| a1 | `client-a` | `humanoid_robot` | `human` | A | 突进 `assault` |
| b1 | `client-b` | `humanoid_robot` | `human` | B | 支援 `support` |

没有 `local_bot`，也没有 `digital_resident`。同型人形可以分属两边。身体、本局阵营、操控者仍是三个字段。

## 这局要发生的事

1. 开局锁定。`MatchStarted` 的 `role_select_open` 是 false。a1 是 `assault`，b1 是 `support`。这一局之后没有第二份 `RolesLocked`，也没有新的 `RoleChosen`。
2. 1.000 秒两端都在 `center`。`client-b` 的拾取先入队，`client-a` 后入队，时间戳相同。批次仍按 `client_id` 排序。只有一条 `CorePicked`：a1、`client-a`、`center`。同一毫秒一条 `CorePickRejected`：b1、`client-b`、原因 `already_held`。b1 空手。全程只有这一次拾取。
3. a1 持芯站到对方端子 `terminal_b`。2.000 秒 `ScoreChannelStarted`，`ends_ms` 为 5000。4.000 秒服务器 `hit` 并且倒地。同一毫秒的顺序是 `ScoreChannelInterrupted`（原因 `hit`，`elapsed_ms` 2000，短于 3 秒）、`CoreDropped`（原因 `downed`，芯留在 `terminal_b`）、`ActorDowned`。没有 `PointScored`。
4. 9.000 秒 a1 `ActorRespawned` 回 `spawn_a`。芯仍在 `terminal_b` 的地上，没有人再捡，没有 `CoreReturnedToCenter`，也没有 `CoreReset`。比分保持 A=0 B=0。
5. 12.000 秒 `MatchClockExpired`，`role_select_open` 为 false，比分 0 比 0，于是 `OvertimeStarted`，`role_select_open` 仍为 false。紧接着 a1、b1 各请求 `assault`、`support`、`recon`。六条都是 `RoleRejected`，原因 `locked`。岗位不变。
6. 17.000 秒只发一次 `MatchSettled`。`kind` 为 `draw`，`winner` 为 null，`score` 为 A=0 B=0，`role_select_open` 为 false。结算之后两端再请求那三个岗位，又是六条 `locked`。然后 a1 改选 B、b1 改选 A，两条 `FactionRejected`，原因 `locked`。a1 仍是 A / `assault`，b1 仍是 B / `support`。`lobby_open` 仍是 false。

镜像持有者是 `-`，镜像比分是 `A=0 B=0`。三端事件正文逐字相同。

## 上机以后

UE 仍挂。装上本机引擎之后才做这些，做不到就停，把安装路径回给 PM-钢潮岛：

1. `--check` 先通过，并且输出 `wired_into_m2_pack=false`。不过就不要上机。
2. 打开 `NeonRift.uproject`。`EngineAssociation` 仍是 `5.4` 占位。不要改。
3. 不要交回 `.umap` / `.uasset`。不要 cook，不要打二进制包。
4. PIE 两个独立输入的客户端。同帧各发一次拾取。不要在 PlayerState 里选第二个持有者。
5. 读条未满 3 秒被击中时，这一次没有 `PointScored`。倒地先打断，再掉芯。
6. 0 比 0 走到时钟结束时，不要重新弹出三选一。`MatchSettled` 的 `role_select_open` 保持 false。
7. 日志按 `docs/rules/DUAL_END_EVENT_LOG.md` 落三份。事件名和 JSON 对得上即可，毫秒可以和样例不同。
8. 双持、打断那一次记了分、或结算之后又能选岗位：三份日志原样退回。不要改胜负条件。
