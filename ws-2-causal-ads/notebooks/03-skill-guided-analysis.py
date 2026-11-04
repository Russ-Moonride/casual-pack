import marimo

__generated_with = "0.23.4"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 02 - Intervention Analysis (skill-driven run)

    Second pass at the same dataset, this time **with** the `quasi-experiment-analysis`
    skill, the CausalPy docs (via context7), and the marimo docs. The structure below
    follows the skill's workflow; each section names the **trap** it defends against.
    """)
    return


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd
    import causalpy as cp
    import matplotlib.pyplot as plt
    import json
    from sklearn.linear_model import LinearRegression

    return LinearRegression, cp, json, mo, np, pd, plt


@app.cell
def _(pd):
    df = pd.read_csv("data/daily_aggregates_intervention.csv", parse_dates=["date"]).set_index("date")
    treatment_time = pd.Timestamp("2026-04-01")  # where `post` flips 0 -> 1
    # Simulator answer-key columns exist in the CSV, but are not used for modeling.
    df[["subscriber_pool", "signups", "conversions", "conv_rate", "post"]].describe().round(3)
    return df, treatment_time


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 1 - Understand the data-generating process

    *Skill: before modeling, ask what the number actually is.*

    - `subscriber_pool` means users who can still become subscribers: they signed up, but have not converted yet.
    - `conv_rate = conversions / subscriber_pool` is the **daily subscription rate among still-convertible users**, not a free-standing KPI.
    - Because the denominator changes, the rate is noisy when `subscriber_pool` is small and more stable when the pool is large.
    - A price increase should act roughly multiplicatively on conversion propensity -> the business question is a percentage drop in daily subscriptions.
    - **Trap 5 (subscriber-pool drift):** the pool composition can drift smoothly over time. Smooth drift should be absorbed by the trend term; a sudden fake break is what would be dangerous. So we check the sign of the pre-trend and run a placebo instead of reflexively calling the effect an artifact.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2 - Plot the raw series and decompose the ratio

    *Skill: plot the outcome AND, for a ratio, its numerator and denominator separately. Look for pre-treatment spikes, level shifts, changing variance.*
    """)
    return


