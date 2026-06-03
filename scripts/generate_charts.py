"""Generate performance comparison charts from benchmark_results.json.

Reads scripts/benchmark_results.json (produced by scripts/benchmark.py)
and writes four PNGs to docs/assets/:

  perf_write_time.png  — build + save time, NavyFox vs python-docx
  perf_read_time.png   — open + iterate time, NavyFox vs python-docx
  perf_size.png        — installed package size comparison

Error bars are shown when benchmark_results.json contains stdev data
(produced by the current benchmark.py). Older result files without stdev
are loaded without error bars.

Usage:
    python scripts/generate_charts.py
"""

from __future__ import annotations

import importlib.util
import json
import os

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

RESULTS_PATH = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "assets")

NAVY_COLOR   = "#0C2340"   # NavyFox navy
DOCX_COLOR   = "#E8952A"   # python-docx amber
GRID_STYLE   = {"linestyle": "--", "alpha": 0.4}
ERR_KW       = {"ecolor": "#555555", "capsize": 3, "capthick": 1, "elinewidth": 1}


def _extract(entry: dict | float) -> tuple[float, float]:
    """Return (mean_ms, stdev_ms) from a JSON entry, handling both formats."""
    if isinstance(entry, dict):
        return entry["mean"] * 1000, entry.get("stdev", 0.0) * 1000
    return entry * 1000, 0.0


def _load_results() -> tuple[
    list[int],
    list[float], list[float], list[float], list[float],
    list[float], list[float], list[float], list[float],
]:
    with open(RESULTS_PATH) as f:
        data = json.load(f)

    sizes = sorted(int(k) for k in data["write"]["python_docx"])

    write_docx_m, write_docx_e = zip(*[_extract(data["write"]["python_docx"][str(s)]) for s in sizes])
    write_navy_m, write_navy_e = zip(*[_extract(data["write"]["navyfox"][str(s)])      for s in sizes])
    read_docx_m,  read_docx_e  = zip(*[_extract(data["read"]["python_docx"][str(s)])   for s in sizes])
    read_navy_m,  read_navy_e  = zip(*[_extract(data["read"]["navyfox"][str(s)])        for s in sizes])

    return (
        sizes,
        list(write_docx_m), list(write_navy_m), list(read_docx_m), list(read_navy_m),
        list(write_docx_e), list(write_navy_e), list(read_docx_e), list(read_navy_e),
    )


def _time_chart(
    sizes: list[int],
    navy_times: list[float],
    docx_times: list[float],
    navy_err: list[float],
    docx_err: list[float],
    title: str,
    out_name: str,
) -> None:
    labels = [f"{s:,}" for s in sizes]
    x = np.arange(len(sizes))
    bar_w = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    navy_err_plot = navy_err if any(v > 0 for v in navy_err) else None
    docx_err_plot = docx_err if any(v > 0 for v in docx_err) else None

    ax.bar(
        x - bar_w / 2, navy_times, bar_w,
        label="NavyFox", color=NAVY_COLOR, zorder=3,
        yerr=navy_err_plot, error_kw=ERR_KW,
    )
    ax.bar(
        x + bar_w / 2, docx_times, bar_w,
        label="python-docx", color=DOCX_COLOR, zorder=3,
        yerr=docx_err_plot, error_kw=ERR_KW,
    )

    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:.4g} ms"))
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Number of paragraphs")
    ax.set_ylabel("Time (ms, log scale)")
    ax.set_title(title)
    ax.legend(framealpha=0)
    ax.grid(axis="y", **GRID_STYLE)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    out = os.path.join(OUT_DIR, out_name)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Wrote {out}")



def _dir_size_mb(path: str) -> float:
    total = sum(
        os.path.getsize(os.path.join(dp, f))
        for dp, _, files in os.walk(path)
        for f in files
    )
    return total / 1024 / 1024


def _package_root(name: str) -> str:
    spec = importlib.util.find_spec(name)
    if spec and spec.origin:
        return os.path.dirname(spec.origin)
    raise ImportError(name)


def _size_chart() -> None:
    navyfox_mb = _dir_size_mb(_package_root("navyfox"))
    pydocx_mb  = _dir_size_mb(_package_root("docx"))

    print(f"  navyfox    : {navyfox_mb:.2f} MB")
    print(f"  python-docx: {pydocx_mb:.2f} MB")

    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    sizes_mb = [navyfox_mb, pydocx_mb]
    bars = ax.bar(
        ["NavyFox", "python-docx"],
        sizes_mb,
        color=[NAVY_COLOR, DOCX_COLOR],
        width=0.45,
        zorder=3,
    )
    top = max(sizes_mb) * 1.12
    for bar, size in zip(bars, sizes_mb):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + top * 0.01,
            f"{size:.2f} MB",
            ha="center", va="bottom",
            fontsize=10, fontweight="bold", color="#333333",
        )

    ax.set_ylabel("Installed size (MB)")
    ax.set_title("Installed package size")
    ax.set_ylim(0, top)
    ax.grid(axis="y", **GRID_STYLE)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    out = os.path.join(OUT_DIR, "perf_size.png")
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Wrote {out}")


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    (
        sizes,
        write_docx, write_navy, read_docx, read_navy,
        write_docx_e, write_navy_e, read_docx_e, read_navy_e,
    ) = _load_results()

    _time_chart(
        sizes, write_navy, write_docx, write_navy_e, write_docx_e,
        title="Write benchmark: build + save — NavyFox vs python-docx",
        out_name="perf_write_time.png",
    )
    _time_chart(
        sizes, read_navy, read_docx, read_navy_e, read_docx_e,
        title="Read benchmark: open + iterate — NavyFox vs python-docx",
        out_name="perf_read_time.png",
    )
    _size_chart()


if __name__ == "__main__":
    main()
