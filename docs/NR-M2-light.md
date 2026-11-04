# NR-M2-light

给游戏组-虚幻引擎操作。这张卡给 M2 一份权威的事件侧灯光契约。模拟在关键对局事件的同一毫秒写下可审计的 `LightCue`。它不打光，也不代替计分。

**不提交贴图，不开 Lumen。** 没有 `.uasset`，没有 `.umap`，没有实机灯光。`NeonRiftLightCues.h` 只列 id。仓内验收是日志，不是画面。

**不新造计分，也不新造计分事件名。** `LightCue` 不在 `sim/steel_tide/events.py` 的 `EVENT_NAMES` 里，也不写进 `match.events`。双端重放仍只看原来的事件。旁路行的 `rules_effect` 是 `none`，`clock` 是 `source_event`：时间从那条权威事件抄来，不另开一个灯光钟。

**肩灯仍是 NR-03。** A 开口人字、灯在左肩；B 闭合环、灯在右肩。形状和灯位是队标。辅助色可以给灯着色（`color_assist`），颜色不是队标。日港和夜港的强度写在 `config/steel_tide_greybox.json` 的 `lighting` 里。同一盏灯要在两档港口亮度下都过 `min_readable_contrast`。

**桥仍是 NR-03。** 4 秒提前量、灯带推进、接通、断开都来自已经入库的 `schedule_bridge_connect` 和 `schedule_bridge_disconnect`。不另写灯带，不另写一套提前量。`BridgeWarningStarted` 是第一盏，`BridgeLightStripAdvanced` 是中间几盏，`BridgeWarningCompleted` 是最后一盏。最后一盏和 `BridgeStateChanged` / `connected` 同一毫秒。断开挂在 `BridgeStateChanged` / `disconnected` 上。

**UE 仍挂。** 本环境没有装 UE，没有 PIE，也没有实机画面。`EngineAssociation` 仍是 `5.4` 占位。不要改它，不要交 `.umap` / `.uasset`，不要 cook。

**不进 `m2-pack` 的步骤表。** 开发包仍是规则链，样例仍是 `docs/evidence/nr-m2-pack/` 里的命令和退出码。灯光是旁路，不新造事件名，不改计分，所以不改那两份样例。写进步骤表会把规则链和可读性契约绑成一次验收，也会和仍开着的音效卡抢同一处步骤。`m2-pack` 最后一步的 `unittest` 会跑 `sim/tests/test_nr_m2_light.py`，所以开发包仍执行这份契约的单元测试；只有 `m2-light --check` 对照 `docs/evidence/nr-m2-light/light.log`。日志表头写着 `wired_into_m2_pack false`。

**验证动作：** 跑下面的 `--check`。它摆三名同一身体的人形（`humanoid_robot`，同一 `face_variant`），锁队后各写一条肩灯，再走一遍出生保护、端子读条、一次得分，以及桥的接通、断开。拒绝不计分，也不点灯。这一局不停在 2 分，只要每个契约 id 至少亮一次。

**通过（仓内，本 PR HEAD）：** `PYTHONPATH=sim python3 -m steel_tide m2-light --check` 退出码为 0。这不是实机通过，也不是已经看到的灯光。

**通过（上机）：** 仍做不到。UE 仍挂。装上本机引擎之前，不要用关卡蓝图写第二套计分或第二套桥预警来换一张「通过」。

## 输入

- 与 NR-01 / NR-02 / NR-03 / NR-M2-bridge 同一工程、同一份 `config/steel_tide_greybox.json`
- 队标：`docs/art/PALETTE_AND_IDS.md`。A `open_chevron`、灯在左肩；B `closed_ring`、灯在右肩
- 强度：`lighting.day_port_intensity`、`lighting.night_port_intensity`，以及肩灯、读条、得分、出生保护、灯带各自的强度。`color_assist` 为 true 时只表示允许辅助色，id 里仍然没有颜色
- 桥事件名仍是 `BridgeWarningStarted`、`BridgeLightStripAdvanced`、`BridgeWarningCompleted`、`BridgeStateChanged`
- 读条、得分、出生保护仍是 `ScoreChannelStarted`、`PointScored`、`MatchStarted` / `HitIgnored` / `ActorRespawned`。这些名字不改
- 头文件：`Source/NeonRift/Public/NeonRiftLightCues.h`。只放 id，不打光
- 样例：`docs/evidence/nr-m2-light/light.log`
- 命令：

```bash
PYTHONPATH=sim python3 -m steel_tide m2-light
PYTHONPATH=sim python3 -m steel_tide m2-light --check
```

上机自己走到体积里，毫秒不必和样例相同。三端若要点灯，跟的是同一条权威事件，不要在客户端另数一次 4 秒，也不要另开一条读条。

## id

| 族 | 权威事件 | cue id |
| --- | --- | --- |
| 肩灯 A | `FactionsLocked` | `light.shoulder.A.open_chevron.shoulder_left` |
| 肩灯 B | `FactionsLocked` | `light.shoulder.B.closed_ring.shoulder_right` |
| 灯带推进 | `BridgeWarningStarted`、`BridgeLightStripAdvanced`、`BridgeWarningCompleted` | `light.bridge.ramp` |
| 桥接通 | `BridgeStateChanged` `connected` | `light.bridge.connect` |
| 桥断开 | `BridgeStateChanged` `disconnected` | `light.bridge.disconnect` |
| 端子读条 | `ScoreChannelStarted` | `light.terminal.read_bar` |
| 得分 | `PointScored` | `light.score` |
| 出生保护 | `MatchStarted`、`HitIgnored`（`spawn_protection`）、`ActorRespawned` | `light.spawn_protection` |