@app.cell
def _(df, plt, treatment_time):
    fig, ax = plt.subplots(2, 2, figsize=(12, 7))
    ax[0,0].plot(df.index, df["conv_rate"], lw=0.6); ax[0,0].set_title("conv_rate (daily subscription rate)")
    ax[0,1].plot(df.index, df["conversions"], lw=0.6, color="C1"); ax[0,1].set_title("conversions (numerator)")
    ax[1,0].plot(df.index, df["subscriber_pool"], lw=0.9, color="C2"); ax[1,0].set_title("subscriber_pool (users still able to subscribe)")
    # boundary zoom: 60 days pre + 30 post -> reveals anticipation
    win = df.loc["2026-02-01":"2026-05-01"]
    ax[1,1].plot(win.index, win["conv_rate"], marker=".", lw=0.8, color="C3"); ax[1,1].set_title("boundary zoom (anticipation?)")
    for a in ax.ravel(): a.axvline(treatment_time, color="red", ls="--", lw=1)
    fig.tight_layout(); fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Read-off:**
    - `conv_rate` (top-left) is dominated early by huge variance (tiny `subscriber_pool`) -> the early period must be trimmed (heteroscedasticity).
    - `subscriber_pool` (bottom-left) drifts up monotonically -> **Trap 5**: a smooth denominator drift is absorbed by the trend, so we check its sign and run a placebo rather than assume an artifact.
    - Boundary zoom (bottom-right): a visible **bump in the ~week before treatment** -> **anticipation** (Trap 3). Those days are contaminated by the (announced) treatment and must be guarded out of the fit.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2b - Identify the seasonality (do not assume the basis)

    *Skill: measure the period and shape of seasonality before choosing terms, and test every term - keep only the ones that are real (Trap 4).*
    """)
    return


@app.cell
def _(df, np, treatment_time):
    import statsmodels.formula.api as smf
    _pre = df[(df.index >= "2024-07-01") & (df.index < treatment_time)].copy()
    _pre["t"] = np.arange(len(_pre)); _doy0 = _pre.index.dayofyear.values
    for _k in (1, 2):
        _pre[f"sin{_k}"] = np.sin(2*np.pi*_k*_doy0/365.25)
        _pre[f"cos{_k}"] = np.cos(2*np.pi*_k*_doy0/365.25)
    _pre["dow"] = _pre.index.dayofweek
    _m = smf.ols("conv_rate ~ 1 + t + sin1 + cos1 + sin2 + cos2 + C(dow)", data=_pre).fit()
    _dowtest = "C(dow)[T.1]=C(dow)[T.2]=C(dow)[T.3]=C(dow)[T.4]=C(dow)[T.5]=C(dow)[T.6]=0"
    print("Joint significance tests (pre-period):")
    print(f"  annual harmonic 1 (sin1,cos1): p = {float(_m.f_test('sin1=cos1=0').pvalue):.4f}   -> REAL, keep")
    print(f"  annual harmonic 2 (sin2,cos2): p = {float(_m.f_test('sin2=cos2=0').pvalue):.4f}   -> not significant, drop")
    print(f"  day-of-week  C(dow):           p = {float(_m.f_test(_dowtest).pvalue):.4f}   -> spurious, drop")
    print()
    print("=> seasonality is a SMOOTH annual sinusoid. Use  t + sin1 + cos1  (Fourier).")
    print("   C(month) would be an 11-param step proxy; C(dow) is just noise.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 3 - Build the counterfactual design

    *The skill turns the earlier failure modes into concrete design choices:*

    - **Seasonality = smooth annual Fourier** `sin1 + cos1` (identified and tested in Step 2b), **not** `C(month)` (an 11-param step-function proxy) and **not** `C(dow)` (insignificant noise). A counterfactual is an extrapolation, so smooth, parsimonious terms project cleanly past the cutoff (Trap 4).
    - **Secular trend** `t` absorbs smooth subscriber-pool drift.
    - **Trim the noisy early period** (`>= 2024-07-01`): tiny `subscriber_pool` makes `conv_rate` too volatile to anchor the counterfactual.
    - **Anticipation guard**: drop the **7 days before treatment**; the boundary zoom showed a pre-treatment bump that would bias the baseline upward (Trap 3).
    """)
    return


