import marimo

__generated_with = "0.23.4"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 02 — Intervention Analysis (blind run, awaiting review)

    Quasi-experimental analysis of the conversion intervention using **CausalPy**.
    Outcome: daily conversion rate. Treatment starts **2026-04-01** (`post`=1).

    This notebook is the work product of a *blind* run (no causal-analysis skill
    loaded). It is being handed to a reviewer **before** any ground truth is
    revealed. The `*_cf` columns in the data file are a simulated counterfactual
    and are deliberately **not** used anywhere below.
    """)
    return


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import causalpy as cp
    import matplotlib.pyplot as plt
    from sklearn.linear_model import LinearRegression

    return LinearRegression, cp, mo, np, pd, plt


@app.cell
def _(pd):
    df = pd.read_csv("data/daily_aggregates_intervention.csv", parse_dates=["date"])
    df = df.set_index("date")
    # treatment indicator is `post`; *_cf are simulated counterfactuals -> NOT used as inputs
    treatment_time = pd.Timestamp("2026-04-01")
    print(df.shape)
    print(df[["subscriber_pool", "signups", "conversions", "conv_rate", "post"]].describe().round(3))
    df.head()
    return df, treatment_time


@app.cell
def _(df, plt, treatment_time):
    fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    axes[0].plot(df.index, df["conv_rate"], lw=0.6)
    axes[0].axvline(treatment_time, color="red", ls="--"); axes[0].set_ylabel("conv_rate")
    axes[1].plot(df.index, df["conversions"], lw=0.6, color="C1")
    axes[1].axvline(treatment_time, color="red", ls="--"); axes[1].set_ylabel("conversions")
    axes[2].plot(df.index, df["subscriber_pool"], lw=0.8, color="C2")
    axes[2].axvline(treatment_time, color="red", ls="--"); axes[2].set_ylabel("subscriber_pool")
    fig.suptitle("Raw series with treatment line (2026-04-01)")
    fig.tight_layout()
    fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Attempt 1 — naive linear ITS

    Outcome `conv_rate`, single linear time trend `t`.
    """)
    return


@app.cell
def _(LinearRegression, cp, df, np, treatment_time):
    d = df.copy()
    d["t"] = np.arange(len(d))
    its1 = cp.InterruptedTimeSeries(
        d, treatment_time,
        formula="conv_rate ~ 1 + t",
        model=LinearRegression(),
    )
    print("pre-period fit (R2):", round(float(its1.score), 4))
    print(its1.effect_summary().text)
    return (its1,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Attempt 2 — trim noisy early period + day-of-week

    Drop first 3 months (tiny `subscriber_pool` => huge rate variance), add `C(dow)`.
    R2 improves 0.01 -> 0.12, and the effect gets **more** negative (~-16%).
    """)
    return


@app.cell
def _(LinearRegression, cp, df, np, treatment_time):
    d2 = df[df.index >= "2024-07-01"].copy()
    d2["t"] = np.arange(len(d2))
    d2["dow"] = d2.index.dayofweek
    its2 = cp.InterruptedTimeSeries(
        d2, treatment_time,
        formula="conv_rate ~ 1 + t + C(dow)",
        model=LinearRegression(),
    )
    print("pre-period R2:", round(float(its2.score), 4))
    print(its2.effect_summary().table[["mean", "ci_lower", "ci_upper", "relative_mean"]].round(5))
    its2.plot()
    return (its2,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Diagnosis — the negative effect looks like an artifact

    `conv_rate = conversions / subscriber_pool` is a daily subscription rate among users still able to subscribe:

    - Signups are flat across treatment (~44/day pre vs post) -> intervention did **not** change inflow.
    - Monthly conversions: Dec 882, Jan 918, Feb 924, **Mar 1126 (pre-treatment spike)**, Apr 883, ... Sep 974.
      Post conversions (883->974) sit on the Dec-Feb baseline; the "drop" is relative to the March spike.
    - `subscriber_pool` keeps growing (19.1k -> 21.0k post) while conversions stay ~flat => `conv_rate` falls
      **mechanically** (pool aging / dynamic selection: survivors are harder to convert).

    => The pre-period `conv_rate` trend looks like a **composition artifact**, not a structural
    relationship that is safe to project. That would violate the ITS stationarity assumption, and a
    Gaussian linear model on a heteroscedastic binomial rate makes it worse.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Current bottom line (for review)

    The pre/post drop in `conv_rate` is **largely a composition artifact** of the aging subscriber
    pool, not a treatment effect. Leaning toward: **the intervention had little or no real effect
    on conversion** — I would not ship a negative number off this analysis. The "more negative with
    better fit" behaviour in Attempt 2 reinforces that the trend term is chasing a mechanical
    denominator drift rather than a behavioural change.

    **Reviewer: is this conclusion sound? What, if anything, is wrong with it?**
    """)
    return


if __name__ == "__main__":
    app.run()
