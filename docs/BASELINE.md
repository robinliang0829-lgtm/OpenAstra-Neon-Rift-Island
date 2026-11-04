# Neon Rift baseline

记录日期：2026-11-04。`NeonRift.uproject` 已进仓。本环境没有 UE，编辑器没有打开过它。

## 工程

- 工程文件是仓库根目录的 `NeonRift.uproject`。`EngineAssociation` 为 `5.4`，这是占位。
- 真实小版本由 **PM-钢潮岛** 按虚幻引擎操作员机器上的安装锁定。不要改去创世岛 Godot 或猎手岛工程。
- 没有提交 `.umap` / `.uasset`。NR-01 坐标在 `Content/Greybox/NR01_SteelTide.layout.json`。
- 分支：`cursor/neon-rift-kickoff-747a`
- 加工程文件之前的规则快照：`f8af352895dd890a7aac01e92682698f591faad2`。
- 操作员 checkout 分支 `cursor/neon-rift-kickoff-747a` 的 HEAD。HEAD 含 `NeonRift.uproject`。

## 内容负责人

| 所有者 | 范围 |
| --- | --- |
| Codex | 比赛规则、`Source/NeonRift`、`NeonRift.uproject`、`config/steel_tide_greybox.json`、`sim/steel_tide`、操作卡上的事件名和数值 |
| 游戏组-虚幻引擎操作 | `.umap`、`.uasset`、编辑器里的摆放、灯光、导入和双端录像 |

编辑器里不维护第二套计分或阵营判定。关卡蓝图只发事件，判定以规则原型为准。

## 已核对、尚未具备

- Notion 概念页与开工包一致：https://app.notion.com/p/3ff0f164d1a2817c9069cfb02c1bfaa7
- 工作流冻结页是创世岛 Godot 主线：https://app.notion.com/p/40d0f164d1a2815ea084c2e10c05ebe7 。本岛 UE 分工图是 `docs/kickoff/03_霓虹断层岛工作流.svg`。
- 已在无 UE 的环境跑通 `PYTHONPATH=sim python3 -m unittest discover -s sim/tests -v`。
- 未跑：编辑器、双端 PIE、打包、实机帧时间。这些要等 NR-01 的机器和路径。

## 快照

- 分支：`cursor/neon-rift-kickoff-747a`
- 加工程文件之前的规则快照：`f8af352895dd890a7aac01e92682698f591faad2`
- 当前基线是该分支 HEAD，PR 描述里的 Baseline HEAD 与 `git rev-parse HEAD` 相同。
