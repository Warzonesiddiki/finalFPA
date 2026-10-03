"""AI Output Validation, Guardrails, Provenance Tracking, and Usage Capping.

Implements requirements per docs/10_AI_INTEGRATION_SPEC.md §8, §9, §10, and §12:
- JSON schema validation of AI responses
- Anti-hallucination number reconciliation (assert numbers mentioned match computed figures)
- AI draft provenance tracking (stamped as 'AI draft — review before use.')
- Usage logging and cost/token capping (FactAIUsage, AICapConfig, AIUsageTracker)
- Model pinning validation and fallback management
"""

from __future__ import annotations

import csv
import io
import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Set, Tuple

import jsonschema
from jsonschema.exceptions import ValidationError as JSONSchemaValidationError

# ---------------------------------------------------------------------------
# Constants & Verdict Language List (§8.1, §5.1, §7)
# ---------------------------------------------------------------------------

AI_DRAFT_STAMP = "AI draft — review before use."

BANNED_VERDICT_PHRASES = [
    "wrong",
    "error",
    "fraud",
    "incorrect",
    "must be corrected",
    "should be reversed",
    "you failed",
    "your mistake",
]

NUMBER_REMOVED_PLACEHOLDER = "[figure removed — not from your data]"
NUMBER_MISMATCH_WARNING = "Some figures were removed because they did not match your data."

# Common word to count mappings for ordinal/prose checking (§8.2)
WORD_TO_COUNT = {
    "single": 1,
    "one": 1,
    "two": 2,
    "double": 2,
    "pair": 2,
    "three": 3,
    "triple": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}

# ---------------------------------------------------------------------------
# Standard Output JSON Schemas (§5, §8)
# ---------------------------------------------------------------------------

PROMPT_01_OUTPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["commentary", "drivers", "confidence", "caveats"],
    "properties": {
        "commentary": {"type": "string", "minLength": 40, "maxLength": 600},
        "drivers": {
            "type": "array",
            "maxItems": 3,
            "items": {
                "type": "object",
                "required": ["label", "direction", "evidence_ids"],
                "properties": {
                    "label": {"type": "string", "maxLength": 80},
                    "direction": {"type": "string", "enum": ["favourable", "unfavourable", "neutral"]},
                    "evidence_ids": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 5,
                        "items": {"type": "string", "maxLength": 20},
                    },
                },
                "additionalProperties": False,
            },
        },
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "caveats": {
            "type": "array",
            "maxItems": 3,
            "items": {"type": "string", "maxLength": 120},
        },
    },
    "additionalProperties": False,
}

PROMPT_02_OUTPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["suggestions"],
    "properties": {
        "suggestions": {
            "type": "array",
            "minItems": 1,
            "maxItems": 60,
            "items": {
                "type": "object",
                "required": ["source_column", "target_field", "confidence", "reason", "evidence_ids"],
                "properties": {
                    "source_column": {"type": "string", "maxLength": 200},
                    "target_field": {"type": "string", "maxLength": 60},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                    "reason": {"type": "string", "maxLength": 200},
                    "evidence_ids": {
                        "type": "array",
                        "maxItems": 5,
                        "items": {"type": "string", "maxLength": 20},
                    },
                },
                "additionalProperties": False,
            },
        }
    },
    "additionalProperties": False,
}

PROMPT_03_OUTPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["summary", "groups", "review_order", "confidence"],
    "properties": {
        "summary": {"type": "string", "minLength": 40, "maxLength": 800},
        "groups": {
            "type": "array",
            "minItems": 1,
            "maxItems": 6,
            "items": {
                "type": "object",
                "required": ["theme", "count", "severity_max", "exception_ids", "note"],
                "properties": {
                    "theme": {"type": "string", "maxLength": 60},
                    "count": {"type": "integer", "minimum": 1, "maximum": 120},
                    "severity_max": {"type": "string", "enum": ["high", "medium", "low"]},
                    "exception_ids": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 120,
                        "items": {"type": "string", "maxLength": 20},
                    },
                    "note": {"type": "string", "maxLength": 200},
                },
                "additionalProperties": False,
            },
        },
        "review_order": {
            "type": "array",
            "maxItems": 10,
            "items": {"type": "string", "maxLength": 20},
        },
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
    },
    "additionalProperties": False,
}

PROMPT_04_OUTPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["subject_line", "body_markdown", "items_referenced", "confidence"],
    "properties": {
        "subject_line": {"type": "string", "minLength": 8, "maxLength": 120},
        "body_markdown": {"type": "string", "minLength": 40, "maxLength": 1800},
        "items_referenced": {
            "type": "array",
            "minItems": 1,
            "maxItems": 25,
            "items": {"type": "string", "maxLength": 20},
        },
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
    },
    "additionalProperties": False,
}

