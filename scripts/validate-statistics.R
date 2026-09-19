#!/usr/bin/env Rscript

source(file.path("scripts", "lesson-data.R"), local = FALSE)

assert_close <- function(actual, expected, tolerance = 1e-12, label = "value") {
  if (length(actual) != length(expected) ||
      any(!is.finite(actual)) ||
      !isTRUE(all.equal(as.numeric(actual), as.numeric(expected),
                        tolerance = tolerance, check.attributes = FALSE))) {
    stop(sprintf("%s mismatch: got %s; expected %s", label,
                 paste(actual, collapse = ", "),
                 paste(expected, collapse = ", ")), call. = FALSE)
  }
}

welch_manual <- function(x, y, alpha = 0.05) {
  nx <- length(x)
  ny <- length(y)
  vx <- stats::var(x)
  vy <- stats::var(y)
  wx <- vx / nx
  wy <- vy / ny
  estimate <- mean(x) - mean(y)
  standard_error <- sqrt(wx + wy)
  degrees_freedom <- (wx + wy)^2 /
    (wx^2 / (nx - 1) + wy^2 / (ny - 1))
  statistic <- estimate / standard_error
  critical_value <- stats::qt(1 - alpha / 2, degrees_freedom)
  list(
    difference = estimate,
    se = standard_error,
    t = statistic,
    df = degrees_freedom,
    ci = estimate + c(-1, 1) * critical_value * standard_error
  )
}

round_half_up_positive <- function(x) floor(x + 0.5)

manual <- welch_manual(a, b, alpha)
assert_close(manual$t, unname(fit$statistic), label = "manual/R t statistic")
assert_close(manual$df, unname(fit$parameter), label = "manual/R degrees of freedom")
assert_close(manual$ci, unname(fit$conf.int), label = "manual/R confidence interval")
assert_close(critical_full, stats::qt(1 - alpha / 2, df),
             label = "full-df critical value")
if (df_class != round_half_up_positive(df)) {
  stop("Displayed degrees of freedom do not use positive half-up rounding", call. = FALSE)
}

# Golden values from the canonical CSV. Keep these at calculation precision.
assert_close(c(m1, m2), c(123, 135), label = "golden means")
assert_close(c(s1, s2), c(4.8989794855663558, 9.7979589711327115),
             label = "golden standard deviations")
assert_close(c(v1, v2), c(3, 12), label = "golden variance contributions")
assert_close(c(w1, w2), c(9 / 7, 144 / 7),
             label = "golden Welch denominator terms")
assert_close(difference, -12, label = "golden difference")
assert_close(se, 3.872983346207417, label = "golden standard error")
assert_close(t_stat, -3.0983866769659336, label = "golden t statistic")
assert_close(df, 10.294117647058824, label = "golden degrees of freedom")
assert_close(unname(fit$p.value), 0.010915000277860661, label = "golden p value")
assert_close(critical_full, 2.2195397546022622, label = "golden critical value")
assert_close(critical, 2.2281388519862744, label = "class critical value")
if (!(abs(t_stat) > critical)) stop("Required decision must reject H0", call. = FALSE)
assert_close(ci, c(-20.596240505819857, -3.4037594941801403),
             label = "golden confidence interval")
if (df_class != 10L) stop("Golden displayed df must be 10", call. = FALSE)

# Unequal group sizes exercise Welch's denominator and half-up df display.
unequal_a <- c(12, 13, 15, 14, 16, 15)
unequal_b <- c(8, 9, 11, 10, 18)
unequal <- welch_manual(unequal_a, unequal_b)
unequal_fit <- stats::t.test(unequal_a, unequal_b, var.equal = FALSE)
assert_close(unequal$t, unname(unequal_fit$statistic), label = "unequal-n t")
assert_close(unequal$df, 4.92086560201894, label = "unequal-n df")
if (round_half_up_positive(unequal$df) != 5L) {
  stop("Unequal-n df should display as 5", call. = FALSE)
}

# Swapping groups changes the sign, while a two-sided p value is unchanged.
swapped <- stats::t.test(b, a, var.equal = FALSE)
assert_close(unname(swapped$statistic), -unname(fit$statistic),
             label = "swapped t sign")
assert_close(swapped$p.value, fit$p.value, label = "swapped two-sided p value")
if ((abs(unname(swapped$statistic)) > critical) != (abs(t_stat) > critical)) {
  stop("Swapping groups must preserve the classroom decision", call. = FALSE)
}

# Equal means yield a zero statistic even when sample variances differ.
equal_a <- c(0, 3, 3)
equal_b <- c(1, 2, 3)
equal_result <- welch_manual(equal_a, equal_b)
assert_close(equal_result$difference, 0, label = "equal-mean difference")
assert_close(equal_result$t, 0, label = "equal-mean t statistic")

assert_close(round_half_up_positive(c(10.49, 10.5, 10.51)), c(10, 11, 11),
             tolerance = 0, label = "positive half-up rounding")

if (!requireNamespace("jsonlite", quietly = TRUE)) {
  stop("Install jsonlite before running validation", call. = FALSE)
}

