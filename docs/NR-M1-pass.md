# NR-M1-pass

给游戏组-虚幻引擎操作。这张卡把近距传球、持芯不能突进、端子读条的两种打断，以及常规时间先到 2 分，收进 `sim/steel_tide`。两个客户端视角加四个本地 bot，能在无引擎的环境里对完日志。

**UE 仍挂。** 本环境没有装 UE，没有 PIE，也没有实机录像。`EngineAssociation` 仍是 `5.4` 占位。不要改它，不要交 `.umap` / `.uasset`。桥的 4 秒预警已经在 NR-03 落地，这张卡只调用 `schedule_bridge_connect`，不另写一套灯带。

**验证动作：** 跑下面的 `--check`。它打一局 3v3：近距把芯传给同队成功，传得太远被拒绝，传给对方被拒绝；持芯时突进被拒绝，传出之后同一段短位移可以再突进；持芯者倒地先掉芯，地上的芯还能被捡起；读条被击中、以及离开端子，这两次都没有 `PointScored`；只有连续满 3 秒的读条才记 1 分并 `CoreReturnedToCenter`。常规时间先到 2 分，`MatchSettled` 的 `kind` 为 `points`，不进入加时。

**通过（仓内，本 PR HEAD）：** `PYTHONPATH=sim python3 -m steel_tide m1-pass --check` 退出码为 0。这不是实机通过。

**通过（上机）：** 仍做不到。UE 仍挂。装上本机引擎之前，不要用关卡蓝图写第二套计分来换一张「通过」。

## 输入

- 与 NR-01 / NR-02 / NR-03 / NR-M1 同一工程、同一关卡距离、同一份 `config/steel_tide_greybox.json`
- 事件名：`Source/NeonRift/Public/NeonRiftEventNames.h`，与 `sim/steel_tide/events.py` 同一集合。这张卡不新增事件名
- 双端格式：`docs/rules/DUAL_END_EVENT_LOG.md`。本卡 schema 是 `nr-m1-pass-dual-end-v1`，表头多一个 `identities`
- 近距：`pass_range_m`（4）。距离小于或等于这个值才能传。更远是 `out_of_range`
- 突进：`assault` 的 `dash`，`range_m` 12。持芯原因是 `holding_core`，不消耗冷却
- 读条：`score_channel_seconds`（3）。受击原因 `hit`，离开端子原因 `left_terminal`
- 先到：`points_to_win`（2）。常规时间里到达就 `kind=points`
- 桥预警：NR-03 已入库的 4 秒。样例在接通前 4.000 秒 `BridgeWarningStarted`（8.000 秒），12.000 秒 `BridgeWarningCompleted` 与 `BridgeStateChanged` 同时发生
- 命令：

```bash
PYTHONPATH=sim python3 -m steel_tide m1-pass
PYTHONPATH=sim python3 -m steel_tide m1-pass --check
```

- 样例：`docs/evidence/nr-m1-pass/server.log`、`docs/evidence/nr-m1-pass/client-a.log`、`docs/evidence/nr-m1-pass/client-b.log`

`place_for_test` 只表示「人已经站在体积里」。它不是事件。上机自己走到体积里，毫秒不必和样例相同。

## 名单

| id | 视角 | 身体 `body` | 操控者 `controller` | 阵营 `faction` | 岗位 |
| --- | --- | --- | --- | --- | --- |
| a1 | `client-a` | `humanoid_robot` | `human` | A | 突进 `assault` |
| a2 | `bot-a2` | `humanoid_robot` | `local_bot` | A | 支援 `support` |
| a3 | `bot-a3` | `human` | `local_bot` | A | 侦察 `recon` |
| b1 | `client-b` | `humanoid_robot` | `human` | B | 侦察 `recon` |
| b2 | `bot-b2` | `humanoid_robot` | `local_bot` | B | 突进 `assault` |
| b3 | `bot-b3` | `beast` | `local_bot` | B | 支援 `support` |

四个 `local_bot` 不是生产数字居民。身体、本局阵营、操控者仍是三个字段。UE 侧只订阅。GameMode / GameState / PlayerState 不加分，也不选第二个持有者。胜负仍只在 `sim/steel_tide`。

## 这局要发生的事

1. 1.000 秒 a1 在 `center` 拾起芯。
2. 1.500 秒 a1 仍持芯，站在 `terminal_a`，向 `bridgehead_a` 突进。`AbilityRejected`，原因 `holding_core`。人和芯都留在 `terminal_a`。这一次不写冷却。
3. 2.000 秒把芯传给站在同一坐标的 b1。`CorePassRejected`，原因 `wrong_faction`。持有者仍是 a1。
4. 2.400 秒把芯传给 a2，a2 比 `pass_range_m` 更远 1 米。`CorePassRejected`，原因 `out_of_range`。持有者仍是 a1。
5. 2.800 秒 a2 站到同一坐标。`CorePassed`，`from_id` a1，`to_id` a2。
6. 3.200 秒 a1 已不再持芯，同一段 `terminal_a` → `bridgehead_a` 突进成功，`AbilityUsed`。芯留在 a2 手上，不跟着 a1 走。冷却从这一次才开始算。
7. 4.000 秒 a2 被击倒。先 `CoreDropped`（`downed`，芯留在 `terminal_a`），再 `ActorDowned`。这一次没有 `PointScored`。4.500 秒 b2 捡起地上的芯。9.000 秒 a2 `ActorRespawned` 回 `spawn_a`，芯不因此再掉一次。
8. 桥在 12.000 秒接通。预警仍是 NR-03 的 4 秒，警报和灯带一起开始。预警不加分。
9. b2 在己方得分端子 `terminal_a` 读条。14.000 秒受击但没有倒地：`ScoreChannelInterrupted`，原因 `hit`，没有 `PointScored`，芯还在 b2 手上。15.500 秒 `leave_terminal`：`ScoreChannelInterrupted`，原因 `left_terminal`，没有 `PointScored`。
10. 16.000 秒再次读条，连续满 3 秒。19.000 秒 `PointScored` 使比分变成 A=0 B=1，同一毫秒 `CoreReturnedToCenter`。这一分不到 2，比赛不结束。
11. b2 再拾起回到中场的芯，再读满 3 秒。23.000 秒 `PointScored` 使比分变成 A=0 B=2，同一毫秒 `CoreReturnedToCenter` 与 `MatchSettled`。`kind` 为 `points`，胜者 B。没有 `OvertimeStarted`，也没有 `MatchClockExpired`。时刻仍在 360 秒常规时间之内。

`leave_terminal` 是服务器的体积边沿，不是玩家自己报的位移。样例不另写一条移动。

## 上机以后

UE 仍挂。装上本机引擎之后才做这些，做不到就停，把安装路径回给 PM-钢潮岛：

1. `--check` 先通过。不过就不要上机。
2. 打开 `NeonRift.uproject`。`EngineAssociation` 仍是 `5.4` 占位。不要改。
3. 不要交回 `.umap` / `.uasset`。
4. PIE 两个独立输入的客户端。四个本地 bot 不要写成数字居民。
5. 不要在 PlayerState 里加分。持有者和 `kind=points` 都从服务器日志抄。
6. 日志按 `docs/rules/DUAL_END_EVENT_LOG.md` 落三份。事件名和 JSON 对得上即可，毫秒可以和样例不同。
7. 双持、持芯仍能突进、打断那一次记了分、或先到 2 分却进入加时：三份日志原样退回。不要改胜负条件。