PROMPT_SCHEMAS: Dict[str, dict] = {
    "PROMPT-01": PROMPT_01_OUTPUT_SCHEMA,
    "commentary": PROMPT_01_OUTPUT_SCHEMA,
    "PROMPT-02": PROMPT_02_OUTPUT_SCHEMA,
    "mapping": PROMPT_02_OUTPUT_SCHEMA,
    "PROMPT-03": PROMPT_03_OUTPUT_SCHEMA,
    "exception_summary": PROMPT_03_OUTPUT_SCHEMA,
    "PROMPT-04": PROMPT_04_OUTPUT_SCHEMA,
    "message_draft": PROMPT_04_OUTPUT_SCHEMA,
}


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class AISchemaValidationError(Exception):
    """Raised when an AI response fails strict JSON or schema validation."""
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.errors = errors or []


class CapExceededException(Exception):
    """Raised when an AI call exceeds configured usage/token/cost caps."""
    def __init__(self, message: str, cap_name: str, current_usage: Any, limit: Any):
        super().__init__(message)
        self.cap_name = cap_name
        self.current_usage = current_usage
        self.limit = limit


# ---------------------------------------------------------------------------
# 1. JSON Schema Validation (§8.1, §8.3)
# ---------------------------------------------------------------------------

def validate_json_schema(raw_response: str | dict, schema_or_prompt_id: str | dict) -> dict:
    """Strictly parse and validate AI response against JSON Schema.
    
    Tolerates clean markdown json code blocks (```json ... ```) but rejects
    trailing arbitrary text, missing fields, invalid types, or extra properties.
    """
    if isinstance(schema_or_prompt_id, str):
        if schema_or_prompt_id not in PROMPT_SCHEMAS:
            raise ValueError(f"Unknown prompt schema identifier: {schema_or_prompt_id}")
        schema = PROMPT_SCHEMAS[schema_or_prompt_id]
    else:
        schema = schema_or_prompt_id

    # Parse JSON strictly
    if isinstance(raw_response, dict):
        data = raw_response
    elif isinstance(raw_response, str):
        cleaned = raw_response.strip()
        # Handle markdown code blocks cleanly if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[len("```json"):].strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:].strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
        
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise AISchemaValidationError(f"Invalid JSON response: {str(exc)}") from exc
    else:
        raise AISchemaValidationError(f"Expected str or dict, got {type(raw_response).__name__}")

    # Validate schema
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        error_msgs = [f"at '{'/'.join(str(p) for p in err.path)}': {err.message}" for err in errors]
        raise AISchemaValidationError(
            f"Schema validation failed ({len(errors)} error(s)): {'; '.join(error_msgs)}",
            errors=error_msgs,
        )

    return data


def sanitize_fields(prompt_id: str, data: dict) -> dict:
    """Apply field-level sanitation per §8.1 step 4.
    
    e.g. Strip newlines or markdown headers/bullets from PROMPT-01 commentary.
    """
    cleaned = dict(data)
    if prompt_id in ("PROMPT-01", "commentary") and "commentary" in cleaned:
        commentary = cleaned["commentary"]
        # Replace newlines with spaces and condense multiple spaces
        commentary = re.sub(r"[\r\n]+", " ", commentary)
        # Strip common markdown headers (#) or list markers (*, -)
        commentary = re.sub(r"^[#*\-\s]+", "", commentary)
        cleaned["commentary"] = re.sub(r"\s+", " ", commentary).strip()

    return cleaned


def check_banned_phrases(text: str) -> List[str]:
    """Check text for banned verdict language (§8.1 step 6)."""
    text_lower = text.lower()
    found = []
    for phrase in BANNED_VERDICT_PHRASES:
        pattern = r"\b" + re.escape(phrase) + r"\b"
        if re.search(pattern, text_lower):
            found.append(phrase)
    return found


