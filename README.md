# 霓虹断层岛｜Neon Rift

OpenAstra 的独立对战岛。可玩成品只用 **Unreal Engine 5**。仓库根上的 `NeonRift.uproject` 是可打开的骨架，`EngineAssociation` 写着 `5.4`，这是占位。真实小版本由 **PM-钢潮岛** 按本机已安装的引擎锁定，不是 PM-Astra。

雨夜海港、湿地反光、工业机械轮廓沿用概念页。阵营按本局选择，不按脸认敌我。`04` 里的人数、时长、比分和桥预警是可调灰盒提案，不是 Robin 已冻结的局规。

## 交接

**游戏组-虚幻引擎操作：** 工程文件已经在仓库根目录：`NeonRift.uproject`。还缺的只有你机器上的 UE 安装路径，由 PM-钢潮岛按本机安装锁定小版本（文件里的 5.4 是占位）。装好后打开这个工程，按 [docs/HANDOFF.md](docs/HANDOFF.md) 和 [docs/NR-01.md](docs/NR-01.md) 只做钢潮港灰盒。坐标在 [Content/Greybox/NR01_SteelTide.layout.json](Content/Greybox/NR01_SteelTide.layout.json)。胜负以 `sim/steel_tide` 的事件为准，不要在关卡蓝图里另写一套计分。

UE operator: open `NeonRift.uproject`. The only missing piece is the local UE install path. PM-钢潮岛 locks the real minor from that install. Then do NR-01. Do not score the match from the level blueprint.

## 里程碑

来自开工包 `01_CODEX_主创施工`。M0 的工程骨架已经在仓里。灰盒关卡要等本机 UE 打开后再做，仓里没有 `.umap`。

| 里程碑 | 完成线 |
| --- | --- |
| M0 | 同一个 UE 工程能启动，两端能进局并选择阵营，先看见港口灰盒。 |
| M1 | 两个实际客户端加 4 个本地机器人打完一局。双方可以同时出现同型人形机器人，结果一致。掉芯、复活、打断得到验证。 |
| M2 | 补上原画方向的美术、灯光、声音、桥的变化和数字居民策略，打出一个别人能运行的开发包。 |

M0 的第一张上机卡是 [docs/NR-01.md](docs/NR-01.md)。M1 的规则复现是 [docs/NR-02.md](docs/NR-02.md)。可读性是 [docs/NR-03.md](docs/NR-03.md)。M1 首切片（两个视角、四个本地 bot、复活、加时、三岗位）是 [docs/NR-M1-prep.md](docs/NR-M1-prep.md)。传球、持芯突进、读条打断和常规先到 2 分是 [docs/NR-M1-pass.md](docs/NR-M1-pass.md)。四个本地 bot 自己走完一局是 [docs/NR-M1-bot.md](docs/NR-M1-bot.md)。一个薄策略数字居民和三个本地 bot 走完同一局是 [docs/NR-M2-resident.md](docs/NR-M2-resident.md)。岗位能力是 [docs/NR-M2-roles.md](docs/NR-M2-roles.md)。桥接通和断开改路线图是 [docs/NR-M2-bridge.md](docs/NR-M2-bridge.md)。事件侧音效契约是 [docs/NR-M2-audio.md](docs/NR-M2-audio.md)：队标音口、4 秒桥预警和芯链各有可审计的 `AudioCue`，没有声音文件。别人能跑的仓内验收是 [docs/NR-M2-pack.md](docs/NR-M2-pack.md)：无头 Python 开发包，不是 UE 包。实机仍等本机 UE。

事件侧灯光契约是 [docs/NR-M2-light.md](docs/NR-M2-light.md)。A 左肩、B 右肩，日港和夜港强度写在配置里，桥灯带跟 NR-03 同一毫秒。仓内命令是 `PYTHONPATH=sim python3 -m steel_tide m2-light --check`。它不进 `m2-pack` 的步骤表，没有贴图，也没有 `.uasset`。

## 阵营

本局选择，进局后锁定。未选择不会被偷偷分队。

| 身体 | 本局可选 |
| --- | --- |
| 人类、天人 | 只可选 A |
| 机器人（人形除外）、兽 | 只可选 B |
| 人形机器人 | A 或 B，两边可以同时有同一套身体 |

身体类型、本局阵营、操控者（人类 / 数字居民 / 本地机器人）分开存。兽是有机兽，四足机不能代替兽。队标用肩章形状、肩灯位置和音效；颜色只是辅助。A 为开口人字、左肩灯；B 为闭合环、右肩灯。

## 首图

先做钢潮港（钢潮港：倒悬潮汐）这一片：高架近但要过桥，机修巷更远、有掩体、桥断开时也能走。信号核心只做远景。断层街区和自动化工厂先留接口，不铺六张空图。

权威可调参数在 [config/steel_tide_greybox.json](config/steel_tide_greybox.json)。Headless 规则在 `sim/steel_tide`：相位芯的拾取、传递、掉落，端子 3 秒读条与受击/离区打断，两条路线，双客户端脚本和 bot 对 bot。

克隆后在仓库根目录设 `PYTHONPATH=sim`，一条验收是 `python3 -m steel_tide m2-pack --check`。规格在 [docs/NR-M2-pack.md](docs/NR-M2-pack.md)。这是无头 Python 开发包，不是 UE 包。

