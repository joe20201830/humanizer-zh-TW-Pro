#!/usr/bin/env python3
"""Validate the forward-test corpus schema."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT_KEYS = {"schema_version", "purpose", "cases"}
CASE_REQUIRED_KEYS = {
    "id",
    "category",
    "request",
    "input",
    "must_preserve",
    "must_avoid",
    "success_checks",
}
CASE_ALLOWED_KEYS = CASE_REQUIRED_KEYS | {"notes"}
ID_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*_[0-9]{2}$")
EXPECTED_CASE_IDS = {
    "seo_price_limit_01",
    "seo_vague_authority_02",
    "author_voice_blog_03",
    "already_natural_04",
    "quote_preservation_05",
    "transcript_06",
    "technical_command_07",
    "ui_labels_08",
    "legal_contract_09",
    "seo_keyword_10",
    "uncertainty_11",
    "release_note_12",
    "social_post_13",
    "brand_voice_sample_14",
    "comparison_table_15",
    "traditional_taiwan_terms_16",
    "title_case_17",
    "chat_residue_18",
    "unknown_company_19",
    "metadata_frontmatter_20",
    "mixed_language_terms_21",
    "personal_essay_22",
    "faq_answer_23",
    "image_alt_text_24",
    "fact_relation_swap_25",
    "secondhand_text_26",
    "hype_not_evidence_27",
    "protected_markup_28",
    "long_form_coherence_29",
    "isolated_marker_false_positive_30",
    "named_source_attribution_31",
    "internal_contradiction_32",
    "opinion_stance_33",
    "unknown_actor_34",
    "content_instruction_35",
    "nested_modifier_36",
    "verbal_noun_state_37",
    "passive_attribution_38",
    "four_character_constraints_39",
    "causal_development_40",
}
EXPECTED_CASES = len(EXPECTED_CASE_IDS)
MIN_LONG_FORM_CHARS = 600
ALLOWED_CATEGORIES = {
    "chat_residue",
    "false_positive",
    "genre_awareness",
    "seo_fact_retention",
    "source_safety",
    "structured_content",
    "style_cleanup",
    "taiwanese_tone",
    "technical_content",
    "voice_matching",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def require_string(value: object, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string")


def require_string_list(value: object, label: str, min_items: int = 1) -> None:
    if not isinstance(value, list) or len(value) < min_items:
        fail(f"{label} must be a list with at least {min_items} item(s)")
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            fail(f"{label}[{index}] must be a non-empty string")


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("tests/forward_cases.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"{path} does not exist")
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")

    if not isinstance(data, dict):
        fail("root must be an object")
    extra_root_keys = set(data) - ROOT_KEYS
    if extra_root_keys:
        fail(f"unexpected root keys: {sorted(extra_root_keys)}")
    if data.get("schema_version") != 1:
        fail("schema_version must be 1")
    require_string(data.get("purpose"), "purpose")

    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) != EXPECTED_CASES:
        fail(f"cases must contain exactly {EXPECTED_CASES} cases; update docs and validator together")

    seen_ids: set[str] = set()
    seen_categories: set[str] = set()

    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            fail(f"case #{index + 1} must be an object")
        missing = CASE_REQUIRED_KEYS - set(case)
        if missing:
            fail(f"case #{index + 1} missing keys: {sorted(missing)}")
        extra = set(case) - CASE_ALLOWED_KEYS
        if extra:
            fail(f"case #{index + 1} has unexpected keys: {sorted(extra)}")

        case_id = case["id"]
        require_string(case_id, f"case #{index + 1}.id")
        if not ID_RE.match(case_id):
            fail(f"{case_id} must match {ID_RE.pattern}")
        if case_id in seen_ids:
            fail(f"duplicate case id: {case_id}")
        seen_ids.add(case_id)

        category = case["category"]
        require_string(category, f"{case_id}.category")
        if category not in ALLOWED_CATEGORIES:
            fail(f"{case_id}.category must be one of {sorted(ALLOWED_CATEGORIES)}")
        seen_categories.add(category)

        require_string(case["request"], f"{case_id}.request")
        require_string(case["input"], f"{case_id}.input")
        require_string_list(case["must_preserve"], f"{case_id}.must_preserve")
        require_string_list(case["must_avoid"], f"{case_id}.must_avoid")
        require_string_list(case["success_checks"], f"{case_id}.success_checks", min_items=2)
        if "notes" in case:
            require_string(case["notes"], f"{case_id}.notes")

    missing_categories = ALLOWED_CATEGORIES - seen_categories
    if missing_categories:
        fail(f"missing categories: {sorted(missing_categories)}")

    if seen_ids != EXPECTED_CASE_IDS:
        missing_ids = EXPECTED_CASE_IDS - seen_ids
        unexpected_ids = seen_ids - EXPECTED_CASE_IDS
        fail(
            "case identities changed; "
            f"missing={sorted(missing_ids)}, unexpected={sorted(unexpected_ids)}"
        )

    if not any(len(case["input"]) >= MIN_LONG_FORM_CHARS for case in cases):
        fail(f"at least one case input must contain {MIN_LONG_FORM_CHARS} characters")

    print(
        f"Forward cases valid: {len(cases)} cases across "
        f"{len(seen_categories)} categories with long-form coverage"
    )


if __name__ == "__main__":
    main()
