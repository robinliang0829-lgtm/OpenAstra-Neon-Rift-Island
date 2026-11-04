# Neon Rift baseline

记录日期：2026-11-04。本文件描述这个开工 PR，不是已经可启动的 UE 工程。

## 工程

- 本仓 **没有** `.uproject`。历史和开工包都没有登记一份可复用的霓虹断层岛工程。不要把空目录说成已经有工程。
- 目标引擎是 UE5。小版本 **未定**，由 PM-Astra 按虚幻引擎操作员机器上的已授权版本填写。在那之前不要写死 5.x 的补丁号，也不要改用创世岛的 Godot 或猎手岛的工程。
- 分支：`cursor/neon-rift-kickoff-747a`
- 规则与文档快照 SHA：见本文件末尾「快照」。操作员 checkout 这个分支的 HEAD。HEAD 比快照多一次基线戳记时，以 HEAD 为准，快照 SHA 用来核对规则文件没有被戳记改写。

## 内容负责人

| 所有者 | 范围 |
| --- | --- |
| Codex | 比赛规则、以后的 C++、`config/steel_tide_greybox.json`、`sim/steel_tide`、操作卡上的事件名和数值 |
| 游戏组-虚幻引擎操作 | `.umap`、`.uasset`、编辑器里的摆放、灯光、导入和双端录像 |

编辑器里不维护第二套计分或阵营判定。关卡蓝图只发事件，判定以规则原型为准。

## 已核对、尚未具备

- Notion 概念页与开工包一致：https://app.notion.com/p/3ff0f164d1a2817c9069cfb02c1bfaa7
- 工作流冻结页是创世岛 Godot 主线：https://app.notion.com/p/40d0f164d1a2815ea084c2e10c05ebe7 。本岛 UE 分工图是 `docs/kickoff/03_霓虹断层岛工作流.svg`。
- 已在无 UE 的环境跑通 `PYTHONPATH=sim python3 -m unittest discover -s sim/tests -v`。
- 未跑：编辑器、双端 PIE、打包、实机帧时间。这些要等 NR-01 的机器和路径。

## 快照

规则与文档快照 SHA（不含本行的戳记提交）：

`SNAPSHOT_SHA`
