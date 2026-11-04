# M2 原画资产规格

给 Blender 操作和游戏组-虚幻引擎操作。这一份把港区色板、阵营肩章几何、贴花和材质命名收成一张可核对的身份契约。

仓内命令：

```bash
PYTHONPATH=sim python3 -m steel_tide m2-art --check
```

`wired_into_m2_pack` 为 false。这条不进 `m2-pack` 的步骤表，不跑一局，不改 `EVENT_NAMES`，不计分。`EngineAssociation` 仍是 `5.4`。不交贴图二进制，不交 `.uasset`。

权威脚本是 `sim/steel_tide/nr_m2_art.py`。色值来自 `sim/steel_tide/palette.py`。机器可读的同一张表是 `config/m2_art_identity.json`。肩章文件仍是 `docs/art/badges/badge_A_open_chevron.svg` 和 `docs/art/badges/badge_B_closed_ring.svg`。环境参考是 `docs/kickoff/refs/01_Neon_Bay.png`，它不是贴图源。
代理轮廓仍以 `docs/art/NR03_PROXIES.json` 为准。这张表不新造兽或四足机的网格。

UE 仍挂。这条 `--check` 不打开编辑器。

## 港区色板

队标是肩章形状和肩灯位置。十六进制只是辅助。五个环境色是港区，两个辅助色只给对应阵营的灯和描边上色。

| token | id | hex | role | family | use |
| --- | --- | --- | --- | --- | --- |
| `wet_concrete` | `mat.wet_concrete` | `#3E4644` | environment | harbor | deck and street |
| `worn_yellow` | `mat.worn_yellow` | `#C4A15A` | environment | harbor | engineering machines |
| `sign_cyan` | `env.sign_cyan` | `#2EC8C3` | environment | harbor | environment sign |
| `sign_magenta` | `env.sign_magenta` | `#D24B7A` | environment | harbor | environment sign |
| `sea_wall` | `env.sea_wall` | `#6E7570` | environment | harbor | sea wall |
| `tide_cyan` | `aux.tide_cyan` | `#3DDFD4` | auxiliary | auxiliary | A auxiliary only |
| `hazard_amber` | `aux.hazard_amber` | `#E2A23A` | auxiliary | auxiliary | B auxiliary only |

| token | Blender | UE 实例 | 备注 |
| --- | --- | --- | --- |
| `wet_concrete` | `NR_Mat_WetConcrete` | `MI_NR_WetConcrete` | 粗糙度高。倒影不是读甲板的条件。 |
| `worn_yellow` | `NR_Mat_WornYellow` | `MI_NR_WornYellow` | 工程机械的比例参照，不是队标。 |
| `sign_cyan` | `NR_Mat_SignCyan` | `MI_NR_SignCyan` | 环境招牌，要比肩章安静。 |
| `sign_magenta` | `NR_Mat_SignMagenta` | `MI_NR_SignMagenta` | 环境招牌，要比肩章安静。 |
| `sea_wall` | `NR_Mat_SeaWall` | `MI_NR_SeaWall` | 非队标的共用漆。兽和四足机仍要不同轮廓。 |
| `tide_cyan` | `NR_Mat_AuxTideCyan` | `MI_NR_AuxTideCyan` | 只给 A 的辅助色，不是队标。 |
| `hazard_amber` | `NR_Mat_AuxHazardAmber` | `MI_NR_AuxHazardAmber` | 只给 B 的辅助色，不是队标。 |

## 肩章几何

视框 `0 0 64 64`。中线 x=32。灯矩形的 x 小于中线是左肩，大于中线是右肩。线宽 6，形状不填色。两名人形共用 `NR_Body_Humanoid`。

| faction | shape | light | socket | primitive | geometry | light rect | stroke | closed | aux |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | `open_chevron` | `shoulder_left` `light.A.shoulder_left` | `socket.shoulder_left` | polyline | `16,44 32,20 48,44` | `4,28,6,8` | 6 square | false | `tide_cyan` `#3DDFD4` |
| B | `closed_ring` | `shoulder_right` `light.B.shoulder_right` | `socket.shoulder_right` | circle | `32,32,16` | `54,28,6,8` | 6 none | true | `hazard_amber` `#E2A23A` |

A 的几何是开口折线，没有圆。B 的几何是圆，没有折线。灰度或色盲模拟只改辅助色，不改这两行。

## 贴花与材质命名

贴花这一行的队标是形状和灯位。`color_is_identity` 为 false。名字里不写辅助色，也不写十六进制。`texture` 全部是 `none`。

