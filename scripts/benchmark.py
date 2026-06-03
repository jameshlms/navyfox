"""Benchmark NavyFox vs python-docx: write and read operations.

Write workload — build and save a document with N paragraphs and N/10 table rows.
Read workload  — open an existing document and iterate all paragraph text and table cells.

Reference files for the read benchmark are created once with python-docx so both
libraries read from identically-structured files.

Results are written to scripts/benchmark_results.json for use by generate_charts.py.

Usage:
    python scripts/benchmark.py
"""

from __future__ import annotations

import json
import os
import statistics
import tempfile
import time

DOCUMENT_SIZES = [100, 500, 1_000, 5_000, 10_000]


def _repeats(n: int) -> int:
    if n >= 5_000:
        return 2
    if n >= 1_000:
        return 3
    return 5


def _temp_path(suffix: str) -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return path


# ---------------------------------------------------------------------------
# Write benchmarks — build + save
# ---------------------------------------------------------------------------

def bench_write_python_docx(n: int) -> float:
    import docx

    times = []
    for _ in range(_repeats(n)):
        path = _temp_path(".docx")
        try:
            t0 = time.perf_counter()
            doc = docx.Document()
            for i in range(n):
                doc.add_paragraph(f"Paragraph {i}: The quick brown fox jumps over the lazy dog.")
            n_rows = max(1, n // 10)
            table = doc.add_table(rows=n_rows, cols=3)
            for r in range(n_rows):
                table.cell(r, 0).text = f"Row {r}"
                table.cell(r, 1).text = "Value A"
                table.cell(r, 2).text = "Value B"
            doc.save(path)
            times.append(time.perf_counter() - t0)
        finally:
            os.unlink(path)
    return statistics.mean(times)


def bench_write_navyfox(n: int) -> float:
    from navyfox import Document

    times = []
    for _ in range(_repeats(n)):
        path = _temp_path(".docx")
        try:
            t0 = time.perf_counter()
            with Document() as doc:
                for i in range(n):
                    doc.add_paragraph(
                        f"Paragraph {i}: The quick brown fox jumps over the lazy dog."
                    )
                n_rows = max(1, n // 10)
                table = doc.add_table(rows=n_rows, cols=3)
                for r in range(n_rows):
                    table[r, 0].text = f"Row {r}"
                    table[r, 1].text = "Value A"
                    table[r, 2].text = "Value B"
                doc.save(path)
            times.append(time.perf_counter() - t0)
        finally:
            os.unlink(path)
    return statistics.mean(times)


# ---------------------------------------------------------------------------
# Read benchmarks — open + iterate all content
# ---------------------------------------------------------------------------

def _create_reference_file(n: int) -> str:
    """Build a reference .docx with python-docx; both libraries will read this file."""
    import docx

    path = _temp_path(".docx")
    doc = docx.Document()
    for i in range(n):
        doc.add_paragraph(f"Paragraph {i}: The quick brown fox jumps over the lazy dog.")
    n_rows = max(1, n // 10)
    table = doc.add_table(rows=n_rows, cols=3)
    for r in range(n_rows):
        table.cell(r, 0).text = f"Row {r}"
        table.cell(r, 1).text = "Value A"
        table.cell(r, 2).text = "Value B"
    doc.save(path)
    return path


def bench_read_python_docx(path: str, n: int) -> float:
    import docx

    times = []
    for _ in range(_repeats(n)):
        t0 = time.perf_counter()
        doc = docx.Document(path)
        for p in doc.paragraphs:
            _ = p.text
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    _ = cell.text
        times.append(time.perf_counter() - t0)
    return statistics.mean(times)


def bench_read_navyfox(path: str, n: int) -> float:
    from navyfox import Document

    times = []
    for _ in range(_repeats(n)):
        t0 = time.perf_counter()
        with Document.open(path) as doc:
            for p in doc.paragraphs:
                _ = p.text
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        _ = cell.text
        times.append(time.perf_counter() - t0)
    return statistics.mean(times)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    results: dict[str, dict[str, dict[str, float]]] = {
        "write": {"python_docx": {}, "navyfox": {}},
        "read":  {"python_docx": {}, "navyfox": {}},
    }

    print("=== Write benchmark (build + save) ===")
    for n in DOCUMENT_SIZES:
        print(f"  python-docx  n={n:>6} ...", end=" ", flush=True)
        t = bench_write_python_docx(n)
        results["write"]["python_docx"][str(n)] = t
        print(f"{t * 1000:.1f} ms")

        print(f"  navyfox      n={n:>6} ...", end=" ", flush=True)
        t = bench_write_navyfox(n)
        results["write"]["navyfox"][str(n)] = t
        print(f"{t * 1000:.1f} ms")

    print()
    print("=== Read benchmark (open + iterate all content) ===")
    for n in DOCUMENT_SIZES:
        print(f"  creating reference file n={n:>6} ...", end=" ", flush=True)
        ref = _create_reference_file(n)
        print("done")

        print(f"  python-docx  n={n:>6} ...", end=" ", flush=True)
        t = bench_read_python_docx(ref, n)
        results["read"]["python_docx"][str(n)] = t
        print(f"{t * 1000:.1f} ms")

        print(f"  navyfox      n={n:>6} ...", end=" ", flush=True)
        t = bench_read_navyfox(ref, n)
        results["read"]["navyfox"][str(n)] = t
        print(f"{t * 1000:.1f} ms")

        os.unlink(ref)

    out = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {out}")
    print("Run scripts/generate_charts.py to produce the performance charts.")


if __name__ == "__main__":
    main()