```bash
PYTHONPATH=sim python3 -m steel_tide m2-pack --check
PYTHONPATH=sim python3 -m unittest discover -s sim/tests -v
PYTHONPATH=sim python3 -m steel_tide repro
PYTHONPATH=sim python3 -m steel_tide nr02 --check
PYTHONPATH=sim python3 -m steel_tide nr03 --check
PYTHONPATH=sim python3 -m steel_tide m1 --check
PYTHONPATH=sim python3 -m steel_tide m1-pass --check
PYTHONPATH=sim python3 -m steel_tide m1-bot --check
PYTHONPATH=sim python3 -m steel_tide m2-resident --check
PYTHONPATH=sim python3 -m steel_tide m2-roles --check
PYTHONPATH=sim python3 -m steel_tide m2-bridge --check
PYTHONPATH=sim python3 -m steel_tide
```

第一条把后面的 `repro`、各张 `--check` 和 `unittest` 串起来，全部退出码为 0 才通过。记录在 `docs/evidence/nr-m2-pack/`。`repro` 打印四条已通过的复现：同帧抢芯只有一人持有、打断不计分、坠海超时芯回中场、超时结算不重新三选一岗位。`nr02` 跑 3v3（两个客户端视角 + 四个本地 bot）并对照 `docs/evidence/nr02/` 的双端日志。`m1` 跑 NR-M1 首切片并对照 `docs/evidence/nr-m1/`。`m1-pass` 跑近距传球、持芯突进、两种读条打断和常规先到 2 分，并对照 `docs/evidence/nr-m1-pass/`。`m1-bot` 让四个 `local_bot` 自己走完一局，并对照 `docs/evidence/nr-m1-bot/`。`m2-resident` 让一个 `digital_resident` 用 `select_match` 和 `decide` 走完同一局路径，并对照 `docs/evidence/nr-m2-resident/`。这仍不是生产数字居民。`m2-roles` 对照 `docs/evidence/nr-m2-roles/`。`m2-bridge` 对照 `docs/evidence/nr-m2-bridge/`：桥接通后跨度可走，断开后跨度离开路线图，机修巷仍可得分。`m2-audio` 不在开发包步骤里。队标音、4 秒桥预警和芯链的音效契约是 `PYTHONPATH=sim python3 -m steel_tide m2-audio --check`，样例在 `docs/evidence/nr-m2-audio/`。规格见 [docs/NR-M2-audio.md](docs/NR-M2-audio.md)。它不改计分，也不把 `AudioCue` 写进双端事件表。最后一条命令是两个本地 bot 的短切片，不在开发包里。UE 侧如何接同一批事件见 [docs/rules/UE_EVENT_WIRING.md](docs/rules/UE_EVENT_WIRING.md)。双端日志格式见 [docs/rules/DUAL_END_EVENT_LOG.md](docs/rules/DUAL_END_EVENT_LOG.md)。

## 资料

- 概念页（与本包对齐）：https://app.notion.com/p/3ff0f164d1a2817c9069cfb02c1bfaa7
- 游戏组工作流冻结页（创世岛原流程）：https://app.notion.com/p/40d0f164d1a2815ea084c2e10c05ebe7
- 开工包原文：[docs/kickoff/](docs/kickoff/)
  - [00_先读.txt](docs/kickoff/00_先读.txt)
  - [01_CODEX_主创施工.txt](docs/kickoff/01_CODEX_主创施工.txt)
  - [02_UE_上机操作.txt](docs/kickoff/02_UE_上机操作.txt)
  - [03_霓虹断层岛工作流.svg](docs/kickoff/03_霓虹断层岛工作流.svg)
  - [04_首局玩法与交接.txt](docs/kickoff/04_首局玩法与交接.txt)
  - [refs/01_Neon_Bay.png](docs/kickoff/refs/01_Neon_Bay.png) 是 2026-10-20 环境参考，不是新的阵营表，也不是实机截图
  - [refs/02_Genesis_Workflow.png](docs/kickoff/refs/02_Genesis_Workflow.png) 是创世岛工作流原图，本岛不替换它
- 待命用的色板和肩章 id：[docs/art/PALETTE_AND_IDS.md](docs/art/PALETTE_AND_IDS.md)。这不是新的里程碑。

冻结页里的创世岛主线用 Godot，工序名字仍写着 PM-Astra。本岛的 UE 工程路径和引擎小版本由 PM-钢潮岛锁定。进引擎的一步是 UE5，以开工包里的 SVG 为准。创世岛和猎手岛继续各自施工。本仓不引用那两个工程，也不另起第二套引擎。Tripo 仍是点召，这次开工不消耗 Tripo 额度，也不依赖另一台机器上的 Blender 压缩包。

## 谁写什么

| 路径 | 负责人 |
| --- | --- |
| `sim/`、`config/`、`Source/`、`NeonRift.uproject` | Codex：规则、C++、配置、工程骨架 |
| `Content/` 里以后的 `.umap`、`.uasset` | 游戏组-虚幻引擎操作 |

已提交 `NeonRift.uproject` 和 C++ 存根。没有提交 `.umap` 或 `.uasset`。灰盒坐标是文本：[Content/Greybox/NR01_SteelTide.layout.json](Content/Greybox/NR01_SteelTide.layout.json)。见 [docs/HANDOFF.md](docs/HANDOFF.md) 和 [docs/BASELINE.md](docs/BASELINE.md)。
