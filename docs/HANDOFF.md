# 交接｜游戏组-虚幻引擎操作

工程文件在仓库根目录：`NeonRift.uproject`。

还缺的只有本机 UE 安装路径。`EngineAssociation` 里的 `5.4` 是占位。真实小版本由 **PM-钢潮岛** 按那台机器的安装锁定。小版本对不上时停下来，把安装路径和版本回给 PM-钢潮岛，不要另建工程。

打开工程后做 [NR-01](NR-01.md)：

1. 允许编辑器编译 `NeonRift` 模块。
2. 按 [Content/Greybox/NR01_SteelTide.layout.json](../Content/Greybox/NR01_SteelTide.layout.json) 摆钢潮港灰盒：A/B 出生、双端子、中央相位芯、高架、机修巷。
3. 用 600 uu/s 量两侧走到中场的时间，交回俯视图和低/高机位截图。
4. 不要在关卡蓝图里写计分。事件名以 `Source/NeonRift/Public/NeonRiftEventNames.h` 和 `sim/steel_tide` 为准。

仓里没有 `.umap`。启动图暂时是 `/Engine/Maps/Entry`。灰盒关卡在编辑器里另存，不把二进制交回，除非 PM-钢潮岛另说。