| kind | id | Blender | UE | socket | texture |
| --- | --- | --- | --- | --- | --- |
| material | `mat.wet_concrete` | `NR_Mat_WetConcrete` | `MI_NR_WetConcrete` | `none` | `none` |
| material | `mat.worn_yellow` | `NR_Mat_WornYellow` | `MI_NR_WornYellow` | `none` | `none` |
| material | `env.sign_cyan` | `NR_Mat_SignCyan` | `MI_NR_SignCyan` | `none` | `none` |
| material | `env.sign_magenta` | `NR_Mat_SignMagenta` | `MI_NR_SignMagenta` | `none` | `none` |
| material | `env.sea_wall` | `NR_Mat_SeaWall` | `MI_NR_SeaWall` | `none` | `none` |
| material | `aux.tide_cyan` | `NR_Mat_AuxTideCyan` | `MI_NR_AuxTideCyan` | `none` | `none` |
| material | `aux.hazard_amber` | `NR_Mat_AuxHazardAmber` | `MI_NR_AuxHazardAmber` | `none` | `none` |
| decal | `badge.A.open_chevron` | `NR_Decal_BadgeA_OpenChevron` | `D_NR_BadgeA_OpenChevron` | `socket.shoulder_left` | `none` |
| decal | `badge.B.closed_ring` | `NR_Decal_BadgeB_ClosedRing` | `D_NR_BadgeB_ClosedRing` | `socket.shoulder_right` | `none` |

## 核对清单

格子留给 Blender / UE 操作员上机时做。仓内 `--check` 核对这些行还在，不把未做的网格算成已交。

| id | 交给 | 仓内 | 要做的事 |
| --- | --- | --- | --- |
| `harbor.tokens` | both | spec_only | 五个港区环境色和两个辅助色的 id、十六进制都来自 `palette.py`。环境色是 `mat.wet_concrete`、`mat.worn_yellow`、`env.sign_cyan`、`env.sign_magenta`、`env.sea_wall`。辅助色是 `aux.tide_cyan` `#3DDFD4`、`aux.hazard_amber` `#E2A23A`。不要在 Blender 或材质实例里另写一版。 |
| `harbor.concrete` | both | spec_only | `mat.wet_concrete`（`#3E4644`）铺甲板和路面。粗糙度高。验收关高反射，倒影不是读这块材质的条件。 |
| `harbor.signs` | both | spec_only | `env.sign_cyan`（`#2EC8C3`）和 `env.sign_magenta`（`#D24B7A`）只做环境招牌。它们不是队标，不能比肩章更抢。 |
| `harbor.yellow` | both | spec_only | `mat.worn_yellow`（`#C4A15A`）只涂港区工程机械，当比例参照。黄漆不是阵营。 |
| `harbor.seawall` | both | spec_only | `env.sea_wall`（`#6E7570`）是海堤色。兽和四足机可以共用这色，轮廓仍必须不同。不要靠换色把四足机当成兽。 |
| `badge.shape` | both | spec_only | A 是开口人字 `open_chevron`，折线 `16,44 32,20 48,44`，不回到起点。B 是闭合环 `closed_ring`，圆心 `32,32`，半径 `16`。视框 `0 0 64 64`，线宽 6。人字用方头。 |
| `badge.light` | both | spec_only | A 的灯矩形从 `4,28` 起，宽 6 高 8，在中线 x=32 的左侧。B 从 `54,28` 起，同样大小，在右侧。遮住颜色以后形状和灯位仍要能分开。 |
| `badge.body` | ue | spec_only | 两名人形共用 `NR_Body_Humanoid`。A 的贴花插槽是 `socket.shoulder_left`，B 是 `socket.shoulder_right`。不要做第二套身体。 |
| `badge.noface` | both | spec_only | 不按脸认敌我。肩章里不出现 face。不要交肖像贴图。 |
| `naming.decal` | both | spec_only | A 的贴花：Blender `NR_Decal_BadgeA_OpenChevron`，UE `D_NR_BadgeA_OpenChevron`。B：`NR_Decal_BadgeB_ClosedRing` / `D_NR_BadgeB_ClosedRing`。名字里不写青、琥珀或十六进制。 |
| `naming.material` | both | spec_only | 材质按命名表。Blender 用 `NR_Mat_*`，UE 实例用 `MI_NR_*`。辅助色实例名带 Aux，角色仍是 auxiliary。母材质和实例都不要交进这个仓。 |
| `naming.notexture` | both | no_binary | 命名表里 texture 是 `none`。不要交 png、tga、exr 或 `.uasset`。 |
| `scale.units` | blender | spec_only | Blender 的 1 米导出成 UE 100 单位，对齐 `ue_units_per_meter`。不要改灰盒配置来迁就模型。 |
| `engine.placeholder` | ue | repo_holds_5.4 | `NeonRift.uproject` 的 `EngineAssociation` 保持 `5.4`。这条检查不打开编辑器。 |
| `pack.unwired` | both | unwired | `wired_into_m2_pack` 为 false。`m2-pack` 的步骤里没有 `m2-art`。不改 `EVENT_NAMES`，不计分。 |

## 不要交进这个仓

- 贴图二进制（png、tga、exr）和 `.uasset` / `.umap`
- 改过的 `EngineAssociation`
- 新的 `EVENT_NAMES`，或另一套计分
- 把 `m2-art` 写进 `m2-pack` 的步骤表
- 把辅助色或脸当成队标
- 为了让这条 `--check` 通过而去打开本机 UE
