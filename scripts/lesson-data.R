# Canonical data and Welch two-sample t-test quantities for this lesson.
# Source this file with the project root as the working directory.

topic_dir <- file.path("topics", "hypothesis-testing")
input_file <- file.path(topic_dir, "data", "independent-t-test.csv")

if (!file.exists(input_file)) {
  stop("Run this lesson from the project root; missing ", input_file, call. = FALSE)
}

lesson_data <- utils::read.csv(input_file, stringsAsFactors = FALSE)
if (!identical(names(lesson_data), c("group", "sbp"))) {
  stop("Expected CSV columns: group,sbp", call. = FALSE)
}
if (!identical(unique(lesson_data$group), c("A", "B"))) {
  stop("Expected groups A and B in that order", call. = FALSE)
}
if (anyNA(lesson_data$sbp) || !is.numeric(lesson_data$sbp)) {
  stop("All sbp values must be numeric and non-missing", call. = FALSE)
}

a <- lesson_data$sbp[lesson_data$group == "A"]
b <- lesson_data$sbp[lesson_data$group == "B"]

n1 <- length(a)
n2 <- length(b)
m1 <- mean(a)
m2 <- mean(b)
s1 <- stats::sd(a)
s2 <- stats::sd(b)
v1 <- stats::var(a) / n1
v2 <- stats::var(b) / n2
w1 <- v1^2 / (n1 - 1)
w2 <- v2^2 / (n2 - 1)
difference <- m1 - m2
se <- sqrt(v1 + v2)
t_stat <- difference / se
df <- (v1 + v2)^2 / (w1 + w2)

alpha <- 0.05
df_class <- floor(df + 0.5)
critical <- stats::qt(1 - alpha / 2, df = df_class)
critical_full <- stats::qt(1 - alpha / 2, df = df)
ci <- difference + c(-1, 1) * critical_full * se
fit <- stats::t.test(a, b, alternative = "two.sided", var.equal = FALSE,
                     conf.level = 1 - alpha)

f <- function(x, digits = 3) {
  formatC(x, format = "f", digits = digits)
}
