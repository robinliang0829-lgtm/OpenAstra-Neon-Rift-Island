# NR-03 资产缺口

规格在 `docs/art/NR03_PROXIES.json`。本文件只列还没有进仓的实机资产。这里没有 PIE 截图，也没有录像。

| 缺口 | 规格里已有 | 还缺 |
| --- | --- | --- |
| `NR_Proxy_Humanoid_A` / `NR_Proxy_Humanoid_B` | 同一 `NR_Body_Humanoid`。A 是 `open_chevron` + 左肩灯，B 是 `closed_ring` + 右肩灯 | 人形网格、肩灯、贴花。不要做两套身体 |
| `NR_Proxy_Beast` | 有机轮廓 `organic_beast` | 兽的网格与动作。不要用四足机涂色代替 |
| `NR_Proxy_Quadruped` | 液压四足轮廓 `hydraulic_quadruped` | 四足机网格。轮廓必须和兽不同 |
| `NR_Proxy_EngineeringMachine` | `mat.worn_yellow` `#C4A15A` | 港区黄漆工程机械的网格与材质实例 |
| `NR_Proxy_WetConcrete` | `mat.wet_concrete` `#3E4644`，高粗糙度 | 湿混凝土材质实例。验收时关高反射 |
| `NR_BridgeSpan` 灯带 | 4 秒事件序列：`BridgeWarningStarted`、`BridgeLightStripAdvanced`、`BridgeWarningCompleted` | 沿跨度的灯。不要靠水面倒影当唯一信号 |
| 警报 | 与灯带第一盏同一毫秒开始 | `Content/Audio/BridgeWarning/` 里的声音。仓内测试不需要音频文件 |
| 肩章贴花 | `docs/art/badges/badge_A_open_chevron.svg`、`docs/art/badges/badge_B_closed_ring.svg` | 引擎里的贴花。不要提交 `.uasset` |
| 同机位前后图、关反射录像、灰度肩章截图 | 无 | 本机 UE 上当前构建的记录。概念图和本仓都不能代替 |

未做：Tripo 生成、另一台机器上的 Blender 包、修改 `EngineAssociation`、提交 `.umap` / `.uasset`。`UNeonRiftReadabilityAsset` 只是数据存根，仓里没有它的资产实例。