def validate_evidence_ids(
    data: dict, allowed_evidence_ids: Set[str] | List[str]
) -> Tuple[dict, bool, List[str]]:
    """Validate evidence IDs against payload IDs (§8.1 step 5).
    
    Strips unknown evidence IDs and returns (updated_data, mismatch_flag, stripped_ids).
    """
    allowed_set = set(allowed_evidence_ids)
    updated = dict(data)
    mismatch_found = False
    stripped: List[str] = []

    if "drivers" in updated and isinstance(updated["drivers"], list):
        new_drivers = []
        for driver in updated["drivers"]:
            ev_ids = driver.get("evidence_ids", [])
            valid_ids = [eid for eid in ev_ids if eid in allowed_set]
            invalid_ids = [eid for eid in ev_ids if eid not in allowed_set]
            if invalid_ids:
                mismatch_found = True
                stripped.extend(invalid_ids)
            driver_copy = dict(driver)
            driver_copy["evidence_ids"] = valid_ids
            new_drivers.append(driver_copy)
        updated["drivers"] = new_drivers

    if "suggestions" in updated and isinstance(updated["suggestions"], list):
        new_sugg = []
        for s in updated["suggestions"]:
            ev_ids = s.get("evidence_ids", [])
            valid_ids = [eid for eid in ev_ids if eid in allowed_set]
            invalid_ids = [eid for eid in ev_ids if eid not in allowed_set]
            s_copy = dict(s)
            if invalid_ids:
                mismatch_found = True
                stripped.extend(invalid_ids)
                s_copy["confidence"] = "low"  # Per §5.2 guardrails
            s_copy["evidence_ids"] = valid_ids
            new_sugg.append(s_copy)
        updated["suggestions"] = new_sugg

    if "groups" in updated and isinstance(updated["groups"], list):
        new_groups = []
        for g in updated["groups"]:
            ex_ids = g.get("exception_ids", [])
            valid_ids = [xid for xid in ex_ids if xid in allowed_set]
            invalid_ids = [xid for xid in ex_ids if xid not in allowed_set]
            g_copy = dict(g)
            if invalid_ids:
                mismatch_found = True
                stripped.extend(invalid_ids)
            g_copy["exception_ids"] = valid_ids
            # Engine count wins per §5.3 guardrails
            g_copy["count"] = len(valid_ids)
            new_groups.append(g_copy)
        updated["groups"] = new_groups

    if "items_referenced" in updated and isinstance(updated["items_referenced"], list):
        item_ids = updated["items_referenced"]
        valid_ids = [iid for iid in item_ids if iid in allowed_set]
        invalid_ids = [iid for iid in item_ids if iid not in allowed_set]
        if invalid_ids:
            mismatch_found = True
            stripped.extend(invalid_ids)
        updated["items_referenced"] = valid_ids

    return updated, mismatch_found, stripped


# ---------------------------------------------------------------------------
# 2. Anti-Hallucination Number Reconciliation (§8.2 - DEC-026)
# ---------------------------------------------------------------------------

def normalize_number_token(token: str) -> Optional[Decimal]:
    """Parse and normalize numeric string tokens across currencies, Indian/Western formatting, percentages."""
    cleaned = token.strip()
    # Strip currency symbols
    cleaned = re.sub(r"^[₹\$€£]|INR|Rs\.?", "", cleaned, flags=re.IGNORECASE).strip()
    # Strip leading sign
    has_plus = cleaned.startswith("+")
    has_minus = cleaned.startswith("-")
    if has_plus or has_minus:
        cleaned = cleaned[1:].strip()

    # Strip percent sign
    is_percent = cleaned.endswith("%")
    if is_percent:
        cleaned = cleaned[:-1].strip()

    # Remove commas
    cleaned = cleaned.replace(",", "").strip()

    if not cleaned:
        return None

    try:
        val = Decimal(cleaned)
        if has_minus:
            val = -val
        return val.normalize()
    except (InvalidOperation, ValueError):
        return None


def extract_payload_numbers(payload: Any) -> Set[Decimal]:
    """Recursively extract all numeric values from payload data structures.
    
    Generates base numbers and valid scaled variants (e.g. millions, lakhs, crores, percentages).
    """
    numbers: Set[Decimal] = set()

    def add_number_variants(dec_val: Decimal):
        dec_norm = dec_val.normalize()
        numbers.add(dec_norm)
        # Add absolute value as well
        numbers.add(abs(dec_norm))

        # Scaled representations for reporting (millions, lakhs, crores)
        # e.g., 10540000 -> 10.54 (millions), 105.4 (lakhs), 1.054 (crores)
        if dec_norm != Decimal(0):
            try:
                numbers.add((dec_norm / Decimal(1_000_000)).normalize())
                numbers.add((dec_norm / Decimal(100_000)).normalize())
                numbers.add((dec_norm / Decimal(10_000_000)).normalize())
                # Percentages: 5.4% <-> 0.054 or 5.4
                numbers.add((dec_norm * Decimal(100)).normalize())
                numbers.add((dec_norm / Decimal(100)).normalize())
            except Exception:
                pass

    def traverse(obj: Any):
        if isinstance(obj, (int, float)):
            try:
                add_number_variants(Decimal(str(obj)))
            except Exception:
                pass
        elif isinstance(obj, Decimal):
            add_number_variants(obj)
        elif isinstance(obj, str):
            # Attempt direct conversion
            parsed = normalize_number_token(obj)
            if parsed is not None:
                add_number_variants(parsed)
            # Also find standalone numbers inside strings
            # Match currency/percent/amounts: ₹1,05,40,000, 10540000, 5.4%, etc.
            tokens = re.findall(r"(?:[₹\$€£]\s*)?[+-]?\d{1,3}(?:,\d{2,3})*(?:\.\d+)?%?|[+-]?\d+(?:\.\d+)?%?", obj)
            for t in tokens:
                p = normalize_number_token(t)
                if p is not None:
                    add_number_variants(p)
        elif isinstance(obj, dict):
            for v in obj.values():
                traverse(v)
        elif isinstance(obj, (list, tuple, set)):
            for item in obj:
                traverse(item)

    traverse(payload)
    return numbers


