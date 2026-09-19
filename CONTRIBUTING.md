# Contributing

## Add or revise a lesson

Create a lesson as `topics/<topic>/<lesson>.qmd`. Copy `_templates/test.qmd` and replace its placeholder title, description, data-type, and numeric order. Topic and lesson listings are generated from page metadata, so do not maintain navigation links by hand.

For a new topic, copy the existing topic's `index.qmd` and `_metadata.yml` into a new `topics/<topic>/` directory, then update the title, description, order and orientation text. Keep the listing local to that directory. The home page discovers topic index pages automatically. Publish a topic only when it has a completed lesson.

Every test lesson uses the same four sections:

1. **Overview** — define the question, data structure, and when the test applies.
2. **Application — required** — teach the hypotheses, assumptions, class calculation conventions, worked example, and reporting language.
3. **Theory — optional** — place deeper mathematical explanation here.
4. **Statistical applications — optional** — show Excel, R and Python workflows, verified output and interpretation.

Every optional section must display this exact notice:

> Optional — not covered or required for this course.

Use the `optional-content` callout class shown in the template. Use `required-content` for material students are expected to know.

## Teaching conventions

- Treat means and standard deviations as prior knowledge.
- Prefer appropriate summary statistics to re-deriving them from raw observations.
- For Welch's test, round degrees of freedom to the nearest whole number, with positive halves rounded up. Keep fractional degrees of freedom for optional software inference where appropriate.
- Use critical values in the required hand and spreadsheet exercises; p-values belong in optional material.
- Keep required material concise and move enrichment into the clearly labelled optional sections.
- State assumptions and conclusions in the context of the research question.

## Files and references

Put lesson downloads inside its topic directory:

- CSV files in `data/`
- Excel workbooks in `downloads/`
- other supporting files in `resources/`

Use relative links so the site works locally and when hosted at a subpath. Add bibliographic records to the shared `references.bib` and cite them with Quarto citation syntax. References used by a page will appear at the end of that page.

Directories whose names begin with an underscore are reserved for support material and are excluded from the render. Do not move `_templates/test.qmd` into the rendered topic tree.

## Check a contribution

From the project root, restore and render with the documented environment, then run:

```bash
Rscript scripts/validate-statistics.R
python3 scripts/check-site.py _site
```

Resolve broken local links, missing fragment targets, unresolved citation keys, and missing downloads before contributing the result.
