#!/usr/bin/env python3
"""Reproduce the lesson's Welch two-sample t-test from its canonical CSV."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
from pathlib import Path

import numpy as np
import scipy
from scipy import stats


SCRIPT_FILE = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_FILE.parents[4]
INPUT_FILE = PROJECT_ROOT / "topics/hypothesis-testing/data/independent-t-test.csv"


def read_groups(path: Path) -> tuple[np.ndarray, np.ndarray]:
    groups: dict[str, list[float]] = {"A": [], "B": []}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["group", "sbp"]:
            raise ValueError("Expected CSV columns: group,sbp")
        for row in reader:
            group = row["group"]
            if group not in groups:
                raise ValueError(f"Unexpected group: {group}")
            groups[group].append(float(row["sbp"]))
    return np.asarray(groups["A"], dtype=float), np.asarray(groups["B"], dtype=float)


def format_number(value: float) -> str:
    return format(float(value), ".17g")


def r_version() -> str:
    result = subprocess.run(
        ["Rscript", "--vanilla", "-e", "cat(as.character(getRversion()))"],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write-provenance",
        type=Path,
        help="Write flat JSON provenance to this path after computing the result.",
    )
    args = parser.parse_args()

    a, b = read_groups(INPUT_FILE)
    n1, n2 = a.size, b.size
    m1, m2 = np.mean(a), np.mean(b)
    variance1, variance2 = np.var(a, ddof=1), np.var(b, ddof=1)
    s1, s2 = np.sqrt(variance1), np.sqrt(variance2)
    w1, w2 = variance1 / n1, variance2 / n2
    difference = m1 - m2
    se = np.sqrt(w1 + w2)
    t_stat = difference / se
    df = (w1 + w2) ** 2 / (w1**2 / (n1 - 1) + w2**2 / (n2 - 1))
    result = stats.ttest_ind(a, b, equal_var=False, alternative="two-sided")
    alpha = 0.05
    df_class = int(np.floor(df + 0.5))
    critical_class = stats.t.ppf(1 - alpha / 2, df_class)
    critical_full = stats.t.ppf(1 - alpha / 2, df)
    ci_lower = difference - critical_full * se
    ci_upper = difference + critical_full * se
    input_md5 = hashlib.md5(INPUT_FILE.read_bytes()).hexdigest()

    if not np.isclose(result.statistic, t_stat, rtol=0, atol=1e-14):
        raise RuntimeError("SciPy t statistic disagrees with the manual formula")
    if not np.isclose(result.df, df, rtol=0, atol=1e-14):
        raise RuntimeError("SciPy degrees of freedom disagree with the manual formula")

    lines = [
        ("input_md5", input_md5),
        ("group_A_n", str(n1)),
        ("group_A_mean", format_number(m1)),
        ("group_A_sd", format_number(s1)),
        ("group_B_n", str(n2)),
        ("group_B_mean", format_number(m2)),
        ("group_B_sd", format_number(s2)),
        ("mean_difference_A_minus_B", format_number(difference)),
        ("standard_error", format_number(se)),
        ("t_statistic", format_number(result.statistic)),
        ("degrees_of_freedom", format_number(result.df)),
        ("p_value_two_sided", format_number(result.pvalue)),
        ("ci_95_lower", format_number(ci_lower)),
        ("ci_95_upper", format_number(ci_upper)),
        ("df_class", str(df_class)),
        ("critical_t_df_class", format_number(critical_class)),
        ("critical_t_full_df", format_number(critical_full)),
        ("numpy_version", np.__version__),
        ("scipy_version", scipy.__version__),
        ("python_version", platform.python_version()),
    ]
    print("\n".join(f"{key}={value}" for key, value in lines))

    if args.write_provenance is not None:
        provenance = {
            "input_file": INPUT_FILE.relative_to(PROJECT_ROOT).as_posix(),
            "input_md5": input_md5,
            "r_version": r_version(),
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
        }
        args.write_provenance.parent.mkdir(parents=True, exist_ok=True)
        args.write_provenance.write_text(
            json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
