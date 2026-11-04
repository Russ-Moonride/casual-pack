# Interrupted Time Series — CausalPy cookbook

```python
import causalpy as cp
import numpy as np
import pandas as pd
```

## Minimal fit (sklearn backend)

```python
from sklearn.linear_model import LinearRegression as SkLR
LinearRegressionCP = cp.create_causalpy_compatible_class(SkLR)

# data needs: a DatetimeIndex, a column matching the outcome variable,
# and columns matching any covariate referenced in the formula.
df = daily.set_index("date").copy()  # daily must have a 'date' column
df["t"] = (df.index - df.index.min()).days
df["month"] = df.index.month

its = cp.InterruptedTimeSeries(
    data=df,
    treatment_time=pd.Timestamp("2026-04-01"),   # MUST be Timestamp here
    formula="conv_rate ~ 1 + t + np.sin(2*np.pi*month/12) + np.cos(2*np.pi*month/12)",
    model=LinearRegressionCP(),
)
print(its)   # prints the summary text + fitted coefficients
```

## Recommended formulas (start here)

The formula choice IS the counterfactual. Default to the simplest spec
that captures the structure visible in the pre-period.

| Data character | Starter formula |
|---|---|
| Daily, mild trend, no seasonality | `y ~ 1 + t` |
| Daily, mild trend, monthly seasonality | `y ~ 1 + t + np.sin(2*np.pi*month/12) + np.cos(2*np.pi*month/12)` |
| Daily, weekly + monthly seasonality | `y ~ 1 + t + C(dow) + np.sin(2*np.pi*month/12) + np.cos(2*np.pi*month/12)` |
| Weekly, yearly cycle | `y ~ 1 + t + np.sin(2*np.pi*week/52) + np.cos(2*np.pi*week/52)` |
| Rate where denominator drifts | `y ~ 1 + t + np.log(n_at_risk) + (seasonality)` |
| Non-linear trend (justify with residuals!) | `y ~ 1 + t + I(t**2) + (seasonality)` |

**Don't add complexity without a residual pattern that demands it.** A
quadratic term added "to be safe" usually over-fits and over-attributes
the intervention.

## Extracting the answer

```python
post_effect = np.asarray(its.post_impact).ravel()
ate = float(post_effect.mean())                # point estimate
cum_effect = np.asarray(its.post_impact_cumulative).ravel()[-1]  # total
```

For PyMC backend:

```python
ate_draws = its.post_impact.mean(dim="obs_ind").values.ravel()  # (n_samples,)
ate_mean = float(ate_draws.mean())

import arviz as az
ate_hdi = az.hdi(ate_draws, hdi_prob=0.94)
print(f"ATE = {ate_mean:+.5f}, 94% HDI [{ate_hdi[0]:+.5f}, {ate_hdi[1]:+.5f}]")
```

## Diagnostics

The built-in `.plot()` shows observed vs counterfactual but doesn't
provide residual diagnostics. Hand-build them:

```python
pre_pred  = np.asarray(its.pre_pred).ravel()
post_pred = np.asarray(its.post_pred).ravel()
fitted    = np.concatenate([pre_pred, post_pred])
resid     = df["y"].to_numpy() - fitted

# Plot residuals over time, by 90-day chunks, and a histogram.
# Look for: smooth drift (trend mis-specified), bumps near treatment
# (anticipation), heavy tails (outliers / shocks), DOW pattern (weekly
# structure not modeled).
```

For autocorrelation:

```python
from statsmodels.stats.stattools import durbin_watson
from statsmodels.graphics.tsaplots import plot_acf
print("Durbin-Watson (pre):", durbin_watson(resid[df["post"] == 0]))
plot_acf(resid[df["post"] == 0], lags=30)
```

Durbin-Watson far from 2 → autocorrelation. Standard errors / HDI are too
narrow; consider AR(1) errors or HAC corrections.

## Three-period (intervention with end-date)

```python
its3 = cp.InterruptedTimeSeries(
    data=df,
    treatment_time=pd.Timestamp("2026-04-01"),
    treatment_end_time=pd.Timestamp("2026-06-01"),   # NEW: end of intervention
    formula=...,
    model=...,
)
```

Use when the intervention is temporary; the post-intervention period
(after `treatment_end_time`) gets analyzed separately, surfacing
effect persistence vs decay.

## Common pitfalls

- **Treatment_time off by one**: `>=` comparison. Observations at exactly
  `treatment_time` are *post*-intervention.
- **Pre-period too short for seasonality**: with monthly Fourier and
  <12 months pre, the seasonal terms are weakly identified — the trend
  absorbs them, biasing the projection.
- **Outcome is a rate on a non-stationary denominator**: see SKILL.md's
  composition drift discussion. Aggregate ITS on `conv_rate` when
  `n_at_risk` grows / shrinks / shifts in composition is sensitive to
  spec choice; consider `~ np.log(n_at_risk) + ...` to absorb it.
- **Index has duplicates**: silent fit failure.

## Plot fallback (when `.plot()` works)

```python
fig, ax = its.plot()   # usually fine for ITS, breaks for DiD
```

If it errors, see [gotchas.md](gotchas.md) for the hand-built recipe.
