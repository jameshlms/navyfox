"""Generate performance comparison charts from benchmark_results.json.

Reads scripts/benchmark_results.json (produced by scripts/benchmark.py)
and writes four PNGs to docs/assets/:

  perf_write_time.png  — build + save time, NavyFox vs python-docx
  perf_read_time.png   — open + iterate time, NavyFox vs python-docx
  perf_speedup.png     — speedup factor for both operations
  perf_size.png        — installed package size comparison

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

NAVY_COLOR   = "#581aa8"
DOCX_COLOR   = "#1aa897"
WRITE_COLOR  = "#581aa8"   # NavyFox write
READ_COLOR   = "#9361d4"   # NavyFox read
GRID_STYLE   = {"linestyle": "--", "alpha": 0.4}


def _load_results() -> tuple[list[int], list[float], list[float], list[float], list[float]]:
    with open(RESULTS_PATH) as f:
        data = json.load(f)

    sizes = sorted(int(k) for k in data["write"]["python_docx"])

    write_docx  = [data["write"]["python_docx"][str(s)] * 1000 for s in sizes]
    write_navy  = [data["write"]["navyfox"][str(s)]      * 1000 for s in sizes]
    read_docx   = [data["read"]["python_docx"][str(s)]   * 1000 for s in sizes]
    read_navy   = [data["read"]["navyfox"][str(s)]        * 1000 for s in sizes]

    return sizes, write_docx, write_navy, read_docx, read_navy


def _time_chart(
    sizes: list[int],
    navy_times: list[float],
    docx_times: list[float],
    title: str,
    out_name: str,
) -> None:
    labels = [f"{s:,}" for s in sizes]
    x = np.arange(len(sizes))
    bar_w = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.bar(x - bar_w / 2, navy_times, bar_w, label="NavyFox",     color=NAVY_COLOR, zorder=3)
    ax.bar(x + bar_w / 2, docx_times, bar_w, label="python-docx", color=DOCX_COLOR, zorder=3)

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


def _speedup_chart(
    sizes: list[int],
    write_docx: list[float],
    write_navy: list[float],
    read_docx: list[float],
    read_navy: list[float],
) -> None:
    write_speedups = [d / n for d, n in zip(write_docx, write_navy)]
    read_speedups  = [d / n for d, n in zip(read_docx,  read_navy)]
    labels = [f"{s:,}" for s in sizes]
    x = np.arange(len(sizes))
    bar_w = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    bars_w = ax.bar(x - bar_w / 2, write_speedups, bar_w, label="Write", color=WRITE_COLOR, zorder=3)
    bars_r = ax.bar(x + bar_w / 2, read_speedups,  bar_w, label="Read",  color=READ_COLOR,  zorder=3)

    all_speedups = write_speedups + read_speedups
    top = max(all_speedups) * 1.12

    for bars, speedups in ((bars_w, write_speedups), (bars_r, read_speedups)):
        for bar, s in zip(bars, speedups):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + top * 0.01,
                f"{s:.1f}×",
                ha="center", va="bottom",
                fontsize=8, fontweight="bold", color="#333333",
            )

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Number of paragraphs")
    ax.set_ylabel("Speedup (× faster than python-docx)")
    ax.set_title("NavyFox speedup over python-docx")
    ax.axhline(1, color="black", linewidth=0.8, linestyle="--")
    ax.set_ylim(0, top)
    ax.legend(framealpha=0)
    ax.grid(axis="y", **GRID_STYLE)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    out = os.path.join(OUT_DIR, "perf_speedup.png")
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
    sizes, write_docx, write_navy, read_docx, read_navy = _load_results()

    _time_chart(
        sizes, write_navy, write_docx,
        title="Write benchmark: build + save — NavyFox vs python-docx",
        out_name="perf_write_time.png",
    )
    _time_chart(
        sizes, read_navy, read_docx,
        title="Read benchmark: open + iterate — NavyFox vs python-docx",
        out_name="perf_read_time.png",
    )
    _speedup_chart(sizes, write_docx, write_navy, read_docx, read_navy)
    _size_chart()


if __name__ == "__main__":
    main()
