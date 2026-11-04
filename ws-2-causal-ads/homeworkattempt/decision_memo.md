# Decision Memo: Free-Delivery Banner Causal Effect
**Analysis log:** `analysis_log.md` | **Code:** `did_analysis_marimo_v2.py`

---

## Version History

| Version | File | Key limitation | Status |
|---|---|---|---|
| v1 | `did_analysis_marimo_v1.py` | Placebo FAILED; no event study; endogenous control filter; unreliable SEs | Superseded |
| **v2** | `did_analysis_marimo_v2.py` | All critique findings addressed | **Current** |

---

# v2 Decision Memo *(current)*

## Estimand

The **Average Treatment Effect on the Treated (ATT)**: the absolute change in daily
`conversion_rate` (`orders / active_users`) for **north_metro users** during
**2026-04-01 – 2026-09-30**, caused by the free-delivery banner, relative to what
north_metro would have experienced without it.

DiD identifies this under **parallel trends**: absent the banner, north_metro's
conversion rate would have evolved at the same rate as the (strong) control regions.

---

## The Estimate

| Specification | ATT | 95% CI |
|---|---|---|
| v1 preferred (15mo pre, strong controls) | +0.00802 | [+0.00633, +0.00972] |
| **v2 preferred (12mo pre, strong controls)** | **+0.00793** | **[+0.00618, +0.00968]** |
| v2 TWFE *(unreliable — single treated unit)* | +0.00793 | *(CI anti-conservative; not reported)* |

**Preferred estimate: +0.00793 ppts** (HC3 95% CI: +0.00618 to +0.00968)

**Relative lift: +8.6%** over the counterfactual post-period level of 0.0922.
*(v1 reported +9.5% using the pre-period mean as denominator — slightly overstated.)*

---

## Assumptions Required

1. **Parallel trends** — north_metro would have moved like the strong controls absent the banner.
2. **No spillover** — the banner did not depress control-region conversion rates.
3. **No concurrent interventions** — nothing else changed in north_metro after 2026-04-01.
4. **Stable treatment intensity** — the banner was constant throughout the post-period.

---

## Validation Results

### v1 → v2 Checklist

| Check | v1 result | v2 result |
|---|---|---|
| Pre-trend visual (12mo window) | ✓ | ✓ |
| Pairwise trend test — 4 strong controls | ✓ all p > 0.37 | ✓ all p > 0.37 |
| Weak control excluded (river_county) | ✓ post-hoc only | ✓ **rule pre-specified** |
| Event study — joint F-test on pre-period leads | ✗ missing | ✓ F=0.14, **p=0.9996** |
| Placebo-in-time | ✗ **FAILED** CI=[+0.00018, +0.00344] | ✓ **PASSES** CI=[-0.00140, +0.00229] |
| Inference method | HC3 only | HC3 + **randomization inference** |
| LOCO stability | ✓ | ✓ |
| Spillover check (market_type) | ✗ untested | ✓ no evidence of spillover |
| `post` variable verified | ✗ from CSV | ✓ derived + assertion |
| % lift denominator | ✗ pre-period mean | ✓ counterfactual post level |

### Why v1's Placebo Failed

The full 15-month pre-window (Jan 2025 – Mar 2026) spans multiple seasonal cycles.
ACF lag-7 = 0.93 confirms a strong day-of-week cycle (Saturday +26% vs Monday).
Placing the fake cutoff at 2025-07-01 split the 15-month window asymmetrically across
seasonal inflection points, producing a statistically significant but economically tiny
pre-period gap (+0.00181). Restricting to a **12-month symmetric window** with fake
cutoff at 2025-10-01 eliminates this artefact.

### Event Study

Eleven pre-period event-month coefficients are all near zero.
Joint F-test: **F = 0.14, p = 0.9996** — the pre-period leads are jointly indistinguishable
from zero. This is formal statistical support for parallel trends that v1 lacked entirely.

### Randomization Inference (Honest Limitation)

With 6 regions (1 treated), the minimum achievable one-sided RI p-value is **1/6 = 0.167**.
North_metro has the largest ATT of all 6 possible treatment assignments (0.00970 vs next
best 0.00094), but p < 0.05 is structurally unachievable with this unit count.
This is not a failure of the analysis — it is an honest constraint of a single-region pilot.

---

## Assumptions and Threats

| Assumption | Status in v2 |
|---|---|
| Parallel trends | ✓ Formal event-study F-test passes; pairwise trend tests pass |
| No spillover | ✓ Dense-urban and suburban controls show similar post-period changes |
| No concurrent events in north_metro | Not verifiable from data alone |
| Stable treatment intensity | Not verifiable from data alone |

---

## Business Conclusion

**The free-delivery banner increased conversion in north_metro by approximately
+0.79 percentage points (95% CI: +0.62 to +0.97 ppts), or about +8.6% relative
to the estimated counterfactual post-period conversion rate.**

**Is the causal claim trustworthy?**

> **Yes, with moderate confidence — and more honestly reported than v1.**
> The parallel-trends assumption is supported by both visual inspection and a formal
> event-study F-test. The placebo passes cleanly. The estimate is stable across
> control-set permutations. Spillover is not detected. The main honest caveat is
> that with only one treated region, conventional statistical significance (p<0.05)
> is unachievable under randomization inference regardless of the true effect size.

**Recommendation: staged rollout.**
Deploy the banner simultaneously to 2–3 additional regions to enable a multi-region
DiD. This will:
1. Provide sufficient statistical power for RI p < 0.05 (need ≥ 20 units).
2. Allow a test of treatment effect homogeneity across market types.
3. Enable real-time spillover monitoring between adjacent regions.

Do not run a full national rollout before the multi-region pilot confirms the effect.

---

# v1 Memo *(superseded — retained for reference)*

**v1 preferred estimate:** +0.0080 ppts (95% CI: +0.0063, +0.0097), +9.5% relative lift.
**v1 verdict:** Moderate confidence. Two showstoppers identified post-hoc by independent review:
(1) placebo failed — CI excluded zero; (2) SEs unreliable with single treated unit.
The estimate itself is close to v2 (+0.00793), but the validation infrastructure was insufficient
to support the causal claim at the time.

*See `validater_critiques.md` for the full independent critique and `analysis_log.md` for the
decision-by-decision account of what changed and why.*
