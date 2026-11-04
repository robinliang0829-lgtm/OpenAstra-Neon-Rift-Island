# NR-M2-hud

给游戏组-虚幻引擎操作。这张卡给 M2 一份权威的事件侧 HUD 契约。模拟在关键对局事件的同一毫秒写下可审计的 `HudCue`。它不画控件，也不代替计分。

**不提交界面资产。** 没有 UMG，没有贴图，没有 `.uasset`。`NeonRiftHudCues.h` 只列 id。仓内验收是日志，不是界面截图。

**不新造计分，也不新造计分事件名。** `HudCue` 不在 `sim/steel_tide/events.py` 的 `EVENT_NAMES` 里，也不写进 `match.events`。双端重放仍只看原来的事件。旁路行的 `rules_effect` 是 `none`，`clock` 是 `source_event`：时间从那条权威事件抄来，不另开一个界面钟。

**颜色只是辅助。** 比分板和选边锁定写出的阵营是肩章形状加肩灯位置。A 是 `open_chevron`、`shoulder_left`。B 是 `closed_ring`、`shoulder_right`。青和琥珀可以跟在载荷里，`color_role` 是 `auxiliary`，`color_is_identity` 是 false。行文字里不写十六进制，也不写辅助色名字。

**UE 仍挂。** 本环境没有装 UE，没有 PIE，也没有实机界面。`EngineAssociation` 仍是 `5.4` 占位。不要改它，不要交 `.umap` / `.uasset`，不要 cook。

**不进 `m2-pack` 的步骤表。** 开发包仍是规则链，样例仍是 `docs/evidence/nr-m2-pack/`。HUD 契约单独验收。`m2-pack` 最后一步的 `unittest` 会跑 `sim/tests/test_nr_m2_hud.py`，所以开发包仍执行这份契约的单元测试；只有 `m2-hud --check` 对照 `docs/evidence/nr-m2-hud/hud.log`。日志表头写着 `wired_into_m2_pack false`。

**验证动作：** 跑下面的 `--check`。它摆两名同一身体的人形（`humanoid_robot`，同一 `face_variant`），锁队之后走出生护盾、端子读条、两次得分和结算，并在开局和结算的同一毫秒拒绝再选岗位和阵营。

**通过（仓内，本 PR HEAD）：** `PYTHONPATH=sim python3 -m steel_tide m2-hud --check` 退出码为 0。这不是实机通过，也不是已经看到的控件。

**通过（上机）：** 仍做不到。UE 仍挂。装上本机引擎之前，不要用关卡蓝图写第二套计分或第二套读条来换一张「通过」。

## 输入

- 与 NR-01 / NR-02 / NR-M1 同一工程、同一份 `config/steel_tide_greybox.json`。不改秒数，不改 `points_to_win`
- 队标：`docs/art/PALETTE_AND_IDS.md`。形状和灯位是队标，颜色不是
- 比分板事件名仍是 `PointScored`、`MatchSettled`
- 读条事件名仍是 `ScoreChannelStarted`、`ScoreChannelInterrupted`
- 护盾事件名仍是 `MatchStarted`、`HitIgnored`（`reason` 为 `spawn_protection`）、`ActorRespawned`
- 锁定事件名仍是 `RoleRejected`（`reason` 为 `locked`）。选边锁定用已有的 `FactionRejected` / `locked`，不新造字段
- 头文件：`Source/NeonRift/Public/NeonRiftHudCues.h`。只放 id，不建控件
- 样例：`docs/evidence/nr-m2-hud/hud.log`
- 覆盖路径：`scoreboard:PointScored+MatchSettled`
- 命令：

```bash
PYTHONPATH=sim python3 -m steel_tide m2-hud
PYTHONPATH=sim python3 -m steel_tide m2-hud --check
```

上机自己走到体积里，毫秒不必和样例相同。三端若要画，画的是同一条权威事件，不要在客户端另判一次得分或另数一次 3 秒读条。

## id

