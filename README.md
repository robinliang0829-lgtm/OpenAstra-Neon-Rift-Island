# 霓虹断层岛｜Neon Rift

OpenAstra 的独立对战岛。可玩成品只用 **Unreal Engine 5**。本仓是钢潮港首图的规则、配置和上机交接，还不是已经能打开的 UE 工程。

雨夜海港、湿地反光、工业机械轮廓沿用概念页。阵营按本局选择，不按脸认敌我。`04` 里的人数、时长、比分和桥预警是可调灰盒提案，不是 Robin 已冻结的局规。

## 交接

**游戏组-虚幻引擎操作：** 本仓还没有 `.uproject`，UE5 小版本以你的机器和 PM-Astra 给出的工程路径为准。拿到工程后按 [docs/NR-01.md](docs/NR-01.md) 只做钢潮港灰盒（出生点、双端子、中央相位芯、高架和机修巷），把俯视图和两侧走到中场的时间交回。胜负以 `sim/steel_tide` 的事件为准，不要在关卡蓝图里另写一套计分。

UE operator: there is no `.uproject` in this repo. After PM-Astra gives you a project path and UE5 minor, start with NR-01 only and send back the Steel Tide greybox measurements. Do not score the match from the level blueprint.

## 里程碑

来自开工包 `01_CODEX_主创施工`，本 PR 还没有进入 M0。

| 里程碑 | 完成线 |
| --- | --- |
| M0 | 同一个 UE 工程能启动，两端能进局并选择阵营，先看见港口灰盒。 |
| M1 | 两个实际客户端加 4 个本地机器人打完一局。双方可以同时出现同型人形机器人，结果一致。掉芯、复活、打断得到验证。 |
| M2 | 补上原画方向的美术、灯光、声音、桥的变化和数字居民策略，打出一个别人能运行的开发包。 |

M0 的第一张上机卡是 [docs/NR-01.md](docs/NR-01.md)。M1 的规则复现是 [docs/NR-02.md](docs/NR-02.md)。可读性是 [docs/NR-03.md](docs/NR-03.md)。

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

```bash
PYTHONPATH=sim python3 -m unittest discover -s sim/tests -v
PYTHONPATH=sim python3 -m steel_tide repro
PYTHONPATH=sim python3 -m steel_tide
```

`repro` 打印四条已通过的复现：同帧抢芯只有一人持有、打断不计分、坠海超时芯回中场、超时结算不重新三选一岗位。最后一条命令是本地 bot 对局，不是已接入的数字居民。UE 侧如何接同一批事件见 [docs/rules/UE_EVENT_WIRING.md](docs/rules/UE_EVENT_WIRING.md)。

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

冻结页里的创世岛主线用 Godot。本岛沿用同一条五步工序（Notion 定范围 → PM-Astra 调度 → Codex 主创 → Blender 出模 → 进引擎），进引擎的一步改为 UE5，以开工包里的 SVG 为准。创世岛和猎手岛继续各自施工。本仓不引用那两个工程，也不另起第二套引擎。Tripo 仍是点召，这次开工不消耗 Tripo 额度，也不依赖另一台机器上的 Blender 压缩包。

## 谁写什么

| 路径 | 负责人 |
| --- | --- |
| `sim/`、`config/`、以后的 `Source/` C++ | Codex：规则、C++、配置 |
| `Content/` 里的 `.umap`、`.uasset` | 游戏组-虚幻引擎操作 |

现在没有 `.uproject`，也没有提交任何 `.uasset`。目录只是以后的位置，见 [Content/README.md](Content/README.md)、[Source/README.md](Source/README.md) 和 [docs/BASELINE.md](docs/BASELINE.md)。
