# Source

`NeonRift.uproject` 在仓库根目录。本目录是 UE 5.4 占位骨架，真实小版本由 PM-钢潮岛按本机安装锁定。

| 文件 | 作用 |
| --- | --- |
| `NeonRift.Target.cs` / `NeonRiftEditor.Target.cs` | Game 与 Editor 目标 |
| `NeonRift/NeonRift.Build.cs` | 运行时模块 |
| `NeonRift/Public/NeonRiftEventNames.h` | 与 `sim/steel_tide/events.py` 相同的事件名 |
| `NeonRift/Public/NeonRiftMatchSubsystem.h` | 唯一广播口 |
| `NeonRift/Public/NeonRiftPhaseCore.h` | 相位芯 |
| `NeonRift/Public/NeonRiftFactionSelect.h` | 选边与锁队 |
| `NeonRift/Public/NeonRiftTerminalScore.h` | 端子读条 |
| `NeonRift/Public/NeonRiftBridgeWarn.h` | 桥预警与路线 |

这些类只把事件名交给子系统。胜负仍以 `sim/steel_tide` 为准。本环境没有编译过这个模块。
