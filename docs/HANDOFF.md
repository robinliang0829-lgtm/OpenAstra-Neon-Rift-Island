# 交接｜游戏组-虚幻引擎操作

工程文件在仓库根目录：`NeonRift.uproject`。

**Only local UE is missing.** 还缺的只有本机 UE。`EngineAssociation` 里的 `5.4` 是占位。真实小版本由 **PM-钢潮岛** 按那台机器的安装锁定。小版本对不上时停下来，把安装路径和版本回给 PM-钢潮岛，不要另建工程，也不要改 `EngineAssociation`。

本环境没有装 UE，也没有跑过编辑器。NR-02 的规则侧已经在仓里：事件名、双端日志、3v3 样例，以及只订阅、不记分的 GameMode / GameState / PlayerState。上机验收差的是你本机的引擎。

## 装好之后

1. 打开 `NeonRift.uproject`，允许编译 `NeonRift`。
2. 若本机还没有灰盒关卡，先按 [NR-01](NR-01.md) 摆 `NR_SteelTide_Greybox`。不要把 `.umap` / `.uasset` 交回这个仓，除非 PM-钢潮岛另说。启动图暂时仍是 `/Engine/Maps/Entry`。
3. 在仓库根目录生成本卡参照日志。`--check` 通过才开始 PIE。这不是第二套规则，它就是 `sim/steel_tide`。

```bash
PYTHONPATH=sim python3 -m steel_tide nr02
PYTHONPATH=sim python3 -m steel_tide nr02 --check
```

4. 格式见 [rules/DUAL_END_EVENT_LOG.md](rules/DUAL_END_EVENT_LOG.md)。参照样例：

- [evidence/nr02/server.log](evidence/nr02/server.log)
- [evidence/nr02/client-a.log](evidence/nr02/client-a.log)
- [evidence/nr02/client-b.log](evidence/nr02/client-b.log)

5. PIE：同一台机器两个能独立输入的客户端。条件允许时再换同网段两台机器，回传里写明是哪一种。两个 `ANeonRiftPlayerState` 分别调用 `SetViewpointClientId`，参数为 `client-a` 和 `client-b`。
6. 服务器只通过 `UNeonRiftMatchSubsystem` 广播。`ANeonRiftGameState` 记下 `AuthoritativeEventLog`，并把同一条再广播给两端。`ANeonRiftPlayerState` 把同一行放进 `ViewpointEventLog`。这三个类不增加分数，也不选举第二个持有者。关卡蓝图不要写计分。
7. 按 [NR-02](NR-02.md) 走同帧抢芯、读条被打断、掉落后再拾取得分、坠海满 8 秒复位。
8. 落三份日志。服务器抄 GameState 的 `AuthoritativeEventLog`。每个视角抄该 PlayerState 的 `ViewpointEventLog`。存根行是 `EventName  {json}`。若你已经把权威毫秒写进行首，则用样例那种 `t_s  EventName  {json}`，并补上 schema 表头。
9. 对齐事件名和 JSON，再按 schema 重放持有者和比分。不要要求毫秒和样例相同。样例里有几处体积位置是 `place_for_test`，上机要自己走到体积里。
10. 通过：全程同时只有一个持有者；打断那一次没有 `PointScored`；另有一次 `PointScored` 加上 `CoreReturnedToCenter`；`CoreReset` 回到 `center` 且比分不变。最终比分和重放结果一致。
11. 出现双持或同一次读条记两分：留下两端日志退回，不要改胜负条件。

胜负以 `sim/steel_tide` 为准。事件名以 `Source/NeonRift/Public/NeonRiftEventNames.h` 为准。
