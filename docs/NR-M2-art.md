# NR-M2-art

给 Blender 操作和游戏组-虚幻引擎操作。这张卡把 M2 的原画收成一份仓内可核对的身份契约：港区色板、阵营肩章几何、贴花和材质命名、交给操作员的资产核对清单。

**不跑一局。** 不调用 `SteelTideMatch`，不写 `match.events`，不新造 `EVENT_NAMES`，不计分。身份来自已经入库的 `sim/steel_tide/palette.py` 和两张肩章 svg。

**不交成品。** 没有贴图二进制，没有 `.uasset`，没有 `.umap`。概念图 `docs/kickoff/refs/01_Neon_Bay.png` 只是环境参考，不是贴图源。

**UE 仍挂。** 本环境没有装 UE，没有 PIE，也没有实机画面。`EngineAssociation` 仍是 `5.4` 占位。不要改它。不要为了这张卡打开编辑器。

**不进 `m2-pack` 的步骤表。** `wired_into_m2_pack` 为 false。开发包仍是规则链，样例仍是 `docs/evidence/nr-m2-pack/`。原画契约单独验收。`unittest` 会跑 `sim/tests/test_nr_m2_art.py`，里面调用这条 `--check`。

**通过（仓内，本 PR HEAD）：** `PYTHONPATH=sim python3 -m steel_tide m2-art --check` 退出码为 0。这不是实机通过，也不是已经做好的模型。

**通过（上机）：** 仍做不到。UE 仍挂。装上本机引擎之前，不要用关卡蓝图写第二套计分来换一张「通过」。

## 输入

- 色值：`sim/steel_tide/palette.py`。说明页仍是 `docs/art/PALETTE_AND_IDS.md`
- 肩章：`docs/art/badges/badge_A_open_chevron.svg`、`docs/art/badges/badge_B_closed_ring.svg`
- 机器可读契约：`config/m2_art_identity.json`
- 操作员清单：`docs/art/M2_ASSET_SPEC.md`
- 核对记录：`docs/evidence/nr-m2-art/identity.log`
- 比例：`config/steel_tide_greybox.json` 的 `ue_units_per_meter` 为 100，`map_slice` 为 `SteelTidePort`。这条不改那份配置
- 命令：

```bash
PYTHONPATH=sim python3 -m steel_tide m2-art
PYTHONPATH=sim python3 -m steel_tide m2-art --check
```

不带 `--check` 时，按当前色板重写上面三份契约。`--check` 对照已提交的三份，不一致就退出码 1。用法不对是 2。

## 契约里有什么

| 块 | 内容 |
| --- | --- |
| 港区色板 | 五个环境色：湿混凝土、磨损黄漆、青蓝招牌、玫红招牌、海堤。两个辅助色：A 的 tide cyan、B 的 hazard amber。十六进制只辅助，不是队标 |
| 肩章几何 | A `open_chevron`，灯在左肩 `shoulder_left`。B `closed_ring`，灯在右肩 `shoulder_right`。视框 `0 0 64 64`，中线 x=32。遮住颜色后形状和灯位仍分开 |
| 贴花与材质命名 | 材质 `NR_Mat_*` / `MI_NR_*`。贴花 `NR_Decal_BadgeA_OpenChevron`、`D_NR_BadgeA_OpenChevron`、`NR_Decal_BadgeB_ClosedRing`、`D_NR_BadgeB_ClosedRing`。贴花名不写辅助色。`texture` 是 `none` |
| 资产核对清单 | `docs/art/M2_ASSET_SPEC.md` 的 15 行。交给 Blender、UE，或两边。未做的网格保持 `spec_only` |

两名人形共用 `NR_Body_Humanoid`。A 的插槽是 `socket.shoulder_left`，B 是 `socket.shoulder_right`。不要做第二套身体，不要按脸分队。

兽和四足机的轮廓仍以 `docs/art/NR03_PROXIES.json` 为准。海堤色可以共用，轮廓必须不同。

## 上机以后

UE 仍挂。装上本机引擎之后才做这些，做不到就停，把安装路径回给 PM-钢潮岛：

1. 先让 `PYTHONPATH=sim python3 -m steel_tide m2-art --check` 退出码为 0。不过就不要开始建模。
2. 打开 `NeonRift.uproject`。`EngineAssociation` 仍是 `5.4` 占位。不要改。
3. 按 `docs/art/M2_ASSET_SPEC.md` 做材质实例和肩章贴花。Blender 1 米对应 UE 100 单位。
4. 不要把 `.umap` / `.uasset` / 贴图二进制交回这个仓。不要 cook。
5. 关卡蓝图不要写计分。胜负仍以 `sim/steel_tide` 为准。
