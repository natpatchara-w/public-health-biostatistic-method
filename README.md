# SPH5002 Companion

This Quarto website is a concise companion to the statistical methods taught in SPH5002. It is organised by topic, with course requirements separated from optional theory and software extensions.

## Environment

The reference environment is:

- R 4.6.0, restored from `renv.lock`
- Quarto 1.9.37
- the Quarto binary bundled with RStudio at `/Applications/RStudio.app/Contents/Resources/app/quarto/bin/quarto` on macOS

The project configuration contains no machine-specific absolute paths. If the required Quarto version is available on `PATH`, replace the full RStudio path in the examples below with `quarto`.

## Set up

Restore the R environment from the project root:

```bash
R -e 'renv::restore()'
```

The website render does not require a Python environment. A Python virtual environment and `requirements-validation.txt` are only needed when running the optional independent statistical validation supplied with the project.

## Render and preview

Render the complete site:

```bash
/Applications/RStudio.app/Contents/Resources/app/quarto/bin/quarto render
```

Preview while editing:

```bash
/Applications/RStudio.app/Contents/Resources/app/quarto/bin/quarto preview
```

Generated files are written to `_site/`. The project deliberately executes pages afresh: Quarto freeze and execution caches are disabled.
Before each render, R checks the statistics and the saved software evidence,
including dataset fingerprints, so an outdated example cannot be published silently.

## Validate

See [VALIDATION.md](VALIDATION.md) for the pilot's tested versions, numerical results,
native Excel checks and browser review.

Run the independent statistics checks:

```bash
Rscript scripts/validate-statistics.R
```

Then check generated pages, links, fragments, citations, assets, and downloads:

```bash
python3 scripts/check-site.py _site
```

For a site hosted below a URL prefix, supply the deployed base URL. The check remains local and does not crawl external sites:

```bash
python3 scripts/check-site.py _site --base-url https://example.org/path/to/site/
```

## Repository layout

- `index.qmd`: home page and topic listing
- `topics/<topic>/index.qmd`: topic overview and lesson listing
- `topics/<topic>/*.qmd`: lesson pages
- `topics/<topic>/data/`: downloadable CSV data
- `topics/<topic>/downloads/`: downloadable workbooks
- `topics/<topic>/resources/`: other supporting files
- `topics/<topic>/_examples/`: software examples and saved validation evidence; QMD files here are not rendered
- `_templates/test.qmd`: starting point for a new test lesson; it is not rendered
- `references.bib`: shared bibliography
- `scripts/`: statistical and generated-site validation

See [CONTRIBUTING.md](CONTRIBUTING.md) before adding a lesson.

## Refresh example evidence and the workbook

The website builds with R and Quarto only. The committed CSV, Excel workbook and
saved software output are ordinary site resources. Neither Excel nor Python is
needed to publish a render.

To rerun the independent Python check:

```bash
python3 -m venv .venv-validation
.venv-validation/bin/python -m pip install -r requirements-validation.txt
.venv-validation/bin/python topics/hypothesis-testing/_examples/independent-t-test/example.py
Rscript scripts/validate-statistics.R --with-python
```

The `--with-python` flag runs the independent live comparison. Routine rendering
checks the saved Python evidence using R and does not execute Python.

The recorded result was checked in Microsoft Excel for Mac 16.113, including the
worksheet `T.TEST` function and Analysis ToolPak. The downloadable workbook was
recalculated, tested by changing and restoring an input, saved and reopened in
Excel. The provenance JSON records the source and output fingerprints. If the
data change, rerun all three software checks before replacing their saved output.

`scripts/build-workbook.mjs` is an optional workbook-authoring utility for a Codex
runtime providing `@oai/artifact-tool`; it is not a website dependency. Run
`Rscript scripts/export-summary.R` first. The builder deliberately writes to
`_build/independent-t-test-unverified.xlsx`. The authoring engine does not evaluate
`T.INV.2T` reliably, so `scripts/prepare-workbook.py` preserves the native Excel
formula and clears its unsupported cache. Open the staged file in Excel,
recalculate, verify B22 and B24, save and reopen before replacing the downloadable
workbook. Do not publish an unverified staged workbook.

`scripts/capture-excel.py` extracts cached values from a locally saved Excel
verification workbook without computing replacement results. Its docstring
describes the expected sheet layout. It updates the saved CSV outputs and the
Excel portion of the provenance record.

No GitHub Actions workflow or deployment configuration is included. The output
artifact for a future workflow is the complete `_site/` directory.
