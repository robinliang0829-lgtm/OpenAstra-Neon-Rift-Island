# NR-M1 首切片

给游戏组-虚幻引擎操作。这张卡把 M1 的第一局规则收进 `sim/steel_tide`。两个客户端视角加四个本地 bot，能在无引擎的环境里对完日志。

**UE 仍挂。** 本环境没有装 UE，没有 PIE，也没有实机录像。`EngineAssociation` 仍是 `5.4` 占位。不要改它，不要交 `.umap` / `.uasset`，不要为这张卡花 Tripo。桥的 4 秒预警已经在 NR-03 落地，这张卡只复用 `schedule_bridge_connect`，不另写一套灯带。

**验证动作：** 跑下面的 `--check`。它打一局 3v3：倒地 5 秒后回本方出生点并重新获得出生保护，持芯者倒地掉芯、芯还能被捡起；常规时间 0-0 结束则进入 60 秒加时，第一笔打破平局的得分立即结束；开局选边后局内锁队；身体、阵营、操控者分三个字段；突进短位移、支援定向护盾、侦察只标记看得到的目标。

**通过（仓内，本 PR HEAD）：** `PYTHONPATH=sim python3 -m steel_tide m1 --check` 退出码为 0。这不是实机通过。

**通过（上机）：** 仍做不到。UE 仍挂。装上本机引擎之前，不要用关卡蓝图写第二套计分来换一张「通过」。

## 输入

- 与 NR-01 / NR-02 / NR-03 同一工程、同一关卡距离、同一份 `config/steel_tide_greybox.json`
- 事件名：`Source/NeonRift/Public/NeonRiftEventNames.h`，与 `sim/steel_tide/events.py` 同一集合。这张卡不新增事件名
- 双端格式：`docs/rules/DUAL_END_EVENT_LOG.md`。本卡 schema 是 `nr-m1-dual-end-v1`，多一个表头 `identities`
- 肩章：NR-03 的 `open_chevron` / `closed_ring`。人形机器人开局可以选 A 或 B，两边用同一套身体
- 桥预警：NR-03 已入库的 4 秒。样例在接通前 16.000 秒 `BridgeWarningStarted`，20.000 秒 `BridgeWarningCompleted` 与 `BridgeStateChanged` 同时发生
- 命令：

```bash
PYTHONPATH=sim python3 -m steel_tide m1
PYTHONPATH=sim python3 -m steel_tide m1 --check
```

- 样例：`docs/evidence/nr-m1/server.log`、`docs/evidence/nr-m1/client-a.log`、`docs/evidence/nr-m1/client-b.log`、`docs/evidence/nr-m1/retie.log`

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

四个 `local_bot` 不是生产数字居民。`digital_resident` 仍是第三种操控者，这局里不出现。

身体、本局阵营、操控者是三个字段，不互相推断。人类身体不能选 B，兽不能选 A，人形机器人在锁队前 A、B 都可以。锁队写在 `FactionsLocked.identities`。局内再选会被 `FactionRejected` / `RoleRejected`，原因 `locked`。岗位 id 是 `assault` / `support` / `recon`。卡片上的「侦察 / scout」不是第二个 id，选 `scout` 会被拒绝。

UE 侧只订阅。`ANeonRiftPlayerState` 的 `BodyType`、`MatchFaction`、`ControllerKind` 由 `SetIdentityLabels` 复制这三个标签。`ANeonRiftGameState::MirroredIdentityPayload` 复制 `FactionsLocked` 的原文。GameMode / GameState / PlayerState 不加分，也不选第二个持有者。胜负仍只在 `sim/steel_tide`。

肩章用 NR-03 的形状和灯位：A 开口人字、左肩；B 闭合环、右肩。脸和颜色不认队。

## 这局要发生的事

