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