| 族 | 权威事件 | cue id | 行在说什么 |
| --- | --- | --- | --- |
| 比分板 | `PointScored` | `hud.scoreboard` | 这一分的阵营、肩章、肩灯和双方分数 |
| 比分板 | `MatchSettled` | `hud.scoreboard` | `kind`、胜者、双方肩章和分数。与致胜的 `PointScored` 同一毫秒 |
| 端子读条 | `ScoreChannelStarted` | `hud.terminal.read_bar` | 空条。`filled` 为 0，时长是配置里的 `score_channel_seconds` |
| 端子读条 | `ScoreChannelInterrupted` | `hud.terminal.read_bar` | 条清掉。`scored` 为 false。这一毫秒没有 `PointScored` |
| 出生护盾 | `MatchStarted` | `hud.spawn_shield` | 每人一条。护盾升到 `protection_until_ms` |
| 出生护盾 | `HitIgnored` `spawn_protection` | `hud.spawn_shield` | 护盾挡住这一下。不倒地 |
| 出生护盾 | `ActorRespawned` | `hud.spawn_shield` | 护盾按复活载荷重新升起 |
| 岗位锁定 | `RoleRejected` `locked` | `hud.role_lock` | 三选一不再打开。不把岗位名写进这条拒绝 |
| 选边锁定 | `FactionRejected` `locked` | `hud.side_lock` | 人留在已锁的肩章上。颜色不是这一行的队标 |

`HitIgnored` 的其他原因（例如护盾技能）不画出生护盾。`RoleRejected` / `unknown_role` 不画锁定。读条自然走完时不另写一条「打断」；那一毫秒的界面是比分板。

每条的 `asset` 是 `none`，`umg` 是 false，`texture` 是 `none`。

## 这局要发生的事

两个人都是 `humanoid_robot`，操控者 `human`，外形变体都是 `plate-7`。`a1` 阵营 A、岗位突进。`b1` 阵营 B、岗位支援。开局前 `a1` 要过一次不存在的 `scout`，那是 `unknown_role`，没有锁定行。位置用测试摆放放到芯或端子上。这不是第二套步行规则。计时仍是配置里的 3 秒出生保护、3 秒读条、5 秒倒地、先到 2 分。

1. 0.000 秒 `MatchStarted`。`a1` 在 `spawn_a`，`b1` 在 `spawn_b`，护盾都到 3.000 秒。同一毫秒大厅已关：两边各被拒绝 `assault` / `support` / `recon`，再各被拒绝换边。岗位行是 `hud.role_lock`。选边行是 `hud.side_lock`，A 写开口人字和左肩，B 写闭合环和右肩。`RoleRejected` 的载荷仍只有 `combatant_id` 和 `reason`。
2. 1.000 秒服务器打 `a1`，`down` 为 true。人还在出生保护里，所以是 `HitIgnored` / `spawn_protection`，一条护盾挡住的行。没有 `ActorDowned`。
3. 3.500 秒保护已过，服务器打倒 `b1`。8.500 秒 `ActorRespawned` 回 `spawn_b`，护盾再到 11.500 秒。
4. 4.000 秒 `a1` 在 `center` 拾取。4.500 秒在 `terminal_b` 开始读条，读条行是空的，时长 3000 毫秒。5.500 秒服务器 `hit` 且 `down` 为 false，`ScoreChannelInterrupted`，`elapsed_ms` 为 1000。读条行清掉，`scored` 为 false。这一毫秒没有 `PointScored`。人没有倒，芯还在手里。
5. 6.000 秒重新读条。9.000 秒 `PointScored` 使比分变成 A=1 B=0，同一毫秒芯回中场。比分板写 A 的肩章。还没到 2 分，没有 `MatchSettled`，也没有加时。8.500 秒的复活落在这段读条里，复活的是 `b1`，不打断 `a1`。
6. 10.000 秒 `a1` 再拾取。10.500 秒再次读条。11.000 秒服务器再打 `b1`。人还在复活护盾里，命中被忽略，没有第二次倒地。13.500 秒 `PointScored` 使比分变成 A=2 B=0，同一毫秒 `MatchSettled`，`kind` 为 `points`，胜者 A。两条比分板行各跟自己的事件。结算行同时写下两边的肩章。没有 `OvertimeStarted`。
7. 13.500 秒结算之后再要一次三选一和换边。拒绝与 `MatchSettled` 同一毫秒。岗位和阵营都不变。大厅不再打开。持有者为空，芯在 `center`。

## 上机以后

UE 仍挂。装上本机引擎之后才做这些，做不到就停，把安装路径回给 PM-钢潮岛：

1. `--check` 先通过。不过就不要上机。
2. 打开 `NeonRift.uproject`。`EngineAssociation` 仍是 `5.4` 占位。不要改。
3. 不要交回 UMG、贴图、`.uasset` 或 `.umap`。不要 cook。
4. 界面跟权威事件走。阵营用肩章形状和肩灯，不要只靠青和黄。读条的 3 秒仍是 `score_channel_seconds`，不要在关卡蓝图里再写一个倒计时。
5. 打断那一毫秒不画得分。护盾挡住的命中不画倒地。锁队之后的拒绝不重新打开三选一。
