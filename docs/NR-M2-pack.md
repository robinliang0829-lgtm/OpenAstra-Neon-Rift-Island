# NR-M2-pack

给要跑仓内验收的人。这一条把已经入库的无头检查串成一个开发包。克隆仓库、设好 `PYTHONPATH`、跑一条命令。每一步退出码都是 0，这条才算通过。

**这是无头 Python 开发包，不是 UE 包。** 不 cook，不打二进制，不开编辑器，不跑 PIE。本环境没有装 UE。`EngineAssociation` 仍是 `5.4` 占位。不要改它，不要交 `.umap` / `.uasset`。

**UE 仍挂。** 下面「已通过」只指这条命令里的仓内切片。实机卡仍等本机 UE。装上引擎之前，不要用关卡蓝图写第二套计分来换一张「通过」。

## 克隆之后

在仓库根目录：

```bash
git clone https://github.com/robinliang0829-lgtm/OpenAstra-Neon-Rift-Island.git
cd OpenAstra-Neon-Rift-Island
export PYTHONPATH=sim
python3 -m steel_tide m2-pack --check
```

不导出变量时，同一条是 `PYTHONPATH=sim python3 -m steel_tide m2-pack --check`。`PYTHONPATH=sim` 是为了让 `python3 -m steel_tide` 找到 `sim/steel_tide`。没有第二套安装步骤，也没有新的依赖。

`--check` 对照 `docs/evidence/nr-m2-pack/`。记录和当场结果不一致，或任一步不是 0，退出码就是 1。用法不对是 2。

## 这条命令串起来的切片

顺序固定。有 `--check` 的卡只对照样例，不改写样例日志。

| 步 | 命令 | 仓内已经覆盖的事 |
| --- | --- | --- |
| repro | `PYTHONPATH=sim python3 -m steel_tide repro` | 同帧抢芯只有一人持有、打断不计分、坠海超时芯回中场、超时结算不重新三选一岗位 |
| nr02 | `PYTHONPATH=sim python3 -m steel_tide nr02 --check` | 3v3 双端日志，对照 `docs/evidence/nr02/` |
| nr03 | `PYTHONPATH=sim python3 -m steel_tide nr03 --check` | 肩章与 4 秒桥预警，对照 `docs/evidence/nr03/` |
| m1 | `PYTHONPATH=sim python3 -m steel_tide m1 --check` | 两个视角、复活、加时、三岗位，对照 `docs/evidence/nr-m1/` |
| m1-pass | `PYTHONPATH=sim python3 -m steel_tide m1-pass --check` | 近距传球、持芯突进、两种读条打断、常规先到 2 分 |
| m1-bot | `PYTHONPATH=sim python3 -m steel_tide m1-bot --check` | 四个 `local_bot` 自己走完一局 |
| m2-resident | `PYTHONPATH=sim python3 -m steel_tide m2-resident --check` | `a2` 用 `select_match` / `decide`。薄策略，不是生产数字居民 |
| m2-roles | `PYTHONPATH=sim python3 -m steel_tide m2-roles --check` | 突进、支援、侦察走岗位口 |
| m2-bridge | `PYTHONPATH=sim python3 -m steel_tide m2-bridge --check` | 桥接通和断开改权威路线图，机修巷仍可得分 |
| unittest | `PYTHONPATH=sim python3 -m unittest discover -s sim/tests -v` | `sim/tests` 全部用例 |

`m2-audio` 不在这张表里。它不新造事件名，也不改计分，所以不改 `docs/evidence/nr-m2-pack/`。队标音、4 秒桥预警和芯链的音效契约用 `PYTHONPATH=sim python3 -m steel_tide m2-audio --check`，样例在 `docs/evidence/nr-m2-audio/`。规格见 [NR-M2-audio](NR-M2-audio.md)。`unittest` 这一步会跑 `sim/tests/test_nr_m2_audio.py`，所以开发包仍会执行这份契约的单元测试。单独的 `--check` 才对照音效样例日志。

规则仍是 `sim/steel_tide`。这条命令不新造计分，不新造事件名，不改 `config/steel_tide_greybox.json`。