肩灯在锁队那一毫秒按人各写一条。`FactionChosen` 不亮，避免还没锁定又亮一次。`color_role` 是 `auxiliary`，`color_is_identity` 是 false。灰度或色盲模拟只改辅助色，形状和灯位不变，所以 id 不变。日港对比是 `shoulder_intensity / day_port_intensity`，夜港对比是 `shoulder_intensity / night_port_intensity`。两档都要 ≥ `min_readable_contrast`。

读条灯只挂在成功的 `ScoreChannelStarted`。`duration_ms` 是这条事件自己的 `ends_ms` 减时间戳，等于配置里的 `score_channel_seconds`。模块不自己计 3 秒。`ScoreChannelRejected` 不亮。`CoreReturnedToCenter` 不再叠一条得分灯；得分灯只跟 `PointScored`。

出生保护在 `MatchStarted` 按人记下已经由 `_place_at_spawn` 写好的 `protection_until_ms`。保护期内的 `HitIgnored` / `spawn_protection` 再写一条，沿用同一个截止毫秒，不把窗口再加一次。`ActorRespawned` 的截止毫秒从复活事件抄来。护盾造成的 `HitIgnored` 不是出生保护。

桥的每一盏都跟它的权威事件同一毫秒。索引 0 在预警开始，1、2、3 在 `BridgeLightStripAdvanced`，最后一盏在 `BridgeWarningCompleted`。接通灯和最后一盏同一毫秒，`paired_event` 指着 `BridgeWarningCompleted`。提前量是配置里的 4000 毫秒，不是灯光模块自己数的。

每条的 `asset` 和 `texture` 都是 `none`。`day_port_intensity` 和 `night_port_intensity` 抄自配置。

## 这局要发生的事

三个人都是 `humanoid_robot`，操控者 `human`，外形变体都是 `plate-7`。`a1` 突进，`a2` 支援，`b1` 突进。`a1` / `a2` 阵营 A，`b1` 阵营 B。位置用测试摆放放到芯或端子上，好让读条和得分各有来源事件。这不是第二套步行规则。计时仍是配置里的 3 秒读条、3 秒出生保护、4 秒桥预警。

1. 0.000 秒 `FactionsLocked`。三条肩灯。`a1` 和 `a2` 是左肩开口人字。`b1` 是右肩闭合环。身体相同，id 不同。同一毫秒 `MatchStarted`，三人各一条出生保护，`protection_until_ms` 为 3000。
2. 0.500 秒服务器 `hit`，`down` 为 true。人在保护内，所以是 `HitIgnored`，原因 `spawn_protection`。一条出生保护灯，截止毫秒仍是 3000。`a1` 没有倒。这一毫秒没有 `PointScored`。
3. 3.200 秒 `a1` 站在 `terminal_b` 但没有芯，`ScoreChannelRejected`，原因 `not_holder`。没有读条灯，也没有得分。
4. 3.500 秒 `a1` 在 `center` 拾取。4.000 秒在 `terminal_b` 开始读条。一条 `light.terminal.read_bar`，`duration_ms` 为 3000，`ends_ms` 为 7000。强度是配置里的 `read_bar_intensity`。
5. 7.000 秒 `PointScored` 使比分变成 A=1 B=0，同一毫秒 `CoreReturnedToCenter`。只有一条 `light.score`，抄的是 `PointScored` 的比分。没有到 2 分，比赛不停。
6. 12.000 秒 `BridgeWarningStarted`，`lead_ms` 为 4000，`alarm_with` 为 `span_light_strip`。灯带索引 0。13.000、14.000、15.000 秒是索引 1、2、3。16.000 秒 `BridgeWarningCompleted` 是索引 4，与 `BridgeStateChanged` `connected` 同一毫秒。五条 `light.bridge.ramp`，一条 `light.bridge.connect`。这一段没有 `PointScored`。
7. 18.000 秒 `BridgeStateChanged` `disconnected`，一条 `light.bridge.disconnect`。跨度上没有人，所以没有 `BridgeOccupantNudged`。断开不加分。持有者为空。比分仍是 A=1 B=0。

## 和 m2-pack 的关系

不接入 `m2-pack` 的步骤表。原因有三条：

1. 开发包验收的是规则链。灯光不改持有者、比分、打断或桥的提前量。
2. 步骤表一改，`docs/evidence/nr-m2-pack/` 的命令和退出码就要重写。这张卡不改那些样例。
3. 单元测试已经挂在开发包最后一步的 `unittest` 上。单独的 `--check` 才对照灯光样例。

配置里的 `lighting` 是给这条契约读的。`m2-pack` 不改写 `config/steel_tide_greybox.json`。

## 上机以后

UE 仍挂。装上本机引擎之后才做这些，做不到就停，把安装路径回给 PM-钢潮岛：

1. `--check` 先通过。不过就不要上机。
2. 打开 `NeonRift.uproject`。`EngineAssociation` 仍是 `5.4` 占位。不要改。
3. 不要交回贴图、`.uasset` 或 `.umap`。不要开 Lumen 当验收，不要 cook。
4. 肩灯用灯位和肩章形状，不要只靠青和黄。日港和夜港的强度用配置，不要在关卡里另填一套。
5. 桥的 4 秒仍是已经入库的灯带。不要在关卡蓝图里再写一个倒计时。读条灯跟 `ScoreChannelStarted`，得分灯跟 `PointScored`。打断和拒绝不亮得分灯。