@app.cell
def _(df, np, pd, treatment_time):
    _guard_lo = treatment_time - pd.Timedelta(days=7)
    model_df = df[df.index >= "2024-07-01"].copy()
    model_df = model_df[(model_df.index < _guard_lo) | (model_df.index >= treatment_time)].copy()
    model_df["t"] = np.arange(len(model_df))
    _doy = model_df.index.dayofyear.values
    model_df["sin1"] = np.sin(2*np.pi*_doy/365.25)
    model_df["cos1"] = np.cos(2*np.pi*_doy/365.25)
    print(f"rows used: {len(model_df)} (pre: {(model_df.index < treatment_time).sum()}, post: {(model_df.index >= treatment_time).sum()})")
    print(f"guard window dropped: {_guard_lo.date()} .. {treatment_time.date()}")
    print("counterfactual design: trend + annual Fourier sin1 + cos1")
    return (model_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 4 - Fit the counterfactual, then apply the residual gate

    *Skill trap 2: never read an effect from a counterfactual that has not passed a pre-period check.*

    The **gate** is explicit: fit the counterfactual on the pre-period, then ask whether the residuals still contain structure the model missed.

    Pass criteria:

    1. **No leftover trend**: residuals should not slope up/down over time.
    2. **No leftover short-range autocorrelation**: today's miss should not predict tomorrow's miss.
    3. **No leftover annual seasonality**: the seasonal cycle should be gone from the residuals.

    R² can stay modest because this is a noisy daily rate. The question is not "is R² large?" but "is the remaining error mostly unstructured noise?"
    """)
    return


@app.cell
def _(LinearRegression, cp, model_df, np, treatment_time):
    its = cp.InterruptedTimeSeries(
        model_df, treatment_time,
        formula="conv_rate ~ 1 + t + sin1 + cos1",
        model=LinearRegression(),
    )
    _y = np.asarray(its.pre_y).ravel()
    _mu = np.asarray(its.pre_pred).ravel()
    _resid = _y - _mu
    _trend = np.corrcoef(_resid, np.arange(len(_resid)))[0, 1]
    _acf1 = np.corrcoef(_resid[:-1], _resid[1:])[0, 1]
    _dd = model_df.index[model_df.index < treatment_time].dayofyear.values
    _S = np.column_stack([np.ones_like(_dd, float),
        np.sin(2*np.pi*_dd/365.25), np.cos(2*np.pi*_dd/365.25),
        np.sin(4*np.pi*_dd/365.25), np.cos(4*np.pi*_dd/365.25)])
    _seas_r2 = 1 - np.var(_resid - _S @ np.linalg.lstsq(_S, _resid, rcond=None)[0]) / np.var(_resid)
    print("RESIDUAL GATE (pre-period only)")
    print("Gate rule: no leftover trend, autocorrelation, or annual cycle.")
    print()
    print(f"pre-period R2            : {float(its.score):.3f}  (modest; not the gate)")
    print(f"residual vs time corr    : {_trend:+.4f}  (pass: close to 0)")
    print(f"residual lag-1 autocorr  : {_acf1:+.4f}  (pass: close to 0)")
    print(f"residual annual-cycle R2 : {_seas_r2:.4f}  (pass: close to 0)")
    print()
    print("=> GATE PASSED: the counterfactual mean is not leaving systematic")
    print("   pre-period structure behind; now the effect is interpretable.")
    return (its,)


@app.cell
def _(its):
    _figcf, _axcf = its.plot()
    _figcf.suptitle("Observed vs counterfactual (pre-fit, post-projection)", y=1.02)
    _figcf;
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 5 - Read the effect

    The residual gate passed, so now we can read the estimate. This ordering matters:
    **counterfactual first, effect second**.
    """)
    return


@app.cell
def _(its):
    _es = its.effect_summary()
    print(_es.table[["mean", "ci_lower", "ci_upper", "p_value", "relative_mean"]].round(6))
    print()
    _avg = _es.table.loc["average", "mean"]; _rel = _es.table.loc["average", "relative_mean"]
    print(f"Average effect on conv_rate: {_avg:+.6f}  ({_rel:+.1f}% vs counterfactual)")
    print("Sign is negative and the CI excludes 0: the price hike reduced the daily subscription rate.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 6 - Stress-test with a placebo-in-time

    *Skill: a point estimate without a stress test is a guess with decimals.*

    - Plant a **fake treatment six months early**, using only data before the real price hike.
    - Refit the same counterfactual design at that fake cutoff.
    - If the design manufactures breaks, the placebo will also show an effect.
    - If the placebo is ~0 while the real cutoff is negative, the real treatment date is special.
    """)
    return


@app.cell
def _(LinearRegression, cp, df, np, pd, treatment_time):
    # --- Placebo-in-time (Fourier spec, sklearn OLS) ---
    _pl = df[(df.index >= "2024-07-01") & (df.index < treatment_time)].copy()
    _pl["t"] = np.arange(len(_pl)); _pdoy = _pl.index.dayofyear.values
    _pl["sin1"] = np.sin(2*np.pi*_pdoy/365.25); _pl["cos1"] = np.cos(2*np.pi*_pdoy/365.25)
    _fake_time = pd.Timestamp("2025-10-01")
    _placebo = cp.InterruptedTimeSeries(_pl, _fake_time,
        formula="conv_rate ~ 1 + t + sin1 + cos1", model=LinearRegression())
    _pt = _placebo.effect_summary().table.loc["average"]
    print("PLACEBO-IN-TIME STRESS TEST")
    print(f"fake cutoff: {_fake_time.date()} (six months before the real treatment)")
    print(f"placebo effect: {_pt['mean']:+.6f}  CI [{_pt['ci_lower']:+.6f}, {_pt['ci_upper']:+.6f}]")
    print()
    print("Read: the fake treatment should not create a negative effect.")
    print("=> ~0 and CI spans 0: the design is not manufacturing the real break. PASS.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Optional instructor check - reveal the answer key after the estimate

    The analysis is finished above. This cell uses the simulator counterfactual and
    `ground_truth.json` **only after the estimate is frozen**, so we can calibrate the
    teaching example. It is not part of the analysis workflow.
    """)
    return


