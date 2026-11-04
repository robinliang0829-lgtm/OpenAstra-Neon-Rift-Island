# NR-M2-audio

给游戏组-虚幻引擎操作。这张卡给 M2 一份权威的事件侧音效契约。模拟在关键对局事件的同一毫秒写下可审计的 `AudioCue`。它不播放，也不代替计分。

**不提交声音文件。** 没有 wav，没有 MetaSound，没有 `.uasset`。`NeonRiftAudioCues.h` 只列 id。仓内验收是日志，不是录音。

**不新造计分，也不新造计分事件名。** `AudioCue` 不在 `sim/steel_tide/events.py` 的 `EVENT_NAMES` 里，也不写进 `match.events`。双端重放仍只看原来的事件。旁路行的 `rules_effect` 是 `none`，`clock` 是 `source_event`：时间从那条权威事件抄来，不另开一个音效钟。

**桥仍是 NR-03。** 4 秒提前量、`BridgeWarningStarted`、`BridgeLightStripAdvanced`、`BridgeWarningCompleted` 都来自已经入库的 `schedule_bridge_connect`。断开调用已经入库的 `schedule_bridge_disconnect`。不另写灯带，不另写一套提前量。`BridgeWarningCompleted` 与接通同一毫秒，接通音挂在 `BridgeStateChanged` / `connected` 上，不给完成事件再叠一条。

**UE 仍挂。** 本环境没有装 UE，没有 PIE，也没有实机录音。`EngineAssociation` 仍是 `5.4` 占位。不要改它，不要交 `.umap` / `.uasset`，不要 cook。

**不进 `m2-pack` 的步骤表。** 开发包仍是规则链，样例仍是 `docs/evidence/nr-m2-pack/`。音效契约单独验收。`m2-pack` 最后一步的 `unittest` 会跑 `sim/tests/test_nr_m2_audio.py`，所以开发包仍执行这份契约的单元测试；只有 `m2-audio --check` 对照 `docs/evidence/nr-m2-audio/audio.log`。日志表头写着 `wired_into_m2_pack false`。

**验证动作：** 跑下面的 `--check`。它摆三名同一身体的人形（`humanoid_robot`，同一 `face_variant`），锁队后各写一条队标音，再走一遍芯链和一次桥的接通、断开。落点和拒绝不计分。这一局不停在 2 分，只要每个契约 id 至少响一次。

**通过（仓内，本 PR HEAD）：** `PYTHONPATH=sim python3 -m steel_tide m2-audio --check` 退出码为 0。这不是实机通过，也不是已经听到的声音。

**通过（上机）：** 仍做不到。UE 仍挂。装上本机引擎之前，不要用关卡蓝图写第二套计分或第二套桥预警来换一张「通过」。

## 输入

- 与 NR-01 / NR-02 / NR-03 / NR-M2-bridge 同一工程、同一份 `config/steel_tide_greybox.json`
- 队标：`docs/art/PALETTE_AND_IDS.md`。A `open_chevron`、灯在左肩；B `closed_ring`、灯在右肩。形状和灯位是队标，颜色不是
- 音口就是肩灯那一侧。id 里没有辅助色，也没有十六进制
- 桥事件名仍是 `BridgeWarningStarted`、`BridgeLightStripAdvanced`、`BridgeWarningCompleted`、`BridgeStateChanged`
- 芯链事件名仍是 `CorePicked`、`CorePassed`、`CoreDropped`、`ScoreChannelStarted`、`ScoreChannelInterrupted`、`PointScored`、`CoreReturnedToCenter`、`CoreReset`
- 头文件：`Source/NeonRift/Public/NeonRiftAudioCues.h`。只放 id，不播放
- 样例：`docs/evidence/nr-m2-audio/audio.log`
- 命令：

```bash
PYTHONPATH=sim python3 -m steel_tide m2-audio
PYTHONPATH=sim python3 -m steel_tide m2-audio --check
```

上机自己走到体积里，毫秒不必和样例相同。三端若要听，听的是同一条权威事件，不要在客户端另判一次拾取或另数一次 4 秒。

## id

| 族 | 权威事件 | cue id |
| --- | --- | --- |
| 队标 A | `FactionsLocked` | `sfx.team.A.open_chevron.mouth.shoulder_left` |
| 队标 B | `FactionsLocked` | `sfx.team.B.closed_ring.mouth.shoulder_right` |
| 桥预警 | `BridgeWarningStarted` | `sfx.bridge.warn` |
| 灯带进度 | `BridgeLightStripAdvanced` | `sfx.bridge.light_strip` |
| 桥接通 | `BridgeStateChanged` `connected` | `sfx.bridge.connect` |
| 桥断开 | `BridgeStateChanged` `disconnected` | `sfx.bridge.disconnect` |
| 拾取 | `CorePicked` | `sfx.core.pickup` |
| 传球 | `CorePassed` | `sfx.core.pass` |
| 掉落 | `CoreDropped` | `sfx.core.drop` |
| 读条开始 | `ScoreChannelStarted` | `sfx.core.channel_start` |
| 打断 | `ScoreChannelInterrupted` | `sfx.core.interrupt` |
| 得分 | `PointScored` | `sfx.core.score` |
| 回中 | `CoreReturnedToCenter` | `sfx.core.return_to_center` |
| 复位 | `CoreReset` | `sfx.core.reset` |

