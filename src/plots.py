import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "output"

"""
To mark the points of events on the currency plot.
"""
def _mark(ax, extremes: pd.DataFrame, code: str, events: dict[str, str], value_col: str, fmt: str):
    for event, color in events.items():
        row = extremes[(extremes["code"] == code) & (extremes["event"] == event)].iloc[0]
        ax.scatter(row["date"], row[value_col], color=color, zorder=3)
        ax.annotate(f"{row[value_col]:{fmt}}\n{row['date']:%Y-%m-%d}",
                    (row["date"], row[value_col]), textcoords="offset points",
                    xytext=(6, 8), fontsize=8, color=color)

def _load_gold(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["date"])

def _save(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)

"""
Plot the exchange rates of currencies over time
with marked minimum and maximum points.
"""
def plot_rate(df: pd.DataFrame, extremes: pd.DataFrame, code: str, path: Path) -> None:
    """Plot the exchange rate of a single currency over time with marked minimum and maximum points."""
    sub = df[df["code"] == code]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(sub["date"], sub["mid"], linewidth=1)
    _mark(ax, extremes, code, {"lowest_rate": "tab:red", "highest_rate": "tab:green"}, "mid", ".4f")
    ax.set_title(f"{code}/PLN: average rate NBP (min red, max green)")
    ax.set_ylabel("PLN")
    ax.grid(alpha=0.3)
    _save(fig, path)

"""
A function to plot normalized exchange rates of currencies over time, starting from a base value of 100.
This allows for a comparison of the relative changes in exchange rates across different currencies.
"""
def plot_normalized(df: pd.DataFrame, path: Path) -> None:
    pivot = df.pivot(index="date", columns="code", values="mid")
    normalized = pivot / pivot.iloc[0] * 100
    fig, ax = plt.subplots(figsize=(11, 5))
    normalized.plot(ax=ax, linewidth=1)
    ax.axhline(100, color="grey", linewidth=0.8, linestyle="--")
    ax.set_ylabel("Rate (start = 100)")
    ax.set_title("Dynamic of Rates Relative to PLN ")
    ax.grid(alpha=0.3)
    _save(fig, path)

"""
Daily percentage change of a single currency over time, with marked points for the biggest daily fall and rise
"""
def plot_daily_change(df: pd.DataFrame, extremes: pd.DataFrame, code: str, path: Path) -> None:
    sub = df[df["code"] == code]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(sub["date"], sub["pct_change"], linewidth=0.7)
    _mark(ax, extremes, code,
          {"biggest_daily_fall": "tab:red", "biggest_daily_rise": "tab:green"}, "pct_change", ".2f")
    ax.axhline(0, color="grey", linewidth=0.6)
    ax.set_title(f"{code}/PLN: daily change (biggest fall red, rise green)")
    ax.set_ylabel("daily change [%]")
    ax.grid(alpha=0.3)
    _save(fig, path)


"""
Function to generate all plots for the given DataFrame and extremes DataFrame, saving them to the specified output directory
"""
def plot_all(df: pd.DataFrame, extremes: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for code in df["code"].unique():
        plot_rate(df, extremes, code, out_dir / f"rate_{code}.png")
    plot_normalized(df, out_dir / "normalized.png")
    for code in df["code"].unique():
        plot_daily_change(df, extremes, code, out_dir / f"daily_change_{code}.png")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    gold = _load_gold(OUTPUT_DIR / "rates.csv")
    extremes = _load_gold(OUTPUT_DIR / "extremes.csv")
    plot_all(gold, extremes, OUTPUT_DIR/"plots")