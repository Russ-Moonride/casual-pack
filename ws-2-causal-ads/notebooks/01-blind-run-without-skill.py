import marimo

__generated_with = "0.23.8"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 02 — From a blind run to a reusable skill

    One loop, four moves:

    **Run** (blind, no skills) → **Log** (append-only, live) → **Validate**
    (independent reviewer, hard checks) → **Distil a skill** (from the *validator*,
    not from the run's self-assessment).

    A second notebook then runs the same problem *with* the distilled skill and
    nails it.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The prompt

    The exact prompt handed to a fresh agent, with **no causal-analysis skill
    loaded** — and the logging instruction that produced the log further down:

    > Analyse the intervention in `data/daily_aggregates_intervention.csv` with
    > **CausalPy**. Treatment starts **2026-04-01** (`post` flips to 1). Estimate
    > the causal effect on the daily conversion rate.
    >
    > Work **blind**: do not load any causal-analysis skill or prior notebook.
    > Keep an **append-only log** (`logs.txt`), written *live* as you work — record
    > what you run, what the API does, every error, every dead end, every wrong
    > turn. The log is the raw material for improving the next run.

    Watch what the run does with this. It fumbles — and the fumble is the point.
    """)
    return


@app.cell(hide_code=True)
def _(df, mo, plt, treatment_time):
    _intro = mo.md("""
    ## The question in one picture

    Daily subscription conversion rate around the 2026-04-01 price hike. The first
    three months are omitted here because the subscriber pool is tiny early on, so a
    single conversion creates huge rate spikes that hide the intervention-scale
    movement.
    """)

    _overview = df.loc[df.index >= "2024-07-01"].copy()
    _rolling = _overview["conv_rate"].rolling(21, center=True, min_periods=7).mean()

    _fig, _ax = plt.subplots(figsize=(11, 4))
    _ax.plot(
        _overview.index,
        _overview["conv_rate"],
        lw=0.6,
        alpha=0.28,
        color="C0",
        label="daily conv_rate",
    )
    _ax.plot(
        _overview.index,
        _rolling,
        lw=2.2,
        color="C0",
        label="21-day rolling mean",
    )
    _ax.axvline(
        treatment_time,
        color="crimson",
        ls="--",
        lw=1.6,
        label="price hike: 2026-04-01",
    )
    _ax.set(
        title="Did the price hike reduce daily subscription conversion?",
        ylabel="conv_rate = conversions / subscriber_pool",
        xlabel="date",
    )
    _ax.grid(alpha=0.18)
    _ax.legend(loc="upper right", frameon=False)
    _fig.tight_layout()
    mo.vstack([_intro, _fig])
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
    display_cols = ["subscriber_pool", "signups", "conversions", "conv_rate", "post"]
    df = pd.read_csv(
        "data/daily_aggregates_intervention.csv",
        parse_dates=["date"],
        usecols=["date", *display_cols],
    ).set_index("date")
    treatment_time = pd.Timestamp("2026-04-01")
    print(f"rows={len(df):,}  span={df.index.min().date()}..{df.index.max().date()}")
    print(f"intervention={treatment_time.date()}  post flips 0 -> 1")
    print()
    print(df[display_cols].describe().round(3))
    df[display_cols].head()
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

    First try: outcome `conv_rate`, single linear time trend `t`.

    This is intentionally too simple. The only thing to read here is the **pre-period
    fit**. If the model barely explains the pre-period, its post-period effect text is
    not useful yet.
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
    r2 = round(float(its1.score), 4)
    print(f"pre-period fit (R²): {r2}")
    print("Stop here: the counterfactual explains almost none of the pre-period structure.")
    print("Reasoning: fix the pre-period fit before reading any treatment-effect text.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Attempt 2 — trim noisy early period + add day-of-week

    The run then diagnoses the poor pre-period fit:

    - Early days have a tiny remaining non-subscriber pool, so `conv_rate` is very noisy.
    - It drops the first three months as a rough variance fix.
    - It adds `C(dow)` as an ad-hoc calendar term.

    This improves R² from ~0.01 to ~0.12, and the estimated effect gets **more**
    negative (~−16%). That is the moment where the run starts rationalizing.
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
    its2.plot();
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The run's self-diagnosis

    This is the narrative the run shipped in its log:

    `conv_rate = conversions / subscriber_pool`, where `subscriber_pool` means users who could
    still become subscribers. The run reasoned:

    - Signups are flat across treatment -> the intervention did not change inflow.
    - `subscriber_pool` keeps growing while conversions stay roughly flat -> maybe the
      subscription rate falls mechanically because the remaining non-subscriber pool
      is harder to convert.
    - The pre-period trend might therefore be **subscriber-pool drift**, not a
      structural relationship safe to project.

    > *"The pre/post drop is largely a composition artifact of the remaining
    > non-subscriber pool, not a treatment effect. The intervention had little or no
    > real effect. I would not ship a negative number."*

    This is plausible. But notice what has **not** happened yet: no placebo-in-time,
    no real pre-period specification check, no independent reviewer. Hold that thought.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    # ⏸  BREAK → slides: what is *validation*, and why a run can't grade itself

    *(Then we come back to this notebook.)*
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    with open("notebooks/support/blind-run-log.txt") as _f:
        _logs = _f.read()
    mo.md(f"""## The append-only log the run emitted

    Written **live** during the work, exactly as instructed. It captures the real
    path — the API gotchas, the numbers, and the wrong turns. Notice it also
    contains the run's own *verdicts and "lessons"*. That is the problem: **a run
    that grades itself launders its mistakes into "insights"** (LLM self-review
    degrades quality — arXiv 2310.01798). The log is great for **facts**; its
    self-authored conclusions are not to be trusted. Judgment comes next, from
    someone with no stake in the result.

    ```text
    {_logs}
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Validation — hand the artifact to an independent reviewer

    We did **not** distil a skill from the log's self-assessment. Instead we ran
    the **`causal-critiquer`** skill as a *fresh sub-agent*: a new context that sees
    only the analysis artifact and hard-check outputs, not the chat history and not
    the simulator answer key.

    Its job is to run checks first — especially **placebo-in-time** — and then
    actively try to refute the headline. Its verdict is below, verbatim.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    with open("notebooks/support/validator-critique.md") as _cf:
        _crit = _cf.read()
    mo.md(_crit)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### What the validator caught that the run missed

    - The run's mechanism is **sign-backwards**: the pre-period `conv_rate` *rises*
      (`corr(conv_rate, subscriber_pool) = +0.33`), so "remaining pool gets harder -> rate
      mechanically falls" cannot explain the result.
    - The **placebo-in-time** is decisive against the drift story: fake interventions
      in the pre-period give ~0; the real date is an outlier (z ≈ −2.1). The trend is
      *not* manufacturing the effect.
    - The pre-period specification is also under-checked: Attempt 2 added day-of-week
      by habit, but did not test the seasonal basis or residual structure before
      reading the effect.
    - The effect is plausibly real, ≈ −12% to −18%. The run nearly shipped "no
      effect" — a false negative that would have hidden a decision-relevant drop.

    The load-bearing piece is the objective check. The reviewer does not win because
    it has nicer prose; it wins because it runs tests the first run skipped.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Stop before the answer key

    For the live story, we stop here. The validator has enough evidence to reject the
    "no effect / subscriber-pool drift" conclusion **without** looking at the hidden
    simulator answer key.

    The hidden ground truth is useful for us as instructors, but showing it here would
    make the validation look easier than it is in a real analysis.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    # ⏸  BREAK → slides: skills as distilled, reusable discipline

    *(Then back to the notebook for the payoff.)*
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Creating a new skill from everything we learned

    Now we distil — but from the **validator's findings**, not the run's
    self-lessons. Two distinct outputs, two distinct sources:

    - **Facts** from the log (API gotchas, what ran) -> the `causalpy-library` skill
      (tooling).
    - **Discipline** from the validator (the traps, ordered by what actually bit)
      -> the `quasi-experiment-analysis` skill (judgment), below.

    Everything dataset-specific is stripped (`conv_rate`, `subscriber_pool`, the price
    hike); what remains are the named traps and why each matters. The traps that
    bit here are now explicit: do not talk yourself out of a surprising result
    without a placebo; do not choose seasonal terms by habit; do not read an effect
    before the pre-period counterfactual has been checked.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    with open("skills/quasi-experiment-analysis/SKILL.md") as _sf:
        _skill = _sf.read()
    mo.md(f"## The distilled skill: `quasi-experiment-analysis`\n\n{_skill}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Next: the same problem, *with* the skill

    `notebooks/03-skill-guided-analysis.py` runs the identical dataset with this
    skill loaded. It identifies the seasonality instead of assuming day-of-week,
    guards out the anticipation window, gates on residual structure, and runs a
    placebo before accepting the effect.

    **The takeaway for students:** your mistakes are valuable training data only
    after an *independent* reviewer has separated real lessons from rationalizations.
    A run that grades itself ships its own blind spots. A validated run ships a skill.
    """)
    return


if __name__ == "__main__":
    app.run()
