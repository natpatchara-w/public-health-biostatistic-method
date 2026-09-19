# Pilot verification record

Verified on 19 September 2026 (Asia/Singapore).

## Render and website

- A fresh full-project render completed with R 4.6.0 and Quarto 1.9.37. All three pages rendered successfully, with caches and freeze disabled.
- The pre-render statistical validation uses R only. Excel and Python are not needed for routine rendering; their saved evidence is checked against the canonical CSV.
- `renv::status()` reported a consistent project environment.
- `python3 scripts/check-site.py _site --base-url http://127.0.0.1:8765/companion-document/` passed for three HTML pages, including internal paths, fragments, citation keys and resources.
- The output was served beneath `/companion-document/`, simulating a GitHub Pages repository path. All 35 generated files returned HTTP 200 with content matching the local files. The downloadable CSV and XLSX matched their source files exactly.
- Desktop (1440 × 1000) and narrow-screen (390 × 844) layouts were inspected. All three pages fit the narrow viewport without document-wide horizontal overflow. Long equations and tables scroll within their own areas. Navigation, section anchors, search, equations and optional notices were checked in the browser.
- No temporary workbook locks, authoring inspection files, Python bytecode or lesson templates are included in the generated site.

## Statistical checks

`Rscript scripts/validate-statistics.R --with-python` passed using Python 3.14.6, NumPy 2.5.3 and SciPy 1.18.1. It compares hand formulas, R's `t.test()`, the independent live Python script, and saved native Excel results under matching conventions.

| Quantity | Verified value |
|---|---:|
| Group means | 123 and 135 |
| Sample SDs | 4.8989794856 and 9.7979589711 |
| Difference, A − B | −12 |
| Standard error | 3.8729833462 |
| Welch statistic | −3.0983866770 |
| Welch df | 10.2941176471 |
| Classroom df | 10 |
| Two-sided 5% classroom critical value | 2.2281388520 |
| Classroom decision | Reject H0 |
| Fractional-df two-sided p-value, optional | 0.01091500028 |
| Fractional-df 95% confidence interval, optional | (−20.59624051, −3.40375949) |

Additional checks cover unequal sample sizes, df 4.9208656 rounding to 5, positive half-up rounding, zero differences, and reversing the group order while retaining the two-sided decision.

## Native Excel and workbook

Microsoft Excel for Mac 16.113 was used for native recalculation and the Analysis ToolPak. Its worksheet `T.TEST(...,2,3)` matched the fractional-df result. The ToolPak reported df 10, critical value 2.2281388520, and the corresponding integer-df two-sided p-value. Saved output and input fingerprints are in `topics/hypothesis-testing/_examples/independent-t-test/provenance.json` and the adjacent CSV files.

The downloadable workbook was recalculated in Excel, checked by changing and restoring an input, saved and reopened without a repair prompt. Both sheets were visually inspected. A subsequent read-only check confirmed:

- **Practice** and **Worked solution** sheets with the supplied sample sizes, means and full-precision SDs;
- blank practice-answer cells and retained solution formulas;
- explicit `ROUND(B20,0)` before `T.INV.2T(B9,B21)`;
- correct cached intermediate results and final decision, with no Excel error cells.

Verified workbook SHA-256:

```text
da697f86931a7d37d8d8a75304b19baf9d1ec53533f080bebbccdcac159b886d
```

The optional workbook-authoring engine cannot reliably evaluate `T.INV.2T`. Its builder therefore creates a separately named unverified staging file; the README documents the native Excel verification required before replacing the download. This limitation does not affect the delivered, natively verified workbook or website rendering.

## Teaching and scope review

The required hand and spreadsheet exercises begin with supplied descriptive statistics, retain calculation precision, use nearest-integer Welch df and reach a critical-value decision. Theory and statistical applications display the course-exclusion notice. The topic contents page and reusable template support further lessons without duplicating navigation lists.

The deliverable is the source project and static `_site/` output. No GitHub Actions workflow was created, and no website was published. GitHub-hosted deployment itself was not tested.