`m2-light` 不在这张表里。它不新造事件名，也不改计分，所以不改 `docs/evidence/nr-m2-pack/`。肩灯、4 秒灯带、端子读条、得分和出生保护的灯光契约是旁路日志，用 `PYTHONPATH=sim python3 -m steel_tide m2-light --check`，样例在 `docs/evidence/nr-m2-light/`。规格见 [NR-M2-light](NR-M2-light.md)。`unittest` 这一步会跑 `sim/tests/test_nr_m2_light.py`，所以开发包仍会执行这份契约的单元测试。单独的 `--check` 才对照灯光样例日志。日港和夜港强度写在配置的 `lighting` 里，由这条契约读取；开发包命令不改写那份配置。

样例只记命令和退出码：

- `docs/evidence/nr-m2-pack/commands.txt`
- `docs/evidence/nr-m2-pack/exit-codes.txt`

`m2-fail` 不在上表里。它不新造事件名，也不改计分，所以不改 `docs/evidence/nr-m2-pack/`。同帧抢芯、受击打断、超时不重新三选一用 `PYTHONPATH=sim python3 -m steel_tide m2-fail --check`，样例在 `docs/evidence/nr-m2-fail/`。规格见 [NR-M2-fail](NR-M2-fail.md)。输出里的 `wired_into_m2_pack` 为 false。`unittest` 这一步会跑 `sim/tests/test_nr_m2_fail.py`。单独的 `--check` 才对照那三份失败路径日志。

## 仍等本机 UE 的卡

这些卡的上机段都还没做。开发包不代替它们。

| 卡 | 还在等的实机动作 |
| --- | --- |
| [NR-01](NR-01.md) | 打开 `NeonRift.uproject`，按灰盒坐标摆关卡，量高架和机修巷的步行时间，回传三张镜头。仓里没有 `.umap` |
| [NR-02](NR-02.md) | 两个独立输入的客户端。同帧抢芯、读条被打断、掉落后再拾取得分、坠海满 8 秒复位。落三份日志 |
| [NR-03](NR-03.md) | 关掉高反射后的桥预警录像，以及灰度下靠肩章形状分队。规格已入库，实机录像仍等 UE |
| [NR-M1](NR-M1-prep.md) | 首切片上机：两个视角、复活、加时、三岗位。仓内 `--check` 不是实机通过 |
| [NR-M1-pass](NR-M1-pass.md) | 近距传球、持芯禁止突进、读条受击或离开都不记分、常规先到 2 分 |
| [NR-M1-bot](NR-M1-bot.md) | 四个本地 bot 在 PIE 里自己走完一局。这不是生产数字居民 |
| [NR-M2-resident](NR-M2-resident.md) | 薄策略数字居民上机。不喂墙后坐标 |
| [NR-M2-roles](NR-M2-roles.md) | 突进、支援、侦察在 PIE 里按岗位使用 |
| [NR-M2-bridge](NR-M2-bridge.md) | 导航网格跟权威路线图。桥张开时跨度不可走，机修巷可走。断开不记分、不击倒 |
| [NR-M2-audio](NR-M2-audio.md) | 队标音口、4 秒桥预警和芯链音效。仓内只有事件旁路日志。实机播放仍等 UE |

M2 里原画方向的美术、灯光、声音也仍在本机 UE 上，不在这个开发包里。不要 cook，不要打二进制包。

仓内灯光契约是 `m2-light`，不在上表。它只核对 `LightCue` 日志。实机灯光仍等 UE。见 [NR-M2-light](NR-M2-light.md)。

## 上机以后

UE 仍挂。装上本机引擎之后才做这些，做不到就停，把安装路径回给 PM-钢潮岛：

1. 先让 `PYTHONPATH=sim python3 -m steel_tide m2-pack --check` 退出码为 0。不过就不要上机。
2. 打开 `NeonRift.uproject`。`EngineAssociation` 仍是 `5.4` 占位。不要改。
3. 不要交回 `.umap` / `.uasset`。不要 cook，不要打二进制包。
4. 按上表的卡逐张做实机。关卡蓝图不要写计分。胜负仍以 `sim/steel_tide` 为准。
