# Palette and badge ids

Standby prep. Not a milestone and not a frozen art pass.

Team identity is the badge shape and the shoulder light slot. Hex color is auxiliary. A portrait is not an id.

| id | token | use |
| --- | --- | --- |
| `mat.wet_concrete` | `#3E4644` | deck and street |
| `mat.worn_yellow` | `#C4A15A` | engineering machines |
| `env.sign_cyan` | `#2EC8C3` | environment sign |
| `env.sign_magenta` | `#D24B7A` | environment sign |
| `env.sea_wall` | `#6E7570` | sea wall |
| `aux.tide_cyan` | `#3DDFD4` | A auxiliary only |
| `aux.hazard_amber` | `#E2A23A` | B auxiliary only |
| `badge.A.open_chevron` | open chevron | `docs/art/badges/badge_A_open_chevron.svg` |
| `light.A.shoulder_left` | left shoulder | A light slot |
| `badge.B.closed_ring` | closed ring | `docs/art/badges/badge_B_closed_ring.svg` |
| `light.B.shoulder_right` | right shoulder | B light slot |

Source of the values is `sim/steel_tide/palette.py`.

## Audio mouths

Team sound ids use the same shape and the same shoulder lamp slot. The mouth is that lamp side. Hex stays auxiliary and is not part of the id. No sound file is stored for these ids.

| id | mouth | shape |
| --- | --- | --- |
| `sfx.team.A.open_chevron.mouth.shoulder_left` | `shoulder_left` | `open_chevron` |
| `sfx.team.B.closed_ring.mouth.shoulder_right` | `shoulder_right` | `closed_ring` |

Source of the ids is `sim/steel_tide/audio.py`. The match log is [NR-M2-audio](../NR-M2-audio.md).

## NR-03 proxies

Shape and shoulder slot identify the humanoid sides. The beast and the quadruped share neither outline. Machine paint and deck concrete are materials, not team ids. Spec file: `docs/art/NR03_PROXIES.json`.

| proxy | uses |
| --- | --- |
| `NR_Proxy_Humanoid_A` | `badge.A.open_chevron`, `light.A.shoulder_left`, body `NR_Body_Humanoid` |
| `NR_Proxy_Humanoid_B` | `badge.B.closed_ring`, `light.B.shoulder_right`, body `NR_Body_Humanoid` |
| `NR_Proxy_Beast` | silhouette `organic_beast` |
| `NR_Proxy_Quadruped` | silhouette `hydraulic_quadruped` |
| `NR_Proxy_EngineeringMachine` | `mat.worn_yellow` |
| `NR_Proxy_WetConcrete` | `mat.wet_concrete` |

## Shoulder lamps

Day-port and night-port intensities live in `config/steel_tide_greybox.json` under `lighting`. The lamp slot is the team mark. Auxiliary color may tint the lamp. It is not the id.

| id | slot | shape |
| --- | --- | --- |
| `light.shoulder.A.open_chevron.shoulder_left` | `shoulder_left` | `open_chevron` |
| `light.shoulder.B.closed_ring.shoulder_right` | `shoulder_right` | `closed_ring` |

Source of the ids is `sim/steel_tide/light.py`. The match log is [NR-M2-light](../NR-M2-light.md).

## HUD lines

Scoreboard and side-lock text use the same shape and the same shoulder slot. Hex stays auxiliary and is not part of the line or the cue id. No widget or texture is stored for these ids.

| id | geometry |
| --- | --- |
| `hud.scoreboard` | A `open_chevron` / `shoulder_left`, B `closed_ring` / `shoulder_right` |
| `hud.side_lock` | the locked combatant's shape and shoulder slot |

Source of the ids is `sim/steel_tide/hud.py`. The match log is [NR-M2-hud](../NR-M2-hud.md).