# Regex to locate numeric tokens in text
# Excludes identifiers such as V-00931, REF/2026/114, Sep-26, EXC-018, col-1, etc.
# Numbers must not be immediately attached to alphabet letters or hyphens forming codes
NUMERIC_TOKEN_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_/-])(?:[₹\$€£]\s*)?[+-]?(?:\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s*%?(?![A-Za-z0-9_/-])"
)

# Sentence splitter (preserves decimal figures like 5.4%)
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9₹\"'\[])")


def split_sentences(text: str) -> List[str]:
    """Split text into sentences cleanly without splitting decimal numbers."""
    # First split on newlines
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    sentences: List[str] = []
    for line in lines:
        parts = SENTENCE_SPLIT_PATTERN.split(line)
        for p in parts:
            if p.strip():
                sentences.append(p.strip())
    return sentences


def check_sentence_numbers(sentence: str, allowed_numbers: Set[Decimal]) -> Tuple[bool, List[str]]:
    """Check if all numeric tokens in a sentence match allowed payload numbers.
    
    Returns (is_valid, offending_tokens).
    """
    matches = NUMERIC_TOKEN_PATTERN.findall(sentence)
    offending: List[str] = []

    for token in matches:
        norm = normalize_number_token(token)
        if norm is None:
            continue
        
        # Check direct or close float match (to handle float rounding e.g. 10.54)
        matched = False
        if norm in allowed_numbers or abs(norm) in allowed_numbers:
            matched = True
        else:
            for allowed in allowed_numbers:
                if abs(norm - allowed) < Decimal("0.0001"):
                    matched = True
                    break
        
        if not matched:
            offending.append(token)

    return len(offending) == 0, offending


def check_word_counts(text: str, allowed_numbers: Set[Decimal]) -> Tuple[bool, List[str]]:
    """Check ordinal and prose counts (e.g. 'three rows', 'two items') against payload counts (§8.2).
    
    Returns (mismatch_detected, warnings). Note: Word counts are flagged, NOT stripped.
    """
    warnings: List[str] = []
    text_lower = text.lower()

    # Pattern for word count followed by target nouns: e.g. 'three rows', 'two items'
    pattern = re.compile(r"\b(" + "|".join(WORD_TO_COUNT.keys()) + r")\s+(rows?|items?|postings?|transactions?|exceptions?|months?)\b")
    for match in pattern.finditer(text_lower):
        word = match.group(1)
        count_val = Decimal(WORD_TO_COUNT[word])
        noun = match.group(2)
        if count_val not in allowed_numbers:
            warnings.append(f"Prose count '{word} {noun}' ({count_val}) does not match any count in payload.")

    return len(warnings) > 0, warnings


@dataclass
class NumberReconciliationResult:
    reconciled_text: str
    number_mismatch_flag: bool
    completely_discarded: bool
    warnings: List[str] = field(default_factory=list)
    removed_sentences_count: int = 0
    total_sentences_count: int = 0


def reconcile_text_numbers(text: str, allowed_numbers: Set[Decimal]) -> NumberReconciliationResult:
    """Reconcile numbers in text per DEC-026: strip offending sentences and replace with placeholder."""
    sentences = split_sentences(text)
    if not sentences:
        return NumberReconciliationResult(
            reconciled_text=text,
            number_mismatch_flag=False,
            completely_discarded=False,
        )

    reconciled_sentences: List[str] = []
    mismatch_flag = False
    warnings: List[str] = []
    removed_count = 0

    for s in sentences:
        valid, offending = check_sentence_numbers(s, allowed_numbers)
        if valid:
            reconciled_sentences.append(s)
        else:
            mismatch_flag = True
            removed_count += 1
            reconciled_sentences.append(NUMBER_REMOVED_PLACEHOLDER)
            warnings.append(f"Offending figures removed: {', '.join(offending)}")

    if mismatch_flag:
        warnings.insert(0, NUMBER_MISMATCH_WARNING)

    # Check prose word counts
    has_word_mismatch, word_warnings = check_word_counts(text, allowed_numbers)
    warnings.extend(word_warnings)

    # Check if completely discarded (i.e. every sentence was removed)
    completely_discarded = removed_count == len(sentences)

    return NumberReconciliationResult(
        reconciled_text=" ".join(reconciled_sentences),
        number_mismatch_flag=mismatch_flag,
        completely_discarded=completely_discarded,
        warnings=warnings,
        removed_sentences_count=removed_count,
        total_sentences_count=len(sentences),
    )


