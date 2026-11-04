# Critique from `causal-critiquer` (blind run)

Produced by a fresh sub-agent with no access to the chat history or simulator
answer key. Input: `notebooks/02-validator-review-input.py` (the blind run, truncated at the
wrong "it's an artifact / no real effect" conclusion). This is the **critique
step that was missing** between the log and the skill.

> *Reviewer: causal-critiquer v1 · detected design: Interrupted Time Series (ITS) · checklist: universal.md + its.md*

---

### Hard checks
| check | result | evidence |
|---|---|---|
| convergence:r_hat | — skipped | sklearn `LinearRegression` backend → no posterior/`idata` to check |
| convergence:divergences | — skipped | same: no MCMC |
| convergence:ess_bulk | — skipped | same: no MCMC |
| placebo_in_time@-90d | ✅ pass | refit HDI [-0.00045, +0.00069] contains 0 |
| placebo_in_time@-180d | ✅ pass | refit HDI [-0.00061, +0.00060] contains 0 |
| placebo_in_time (dense sweep) | ✅ pass | 16 fake dates: mean −1.6%, std 6.7%, range [−9.6%, +10.4%]; real effect −15.8% at z = −2.1, outside the placebo distribution |
| prior_sensitivity | — skipped | `cp.checks.PriorSensitivity` absent in CausalPy 0.8.1; sklearn backend has no prior |

---

### Showstoppers

**1. The central mechanistic claim has the sign backwards: the pre-period rate is RISING, not decaying, so "remaining non-subscriber pool → mechanically falling rate" is false.**
The diagnosis cell asserts that the pool of users still able to subscribe mechanically makes `conv_rate` fall. The data say the opposite. Over the trimmed pre-period the `conv_rate` slope is **+7.5e-7/day (rising)** and `corr(conv_rate, subscriber_pool) = +0.33` — the rate goes *up* as the remaining non-subscriber pool grows. Because the pre-trend slopes up, projecting it forward yields a *higher* counterfactual (0.001837) than the actual post mean (0.001546): a genuine **−16% gap**. The artifact invoked would push the estimate toward *positive*; the model finds negative because there is a real downward break.

**2. The placebo-in-time test (never run) refutes "the trend term is just chasing denominator drift."**
16 fake interventions across the pre-period, refitting Attempt-2's exact spec, give effects centered at zero (mean −1.6%, std 6.7%); −16% appears **only at the true date** (z = −2.1). If the trend were chasing mechanical drift, the pre-period placebos would show the same −16% — they don't.

---

### Important

**3. "The March spike drives the drop" is wrong — the effect survives its removal.**
Removing March 2026 from the fit still yields **−12.5%** (vs −15.8%). March inflates the magnitude modestly; it is not the source of the sign.

**4. Three different "conversion" quantities are conflated; the eyeball argument uses the wrong one.**
The diagnosis compares monthly conversion *sums* against a *daily per-pool rate*. The denominator nearly doubles pre→post (11.5k→20k), so flat monthly sums say nothing about the rate. The decision-relevant series — last 60 pre days 0.001856 vs first 60 post days 0.001522, a clean **−18% step** — is never plotted.

**5. No estimand, no counterfactual sentence, no model-native uncertainty.**
Estimand never named (ATT on the post-period daily subscription rate among users still able to subscribe, level scale); no "if we hadn't intervened, the rate would have been X" sentence; sklearn backend gives no posterior/HDI.

**6. The pre-period specification is under-checked: day-of-week was added by habit, not justified by the data.**
Attempt 2 improves fit by trimming the noisy early period and adding `C(dow)`, then immediately reads the treatment effect. That is not enough. Before interpreting an ITS effect, the analysis needs to test the pre-period mean structure: trend, seasonality, residual autocorrelation, and alternative seasonal bases. In particular, daily business data does not automatically imply a day-of-week effect; the analyst should compare plausible seasonal forms and show that residuals no longer contain systematic structure.

---

### Worth noting

**7. "More negative with better fit" is expected, not a red flag.**
Trimming the high-variance early period and adding terms sharpens the counterfactual; a larger, better-identified effect is the normal consequence. R²=0.12 is low but irrelevant to bias.

**8. Residual autocorrelation is actually fine — but unchecked (got lucky).**
Durbin-Watson = 1.98, lag-1 residual autocorr = 0.01. The iid assumption holds; note it explicitly rather than leaving it unstated.

---

### Verdict: DISAGREE with the "it's an artifact / no real effect" bottom line.

The three load-bearing claims — (a) baseline decays as the pool ages, (b) the linear
trend mechanically fabricates the negative, (c) the March spike drives the drop — are
each contradicted by the allowed data: the pre-trend *rises*, placebo effects are ~0
while the real cut is −16% (z ≈ −2.1), and the effect survives removing March (−12.5%).
There is a clean, robust **negative discontinuity of roughly −12% to −18%** at
2026-04-01. Ship a negative number off a corrected version, not "no effect."

### Recommended changes
- Run the placebo-in-time sweep and put it in the notebook — it is the decisive check and overturns the headline.
- Kill or substantiate the subscriber-pool drift story; the pre-period rate rises and correlates *positively* with pool size.
- Add a pre-period specification gate before reading the effect: test trend/seasonality choices, justify or drop day-of-week, and inspect residual structure.
- Argue on the fitted outcome series, not monthly numerator sums; add the March-excluded fit (−12.5%) and the raw last-60/first-60 step (−18%).
