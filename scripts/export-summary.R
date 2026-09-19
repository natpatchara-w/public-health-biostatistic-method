#!/usr/bin/env Rscript

source(file.path("scripts", "lesson-data.R"), local = FALSE)

if (!requireNamespace("jsonlite", quietly = TRUE)) {
  stop("Install jsonlite before exporting the summary", call. = FALSE)
}

summary_values <- list(
  a = unname(a),
  b = unname(b),
  n1 = n1,
  n2 = n2,
  m1 = m1,
  m2 = m2,
  s1 = s1,
  s2 = s2,
  v1 = v1,
  v2 = v2,
  w1 = w1,
  w2 = w2,
  difference = difference,
  se = se,
  t_stat = t_stat,
  df = df,
  df_class = df_class,
  critical = critical,
  critical_full = critical_full,
  alpha = alpha,
  ci = unname(ci),
  source_md5 = unname(tools::md5sum(input_file))
)

dir.create("_build", recursive = TRUE, showWarnings = FALSE)
jsonlite::write_json(
  summary_values,
  path = file.path("_build", "summary.json"),
  auto_unbox = TRUE,
  pretty = TRUE,
  digits = 17
)
cat("Wrote _build/summary.json\n")
