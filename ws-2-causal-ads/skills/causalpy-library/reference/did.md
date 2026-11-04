# Difference-in-Differences — CausalPy cookbook

```python
import causalpy as cp
import numpy as np
import pandas as pd
```

## Minimal fit

```python
# data needs: a time column, a group/treated indicator, a post indicator,
# AND a `unit` column (CausalPy uses it for plotting) — see gotcha below.
panel = daily.copy()
panel["treated"] = (panel["market"] == "US").astype(int)
panel["post"]    = (panel["date"] >= pd.Timestamp("2026-04-01")).astype(int)
panel["unit"]    = panel["market"]      # required, see gotcha #1
panel["group"]   = panel["treated"]     # required, see gotcha #2

from sklearn.linear_model import LinearRegression as SkLR
LinearRegressionCP = cp.create_causalpy_compatible_class(SkLR)

did = cp.DifferenceInDifferences(
    data=panel,
    formula="conv_rate ~ 1 + treated * post",     # `treated:post` is the ATE
    time_variable_name="date",
    group_variable_name="treated",                # the column with 0/1 treatment status
    post_treatment_variable_name="post",          # the column with 0/1 pre/post
    model=LinearRegressionCP(),
)
print(did)

ate = float(did.causal_impact)                    # the treated:post coefficient
```

## Extracting the answer

```python
# Point estimate (the interaction coefficient)
ate = float(did.causal_impact)

# Or pull from the printed coefficient table
did.print_coefficients()
```

## Gotchas specific to DiD

### Gotcha #1 — `unit` column is required even though it's not documented

```
DataException: Require a `unit` column to label unique units. This is
used for plotting purposes
```

Fix: add `panel["unit"] = panel["market"]` (or whatever your unit
identifier is) before constructing the estimator. The column is only used
by the plotting code, but the constructor validates its presence.

### Gotcha #2 — `did.plot()` crashes on recent matplotlib

```
TypeError: only length-1 arrays can be converted to Python scalars
```

Cause: CausalPy's internal `_ols_plot` calls `sns.lineplot(..., hue="group", ...)`
which fails if the column is named differently than expected; even when
fixed, it triggers a constrained-layout / annotate bug in matplotlib.

**Workaround #1**: add a `group` column duplicating your treatment indicator:

```python
panel["group"] = panel["treated"]
```

**Workaround #2** (when that's not enough — hand-built plot):

```python
import matplotlib.pyplot as plt

us_d = panel[panel["market"] == "US"].sort_values("date").copy()
ca_d = panel[panel["market"] == "CA"].sort_values("date").copy()
us_d["smoothed"] = us_d["conv_rate"].rolling(14, min_periods=3, center=True).mean()
ca_d["smoothed"] = ca_d["conv_rate"].rolling(14, min_periods=3, center=True).mean()

# Counterfactual: shift control trajectory up by the pre-period gap
pre_gap = (us_d.loc[us_d["post"] == 0, "conv_rate"].mean()
           - ca_d.loc[ca_d["post"] == 0, "conv_rate"].mean())
us_d["counterfactual"] = ca_d["smoothed"].to_numpy() + pre_gap

fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(us_d["date"], us_d["smoothed"],    color="tab:blue",   lw=2, label="treated (observed)")
ax.plot(ca_d["date"], ca_d["smoothed"],    color="tab:orange", lw=2, label="control")
ax.plot(us_d["date"], us_d["counterfactual"], color="tab:blue", lw=2, ls="--",
        label="treated counterfactual (control + pre-gap)")
ax.axvline(pd.Timestamp("2026-04-01"), color="red", ls="--", alpha=0.6, label="Intervention")
ax.fill_between(us_d.loc[us_d["post"] == 1, "date"],
                us_d.loc[us_d["post"] == 1, "smoothed"],
                us_d.loc[us_d["post"] == 1, "counterfactual"],
                alpha=0.2, color="red", label=f"Estimated effect ({did.causal_impact:+.5f})")
ax.set_title("DiD: observed vs counterfactual (from control)")
ax.legend(loc="best"); ax.grid(alpha=0.3)
fig.autofmt_xdate(); plt.tight_layout()
fig
```

### Gotcha #3 — Parallel-trends check is on you

CausalPy doesn't automatically test or visualize parallel trends. Add an
event-study cell that fits leads in the pre-period and inspects them.
See the `causal-critiquer` checklist `did.md` for the framework.

## Recommended formulas

| Setup | Formula |
|---|---|
| Standard DiD | `y ~ 1 + treated * post` |
| With time-varying controls | `y ~ 1 + treated * post + x1 + x2` |
| Event-study (parallel-trends check) | `y ~ 1 + C(time, Treatment(reference=t0)) * treated` |
| With unit fixed effects | `y ~ 1 + C(unit) + treated * post` (cluster SEs by unit) |

## Standard errors

CausalPy's default LR doesn't cluster standard errors. With panel data
this is wrong (SEs are too narrow). For honest inference either:

- Use the PyMC backend and report HDIs (which capture posterior variance)
- Bootstrap at the unit level and re-fit
- Switch to a statsmodels OLS fit with clustered SEs (outside CausalPy)
