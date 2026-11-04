# Critique from `causal-critiquer`

> *Reviewer: causal-critiquer v1 · detected design: DiD · checklist: universal.md + did.md*

---

### Hard checks

| check | result | evidence |
|---|---|---|
| placebo_in_time@-275d | ❌ FAIL | ATT=0.00181, CI=[0.00018, 0.00344] — excludes zero. Pre-period is not clean. |
| se_sensitivity:hc3_vs_clustered | ✅ pass | Both CIs positive; point estimates identical |
| functional_form:log_vs_levels | ✅ pass | Log-outcome ATT ~8.1% lift, consistent direction |
| convergence:r_hat | — n/a | OLS/HC3 — no MCMC |
| convergence:divergences | — n/a | OLS — not applicable |
| convergence:ess_bulk | — n/a | OLS — not applicable |
| prior_sensitivity | — n/a | Frequentist OLS — no prior; SE robustness substituted |

---

### Showstoppers

**S1. The placebo-in-time test failed, and the memo buries it.**

The hard-check JSON records `"passed": false` on the placebo. The CI `[0.00018, 0.00344]` excludes zero — meaning the model detects a statistically significant "effect" during a period when there was no treatment. The memo (Validation §3) dismisses this as "likely driven by mild seasonal patterns" with no supporting evidence for that claim. Seasonal confounding is precisely the threat DiD cannot absorb without additional controls. A failed placebo is not a footnote; it is an unresolved threat to the entire identification strategy.

**Fix:** Do not proceed to a business recommendation until the failed placebo is explained. Options: (a) add month or quarter fixed effects to absorb seasonality, then re-run the placebo; (b) narrow the pre-period to a window where the placebo passes; (c) downgrade the causal claim explicitly to "likely attributable" rather than "caused by." The memo must report the failed placebo as a finding, not explain it away in one sentence.

---

**S2. Standard errors are clustered at the observation level, not the treatment unit — the TWFE CI is anti-conservative by an order of magnitude.**

The TWFE model applies heteroskedasticity-robust SEs (HC3) across all region-date observations. With only **one treated unit** (north_metro), the unit-of-treatment is the region. HC3 treats each row as independent, which is wrong: observations within a region are serially correlated. The hard-check SE sensitivity shows HC3 CI width = `[0.00633, 0.00972]` (width ≈ 0.0034) vs. clustered-by-region = `[0.00760, 0.00844]` (width ≈ 0.0008). The clustered CI is *narrower*, not wider — a red flag indicating the clustered SEs are also unreliable with only six regions total. With N=6 clusters, asymptotic cluster-SE theory does not hold; the CI is likely anti-conservative regardless of which HC variant is used.

**Fix:** Use wild cluster bootstrap (e.g., `wildboottest` package in Python) clustered at the region level, or report randomization-inference p-values. With six regions, RI is tractable: permute treatment assignment across regions, recompute DiD, and report the rank of the observed ATT. The memo should note that conventional p-values are unreliable with a single treated unit.

---

### Important

**I1. No event-study / dynamic DiD — the parallel trends claim rests only on a visual inspection and a single linear-trend test.**

The code runs a pooled interaction `is_treated * time_idx` to test for pre-period divergence. This is a single-degree-of-freedom test for linear trend differences. It will miss non-linear pre-period divergence. The spec explicitly requires "formal parallel trends test (event-study with leads)." No event-study coefficients are computed or plotted.

**Fix:** Estimate a dynamic DiD with event-time indicators from at least −8 weeks through +8 weeks relative to cutoff. The pre-period leads should be jointly insignificant (F-test or chi-squared). This is the standard of evidence for parallel trends, not a bivariate linear-slope comparison.

---

**I2. The "strong controls" filter is itself endogenous and undocumented in the memo.**

The preferred estimate (`att_strong = 0.00802`) is derived by dropping `river_county` because its pre-period trend p-value < 0.05. This filtering decision is made on the same pre-period data used to estimate the DiD, with no pre-registered decision rule stated in the memo. More concretely: if you run the same filter on the placebo date (2025-07-01), you might also drop controls that drive the failed placebo — which would be circular. The memo presents `att_strong` as the "preferred estimate" without acknowledging this researcher degree of freedom.