def reconcile_numbers(
    data: dict, payload: Any, prompt_id: Optional[str] = None
) -> Tuple[dict, NumberReconciliationResult]:
    """Reconcile all numbers across response fields (commentary, drivers, caveats, body_markdown)."""
    allowed_numbers = extract_payload_numbers(payload)
    updated = dict(data)
    primary_text = ""

    if "commentary" in updated:
        primary_text = updated["commentary"]
        res = reconcile_text_numbers(primary_text, allowed_numbers)
        updated["commentary"] = res.reconciled_text
    elif "body_markdown" in updated:
        primary_text = updated["body_markdown"]
        res = reconcile_text_numbers(primary_text, allowed_numbers)
        updated["body_markdown"] = res.reconciled_text
    elif "summary" in updated:
        primary_text = updated["summary"]
        res = reconcile_text_numbers(primary_text, allowed_numbers)
        updated["summary"] = res.reconciled_text
    else:
        res = NumberReconciliationResult(
            reconciled_text="",
            number_mismatch_flag=False,
            completely_discarded=False,
        )

    # Reconcile caveats if present (§8.2)
    if "caveats" in updated and isinstance(updated["caveats"], list):
        new_caveats = []
        for cav in updated["caveats"]:
            valid, offending = check_sentence_numbers(cav, allowed_numbers)
            if valid:
                new_caveats.append(cav)
            else:
                res.number_mismatch_flag = True
                res.warnings.append(f"Caveat removed due to unreconciled figures: {', '.join(offending)}")
        updated["caveats"] = new_caveats

    # Reconcile driver labels if present (§8.2)
    if "drivers" in updated and isinstance(updated["drivers"], list):
        new_drivers = []
        for drv in updated["drivers"]:
            label = drv.get("label", "")
            valid, offending = check_sentence_numbers(label, allowed_numbers)
            drv_copy = dict(drv)
            if not valid:
                res.number_mismatch_flag = True
                drv_copy["label"] = NUMBER_REMOVED_PLACEHOLDER
                res.warnings.append(f"Driver label modified due to unreconciled figures: {', '.join(offending)}")
            new_drivers.append(drv_copy)
        updated["drivers"] = new_drivers

    return updated, res


# ---------------------------------------------------------------------------
# 3. AI Draft Provenance Tracking (§12)
# ---------------------------------------------------------------------------

@dataclass
class AIDraftProvenance:
    feature_code: str
    prompt_id: str
    prompt_version: str
    model: str
    provider: str
    input_scope: dict
    draft_id: str = field(default_factory=lambda: f"draft_{uuid.uuid4().hex[:12]}")
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    redaction_applied: bool = True
    truncated: bool = False
    number_mismatch_flag: bool = False
    confidence: str = "medium"
    status: str = "draft"  # 'draft', 'approved', 'rejected', 'superseded'
    stamp: str = AI_DRAFT_STAMP
    warnings: List[str] = field(default_factory=list)
    banned_phrases_detected: List[str] = field(default_factory=list)
    evidence_mismatch_flag: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def stamp_ai_draft(output_data: dict, provenance: AIDraftProvenance) -> dict:
    """Stamp draft with required provenance and visible AI draft label per §5, §12."""
    return {
        "stamp": provenance.stamp,
        "provenance": provenance.to_dict(),
        "data": output_data,
        "is_ai_draft": True,
    }


# ---------------------------------------------------------------------------
# 4. Usage Logging and Cost / Token Capping (§9)
# ---------------------------------------------------------------------------

@dataclass
class AICapConfig:
    """Configurable token and spend caps per docs/10_AI_INTEGRATION_SPEC.md §9.1."""
    output_tokens_per_call: int = 800
    input_tokens_per_call: int = 6000
    calls_per_hour: int = 60
    monthly_tokens: int = 2_000_000
    monthly_cost: float = 1500.0  # In INR
    # Default rates per 1,000 tokens in INR (§9.2)
    input_rate_per_1k: float = 0.15
    output_rate_per_1k: float = 0.77
    # Feature-specific output token limits
    feature_output_token_caps: Dict[str, int] = field(
        default_factory=lambda: {
            "PROMPT-01": 800,
            "commentary": 800,
            "PROMPT-02": 1200,
            "mapping": 1200,
            "PROMPT-03": 1500,
            "exception_summary": 1500,
            "PROMPT-04": 800,
            "message_draft": 800,
        }
    )


