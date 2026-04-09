"""Lossless-ish text compression for Congressional bill text."""

from __future__ import annotations

import re

STATES = (
    "Alabama",
    "Alaska",
    "Arizona",
    "Arkansas",
    "California",
    "Colorado",
    "Connecticut",
    "Delaware",
    "Florida",
    "Georgia",
    "Hawaii",
    "Idaho",
    "Illinois",
    "Indiana",
    "Iowa",
    "Kansas",
    "Kentucky",
    "Louisiana",
    "Maine",
    "Maryland",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Mississippi",
    "Missouri",
    "Montana",
    "Nebraska",
    "Nevada",
    "New Hampshire",
    "New Jersey",
    "New Mexico",
    "New York",
    "North Carolina",
    "North Dakota",
    "Ohio",
    "Oklahoma",
    "Oregon",
    "Pennsylvania",
    "Rhode Island",
    "South Carolina",
    "South Dakota",
    "Tennessee",
    "Texas",
    "Utah",
    "Vermont",
    "Virginia",
    "Washington",
    "West Virginia",
    "Wisconsin",
    "Wyoming",
    "Puerto Rico",
    "Guam",
    "American Samoa",
    "District of Columbia",
    "US Virgin Islands",
)
STATE_PATTERNS = [(re.compile(re.escape(state), re.IGNORECASE), state) for state in STATES]


def normalize_state_names(text: str) -> str:
    """Replace any casing of state names with title case."""
    for pattern, replacement in STATE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def strip_number_commas(text: str) -> str:
    """Remove commas from numeric thousands separators."""
    return re.sub(r"(\d{1,3}(?:,\d{3})+)", lambda match: match.group().replace(",", ""), text)


def strip_horizontal_rules(text: str) -> str:
    """Remove ASCII horizontal-rule lines built from underscores, dashes, equals, or asterisks."""
    return re.sub(r"^\s*[_\-=\*]{3,}\s*$", "", text, flags=re.MULTILINE)


def collapse_double_dashes(text: str) -> str:
    """Replace ``--`` em-dash stand-ins with a single space so they don't tokenize oddly."""
    return text.replace("--", " ")


def collapse_inline_whitespace(text: str) -> str:
    """Collapse runs of horizontal whitespace (spaces, tabs) into a single space, leaving newlines intact."""
    return re.sub(r"[^\S\n]+", " ", text)


def collapse_blank_lines(text: str) -> str:
    """Collapse three-or-more consecutive newlines down to a blank-line separator."""
    return re.sub(r"\n{3,}", "\n\n", text)


def trim_line_edges(text: str) -> str:
    """Strip spaces immediately before and after newline characters on every line."""
    text = re.sub(r" +\n", "\n", text)
    return re.sub(r"\n +", "\n", text)


def shorten_section_markers(text: str) -> str:
    """Rewrite ``Sec. 12.`` style section headings as the more compact ``SEC 12``."""
    return re.sub(r"(?i)sec\.\s*(\d+[a-zA-Z]?)\.", r"SEC \1", text)


def unwrap_parens(text: str) -> str:
    """Strip parentheses around short alphanumeric labels like ``(a)`` or ``(12)``."""
    return re.sub(r"\(([a-zA-Z0-9]+)\)", r"\1", text)


def strip_typeset_quotes(text: str) -> str:
    """Remove the `` and '' typeset quote markers used in the GPO bill format."""
    return text.replace("``", "").replace("''", "")


def normalize_usc_acronym(text: str) -> str:
    """Collapse ``U.S.C.`` to ``USC`` to save tokens on the common citation."""
    return text.replace("U.S.C.", "USC")


def normalize_us_acronym(text: str) -> str:
    """Normalize the various ``U.S.``/``U. S.`` spellings to the bare ``US`` form."""
    for acronym in ("U. S.", "u. s.", "U.S. ", "u.s. "):
        text = text.replace(acronym, "US ")
    return text


def collapse_ellipses(text: str) -> str:
    """Collapse runs of two-or-more periods (``...``, ``....``) down to a single period."""
    return re.sub(r"\.{2,}", ".", text)


COMPRESSION_STEPS = (
    strip_horizontal_rules,
    collapse_double_dashes,
    collapse_inline_whitespace,
    collapse_blank_lines,
    trim_line_edges,
    shorten_section_markers,
    unwrap_parens,
    strip_typeset_quotes,
    normalize_usc_acronym,
    normalize_us_acronym,
    strip_number_commas,
    collapse_ellipses,
    normalize_state_names,
)


def compress_bill_text(text: str) -> str:
    """Apply lossless-ish whitespace and boilerplate compression to bill text.

    Runs every transform in :data:`COMPRESSION_STEPS` in order, then strips
    leading/trailing whitespace from the final result.
    """
    for step in COMPRESSION_STEPS:
        text = step(text)
    return text.strip()
