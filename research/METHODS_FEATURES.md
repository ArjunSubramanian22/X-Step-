# Feature methods

Production models use a **59-dimensional** vector from `xstep_ml.biomechanics.extract_features` (stable length for shipped artifacts). Extended features in `xstep_ml.features` are documented here and used in ablation/explainability; they are **not** silently concatenated onto production checkpoints.

Notation: window \(W \in \mathbb{R}^{T \times 8}\), left sites then right, order `met1, met2, met5, heel`. \(\Delta t = 1/f_s\).

All current gait-label experiments use **synthetic** windows unless a human loader is wired in.

| Name | Definition | Unit | Interpretation |
| --- | --- | --- | --- |
| `{L,R}_{site}_peak` | \(\max_t p(t)\) | kPa | Peak plantar pressure (PPP) |
| `{L,R}_{site}_mean` | \(\mathrm{mean}_t p(t)\) | kPa | Mean pressure |
| `{L,R}_{site}_pti` | \(\sum_t p(t)\,\Delta t\) | kPa·s | Pressure-time integral (PTI) |
| `{L,R}_{site}_load` | \(\mathrm{mean}_t \mathbf{1}[p>30]\) | 1 | Loaded-contact fraction (engineering 30 kPa) |
| `{L,R}_{site}_high` | \(\mathrm{mean}_t \mathbf{1}[p>\tau_{\mathrm{high}}]\) | 1 | Fraction above literature high-PPP band (default 200 kPa) |
| `{L,R}_{site}_cv` | \(\mathrm{std}/\max(\mathrm{mean},\varepsilon)\) | 1 | Temporal coefficient of variation |
| `asym_{site}` | \(\lvert PPP_L-PPP_R\rvert / ((PPP_L+PPP_R)/2)\) | 1 | Bilateral symmetry index |
| `cadence_spm` | \(60 \times n_{\mathrm{strikes}} / T_{\mathrm{window}}\) | steps/min | Heel-strike cadence estimate |
| `stance_ratio` | \(\mathrm{mean}_t \mathbf{1}[\max p > 15]\) | 1 | Approximate duty factor |
| `cop_ap` / `forefoot_share` | forefoot mass / total mass | 1 | Anterior pressure share |
| `peak_any` | \(\max W\) | kPa | Window peak |
| `pti_total` | \(\sum W\,\Delta t\) | kPa·s | Total PTI |
| `temp_asym_max` | max contralateral \(\lvert \Delta T\rvert\) | °C | 0 if thermistors absent |
| `loading_rate_max` | \(\max_t (dp_{\max}/dt)\) | kPa/s | Peak loading rate |
| `unloading_rate_min` | \(\min_t (dp_{\max}/dt)\) | kPa/s | Peak unloading rate |
| `contact_duration_s` | \(\sum \mathbf{1}[\max p>15]\,\Delta t\) | s | Contact duration |
| `stride_duration_s` | median inter-strike interval | s | 0 if <2 strikes |
| `stance_duration_s` | contact / max(strikes,1) | s | Crude stance estimate |
| `swing_duration_s` | \(\max(\mathrm{stride}-\mathrm{stance},0)\) | s | Crude swing estimate |
| `cop_ml` | \((\Sigma\mathrm{MET5}-\Sigma\mathrm{MET1})/(\Sigma\mathrm{MET5}+\Sigma\mathrm{MET1})\) | 1 | ML centroid approximation |
| `forefoot_heel_ratio` | \(\Sigma\mathrm{fore}/\max(\Sigma\mathrm{heel},\varepsilon)\) | 1 | Regional ratio |
| `overload_duration_s` | time with \(\max p > \tau_{\mathrm{alert}}\) | s | Engineering alert occupancy |
| `overload_events` | contiguous runs above \(\tau_{\mathrm{alert}}\) | 1 | Repeated overload count |
| `cumulative_overload_pti` | \(\sum \max(p_{\max}-\tau_{\mathrm{alert}},0)\,\Delta t\) | kPa·s | Cumulative overload exposure |
| `l_r_load_asym` | whole-foot PTI symmetry | 1 | Load asymmetry |

\(\tau_{\mathrm{alert}}\) defaults to 75 kPa and is an **engineering risk-alert threshold**, not a clinically validated cut-point.

Code: `xstep_ml/biomechanics.py`, `xstep_ml/features.py`. Tests: `tests/test_features.py`.