@dataclass
class FactAIUsage:
    """Usage log entry per docs/03_DATA_DICTIONARY.md §5 and §9.3."""
    usage_id: str
    occurred_at: str
    feature_code: str
    model: str
    prompt_version: str
    input_row_count: int
    tokens_in: int
    tokens_out: int
    estimated_cost: Decimal
    latency_ms: int
    outcome: str  # 'ok', 'schema_error', 'timeout', 'cap_exceeded', 'refused', 'network_error'
    provider: str = "azure"
    truncation_flags: bool = False
    redaction_applied: bool = True

    def to_dict(self) -> dict:
        d = asdict(self)
        d["estimated_cost"] = str(self.estimated_cost)
        return d


@dataclass
class CapCheckResult:
    allowed: bool
    cap_name: Optional[str] = None
    current_usage: Any = None
    limit: Any = None
    reset_date: Optional[str] = None
    message: Optional[str] = None
    outcome: str = "ok"


class AIUsageTracker:
    """In-memory and persistent tracker for AI usage and cap enforcement (§9)."""

    def __init__(self, config: Optional[AICapConfig] = None):
        self.config = config or AICapConfig()
        self.logs: List[FactAIUsage] = []

    def calculate_estimated_cost(self, tokens_in: int, tokens_out: int) -> Decimal:
        """Calculate estimated cost in INR from token counts and rates (§9.2)."""
        cost_in = (Decimal(tokens_in) / Decimal(1000)) * Decimal(str(self.config.input_rate_per_1k))
        cost_out = (Decimal(tokens_out) / Decimal(1000)) * Decimal(str(self.config.output_rate_per_1k))
        total = (cost_in + cost_out).quantize(Decimal("0.000001"))
        return total

    def get_hourly_call_count(self, now: Optional[datetime] = None) -> int:
        """Return number of calls in the past 60 minutes."""
        current_time = now or datetime.now(timezone.utc)
        count = 0
        for entry in self.logs:
            try:
                entry_dt = datetime.fromisoformat(entry.occurred_at)
                diff = (current_time - entry_dt).total_seconds()
                if 0 <= diff <= 3600:
                    count += 1
            except Exception:
                pass
        return count

    def get_monthly_usage(self, now: Optional[datetime] = None) -> Tuple[int, Decimal]:
        """Return (total_tokens, total_cost) for current month."""
        current_time = now or datetime.now(timezone.utc)
        curr_year = current_time.year
        curr_month = current_time.month

        total_tokens = 0
        total_cost = Decimal("0.000000")

        for entry in self.logs:
            try:
                entry_dt = datetime.fromisoformat(entry.occurred_at)
                if entry_dt.year == curr_year and entry_dt.month == curr_month:
                    total_tokens += (entry.tokens_in + entry.tokens_out)
                    total_cost += entry.estimated_cost
            except Exception:
                pass

        return total_tokens, total_cost

    def check_caps(
        self,
        feature_code: str,
        estimated_input_tokens: int = 0,
        now: Optional[datetime] = None,
    ) -> CapCheckResult:
        """Check whether current call is permitted under configured caps (§9.1)."""
        current_time = now or datetime.now(timezone.utc)
        # Compute reset date (first day of next month)
        if current_time.month == 12:
            reset_dt = datetime(current_time.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            reset_dt = datetime(current_time.year, current_time.month + 1, 1, tzinfo=timezone.utc)
        reset_date_str = reset_dt.strftime("%Y-%m-%d")

        # 1. Per-call input token cap
        if estimated_input_tokens > self.config.input_tokens_per_call:
            return CapCheckResult(
                allowed=False,
                cap_name="input_tokens_per_call",
                current_usage=estimated_input_tokens,
                limit=self.config.input_tokens_per_call,
                reset_date=None,
                message=f"Payload exceeds input token limit of {self.config.input_tokens_per_call} (got {estimated_input_tokens}).",
                outcome="cap_exceeded",
            )

        # 2. Hourly calls cap
        hourly_calls = self.get_hourly_call_count(current_time)
        if hourly_calls >= self.config.calls_per_hour:
            return CapCheckResult(
                allowed=False,
                cap_name="calls_per_hour",
                current_usage=hourly_calls,
                limit=self.config.calls_per_hour,
                reset_date=None,
                message=f"Hourly AI call limit reached ({hourly_calls}/{self.config.calls_per_hour}). Throttled until next hour.",
                outcome="cap_exceeded",
            )

        # 3. Monthly token cap
        monthly_tokens, monthly_cost = self.get_monthly_usage(current_time)
        if monthly_tokens >= self.config.monthly_tokens:
            return CapCheckResult(
                allowed=False,
                cap_name="monthly_tokens",
                current_usage=monthly_tokens,
                limit=self.config.monthly_tokens,
                reset_date=reset_date_str,
                message=f"Monthly token cap reached ({monthly_tokens:,}/{self.config.monthly_tokens:,}). Resets on {reset_date_str}.",
                outcome="cap_exceeded",
            )

        # 4. Monthly cost cap
        if float(monthly_cost) >= self.config.monthly_cost:
            return CapCheckResult(
                allowed=False,
                cap_name="monthly_cost",
                current_usage=float(monthly_cost),
                limit=self.config.monthly_cost,
                reset_date=reset_date_str,
                message=f"Monthly cost cap reached (₹{monthly_cost:.2f}/₹{self.config.monthly_cost:.2f}). Resets on {reset_date_str}.",
                outcome="cap_exceeded",
            )

        return CapCheckResult(allowed=True, outcome="ok")

    def record_usage(
        self,
        feature_code: str,
        prompt_version: str,
        model: str,
        provider: str,
        input_row_count: int,
        tokens_in: int,
        tokens_out: int,
        latency_ms: int,
        outcome: str = "ok",
        truncation_flags: bool = False,
        redaction_applied: bool = True,
        timestamp: Optional[str] = None,
    ) -> FactAIUsage:
        """Record an AI call into the usage log (§9.3)."""
        cost = self.calculate_estimated_cost(tokens_in, tokens_out)
        usage_entry = FactAIUsage(
            usage_id=f"ai_{uuid.uuid4().hex[:12]}",
            occurred_at=timestamp or datetime.now(timezone.utc).isoformat(),
            feature_code=feature_code,
            model=model,
            prompt_version=prompt_version,
            provider=provider,
            input_row_count=input_row_count,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            estimated_cost=cost,
            latency_ms=latency_ms,
            outcome=outcome,
            truncation_flags=truncation_flags,
            redaction_applied=redaction_applied,
        )
        self.logs.append(usage_entry)
        return usage_entry

    def export_csv(self) -> str:
        """Export usage log as CSV per §9.3 (contains no payload content)."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "usage_id",
            "occurred_at",
            "feature_code",
            "model",
            "prompt_version",
            "provider",
            "input_row_count",
            "tokens_in",
            "tokens_out",
            "estimated_cost",
            "latency_ms",
            "outcome",
            "truncation_flags",
            "redaction_applied",
        ])
        for entry in self.logs:
            writer.writerow([
                entry.usage_id,
                entry.occurred_at,
                entry.feature_code,
                entry.model,
                entry.prompt_version,
                entry.provider,
                entry.input_row_count,
                entry.tokens_in,
                entry.tokens_out,
                str(entry.estimated_cost),
                entry.latency_ms,
                entry.outcome,
                entry.truncation_flags,
                entry.redaction_applied,
            ])
        return output.getvalue()


# ---------------------------------------------------------------------------
# 5. Model Pinning and Fallback Management (§10)
# ---------------------------------------------------------------------------

class ModelPinningManager:
    """Enforces explicit model versions and manages ordered fallback chain (§10)."""

    FORBIDDEN_FLOATING_ALIASES = {"latest", "gpt-4o-latest", "claude-latest", "current"}

    def __init__(
        self,
        pinned_model: str = "gpt-4o-2024-08-06",
        fallbacks: Optional[List[str]] = None,
    ):
        self.validate_model_name(pinned_model)
        self.pinned_model = pinned_model
        self.fallbacks: List[str] = []
        if fallbacks:
            for fb in fallbacks[:3]:  # Max 3 entries per §10.3
                self.validate_model_name(fb)
                self.fallbacks.append(fb)

    @classmethod
    def validate_model_name(cls, model_name: str) -> None:
        """Assert no floating unversioned aliases are configured (§10.1)."""
        name_lower = model_name.strip().lower()
        if name_lower in cls.FORBIDDEN_FLOATING_ALIASES or name_lower.endswith("-latest"):
            raise ValueError(
                f"Floating model alias '{model_name}' is forbidden by DEC-026/§10.1. "
                "Must use an explicit pinned model version."
            )

    def get_execution_chain(self) -> List[str]:
        """Return ordered list of models ending with 'rule_based' fallback (§10.3)."""
        return [self.pinned_model] + self.fallbacks + ["rule_based"]


# ---------------------------------------------------------------------------
# 6. End-to-End Guardrail Pipeline (§8.1)
# ---------------------------------------------------------------------------

class AIGuardrailPipeline:
    """Executes the complete 10-step AI output validation pipeline (§8.1)."""

    def __init__(
        self,
        usage_tracker: Optional[AIUsageTracker] = None,
        model_manager: Optional[ModelPinningManager] = None,
    ):
        self.usage_tracker = usage_tracker or AIUsageTracker()
        self.model_manager = model_manager or ModelPinningManager()

    def process_ai_output(
        self,
        raw_response: str | dict,
        prompt_id: str,
        prompt_version: str,
        payload: Any,
        input_scope: dict,
        allowed_evidence_ids: Optional[Set[str] | List[str]] = None,
        model: Optional[str] = None,
        provider: str = "azure",
        tokens_in: int = 0,
        tokens_out: int = 0,
        latency_ms: int = 0,
        redaction_applied: bool = True,
    ) -> Tuple[Optional[dict], AIDraftProvenance, Optional[FactAIUsage]]:
        """Validate and reconcile AI response through §8.1 pipeline."""
        chosen_model = model or self.model_manager.pinned_model
        warnings: List[str] = []
        truncated = False

        # Step 2 & 3: Parse JSON & Schema Validation
        try:
            parsed = validate_json_schema(raw_response, prompt_id)
        except AISchemaValidationError as err:
            usage = self.usage_tracker.record_usage(
                feature_code=prompt_id,
                prompt_version=prompt_version,
                model=chosen_model,
                provider=provider,
                input_row_count=len(payload) if isinstance(payload, (list, dict)) else 1,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=latency_ms,
                outcome="schema_error",
                truncation_flags=False,
                redaction_applied=redaction_applied,
            )
            provenance = AIDraftProvenance(
                feature_code=prompt_id,
                prompt_id=prompt_id,
                prompt_version=prompt_version,
                model=chosen_model,
                provider=provider,
                input_scope=input_scope,
                confidence="low",
                status="rejected",
                warnings=[f"Schema validation failure: {str(err)}"],
            )
            return None, provenance, usage

        # Step 4: Field-level sanitation
        cleaned = sanitize_fields(prompt_id, parsed)

        # Step 5: Evidence ID validation
        evidence_mismatch = False
        if allowed_evidence_ids is not None:
            cleaned, evidence_mismatch, stripped_ids = validate_evidence_ids(
                cleaned, allowed_evidence_ids
            )
            if evidence_mismatch:
                warnings.append(f"Unknown evidence IDs stripped: {', '.join(stripped_ids)}")

        # Step 6: Banned-phrase / verdict language check
        banned_found: List[str] = []
        for text_field in ("commentary", "body_markdown", "summary"):
            if text_field in cleaned and isinstance(cleaned[text_field], str):
                banned_found.extend(check_banned_phrases(cleaned[text_field]))
        if banned_found:
            warnings.append(f"Banned verdict language detected: {', '.join(banned_found)}")

        # Step 7: Anti-hallucination number reconciliation (§8.2)
        cleaned, recon_result = reconcile_numbers(cleaned, payload, prompt_id)
        warnings.extend(recon_result.warnings)

        # Step 8: Length check & sentence boundary truncation
        if "commentary" in cleaned and len(cleaned["commentary"]) > 600:
            truncated = True
            commentary = cleaned["commentary"]
            sentences = split_sentences(commentary)
            curr = ""
            for s in sentences:
                candidate = (curr + " " + s).strip() if curr else s
                if len(candidate) <= 600:
                    curr = candidate
                else:
                    break
            cleaned["commentary"] = curr
            warnings.append("Commentary exceeded 600 characters and was truncated at sentence boundary.")

        # Step 9: Confidence present & valid
        confidence = cleaned.get("confidence", "medium")
        if evidence_mismatch:
            confidence = "low"

        # Record successful usage
        usage = self.usage_tracker.record_usage(
            feature_code=prompt_id,
            prompt_version=prompt_version,
            model=chosen_model,
            provider=provider,
            input_row_count=len(payload) if isinstance(payload, (list, dict)) else 1,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            outcome="ok",
            truncation_flags=truncated,
            redaction_applied=redaction_applied,
        )

        # Step 10: Store as AIDraft with provenance
        provenance = AIDraftProvenance(
            feature_code=prompt_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            model=chosen_model,
            provider=provider,
            input_scope=input_scope,
            redaction_applied=redaction_applied,
            truncated=truncated,
            number_mismatch_flag=recon_result.number_mismatch_flag,
            confidence=confidence,
            status="draft",
            stamp=AI_DRAFT_STAMP,
            warnings=warnings,
            banned_phrases_detected=banned_found,
            evidence_mismatch_flag=evidence_mismatch,
        )

        if recon_result.completely_discarded:
            provenance.status = "rejected"
            warnings.append("Entire draft was removed because no figures matched payload data. Discarded.")
            return None, provenance, usage

        stamped = stamp_ai_draft(cleaned, provenance)
        return stamped, provenance, usage