example_dir <- file.path(topic_dir, "_examples", "independent-t-test")
python_output_file <- file.path(example_dir, "python-output.txt")
provenance_file <- file.path(example_dir, "provenance.json")
if (!file.exists(python_output_file) || !file.exists(provenance_file)) {
  stop("Missing saved Python output or provenance", call. = FALSE)
}

parse_key_value <- function(path) {
  lines <- readLines(path, warn = FALSE)
  positions <- regexpr("=", lines, fixed = TRUE)
  if (any(positions < 1L)) stop("Malformed key=value output: ", path, call. = FALSE)
  keys <- substr(lines, 1L, positions - 1L)
  values <- substr(lines, positions + 1L, nchar(lines))
  stats::setNames(as.list(values), keys)
}

python_output <- parse_key_value(python_output_file)
provenance <- jsonlite::read_json(provenance_file, simplifyVector = TRUE)
source_md5 <- unname(tools::md5sum(input_file))
if (!identical(python_output$input_md5, source_md5) ||
    !identical(provenance$input_md5, source_md5)) {
  stop("Python output/provenance source fingerprint is stale", call. = FALSE)
}
if (!identical(provenance$input_file, input_file)) {
  stop("Provenance input_file does not identify the canonical CSV", call. = FALSE)
}

python_numeric <- c(
  group_A_n = n1,
  group_A_mean = m1,
  group_A_sd = s1,
  group_B_n = n2,
  group_B_mean = m2,
  group_B_sd = s2,
  mean_difference_A_minus_B = difference,
  standard_error = se,
  t_statistic = t_stat,
  degrees_of_freedom = df,
  p_value_two_sided = unname(fit$p.value),
  ci_95_lower = ci[1],
  ci_95_upper = ci[2],
  df_class = df_class,
  critical_t_df_class = critical,
  critical_t_full_df = critical_full
)
saved_numeric <- vapply(names(python_numeric), function(key) {
  value <- python_output[[key]]
  if (is.null(value)) stop("Python output missing key: ", key, call. = FALSE)
  as.numeric(value)
}, numeric(1))
assert_close(saved_numeric, python_numeric, label = "saved Python output")

for (key in c("python_version", "numpy_version", "scipy_version")) {
  if (!identical(python_output[[key]], provenance[[key]])) {
    stop("Python output/provenance version mismatch for ", key, call. = FALSE)
  }
}
for (key in c("r_version", "python_version", "numpy_version", "scipy_version")) {
  value <- provenance[[key]]
  if (is.null(value) || length(value) != 1L || !nzchar(value)) {
    stop("Provenance must record a nonempty ", key, call. = FALSE)
  }
}

requirements <- readLines("requirements-validation.txt", warn = FALSE)
requirements <- requirements[nzchar(requirements) & !startsWith(requirements, "#")]
requirement_parts <- strsplit(requirements, "==", fixed = TRUE)
if (any(lengths(requirement_parts) != 2L)) {
  stop("requirements-validation.txt must use exact package==version pins",
       call. = FALSE)
}
requirement_versions <- stats::setNames(
  vapply(requirement_parts, `[[`, character(1), 2L),
  vapply(requirement_parts, `[[`, character(1), 1L)
)
for (package in c("numpy", "scipy")) {
  expected_version <- requirement_versions[[package]]
  recorded_version <- provenance[[paste0(package, "_version")]]
  if (is.null(expected_version) || !identical(recorded_version, expected_version)) {
    stop("Recorded ", package, " version must match requirements-validation.txt",
         call. = FALSE)
  }
}

python_bin <- file.path(".venv-validation", "bin", "python")
if ("--with-python" %in% commandArgs(trailingOnly = TRUE)) {
  if (!file.exists(python_bin)) {
    stop("Create .venv-validation and install requirements-validation.txt first",
         call. = FALSE)
  }
  fresh_output <- system2(
    python_bin,
    file.path(example_dir, "example.py"),
    stdout = TRUE,
    stderr = TRUE
  )
  status <- attr(fresh_output, "status")
  if (!is.null(status) && status != 0L) {
    stop("Live Python validation failed:\n", paste(fresh_output, collapse = "\n"),
         call. = FALSE)
  }
  fresh_file <- tempfile(fileext = ".txt")
  on.exit(unlink(fresh_file), add = TRUE)
  writeLines(fresh_output, fresh_file)
  fresh_values <- parse_key_value(fresh_file)
  if (!identical(fresh_values$input_md5, source_md5)) {
    stop("Live Python output used a different source CSV", call. = FALSE)
  }
  fresh_numeric <- vapply(names(python_numeric), function(key) {
    value <- fresh_values[[key]]
    if (is.null(value)) stop("Live Python output missing key: ", key, call. = FALSE)
    as.numeric(value)
  }, numeric(1))
  assert_close(fresh_numeric, python_numeric, label = "live Python output")

  live_versions <- vapply(
    c("python_version", "numpy_version", "scipy_version"),
    function(key) fresh_values[[key]], character(1)
  )
  recorded_versions <- vapply(
    c("python_version", "numpy_version", "scipy_version"),
    function(key) provenance[[key]], character(1)
  )
  if (!identical(live_versions, recorded_versions)) {
    message(
      "Live Python versions differ from recorded provenance; numerical checks passed. ",
      "Install requirements-validation.txt to reproduce the recorded environment."
    )
  }
}

