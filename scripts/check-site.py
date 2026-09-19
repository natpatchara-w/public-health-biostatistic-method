#!/usr/bin/env python3
"""Validate local links, fragments, citations, and resources in a Quarto site."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from html.parser import HTMLParser
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import sys
import unicodedata
from urllib.parse import unquote, urlsplit


SKIP_SCHEMES = {"mailto", "tel", "sms", "javascript", "data", "blob"}
URL_ATTRS = {
    "a": ("href",),
    "area": ("href",),
    "audio": ("src",),
    "embed": ("src",),
    "form": ("action",),
    "iframe": ("src",),
    "img": ("src", "srcset"),
    "input": ("src",),
    "link": ("href",),
    "object": ("data",),
    "script": ("src",),
    "source": ("src", "srcset"),
    "track": ("src",),
    "video": ("src", "poster"),
}
BAD_PERCENT = re.compile(r"%(?![0-9A-Fa-f]{2})")
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HTML_LINK = re.compile(r"(?:href|src)\s*=\s*['\"]([^'\"]+)['\"]", re.I)
FENCED_CODE = re.compile(r"^\s*(```|~~~).*?^\s*\1\s*$", re.M | re.S)
INLINE_CODE = re.compile(r"`[^`]*`")
BIB_KEY = re.compile(r"^\s*@\w+\s*\{\s*([^,\s]+)\s*,", re.M)
CITATION = re.compile(r"(?<![\w@])@([A-Za-z][A-Za-z0-9_:.\-/]*)")
CROSSREF_PREFIXES = (
    "fig-",
    "tbl-",
    "sec-",
    "eq-",
    "lst-",
    "thm-",
    "lem-",
    "cor-",
    "prp-",
    "cnj-",
    "def-",
    "exm-",
    "exr-",
)


@dataclass
class HtmlPage:
    path: Path
    ids: set[str] = field(default_factory=set)
    links: list[tuple[int, str, str]] = field(default_factory=list)


class SiteParser(HTMLParser):
    def __init__(self, path: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.page = HtmlPage(path)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.lower(): value for name, value in attrs if value is not None}
        if "id" in values:
            self.page.ids.add(unicodedata.normalize("NFC", values["id"]))
        if tag.lower() == "a" and "name" in values:
            self.page.ids.add(unicodedata.normalize("NFC", values["name"]))
        for attr in URL_ATTRS.get(tag.lower(), ()):
            value = values.get(attr)
            if not value:
                continue
            if attr == "srcset":
                if value.lstrip().lower().startswith("data:"):
                    continue
                for item in value.split(","):
                    url = item.strip().split(maxsplit=1)[0]
                    if url:
                        self.page.links.append((self.getpos()[0], attr, url))
            else:
                self.page.links.append((self.getpos()[0], attr, value.strip()))


@dataclass(frozen=True)
class BaseUrl:
    scheme: str
    netloc: str
    prefix: str


def parse_base_url(value: str | None) -> BaseUrl | None:
    if value is None:
        return None
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("--base-url must be an absolute http:// or https:// URL")
    prefix = "/" + parsed.path.strip("/")
    if prefix == "/":
        prefix = ""
    return BaseUrl(parsed.scheme.lower(), parsed.netloc.lower(), prefix)


def read_html(path: Path) -> HtmlPage:
    parser = SiteParser(path)
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    parser.close()
    return parser.page


def public_path(path: Path, site_dir: Path) -> str:
    return path.relative_to(site_dir).as_posix()


def strip_base_prefix(path: str, base: BaseUrl) -> tuple[str | None, str | None]:
    if not path.startswith("/"):
        return path, None
    if not base.prefix:
        return path.lstrip("/"), None
    if path == base.prefix or path == base.prefix + "/":
        return "", None
    expected = base.prefix + "/"
    if not path.startswith(expected):
        return None, f"root-relative URL is outside the configured base path {expected}"
    return path[len(expected) :], None


def decode_url_piece(value: str) -> tuple[str | None, str | None]:
    if BAD_PERCENT.search(value):
        return None, "contains an invalid percent escape"
    try:
        return unquote(value, encoding="utf-8", errors="strict"), None
    except UnicodeDecodeError:
        return None, "contains invalid UTF-8 URL encoding"


def resolve_link_path(
    raw_url: str,
    source_public: str,
    base: BaseUrl | None,
) -> tuple[str | None, str | None, str | None]:
    """Return (site-relative path, decoded fragment, error). None path means skip."""
    parsed = urlsplit(raw_url)
    scheme = parsed.scheme.lower()
    if scheme in SKIP_SCHEMES:
        return None, None, None
    if scheme and scheme not in {"http", "https"}:
        return None, None, None

    url_path = parsed.path
    if scheme in {"http", "https"} or parsed.netloc:
        if base is None:
            return None, None, None
        if scheme and scheme != base.scheme:
            return None, None, None
        if parsed.netloc.lower() != base.netloc:
            return None, None, None
        url_path, error = strip_base_prefix(url_path, base)
        if error:
            return None, None, error
        assert url_path is not None
    elif url_path.startswith("/"):
        if base is not None:
            url_path, error = strip_base_prefix(url_path, base)
            if error:
                return None, None, error
            assert url_path is not None
        else:
            url_path = url_path.lstrip("/")
    else:
        if url_path:
            parent = posixpath.dirname(source_public)
            url_path = posixpath.join(parent, url_path)
        else:
            # A bare fragment or query belongs to the page containing the link.
            url_path = source_public

    decoded_path, error = decode_url_piece(url_path)
    if error:
        return None, None, error
    decoded_fragment, fragment_error = decode_url_piece(parsed.fragment)
    if fragment_error:
        return None, None, fragment_error
    assert decoded_path is not None and decoded_fragment is not None
    if "\\" in decoded_path:
        return None, None, "uses a backslash in a URL path"

    trailing_slash = decoded_path.endswith("/")
    normal = posixpath.normpath(decoded_path)
    if normal == ".":
        normal = ""
    if normal == ".." or normal.startswith("../") or normal.startswith("/"):
        return None, None, "escapes the generated site directory"
    if trailing_slash and normal:
        normal += "/"
    return normal, unicodedata.normalize("NFC", decoded_fragment), None


def choose_target(path: str, files: set[str]) -> str | None:
    candidates: list[str] = []
    if not path:
        candidates.append("index.html")
    elif path.endswith("/"):
        candidates.append(path + "index.html")
    else:
        candidates.append(path)
        suffix = PurePosixPath(path).suffix
        if not suffix:
            candidates.extend((path + ".html", path + "/index.html"))
    return next((candidate for candidate in candidates if candidate in files), None)


def check_generated_site(site_dir: Path, base: BaseUrl | None) -> list[str]:
    issues: list[str] = []
    if not site_dir.is_dir():
        return [f"generated site directory does not exist: {site_dir}"]

    all_files = {
        path.relative_to(site_dir).as_posix()
        for path in site_dir.rglob("*")
        if path.is_file()
    }
    html_paths = sorted(path for path in site_dir.rglob("*.html") if path.is_file())
    if not html_paths:
        issues.append(f"no HTML files found below {site_dir}")
        return issues
    if ".nojekyll" not in all_files:
        issues.append("generated site is missing .nojekyll at its root")
    accidental = sorted(name for name in all_files if name.startswith("_templates/") or "/_templates/" in name)
    if accidental:
        issues.append("template files were rendered or copied: " + ", ".join(accidental))

    pages = {public_path(path, site_dir): read_html(path) for path in html_paths}
    lowered_signals = ("citation-not-found", "citeproc-not-found")
    for name, page in pages.items():
        html_text = page.path.read_text(encoding="utf-8", errors="replace").lower()
        for signal in lowered_signals:
            if signal in html_text:
                issues.append(f"{name}: contains unresolved-citation marker {signal!r}")
        for line, attr, url in page.links:
            target_path, fragment, error = resolve_link_path(url, name, base)
            label = f"{name}:{line}: {attr}={url!r}"
            if error:
                issues.append(f"{label}: {error}")
                continue
            if target_path is None:
                continue
            target = choose_target(target_path, all_files)
            if target is None:
                issues.append(f"{label}: target does not exist in generated site")
                continue
            if fragment and target.endswith(".html"):
                target_page = pages.get(target)
                if target_page is None:
                    issues.append(f"{label}: could not inspect fragment target {target}")
                elif fragment not in target_page.ids:
                    issues.append(f"{label}: fragment #{fragment} does not exist in {target}")
    return issues


def clean_markdown_target(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("<") and ">" in raw:
        return raw[1 : raw.index(">")]
    match = re.match(r"([^\s]+)", raw)
    return match.group(1) if match else raw


def iter_source_qmd(project: Path) -> list[Path]:
    files: list[Path] = []
    root_page = project / "index.qmd"
    if root_page.is_file():
        files.append(root_page)
    topics = project / "topics"
    if topics.is_dir():
        for path in topics.rglob("*.qmd"):
            relative_parts = path.relative_to(topics).parts
            if not any(part.startswith("_") for part in relative_parts[:-1]):
                files.append(path)
    return sorted(set(files))


def source_target_exists(source: Path, url: str, project: Path) -> bool:
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return True
    decoded, error = decode_url_piece(parsed.path)
    if error or decoded is None:
        return False
    if decoded.startswith("/"):
        target = project / decoded.lstrip("/")
    else:
        target = source.parent / decoded
    target = Path(os.path.normpath(target))
    try:
        target.relative_to(project)
    except ValueError:
        return False
    if target.exists():
        return True
    if target.suffix == ".html" and target.with_suffix(".qmd").exists():
        return True
    if not target.suffix and (target.with_suffix(".qmd").exists() or (target / "index.qmd").exists()):
        return True
    return False


def check_sources(project: Path) -> list[str]:
    issues: list[str] = []
    qmd_files = iter_source_qmd(project)
    bibliography = project / "references.bib"
    if not bibliography.is_file():
        issues.append("source bibliography is missing: references.bib")
        bib_keys: set[str] = set()
    else:
        bib_keys = set(BIB_KEY.findall(bibliography.read_text(encoding="utf-8", errors="replace")))

    for source in qmd_files:
        relative = source.relative_to(project).as_posix()
        text = source.read_text(encoding="utf-8", errors="replace")
        prose = INLINE_CODE.sub("", FENCED_CODE.sub("", text))
        urls = [clean_markdown_target(match) for match in MARKDOWN_LINK.findall(prose)]
        urls.extend(HTML_LINK.findall(prose))
        for url in urls:
            parsed = urlsplit(url)
            if parsed.scheme.lower() in SKIP_SCHEMES or parsed.scheme in {"http", "https"} or parsed.netloc:
                continue
            if BAD_PERCENT.search(parsed.path):
                issues.append(f"{relative}: local link has an invalid percent escape: {url!r}")
            elif not source_target_exists(source, url, project):
                issues.append(f"{relative}: local link target does not exist: {url!r}")

        citation_prose = MARKDOWN_LINK.sub("", prose)
        citation_prose = HTML_LINK.sub("", citation_prose)
        citation_keys = {
            key.rstrip(".,;")
            for key in CITATION.findall(citation_prose)
            if not key.startswith(CROSSREF_PREFIXES)
        }
        for key in sorted(citation_keys - bib_keys):
            issues.append(f"{relative}: unresolved citation key @{key}")
    return issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check a rendered Quarto site without crawling external URLs."
    )
    parser.add_argument("site_dir", type=Path, help="generated site directory, usually _site")
    parser.add_argument(
        "--base-url",
        help="deployed HTTP(S) base URL; same-site links are checked below its path prefix",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        base = parse_base_url(args.base_url)
    except ValueError as error:
        print(f"check-site: {error}", file=sys.stderr)
        return 2

    site_dir = args.site_dir.resolve()
    project = Path(__file__).resolve().parent.parent
    issues = check_sources(project)
    issues.extend(check_generated_site(site_dir, base))

    if issues:
        print(f"Site validation failed with {len(issues)} issue(s):", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    page_count = sum(1 for _ in site_dir.rglob("*.html"))
    suffix = f" using base URL {args.base_url}" if args.base_url else ""
    print(f"Site validation passed for {page_count} HTML page(s){suffix}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
