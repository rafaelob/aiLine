"""Validate SKILL.md files against the agentskills.io specification.

This module provides strict validation of SKILL.md frontmatter and body
content, returning structured results with errors and warnings. It is
self-contained, depending only on PyYAML and the stdlib.

Specification rules enforced:
    1. Frontmatter (--- ... ---) must exist.
    2. Only allowed frontmatter keys: name, description, license,
       compatibility, allowed-tools, metadata.
    3. ``name``: required, 3-64 chars, lowercase alphanumeric + hyphens,
       no consecutive hyphens, no start/end with hyphen.
    4. ``description``: required, 1-1024 chars, non-empty after strip.
    5. ``license``: optional string.
    6. ``compatibility``: optional string (max 500 chars).
    7. ``metadata``: optional dict[str, str] -- values must be strings only.
    8. ``allowed-tools``: optional, space-delimited string (not a YAML list).
    9. Body (instructions markdown) must exist and be non-empty.
   10. Instructions should be under ~5000 tokens (heuristic: chars / 4).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import yaml  # type: ignore[import-untyped]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)

_ALLOWED_FRONTMATTER_KEYS: frozenset[str] = frozenset(
    {
        "name",
        "description",
        "license",
        "compatibility",
        "allowed-tools",
        "metadata",
    }
)

_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9]|-(?=[a-z0-9]))*$")
"""Match a valid skill name: lowercase alnum + single hyphens, no start/end hyphen."""

_NAME_MIN_LEN = 3
_NAME_MAX_LEN = 64
_DESCRIPTION_MAX_LEN = 1024
_COMPATIBILITY_MAX_LEN = 500
_INSTRUCTIONS_TOKEN_WARN = 5000
_CHARS_PER_TOKEN = 4

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class SkillSpecValidationResult:
    """Structured result of validating a SKILL.md against the agentskills.io spec.

    Attributes:
        ok: True when there are zero errors (warnings are acceptable).
        errors: Hard failures that violate the specification.
        warnings: Soft issues that do not block but should be addressed.
        frontmatter: The parsed frontmatter dict (empty on parse failure).
        instructions_md: The body markdown after the frontmatter delimiter.
    """

    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    frontmatter: dict[str, Any] = field(default_factory=dict)
    instructions_md: str = ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_skill_spec(content: str) -> SkillSpecValidationResult:
    """Validate a SKILL.md string against the agentskills.io specification.

    Args:
        content: The full text content of a SKILL.md file.

    Returns:
        A ``SkillSpecValidationResult`` with errors, warnings, and parsed data.
    """
    result = SkillSpecValidationResult()

    # ------------------------------------------------------------------
    # 1. Frontmatter must exist
    # ------------------------------------------------------------------
    match = _FRONTMATTER_RE.match(content)
    if match is None:
        result.errors.append("Frontmatter block (--- ... ---) is missing.")
        result.ok = False
        return result

    raw_yaml_text = match.group(1)
    body = content[match.end() :]

    # Parse YAML safely
    try:
        parsed = yaml.safe_load(raw_yaml_text)
    except yaml.YAMLError as exc:
        result.errors.append(f"Frontmatter YAML is malformed: {exc}")
        result.ok = False
        return result

    if not isinstance(parsed, dict):
        result.errors.append(
            "Frontmatter must be a YAML mapping (key: value pairs), "
            f"got {type(parsed).__name__}."
        )
        result.ok = False
        return result

    result.frontmatter = parsed

    # ------------------------------------------------------------------
    # 2. Only allowed frontmatter keys
    # ------------------------------------------------------------------
    unknown_keys = set(parsed.keys()) - _ALLOWED_FRONTMATTER_KEYS
    if unknown_keys:
        result.errors.append(
            f"Unknown frontmatter keys: {sorted(unknown_keys)}. "
            f"Allowed: {sorted(_ALLOWED_FRONTMATTER_KEYS)}."
        )

    # ------------------------------------------------------------------
    # 3. name field: required, 3-64 chars, valid pattern
    # ------------------------------------------------------------------
    _validate_name(parsed, result)

    # ------------------------------------------------------------------
    # 4. description field: required, 1-1024 chars
    # ------------------------------------------------------------------
    _validate_description(parsed, result)

    # ------------------------------------------------------------------
    # 5. license: optional string
    # ------------------------------------------------------------------
    _validate_optional_string(parsed, "license", result, max_len=None)

    # ------------------------------------------------------------------
    # 6. compatibility: optional string (max 500 chars)
    # ------------------------------------------------------------------
    _validate_optional_string(
        parsed,
        "compatibility",
        result,
        max_len=_COMPATIBILITY_MAX_LEN,
    )

    # ------------------------------------------------------------------
    # 7. metadata: optional dict[str, str]
    # ------------------------------------------------------------------
    _validate_metadata(parsed, result)

    # ------------------------------------------------------------------
    # 8. allowed-tools: optional, space-delimited string
    # ------------------------------------------------------------------
    _validate_allowed_tools(parsed, result)

    # ------------------------------------------------------------------
    # 9. Body (instructions) must exist
    # ------------------------------------------------------------------
    instructions = body.strip()
    result.instructions_md = instructions

    if not instructions:
        result.errors.append("Instructions body (markdown after frontmatter) is empty.")

    # ------------------------------------------------------------------
    # 10. Instructions token-length warning
    # ------------------------------------------------------------------
    if instructions:
        estimated_tokens = len(instructions) / _CHARS_PER_TOKEN
        if estimated_tokens > _INSTRUCTIONS_TOKEN_WARN:
            result.warnings.append(
                f"Instructions are ~{int(estimated_tokens)} tokens "
                f"(estimated). Recommend staying under {_INSTRUCTIONS_TOKEN_WARN}."
            )

    # ------------------------------------------------------------------
    # Final ok status
    # ------------------------------------------------------------------
    result.ok = len(result.errors) == 0
    return result


def fix_metadata_values(metadata: dict[str, Any]) -> dict[str, str]:
    """Convert non-string metadata values to their string representations.

    The agentskills.io spec requires all metadata values to be plain strings.
    This helper normalises common violations:

    * ``list`` / ``tuple`` -- joined with ``", "`` (e.g., ``["a", "b"]`` -> ``"a, b"``).
    * ``dict`` -- serialised to a compact YAML string.
    * ``int`` / ``float`` -- ``str()`` conversion.
    * ``bool`` -- lowered to ``"true"`` / ``"false"``.
    * ``None`` -- converted to empty string ``""``.
    * Already a ``str`` -- returned as-is.

    Args:
        metadata: A dict whose values may not all be strings.

    Returns:
        A new dict with every value coerced to ``str``.
    """
    fixed: dict[str, str] = {}
    for key, value in metadata.items():
        fixed[str(key)] = _coerce_to_string(value)
    return fixed


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _coerce_to_string(value: Any) -> str:
    """Coerce a single value to its string representation."""
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    if isinstance(value, bool):
        # Must check before int because bool is a subclass of int in Python.
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, list | tuple):
        return ", ".join(_coerce_to_string(item) for item in value)
    if isinstance(value, dict):
        # Compact YAML serialisation for nested structures.
        dumped: str = yaml.dump(value, default_flow_style=True).strip()
        return dumped
    result: str = str(value)
    return result


def _validate_name(parsed: dict[str, Any], result: SkillSpecValidationResult) -> None:
    """Validate the ``name`` frontmatter field."""
    name = parsed.get("name")

    if name is None:
        result.errors.append("Required field 'name' is missing.")
        return

    if not isinstance(name, str):
        result.errors.append(
            f"Field 'name' must be a string, got {type(name).__name__}."
        )
        return

    length = len(name)
    if length < _NAME_MIN_LEN:
        result.errors.append(
            f"Field 'name' is too short ({length} chars). "
            f"Minimum is {_NAME_MIN_LEN}."
        )
    elif length > _NAME_MAX_LEN:
        result.errors.append(
            f"Field 'name' is too long ({length} chars). "
            f"Maximum is {_NAME_MAX_LEN}."
        )

    if not _NAME_RE.match(name):
        reasons: list[str] = []
        if name != name.lower():
            reasons.append("contains uppercase characters")
        if name.startswith("-") or name.endswith("-"):
            reasons.append("starts or ends with a hyphen")
        if "--" in name:
            reasons.append("contains consecutive hyphens")
        if re.search(r"[^a-z0-9-]", name):
            reasons.append("contains invalid characters (only a-z, 0-9, - allowed)")
        detail = "; ".join(reasons) if reasons else "does not match pattern"
        result.errors.append(f"Field 'name' is invalid: {detail}.")


def _validate_description(
    parsed: dict[str, Any],
    result: SkillSpecValidationResult,
) -> None:
    """Validate the ``description`` frontmatter field."""
    description = parsed.get("description")

    if description is None:
        result.errors.append("Required field 'description' is missing.")
        return

    if not isinstance(description, str):
        result.errors.append(
            f"Field 'description' must be a string, got {type(description).__name__}."
        )
        return

    stripped = description.strip()
    if not stripped:
        result.errors.append("Field 'description' is empty or whitespace-only.")
        return

    if len(stripped) > _DESCRIPTION_MAX_LEN:
        result.errors.append(
            f"Field 'description' is too long ({len(stripped)} chars). "
            f"Maximum is {_DESCRIPTION_MAX_LEN}."
        )


def _validate_optional_string(
    parsed: dict[str, Any],
    key: str,
    result: SkillSpecValidationResult,
    *,
    max_len: int | None,
) -> None:
    """Validate an optional string field."""
    value = parsed.get(key)
    if value is None:
        return

    if not isinstance(value, str):
        result.errors.append(
            f"Field '{key}' must be a string, got {type(value).__name__}."
        )
        return

    if max_len is not None and len(value) > max_len:
        result.errors.append(
            f"Field '{key}' is too long ({len(value)} chars). " f"Maximum is {max_len}."
        )


def _validate_metadata(
    parsed: dict[str, Any],
    result: SkillSpecValidationResult,
) -> None:
    """Validate the ``metadata`` frontmatter field.

    Per the spec, metadata must be a flat dict[str, str]. Non-string values
    are flagged as errors.
    """
    metadata = parsed.get("metadata")
    if metadata is None:
        return

    if not isinstance(metadata, dict):
        result.errors.append(
            f"Field 'metadata' must be a mapping, got {type(metadata).__name__}."
        )
        return

    for key, value in metadata.items():
        if not isinstance(key, str):
            result.errors.append(
                f"Metadata key {key!r} must be a string, got {type(key).__name__}."
            )
        if not isinstance(value, str):
            result.warnings.append(
                f"Metadata value for '{key}' should be a string, "
                f"got {type(value).__name__} ({value!r}). "
                f"Use fix_metadata_values() to auto-convert."
            )


def _validate_allowed_tools(
    parsed: dict[str, Any],
    result: SkillSpecValidationResult,
) -> None:
    """Validate the ``allowed-tools`` frontmatter field.

    Per the spec, allowed-tools is a single space-delimited string in YAML,
    not a YAML list.
    """
    value = parsed.get("allowed-tools")
    if value is None:
        return

    if isinstance(value, list):
        result.errors.append(
            "Field 'allowed-tools' must be a space-delimited string, "
            "not a YAML list. Write: allowed-tools: Tool1 Tool2"
        )
        return

    if not isinstance(value, str):
        result.errors.append(
            f"Field 'allowed-tools' must be a string, got {type(value).__name__}."
        )
        return

    stripped = value.strip()
    if not stripped:
        result.warnings.append("Field 'allowed-tools' is present but empty.")