excel_output_file <- file.path(example_dir, "excel-output.csv")
toolpak_output_file <- file.path(example_dir, "excel-toolpak.csv")
missing_excel_files <- c(excel_output_file, toolpak_output_file)[
  !file.exists(c(excel_output_file, toolpak_output_file))
]
if (length(missing_excel_files)) {
  stop("Missing required native Excel evidence: ",
       paste(missing_excel_files, collapse = ", "), call. = FALSE)
}

excel_provenance <- provenance$excel
if (is.null(excel_provenance) || !is.list(excel_provenance)) {
  stop("Provenance must contain nested Excel metadata", call. = FALSE)
}
for (key in c("source_md5", "output_md5", "toolpak_output_md5", "version")) {
  value <- excel_provenance[[key]]
  if (is.null(value) || length(value) != 1L || !nzchar(value)) {
    stop("Excel provenance must record a nonempty ", key, call. = FALSE)
  }
}
if (!identical(excel_provenance$source_md5, source_md5) ||
    !identical(excel_provenance$output_md5,
               unname(tools::md5sum(excel_output_file))) ||
    !identical(excel_provenance$toolpak_output_md5,
               unname(tools::md5sum(toolpak_output_file)))) {
  stop("Excel evidence fingerprint is stale", call. = FALSE)
}

excel_output <- utils::read.csv(excel_output_file, stringsAsFactors = FALSE)
if (!identical(names(excel_output), c("key", "value"))) {
  stop("excel-output.csv must have key,value columns", call. = FALSE)
}
excel_values <- stats::setNames(excel_output$value, excel_output$key)
required_excel <- c(
  m1 = m1,
  m2 = m2,
  n1 = n1,
  n2 = n2,
  variance_a = stats::var(a),
  variance_b = stats::var(b),
  t_stat = t_stat,
  df_class = df_class,
  critical = critical,
  p_value = fit$p.value,
  toolpak_p_value = 2 * stats::pt(-abs(t_stat), df = df_class)
)
missing_keys <- setdiff(names(required_excel), names(excel_values))
if (length(missing_keys)) {
  stop("excel-output.csv missing keys: ", paste(missing_keys, collapse = ", "),
       call. = FALSE)
}
assert_close(as.numeric(excel_values[names(required_excel)]), required_excel,
             tolerance = 1e-10, label = "required Excel output")

optional_excel <- c(
  s1 = s1,
  s2 = s2,
  difference = difference,
  se = se,
  df = df,
  critical_full = critical_full,
  alpha = alpha,
  ci_lower = ci[1],
  ci_upper = ci[2]
)
present_optional <- intersect(names(optional_excel), names(excel_values))
if (length(present_optional)) {
  assert_close(as.numeric(excel_values[present_optional]),
               optional_excel[present_optional], tolerance = 1e-10,
               label = "optional Excel output")
}

toolpak_output <- utils::read.csv(
  toolpak_output_file,
  stringsAsFactors = FALSE,
  check.names = FALSE,
  na.strings = ""
)
if (!identical(names(toolpak_output),
               c("Statistic", "Group A / result", "Group B"))) {
  stop("excel-toolpak.csv has unexpected columns", call. = FALSE)
}
toolpak_rows <- stats::setNames(
  seq_len(nrow(toolpak_output)),
  toolpak_output$Statistic
)
toolpak_value <- function(statistic, column) {
  row <- toolpak_rows[[statistic]]
  if (is.null(row)) stop("excel-toolpak.csv missing row: ", statistic,
                         call. = FALSE)
  as.numeric(toolpak_output[[column]][row])
}
toolpak_a <- c(
  Mean = m1,
  Variance = stats::var(a),
  Observations = n1,
  `Hypothesized Mean Difference` = 0,
  df = df_class,
  `t Stat` = t_stat,
  `P(T<=t) one-tail` = stats::pt(t_stat, df = df_class),
  `t Critical one-tail` = stats::qt(1 - alpha, df = df_class),
  `P(T<=t) two-tail` = 2 * stats::pt(-abs(t_stat), df = df_class),
  `t Critical two-tail` = critical
)
captured_toolpak_a <- vapply(
  names(toolpak_a), toolpak_value, numeric(1), column = "Group A / result"
)
assert_close(captured_toolpak_a, toolpak_a, tolerance = 1e-10,
             label = "Excel ToolPak output")
assert_close(
  c(toolpak_value("Mean", "Group B"),
    toolpak_value("Variance", "Group B"),
    toolpak_value("Observations", "Group B")),
  c(m2, stats::var(b), n2),
  tolerance = 1e-10,
  label = "Excel ToolPak group B output"
)

cat("All statistical validation checks passed.\n")