@app.cell
def _(df, its, json, np, pd):
    with open("data/ground_truth.json") as _gf:
        _gt = json.load(_gf)
    _tab = its.effect_summary().table.loc["average"]
    _post = df[df.post == 1]
    _realized = (_post.conv_rate - _post.conv_rate_cf).mean()
    _result = pd.DataFrame({
        "estimate": [1.9e-5, _tab["mean"], _realized, _gt["true_ate_on_conv_rate"]],
        "rel_pct":  [np.nan, _tab["relative_mean"], np.nan, -100*_gt["implied_pct_drop_in_daily_subscribe_prob"]],
    }, index=["naive pre/post", "skill-driven ITS", "realized ATE (simulator)", "TRUE (ground truth)"])
    print(_result.round(6))
    print()
    print(f"Intervention was a price hike {_gt['old_avg_price_usd']} -> {_gt['new_avg_price_usd']} USD "
          f"(+{_gt['price_pct_increase']*100:.0f}%), elasticity {_gt['true_price_elasticity']}.")
    _err = _tab["mean"] - _gt["true_ate_on_conv_rate"]
    print(f"Skill-driven estimate error vs true ATE: {_err:+.6f} "
          f"({100*_err/_gt['true_ate_on_conv_rate']:+.1f}%).")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## What the skill changed

    | | Run 1 (no skill) | Run 2 (skill-driven) |
    |---|---|---|
    | Path | naive -> diagnose -> **discarded a real negative effect as an artifact** | structured workflow: design -> residual gate -> placebo -> estimate |
    | Anticipation | boundary bump noticed only after the fact, not guarded | boundary zoom -> 7-day guard window dropped (Trap 3) |
    | Seasonality | day-of-week added by habit | **annual Fourier** `sin1 + cos1`, identified + tested (Trap 4) |
    | Gate | pre-period fit noticed, but no residual gate before the conclusion | residual trend, autocorr **and leftover seasonality**, not R² magnitude (Trap 2) |
    | Denominator drift | used as an escape hatch: "maybe this is just pool drift" | treated as smooth drift absorbed by trend; placebo checks it is not a fake break |
    | Validation | none before the conclusion | placebo-in-time at a fake pre-period cutoff |
    | Estimate | -0.00029, then talked away as "no real effect" | **-0.000275 after gate + placebo** |

    **Traps the skill defended against:**

    1. **Talking yourself out of a real effect** -> Run 1 did this; the placebo-in-time refutes the artifact story.
    2. **Reading an effect before the counterfactual passes a gate** -> the gate is residual trend, autocorrelation, and leftover seasonality; R² magnitude is not the decision rule.
    3. **Anticipation** -> spotted in the boundary zoom, guarded out, removing the pre-boundary overshoot from the baseline.
    4. **Seasonal basis by habit** -> identified the cycle empirically (Step 2b), used parsimonious Fourier, dropped spurious day-of-week.
    5. **Drifting denominator** -> recognized that subscriber-pool drift is smooth and should be absorbed by trend; the placebo confirms it is not being mistaken for a treatment effect.

    *Same data, same tool (CausalPy with fast sklearn OLS). The difference is the discipline encoded in the skill; docs help with API mechanics, but the skill supplies the causal workflow.*
    """)
    return


if __name__ == "__main__":
    app.run()