队标在锁队那一毫秒按人各写一条。`FactionChosen` 不响，避免还没锁定又响一次。`color_role` 是 `auxiliary`，`color_is_identity` 是 false。灰度或色盲模拟只改辅助色，形状和音口不变，所以 id 不变。

拒绝不响。同帧第二人 `CorePickRejected` / `already_held` 没有拾取音。`BridgeWarningCompleted` 没有自己的一条；接通音和它同一毫秒，`paired_event` 指着它。

每条的 `asset` 是 `none`。

## 这局要发生的事

三个人都是 `humanoid_robot`，操控者 `human`，外形变体都是 `plate-7`。`a1` 突进，`a2` 支援，`b1` 突进。`a1` / `a2` 阵营 A，`b1` 阵营 B。位置用测试摆放放到芯或端子上，好让每一条音都有来源事件。这不是第二套步行规则。计时仍是配置里的 3 秒读条、4 秒桥预警、8 秒复位。

1. 0.000 秒 `FactionsLocked`。三条队标音。`a1` 和 `a2` 是左肩开口人字。`b1` 是右肩闭合环。身体相同，id 不同。
2. 0.500 秒 `a1` 与 `a2` 同帧抢芯。一条 `CorePicked` 给 `a1`，一条 `sfx.core.pickup`。`a2` 是 `CorePickRejected`，原因 `already_held`，没有音。
3. 1.000 秒 `CorePassed`，`a1` 传给 `a2`，一条 `sfx.core.pass`。
4. 1.500 秒 `a2` 主动 `CoreDropped`，一条 `sfx.core.drop`，`reason` 为 `voluntary`。
5. 3.500 秒 `a1` 再拾取。4.000 秒在 `terminal_b` 开始读条。5.000 秒服务器 `hit` 且 `down` 为 false，`ScoreChannelInterrupted`，`elapsed_ms` 为 1000。这一毫秒没有 `PointScored`，也没有得分音。人没有倒。
6. 5.500 秒重新读条。8.500 秒 `PointScored` 使比分变成 A=1 B=0，同一毫秒 `CoreReturnedToCenter`。两条音各跟自己的事件。没有到 2 分，比赛不停。
7. 12.000 秒 `BridgeWarningStarted`，`lead_ms` 为 4000，`alarm_with` 为 `span_light_strip`，`readable_without_reflection` 为 true。一条 `sfx.bridge.warn`。灯带进度在 13.000、14.000、15.000 秒，索引 1、2、3，各一条 `sfx.bridge.light_strip`。这一段没有 `PointScored`。
8. 16.000 秒 `BridgeWarningCompleted` 与 `BridgeStateChanged` `connected` 同一毫秒。只有接通音。`paired_event` 是 `BridgeWarningCompleted`。提前量是配置里的 4000 毫秒，不是音效模块自己数的。
9. 18.000 秒 `BridgeStateChanged` `disconnected`，一条 `sfx.bridge.disconnect`。跨度上没有人，所以没有 `BridgeOccupantNudged`。断开不加分。
10. 19.000 秒 `a1` 在 `center` 拾取。19.500 秒服务器把芯标成坠海，先 `CoreDropped`（`reason` 为 `overboard`），再 `CoreMarkedUnpickable`。掉落有音，标记没有音。27.500 秒 `CoreReset`，`anchor` 为 `center`。这一毫秒没有 `PointScored`。持有者为空。比分仍是 A=1 B=0。

## 上机以后

UE 仍挂。装上本机引擎之后才做这些，做不到就停，把安装路径回给 PM-钢潮岛：

1. `--check` 先通过。不过就不要上机。
2. 打开 `NeonRift.uproject`。`EngineAssociation` 仍是 `5.4` 占位。不要改。
3. 不要交回 wav、MetaSound、`.uasset` 或 `.umap`。不要 cook。
4. 播放跟权威事件走。队标用音口和肩章形状，不要只靠青和黄。桥的 4 秒仍是灯带和警报，不要在关卡蓝图里再写一个倒计时。
5. 打断那一毫秒不播得分音。复位不播得分音。回中和复位是两条 id。