1. 开局 3 秒出生保护里，打 a1 得到 `HitIgnored` / `spawn_protection`，不倒地。保护先于护盾：保护期内的命中不消耗已经套上的定向护盾。
2. 两边突进各做一次不超过 12 米的短位移（`spawn_*` → 本方端子）。同一帧再突进一次被冷却拒绝。桥跨度 24 米，接通之后再突进到 `center` 被 `out_of_range` 拒绝，人留在桥头。
3. 侦察先标记巷内目标，`not_visible`，载荷里没有坐标。目标走到同一锚点后再标记，`AbilityUsed` 只有 `target_id`。
4. 支援的护盾 `range_m` 为 0，不能隔着锚点放。放到同一坐标的队友身上后，下一发打这个队友被 `HitIgnored` / `shield`，`directed_by` 是支援者。站在旁边的支援自己仍会被打倒。护盾不能套到对方阵营。
5. a1 与 b1 同帧抢芯，只有 a1 拿住。读条中被击倒：先 `CoreDropped`（`downed`，芯留在 `terminal_b`），再 `ActorDowned`，这一次没有 `PointScored`。`down_seconds`（5.0）后 `ActorRespawned` 回 `spawn_a`，`protection_until_ms` 再覆盖 `spawn_protection_seconds`（3.0）。b2 捡起地上的芯。复活后的那一发再次被出生保护挡住，芯不因此掉落。
6. 桥在 20 秒接通。预警仍是 NR-03 的 4 秒，警报和灯带一起开始。预警不加分。
7. 常规 360 秒结束时比分 0-0，`OvertimeStarted`，截止 420 秒，`role_select_open` 为 false。b2 在加时读条，364 秒 `PointScored` 使比分变成 A=0 B=1，同一毫秒 `MatchSettled`，`kind` 为 `score`，胜者 B。不到 2 分，也不等到 420 秒。

`retie.log` 是同一份名单、没有人得分。360 秒进入加时，420 秒仍是 0-0，`kind` 为 `draw`，`winner` 为空。没有第二段加时，锁队保持。

## 加时

灰盒提案仍是 `04_首局玩法与交接`：时间到比得分，同分加时 60 秒，先得分结束，再同分就平局。这里把「再同分」写成模拟可以核对的四条，避免和「先到 2 分」混在一起。

| 时机 | 结算 |
| --- | --- |
| 常规时间结束，一方领先 | `MatchSettled` `kind=score`。不进入加时 |
| 常规时间结束，同分 | `OvertimeStarted`。时长 `overtime_seconds`（60）。不重新选边、不重新选岗位 |
| 加时里一笔 `PointScored` 让一方领先，且还没到 `points_to_win` | 立即 `kind=score`。样例就是这条：0-0 进入，1 分结束 |
| 加时里一笔 `PointScored` 达到 `points_to_win`（提案 2） | 立即 `kind=points` |
| 加时里一笔 `PointScored` 之后两边仍然同分（再同分） | 立即 `kind=draw`。单芯、从平局进入时，+1 一定打破平局，所以这条不会出现在样例正文里。`--check` 另用一笔预先计入的领先分，让下一分把比分打回相同，锁住这个分支 |
| 加时 60 秒走完仍然同分 | `kind=draw`，`winner` 为空。不开启第二段加时 |

击倒只掉芯、只让人倒地。不算人头分。

## 上机以后

UE 仍挂。装上本机引擎之后才做这些，做不到就停，把安装路径回给 PM-钢潮岛：

1. `--check` 先通过。不过就不要上机。
2. 打开 `NeonRift.uproject`。`EngineAssociation` 仍是 `5.4` 占位。不要改。
3. 不要交回 `.umap` / `.uasset`。
4. PIE 两个独立输入的客户端，`SetViewpointClientId` 分别为 `client-a`、`client-b`。四个本地 bot 不要写成数字居民。
5. `SetIdentityLabels` 只填身体、阵营、操控者。不要在 PlayerState 里加分。
6. 日志按 `docs/rules/DUAL_END_EVENT_LOG.md` 落三份。事件名和 JSON 对得上即可，毫秒可以和样例不同。
7. 双持、一次读条两分、或加时打平后又开一段：三份日志原样退回。不要改胜负条件。