**Fix:** Pre-specify the control selection rule (e.g., "drop any region with p<0.05 on the pre-trend test") and state it in the methods section, not derive it post-hoc. Alternatively, use a synthetic control method that weights all regions optimally rather than a binary include/exclude decision. At minimum, add a footnote that the preferred estimate is conditional on a data-driven control selection.

---

**I3. Spillover is listed as "untested" in the assumptions table but is a plausible and testable threat.**

north_metro is one of six regions. If the free-delivery banner caused users in adjacent control regions to switch to north_metro (or affected app-wide behavior), control region conversion rates would be depressed, biasing the ATT upward. The `market_type` column is loaded from `food_delivery_regions.csv` but never used in any model or check.

**Fix:** (a) Use the `market_type` variable to test whether controls of the same market type as north_metro show different post-period trends than dissimilar controls — a partial spillover check. (b) State explicitly in the memo whether north_metro and the controls are geographic neighbors or logically separated markets. If they are neighbors, the upward bias from spillover could be material and the "proceed with rollout" recommendation is premature.

---

**I4. The `post` variable is taken as given from the raw data — its construction is never verified.**

The code uses `did_df["post"]` directly but never constructs `post` from the cutoff date. There is no line `daily["post"] = (daily["date"] >= CUTOFF).astype(int)` in the analysis code. If `post` is a pre-existing column in the CSV, its definition (inclusive/exclusive of 2026-04-01, timezone handling, etc.) is unverified. A one-day error in the cutoff shifts observations between pre and post periods.

**Fix:** Construct `post` explicitly: `daily["post"] = (daily["date"] >= CUTOFF).astype(int)` and add an assertion that the count of post-period rows for the treated region matches expectation. Log the exact cutoff and count of pre/post observations per region.

---

### Worth noting

**W1. The TWFE CI is reported as `[+0.00947, +0.01064]` — implausibly tighter than the 2×2 CI — and this is never flagged.**

The TWFE CI width (≈ 0.0012) is roughly 4× narrower than the 2×2 HC3 CI width (≈ 0.0034). This counter-intuitive result, combined with the S2 finding about HC3 with one treated unit, strongly suggests the TWFE SE is spuriously small. The memo reports this without comment.

**Fix:** Footnote the TWFE CI as unreliable given the single treated unit, and remove it from the primary estimate table or label it clearly as illustrative only.

---

**W2. The 9.5% relative lift calculation uses pre-period mean, not the counterfactual control trajectory.**

`pct_lift = att_strong / treated_pre_mean * 100` divides the absolute ATT by north_metro's pre-period mean conversion rate. This is correct only if the counterfactual post-period rate equals the pre-period mean — i.e., no trend. Given the failed placebo suggests some pre-period dynamics, the denominator should be the estimated counterfactual post-period level, not simply the pre-period mean.

**Fix:** Report relative lift as `att / estimated_counterfactual_post`, where the counterfactual is derived from the control group's average post-period level adjusted for the pre-period gap.

---

**W3. No discussion of heterogeneity or mechanism — the "proceed with rollout" recommendation is unqualified.**

The memo recommends rolling out to all regions without asking whether the +9.5% lift is uniform across user segments, days of week, or order sizes. north_metro may be systematically different from the remaining five regions (it was selected as the pilot). Extrapolating the ATT to other regions assumes treatment effect homogeneity, which is an assumption, not a conclusion.

**Fix:** Add one sentence to the memo: "This ATT is specific to north_metro. External validity to other regions requires an assumption of treatment effect homogeneity that has not been tested. A staged rollout with region-level monitoring is recommended over a simultaneous full rollout."

---

### Recommended changes (priority order)

1. **Re-run with seasonality controls or a restricted pre-window until the placebo passes.** Do not advance to a recommendation with a failed falsification check.
2. **Implement wild cluster bootstrap or randomization inference** for all reported p-values and CIs. Remove the HC3 TWFE CI from the summary table or label it unreliable.
3. **Add an event-study plot** with pre-period leads and report a joint F-test on the leads as the parallel-trends test.
4. **Pre-specify the control selection rule** or replace binary filtering with synthetic control weights. Document the rule in the methods section.
5. **Investigate spillover** using the `market_type` column and geographic adjacency information.
6. **Construct and verify `post` explicitly** in code rather than relying on a column from the CSV.
7. **Recompute relative lift** using the estimated counterfactual post-period level, not the pre-period mean.
8. **Qualify the rollout recommendation** with a staged-rollout caveat and external validity note.
