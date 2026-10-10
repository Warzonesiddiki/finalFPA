"""AI Integration Client, Redaction Engine, Prompt Loader, and Rule-Based Fallback.

Implements doc 10 (AI Integration Specification) §1 through §7, §8, §11:
- OpenAI-compatible and Azure OpenAI chat completions caller via httpx
- Vendor name, confidential amount, and description redaction engine
- Versioned prompt template loader for PROMPT-01 through PROMPT-04
- Offline deterministic rule-based narrative generator fallback (Keyless mode)
- Output validation pipeline with strict schema checking, banned-phrase detection,
  evidence ID validation, and DEC-026 number-mismatch stripping
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import httpx
import jsonschema

logger = logging.getLogger(__name__)

BANNED_PHRASES = [
    "wrong",
    "error",
    "fraud",
    "incorrect",
    "must be corrected",
    "should be reversed",
]

# ---------------------------------------------------------------------------
# Configuration & Result Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class AIConfig:
    """Configuration for AI Integration."""

    provider: str = "none"  # "none", "openai_compatible", "azure_openai"
    base_url: str = ""  # Base URL for OpenAI-compatible or endpoint for Azure
    api_key: str = ""
    model: str = "gpt-4o"
    api_version: str = "2024-02-15-preview"  # Azure only
    temperature: float = 0.2
    timeout_seconds: float = 30.0
    max_retries: int = 2
    mask_vendors: bool = True
    mask_descriptions: bool = True
    mask_confidential_amounts: bool = False
    confidential_amounts: list[str] = field(default_factory=list)
    custom_mask_patterns: list[str] = field(default_factory=list)


@dataclass
class AIDraftResult:
    """Result of an AI generation or fallback invocation."""

    content: dict[str, Any]
    raw_response: str
    is_ai_draft: bool
    label: str  # "AI draft — review before use." or "Rule-based summary"
    prompt_id: str
    prompt_version: str
    model: str
    provider: str
    number_mismatch_flag: bool = False
    banned_phrase_flag: bool = False
    evidence_flag: bool = False
    redaction_applied: bool = False
    truncated: bool = False
    outcome: str = "ok"  # ok, schema_error, timeout, network_error, refused, cap_exceeded
    latency_ms: float = 0.0
    vendor_mapping: dict[str, str] = field(default_factory=dict)
    warning: str | None = None


# ---------------------------------------------------------------------------
# Redaction Engine (§6 & §7)
# ---------------------------------------------------------------------------


class RedactionEngine:
    """Engine for redacting vendor names, descriptions, confidential amounts,

    and sanitizing inputs against prompt-injection.
    """

    VENDOR_PATTERN = re.compile(
        r"\b(?:Vendor\s+)?([Vv](?:endor)?[-_ ]?[A-Za-z0-9]{3,10}|[A-Z][A-Za-z0-9&., ]{2,30}\s+(?:Ltd|LLC|Inc|Corp|Pvt|GmbH|Services|Supplies|Repairs))\b",
        re.IGNORECASE,
    )
    EXPLICIT_VENDOR_ID_PATTERN = re.compile(r"\bV-\d{3,6}\b", re.IGNORECASE)

    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
    PHONE_PATTERN = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
    LONG_DIGIT_PATTERN = re.compile(r"\b\d{9,}\b")

    HTML_TAG_PATTERN = re.compile(r"<[^>]*>")
    DELIMITER_ESCAPE_PATTERN = re.compile(r"</?data>", re.IGNORECASE)
    ZERO_WIDTH_PATTERN = re.compile(r"[\u200B-\u200D\uFEFF]")
    RTL_OVERRIDE_PATTERN = re.compile(r"[\u202A-\u202E\u2066-\u2069]")
    CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")

    def __init__(self, config: AIConfig | None = None):
        self.config = config or AIConfig()

    def sanitize_text(self, text: str, max_length: int | None = None) -> str:
        """Sanitizes imported text per §7: strips HTML, control characters,

        zero-width chars, RTL overrides, and delimiter escapes.
        """
        if not text:
            return ""
        # Strip delimiter escapes first to avoid breaking <data>...</data> boundary
        cleaned = self.DELIMITER_ESCAPE_PATTERN.sub("", text)
        cleaned = self.HTML_TAG_PATTERN.sub("", cleaned)
        cleaned = self.ZERO_WIDTH_PATTERN.sub("", cleaned)
        cleaned = self.RTL_OVERRIDE_PATTERN.sub("", cleaned)
        cleaned = self.CONTROL_CHAR_PATTERN.sub("", cleaned)

        if max_length and len(cleaned) > max_length:
            cleaned = cleaned[:max_length]

        return cleaned

    def mask_description(self, description: str, max_length: int = 120) -> str:
        """Masks sensitive elements in transaction descriptions per §6.2:

        email addresses, URLs, phone numbers, long digit runs, and caps length.
        """
        sanitized = self.sanitize_text(description)
        masked = self.EMAIL_PATTERN.sub("[EMAIL]", sanitized)
        masked = self.URL_PATTERN.sub("[URL]", masked)
        masked = self.PHONE_PATTERN.sub("[PHONE]", masked)
        masked = self.LONG_DIGIT_PATTERN.sub("[REDACTED_NUM]", masked)

        if len(masked) > max_length:
            masked = masked[:max_length]
        return masked

    def mask_vendors(
        self,
        text: str,
        vendor_map: dict[str, str] | None = None,
        known_vendors: list[str] | None = None,
    ) -> tuple[str, dict[str, str]]:
        """Masks vendor names and codes with stable pseudonyms (Vendor A, Vendor B...)

        per §6.2. Returns the masked text and the private pseudonym mapping.
        """
        mapping = dict(vendor_map or {})
        existing_pseudonyms = set(mapping.values())

        def get_next_pseudonym() -> str:
            idx = len(existing_pseudonyms)
            # A, B, ..., Z, AA, AB...
            letters = ""
            while idx >= 0:
                letters = chr(65 + (idx % 26)) + letters
                idx = (idx // 26) - 1
            pseudo = f"Vendor {letters}"
            existing_pseudonyms.add(pseudo)
            return pseudo

        # 1. Mask explicitly known vendor list if provided
        result = text
        if known_vendors:
            # Sort longest first so "Vendor ABC Inc" is replaced before "Vendor ABC"
            for v in sorted(known_vendors, key=len, reverse=True):
                if not v or len(v.strip()) < 2:
                    continue
                if v not in mapping:
                    mapping[v] = get_next_pseudonym()
                pattern = re.compile(re.escape(v), re.IGNORECASE)
                result = pattern.sub(mapping[v], result)

        # 2. Mask regex vendor codes like V-00931 or V-00412
        def replace_vendor_code(match: re.Match) -> str:
            raw = match.group(0)
            if raw not in mapping:
                mapping[raw] = get_next_pseudonym()
            return mapping[raw]

        result = self.EXPLICIT_VENDOR_ID_PATTERN.sub(replace_vendor_code, result)

        return result, mapping

    def mask_confidential_amounts(
        self,
        text: str,
        confidential_amounts: list[str] | None = None,
        replacement: str = "[CONFIDENTIAL_AMOUNT]",
    ) -> str:
        """Redacts specified confidential figures or custom sensitive amounts."""
        if not confidential_amounts:
            return text
        result = text
        for amt in confidential_amounts:
            if not amt:
                continue
            # Escaped pattern matching currency symbols and number
            pattern = re.compile(
                r"(?:[₹\$€£]\s*)?" + re.escape(amt.strip()) + r"(?:\.00)?",
                re.IGNORECASE,
            )
            result = pattern.sub(replacement, result)
        return result

    def apply_custom_patterns(self, text: str, patterns: list[str] | None = None) -> str:
        """Applies user-configured regex patterns to mask sensitive tokens."""
        if not patterns:
            return text
        result = text
        for pat in patterns:
            try:
                regex = re.compile(pat, re.IGNORECASE)
                result = regex.sub("[REDACTED]", result)
            except re.error as e:
                logger.warning(f"Invalid custom mask pattern skipped: {pat}, error: {e}")
        return result

    def reverse_mask_vendors(self, text: str, vendor_map: dict[str, str]) -> str:
        """Locally substitutes pseudonyms back with original vendor names."""
        result = text
        for original, pseudonym in vendor_map.items():
            result = result.replace(pseudonym, original)
        return result

    def redact_payload_value(
        self,
        val: Any,
        vendor_map: dict[str, str],
        known_vendors: list[str] | None = None,
    ) -> Any:
        """Recursively redacts dictionary, list, or string structures."""
        if isinstance(val, str):
            res = self.sanitize_text(val)
            if self.config.mask_descriptions and len(res) > 20:
                res = self.mask_description(res)
            if self.config.mask_vendors:
                res, _ = self.mask_vendors(res, vendor_map=vendor_map, known_vendors=known_vendors)
            if self.config.mask_confidential_amounts:
                res = self.mask_confidential_amounts(res, self.config.confidential_amounts)
            if self.config.custom_mask_patterns:
                res = self.apply_custom_patterns(res, self.config.custom_mask_patterns)
            return res
        elif isinstance(val, list):
            return [
                self.redact_payload_value(item, vendor_map, known_vendors=known_vendors)
                for item in val
            ]
        elif isinstance(val, dict):
            new_dict = {}
            for k, v in val.items():
                # Specific field handling
                if k in ("description", "note") and isinstance(v, str):
                    clean_v = self.mask_description(v)
                    if self.config.mask_vendors:
                        clean_v, _ = self.mask_vendors(
                            clean_v,
                            vendor_map=vendor_map,
                            known_vendors=known_vendors,
                        )
                    new_dict[k] = clean_v
                elif k in ("vendor", "vendor_name", "vendor_code") and isinstance(v, str):
                    if self.config.mask_vendors:
                        masked_v, _ = self.mask_vendors(
                            v, vendor_map=vendor_map, known_vendors=known_vendors
                        )
                        new_dict[k] = masked_v
                    else:
                        new_dict[k] = self.sanitize_text(v)
                elif k in ("amount", "value") and self.config.mask_confidential_amounts:
                    v_str = str(v)
                    new_dict[k] = self.mask_confidential_amounts(
                        v_str, self.config.confidential_amounts
                    )
                else:
                    new_dict[k] = self.redact_payload_value(
                        v, vendor_map, known_vendors=known_vendors
                    )
            return new_dict
        return val


# ---------------------------------------------------------------------------
# Output Validation Pipeline & Number Mismatch (§8.1 & §8.2 DEC-026)
# ---------------------------------------------------------------------------


class OutputValidator:
    """Validates LLM output against schemas, checks evidence IDs, detects

    banned verdict language, and enforces DEC-026 number-mismatch stripping.
    """

    # Numeric token grammar.
    #
    # DEC-026 (docs/10 §8.2) requires that "a numeric token in the AI text
    # matches a value present in the payload (after normalising separators,
    # symbols, grouping and trailing zeros)" be ACCEPTED. That makes correct
    # tokenisation load-bearing: a token that does not correspond to the whole
    # number in the text can never match, so the sentence is wrongly stripped.
    #
    # The previous pattern led with an unanchored `\d{1,3}(?:,\d{2,3})*`, so
    # findall() consumed a bare 4+ digit number three digits at a time:
    # '5000' -> [' 500', '0'] and '1200.50' -> [' 120', '0.50']. Those
    # fragments are absent from `valid_numbers` when the data arrives as a
    # number, so DEC-026 deleted sentences whose figures were correct.
    #
    # This version:
    #   * requires either a comma-grouped form (\d{1,3}(?:,\d{2,3})+, covering
    #     both Indian 1,20,000 and Western 1,200,000) or a plain \d+ run,
    #     instead of a fixed-width first group;
    #   * anchors both ends with (?<!\d) / (?!\d) so a match can never begin or
    #     end mid-digit-run, which is what produced the chunking;
    #   * keeps the optional currency symbol, sign, decimal part and percent
    #     sign that DEC-026 normalisation relies on.
    NUMBER_TOKEN_PATTERN = re.compile(
        r"(?<!\d)[₹\$€£]?\s*[-+]?(?:\d{1,3}(?:,\d{2,3})+|\d+)(?:\.\d+)?%?(?!\d)"
    )

    @staticmethod
    def extract_numbers_from_obj(obj: Any) -> set[str]:
        """Collects all numeric representations from arbitrary object/JSON."""
        numbers: set[str] = set()

        def extract(val: Any):
            if isinstance(val, (int, float, Decimal)):
                val_str = str(val)
                numbers.add(val_str)
                try:
                    d = Decimal(val_str)
                    numbers.add(f"{d:.2f}")
                    numbers.add(f"{d:.1f}")
                    numbers.add(f"{int(d)}")
                except InvalidOperation:
                    pass
            elif isinstance(val, str):
                # Search for all number-like tokens in strings
                matches = OutputValidator.NUMBER_TOKEN_PATTERN.findall(val)
                for m in matches:
                    clean = re.sub(r"[₹\$€£,\s+]", "", m)
                    if clean.endswith("%"):
                        clean = clean[:-1]
                    if clean:
                        numbers.add(clean)
                        try:
                            d = Decimal(clean)
                            numbers.add(f"{d:.2f}")
                            numbers.add(f"{d:.1f}")
                            numbers.add(f"{int(d)}")
                            # Millions & Lakhs
                            numbers.add(f"{d / Decimal('1000000'):.2f}")
                            numbers.add(f"{d / Decimal('100000'):.2f}")
                        except InvalidOperation:
                            pass
            elif isinstance(val, list):
                for item in val:
                    extract(item)
            elif isinstance(val, dict):
                for k, v in val.items():
                    extract(k)
                    extract(v)

        extract(obj)
        return numbers

    @staticmethod
    def extract_evidence_ids_from_obj(obj: Any) -> set[str]:
        """Collects all IDs present in payload data."""
        ids: set[str] = set()

        def extract(val: Any):
            if isinstance(val, dict):
                if "id" in val and isinstance(val["id"], str):
                    ids.add(val["id"])
                if "rule_id" in val and isinstance(val["rule_id"], str):
                    ids.add(val["rule_id"])
                for v in val.values():
                    extract(v)
            elif isinstance(val, list):
                for item in val:
                    extract(item)

        extract(obj)
        return ids

    @staticmethod
    def check_banned_phrases(text: str) -> list[str]:
        """Detects banned verdict phrases."""
        found = []
        lowered = text.lower()
        for phrase in BANNED_PHRASES:
            if re.search(r"\b" + re.escape(phrase) + r"\b", lowered):
                found.append(phrase)
        return found

    @classmethod
    def validate_and_sanitize_numbers(
        cls,
        text: str,
        valid_numbers: set[str],
    ) -> tuple[str, bool]:
        """Enforces DEC-026 number-mismatch check.

        If a sentence contains a number not present in valid_numbers,
        the sentence is removed and replaced with [figure removed — not from your data].
        Returns (new_text, mismatch_flag).
        """
        # Split into sentences preserving punctuation
        sentence_end = re.compile(r"(?<=[.!?])\s+")
        sentences = sentence_end.split(text)
        if not sentences or (len(sentences) == 1 and not sentences[0]):
            return text, False

        mismatch_found = False
        cleaned_sentences: list[str] = []

        for sentence in sentences:
            tokens = cls.NUMBER_TOKEN_PATTERN.findall(sentence)
            sentence_mismatch = False
            for tok in tokens:
                clean_tok = re.sub(r"[₹\$€£,\s+]", "", tok)
                if clean_tok.endswith("%"):
                    clean_tok = clean_tok[:-1]
                if not clean_tok:
                    continue

                is_valid = False
                if clean_tok in valid_numbers:
                    is_valid = True
                else:
                    try:
                        d = Decimal(clean_tok)
                        # Check equality with any decimal in valid_numbers
                        for vn in valid_numbers:
                            try:
                                if Decimal(vn) == d:
                                    is_valid = True
                                    break
                            except InvalidOperation:
                                continue
                    except InvalidOperation:
                        pass

                if not is_valid:
                    sentence_mismatch = True
                    mismatch_found = True
                    break

            if sentence_mismatch:
                cleaned_sentences.append("[figure removed — not from your data]")
            else:
                cleaned_sentences.append(sentence)

        result = " ".join(cleaned_sentences)
        return result, mismatch_found


# ---------------------------------------------------------------------------
# Versioned Prompt Template Loader (§4 & §5)
# ---------------------------------------------------------------------------


@dataclass
class PromptTemplate:
    """Loaded prompt template definition."""

    prompt_id: str
    version: str
    feature_code: str
    system_prompt: str
    user_template: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    max_input_tokens: int = 6000
    max_output_tokens: int = 800

    def render_payload(self, variables: dict[str, Any]) -> str:
        """Validates variables against input_schema and renders the user payload.

        Refuses to return a payload with any unresolved {{TOKEN}}.
        """
        # Validate input schema
        jsonschema.validate(instance=variables, schema=self.input_schema)

        # Substitute tokens
        rendered = self.user_template
        for k, v in variables.items():
            token = f"{{{{{k}}}}}"
            rendered = rendered.replace(token, str(v))

        # Check for unresolved tokens
        unresolved = re.findall(r"\{\{([A-Za-z0-9_]+)\}\}", rendered)
        if unresolved:
            raise ValueError(f"Unresolved placeholders in template {self.prompt_id}: {unresolved}")

        return rendered


class PromptTemplateLoader:
    """Loads and caches prompt templates from disk or built-in registry."""

    _BUILTIN_PROMPTS: dict[str, PromptTemplate] = {}

    def __init__(self, prompts_dir: Path | None = None):
        self.prompts_dir = prompts_dir or (Path(__file__).parent / "prompts")
        self._cache: dict[str, PromptTemplate] = {}

    @classmethod
    def register_builtin(cls, template: PromptTemplate):
        key = f"{template.prompt_id}.{template.version}"
        cls._BUILTIN_PROMPTS[key] = template

    def get_template(self, prompt_id: str, version: str = "v1") -> PromptTemplate:
        key = f"{prompt_id}.{version}"
        if key in self._cache:
            return self._cache[key]

        # Try loading from file
        file_path = self.prompts_dir / f"{prompt_id}.{version}.md"
        if file_path.is_file():
            template = self._parse_template_file(file_path)
            self._cache[key] = template
            return template

        # Fallback to built-in registry
        if key in self._BUILTIN_PROMPTS:
            return self._BUILTIN_PROMPTS[key]

        raise FileNotFoundError(
            f"Prompt template {key} not found at {file_path} and not in built-in registry."
        )

    def _parse_template_file(self, path: Path) -> PromptTemplate:
        content = path.read_text(encoding="utf-8")

        # Parse YAML-like header
        header_match = re.search(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not header_match:
            raise ValueError(f"Template {path.name} is missing YAML header block.")

        header_text = header_match.group(1)
        meta: dict[str, Any] = {}
        for line in header_text.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()

        # Parse sections
        body = content[header_match.end() :]
        sections = re.split(r"^#\s+(.+)$", body, flags=re.MULTILINE)

        parsed_sections: dict[str, str] = {}
        for i in range(1, len(sections), 2):
            sec_title = sections[i].strip()
            sec_content = sections[i + 1].strip()
            parsed_sections[sec_title] = sec_content

        system_prompt = parsed_sections.get("System Prompt", "").strip()
        user_template = parsed_sections.get("User Payload Template", "").strip()

        input_schema_raw = parsed_sections.get("Input Schema", "")
        input_schema_json = self._extract_json_block(input_schema_raw)

        output_schema_raw = parsed_sections.get("Output Schema", "")
        output_schema_json = self._extract_json_block(output_schema_raw)

        return PromptTemplate(
            prompt_id=meta.get("prompt_id", path.stem.split(".")[0]),
            version=meta.get("version", "v1"),
            feature_code=meta.get("feature_code", "generic"),
            system_prompt=system_prompt,
            user_template=user_template,
            input_schema=input_schema_json,
            output_schema=output_schema_json,
            max_input_tokens=int(meta.get("max_input_tokens", 6000)),
            max_output_tokens=int(meta.get("max_output_tokens", 800)),
        )

    @staticmethod
    def _extract_json_block(text: str) -> dict[str, Any]:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        # Try direct parse
        return json.loads(text)


# ---------------------------------------------------------------------------
# Offline Deterministic Rule-Based Fallback Generator (§11)
# ---------------------------------------------------------------------------


class RuleBasedNarrativeGenerator:
    """Offline, deterministic generator producing usable structured outputs

    with the label 'Rule-based summary' and zero external dependencies.
    """

    @classmethod
    def generate_prompt_01(cls, variables: dict[str, Any]) -> dict[str, Any]:
        """PROMPT-01: Variance commentary draft fallback."""
        data_raw = variables.get("data_block_json", "{}")
        data = json.loads(data_raw) if isinstance(data_raw, str) else data_raw

        subject = data.get("subject", {})
        account_name = subject.get("account_name", "Account")
        measures = {m.get("label"): m for m in data.get("measures", [])}
        period_label = variables.get("period_label", "current period")

        var_pct = measures.get("Variance %", {}).get("value", "0.0")
        favourability = measures.get("Favourability", {}).get("value", "Unfavourable")
        var_amt = measures.get("Variance", {}).get("value", "0.00")
        currency = measures.get("Variance", {}).get("currency", "")

        contributors = data.get("contributors", [])
        driver_items = []
        contrib_texts = []
        for c in contributors[:2]:
            c_label = c.get("label", "Contributor")
            c_amt = c.get("amount", "")
            driver_items.append(
                {
                    "label": f"{c_label} ({c_amt})",
                    "direction": "unfavourable"
                    if favourability.lower() == "unfavourable"
                    else "favourable",
                    "evidence_ids": [c.get("id")] if c.get("id") else [],
                }
            )
            contrib_texts.append(f"{c_label} for {c_amt}")

        contrib_str = ", driven by " + " and ".join(contrib_texts) if contrib_texts else ""
        currency_prefix = f"{currency} " if currency else ""

        commentary = (
            f"{account_name} is {var_pct}% {favourability.lower()} to budget for {period_label} "
            f"with a variance of {currency_prefix}{var_amt}{contrib_str}. "
            f"Figures are extracted from engine calculations for human review."
        )
        if len(commentary) > 600:
            commentary = commentary[:597] + "..."

        return {
            "commentary": commentary,
            "drivers": driver_items[:3],
            "confidence": "low",
            "caveats": ["Rule-based summary assembled directly from engine numbers without AI."],
        }

    @classmethod
    def generate_prompt_02(cls, variables: dict[str, Any]) -> dict[str, Any]:
        """PROMPT-02: Mapping suggestion fallback using rule-based fingerprinting."""
        unmapped_raw = variables.get("unmapped_columns_json", "[]")
        unmapped_cols = json.loads(unmapped_raw) if isinstance(unmapped_raw, str) else unmapped_raw

        accepted_raw = variables.get("accepted_mappings_json", "[]")
        accepted_mappings = (
            json.loads(accepted_raw) if isinstance(accepted_raw, str) else accepted_raw
        )

        target_field_list_str = variables.get("target_field_list", "")
        allowed_targets = {
            f.strip()
            for f in target_field_list_str.replace("\n", ",").replace(";", ",").split(",")
            if f.strip()
        }
        allowed_targets.add("ignore")

        # Map by normalized string similarity/tokens
        accepted_dict = {m.get("source_column", "").strip().lower(): m for m in accepted_mappings}

        COMMON_FIELD_PATTERNS = {
            "period": "period_code",
            "fiscal": "period_code",
            "month": "period_code",
            "account": "account_code",
            "gl": "account_code",
            "ledger": "account_code",
            "center": "cost_center_code",
            "centre": "cost_center_code",
            "entity": "entity_code",
            "company": "entity_code",
            "debit": "debit_amount",
            "credit": "credit_amount",
            "vendor": "vendor_code",
            "supplier": "vendor_code",
            "invoice": "invoice_number",
            "voucher": "invoice_number",
            "desc": "description",
            "narrative": "description",
        }

        suggestions = []
        for col in unmapped_cols:
            col_name = col.get("source_column", "")
            norm = col_name.strip().lower()

            target = "ignore"
            confidence = "low"
            reason = "No high-confidence deterministic match found."
            evidence_ids = []

            # Check accepted mappings
            if norm in accepted_dict:
                acc = accepted_dict[norm]
                acc_field = acc.get("accepted_field", "")
                if acc_field in allowed_targets:
                    target = acc_field
                    confidence = "high"
                    reason = f"Matches previous accepted mapping for {col_name}."
                    if acc.get("id"):
                        evidence_ids.append(acc["id"])

            # Check common patterns if still ignore
            if target == "ignore":
                for token, mapped_target in COMMON_FIELD_PATTERNS.items():
                    if token in norm and mapped_target in allowed_targets:
                        target = mapped_target
                        confidence = "medium"
                        reason = f"Column name contains '{token}' matching target field."
                        break

            suggestions.append(
                {
                    "source_column": col_name,
                    "target_field": target,
                    "confidence": confidence,
                    "reason": reason[:200],
                    "evidence_ids": evidence_ids,
                }
            )

        return {"suggestions": suggestions}

    @classmethod
    def generate_prompt_03(cls, variables: dict[str, Any]) -> dict[str, Any]:
        """PROMPT-03: Exception summary fallback."""
        exc_raw = variables.get("exceptions_json", "[]")
        exceptions = json.loads(exc_raw) if isinstance(exc_raw, str) else exc_raw

        period_label = variables.get("period_label", "current period")
        open_count = len(exceptions)

        # Group by rule or category
        theme_groups: dict[str, list[dict]] = {}
        for ex in exceptions:
            rule_name = ex.get("rule", "General exception")
            theme_groups.setdefault(rule_name, []).append(ex)

        groups = []
        for theme, items in list(theme_groups.items())[:6]:
            sev_max = "low"
            for it in items:
                sev = it.get("severity", "low").lower()
                if sev == "high":
                    sev_max = "high"
                    break
                elif sev == "medium":
                    sev_max = "medium"

            ids = [it.get("id") for it in items if it.get("id")]
            groups.append(
                {
                    "theme": theme[:60],
                    "count": len(items),
                    "severity_max": sev_max,
                    "exception_ids": ids,
                    "note": f"{len(items)} item(s) flagged under {theme}"[:200],
                }
            )

        # High severity first, then by age/id
        sorted_ex = sorted(
            exceptions,
            key=lambda x: (
                0 if x.get("severity") == "high" else 1,
                -x.get("age_days", 0),
            ),
        )
        review_order = [x.get("id") for x in sorted_ex if x.get("id")][:10]

        summary = (
            f"{open_count} potential exception(s) open for {period_label}. "
            f"Items are grouped deterministically by rule family for human inspection."
        )

        return {
            "summary": summary[:800],
            "groups": groups
            if groups
            else [
                {
                    "theme": "Open items",
                    "count": open_count,
                    "severity_max": "low",
                    "exception_ids": review_order,
                    "note": "Deterministic review list.",
                }
            ],
            "review_order": review_order,
            "confidence": "high",
        }

    @classmethod
    def generate_prompt_04(cls, variables: dict[str, Any]) -> dict[str, Any]:
        """PROMPT-04: Follow-up message fallback."""
        exc_raw = variables.get("owner_exceptions_json", "[]")
        exceptions = json.loads(exc_raw) if isinstance(exc_raw, str) else exc_raw

        owner_name = variables.get("owner_name", "Owner")
        period_label = variables.get("period_label", "current period")
        section_name = variables.get("section_name", "Accounting")

        bullets = []
        item_ids = []
        for ex in exceptions[:25]:
            ex_id = ex.get("id", "")
            if ex_id:
                item_ids.append(ex_id)
            rule = ex.get("rule", "Potential exception")
            subj = ex.get("subject", "")
            amt = ex.get("amount", "")
            curr = ex.get("currency", "")
            bullets.append(f"- {rule}: {subj} ({curr} {amt})")

        bullet_str = "\n".join(bullets)
        subject_line = (
            f"{period_label} close: {len(exceptions)} item(s) for review in {section_name}"
        )
        if len(subject_line) > 120:
            subject_line = subject_line[:120]

        body = (
            f"Hi {owner_name},\n\n"
            f"Ahead of the {period_label} close review, please find potential exceptions flagged for review in {section_name}:\n\n"
            f"{bullet_str}\n\n"
            f"These are potential exceptions for human verification — no automatic action is taken. "
            f"Could you please confirm whether each is expected?\n\n"
            f"Thanks,\nFP&A Team"
        )
        if len(body) > 1800:
            body = body[:1797] + "..."

        return {
            "subject_line": subject_line,
            "body_markdown": body,
            "items_referenced": item_ids if item_ids else ["ex-none"],
            "confidence": "high",
        }

    @classmethod
    def generate(cls, prompt_id: str, variables: dict[str, Any]) -> dict[str, Any]:
        """Dispatches to the appropriate deterministic rule-based generator."""
        if prompt_id == "PROMPT-01":
            return cls.generate_prompt_01(variables)
        elif prompt_id == "PROMPT-02":
            return cls.generate_prompt_02(variables)
        elif prompt_id == "PROMPT-03":
            return cls.generate_prompt_03(variables)
        elif prompt_id == "PROMPT-04":
            return cls.generate_prompt_04(variables)
        raise ValueError(f"No rule-based fallback implemented for {prompt_id}")


# ---------------------------------------------------------------------------
# AI Client Implementation (§3, §8, §11)
# ---------------------------------------------------------------------------


class AIClient:
    """Client for calling OpenAI-compatible or Azure OpenAI endpoints via httpx,

    redacting payloads, validating outputs against schemas, and providing
    automatic fallback to deterministic rule-based summaries.
    """

    def __init__(
        self,
        config: AIConfig | None = None,
        prompts_dir: Path | None = None,
        http_client: httpx.Client | None = None,
    ):
        self.config = config or AIConfig()
        self.prompt_loader = PromptTemplateLoader(prompts_dir=prompts_dir)
        self.redaction_engine = RedactionEngine(self.config)
        self.fallback_generator = RuleBasedNarrativeGenerator()
        self._custom_http_client = http_client

    def _get_http_client(self) -> httpx.Client:
        if self._custom_http_client is not None:
            return self._custom_http_client
        return httpx.Client(timeout=self.config.timeout_seconds)

    def is_configured(self) -> bool:
        """Returns True if AI is enabled and configured with an endpoint and key."""
        if self.config.provider in ("none", ""):
            return False
        if not self.config.api_key:
            return False
        if not self.config.base_url:
            return False
        return True

    def test_connection(self) -> dict[str, Any]:
        """Probes the configured endpoint with a minimal data-free request."""
        if not self.is_configured():
            return {
                "success": False,
                "message": "AI is disabled or missing credentials.",
            }

        client = self._get_http_client()
        url, headers, payload = self._build_request_params(
            system_prompt='You are a health-check responder. Output JSON only: {"status": "ok"}',
            user_prompt="Respond with status ok in JSON.",
        )
        try:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                return {
                    "success": True,
                    "message": "Connection and credentials verified.",
                }
            elif resp.status_code in (401, 403):
                return {
                    "success": False,
                    "message": "The AI key was rejected. Check your key in Settings.",
                }
            else:
                return {
                    "success": False,
                    "message": f"Provider returned HTTP {resp.status_code}: {resp.text[:200]}",
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Couldn't reach the AI provider: {str(e)}",
            }

    def _build_request_params(
        self, system_prompt: str, user_prompt: str
    ) -> tuple[str, dict[str, str], dict[str, Any]]:
        """Constructs endpoint URL, headers, and request body based on provider."""
        headers = {"Content-Type": "application/json"}
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        body = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "response_format": {"type": "json_object"},
        }

        if self.config.provider == "azure_openai":
            headers["api-key"] = self.config.api_key
            base = self.config.base_url.rstrip("/")
            url = f"{base}/openai/deployments/{self.config.model}/chat/completions?api-version={self.config.api_version}"
        else:  # openai_compatible
            headers["Authorization"] = f"Bearer {self.config.api_key}"
            base = self.config.base_url.rstrip("/")
            if base.endswith("/chat/completions"):
                url = base
            else:
                url = f"{base}/chat/completions"

        return url, headers, body

    def generate(
        self,
        prompt_id: str,
        variables: dict[str, Any],
        version: str = "v1",
        known_vendors: list[str] | None = None,
    ) -> AIDraftResult:
        """Main entry point: loads template, redacts payload, calls provider,

        validates output against schema, checks numbers, or falls back to
        the rule-based summary if keyless/offline.
        """
        template = self.prompt_loader.get_template(prompt_id, version=version)

        # If keyless or disabled, immediately return rule-based fallback
        if not self.is_configured():
            fb_content = self.fallback_generator.generate(prompt_id, variables)
            return AIDraftResult(
                content=fb_content,
                raw_response=json.dumps(fb_content),
                is_ai_draft=False,
                label="Rule-based summary",
                prompt_id=prompt_id,
                prompt_version=f"{prompt_id}.{version}",
                model="deterministic-rule-engine",
                provider="none",
                outcome="ok",
            )

        # Redact payload variables
        vendor_map: dict[str, str] = {}
        redacted_vars: dict[str, Any] = {}
        for k, v in variables.items():
            if isinstance(v, str) and (v.startswith("{") or v.startswith("[")):
                try:
                    parsed = json.loads(v)
                    redacted = self.redaction_engine.redact_payload_value(
                        parsed, vendor_map, known_vendors=known_vendors
                    )
                    redacted_vars[k] = json.dumps(redacted)
                    continue
                except json.JSONDecodeError:
                    pass
            redacted_vars[k] = self.redaction_engine.redact_payload_value(
                v, vendor_map, known_vendors=known_vendors
            )

        redaction_applied = bool(
            self.config.mask_vendors
            or self.config.mask_descriptions
            or self.config.mask_confidential_amounts
        )

        try:
            rendered_user_payload = template.render_payload(redacted_vars)
        except Exception as e:
            logger.error(f"Payload rendering error for {prompt_id}: {e}. Reverting to fallback.")
            fb_content = self.fallback_generator.generate(prompt_id, variables)
            return AIDraftResult(
                content=fb_content,
                raw_response=json.dumps(fb_content),
                is_ai_draft=False,
                label="Rule-based summary",
                prompt_id=prompt_id,
                prompt_version=f"{prompt_id}.{version}",
                model="deterministic-rule-engine",
                provider="none",
                outcome="schema_error",
                warning=f"Input payload validation error: {str(e)}",
            )

        # Execute network call with retry logic
        url, headers, body = self._build_request_params(
            system_prompt=template.system_prompt,
            user_prompt=rendered_user_payload,
        )

        client = self._get_http_client()
        raw_response_text = ""
        success = False
        outcome = "ok"

        for attempt in range(self.config.max_retries + 1):
            try:
                resp = client.post(url, headers=headers, json=body)
                if resp.status_code == 200:
                    resp_json = resp.json()
                    choices = resp_json.get("choices", [])
                    if choices:
                        raw_response_text = choices[0].get("message", {}).get("content", "")
                        success = True
                        break
                    else:
                        outcome = "refused"
                elif resp.status_code == 429:
                    outcome = "rate_limit"
                    if attempt < self.config.max_retries:
                        continue
                elif resp.status_code in (401, 403):
                    outcome = "unauthorized"
                    break
                elif resp.status_code >= 500:
                    outcome = "server_error"
                    if attempt < self.config.max_retries:
                        continue
                else:
                    outcome = f"http_{resp.status_code}"
            except httpx.TimeoutException:
                outcome = "timeout"
            except httpx.NetworkError:
                outcome = "network_error"
            except Exception as e:
                outcome = f"error_{type(e).__name__}"
                logger.warning(f"Error calling AI endpoint: {e}")

        if not success or not raw_response_text:
            fb_content = self.fallback_generator.generate(prompt_id, variables)
            return AIDraftResult(
                content=fb_content,
                raw_response=raw_response_text,
                is_ai_draft=False,
                label="Rule-based summary",
                prompt_id=prompt_id,
                prompt_version=f"{prompt_id}.{version}",
                model=self.config.model,
                provider=self.config.provider,
                outcome=outcome,
                redaction_applied=redaction_applied,
                vendor_mapping=vendor_map,
                warning=f"AI provider call failed ({outcome}); fell back to rule-based summary.",
            )

        # Parse & Validate Output (§8)
        parsed_output, parse_err = self._parse_json_strictly(raw_response_text)
        if parse_err or not isinstance(parsed_output, dict):
            # One silent retry with stricter instruction if not done yet
            logger.info("Output failed JSON parse. Falling back to rule-based.")
            fb_content = self.fallback_generator.generate(prompt_id, variables)
            return AIDraftResult(
                content=fb_content,
                raw_response=raw_response_text,
                is_ai_draft=False,
                label="Rule-based summary",
                prompt_id=prompt_id,
                prompt_version=f"{prompt_id}.{version}",
                model=self.config.model,
                provider=self.config.provider,
                outcome="schema_error",
                redaction_applied=redaction_applied,
                vendor_mapping=vendor_map,
                warning="AI response was not valid JSON; fell back to rule-based summary.",
            )

        try:
            jsonschema.validate(instance=parsed_output, schema=template.output_schema)
        except jsonschema.ValidationError as ve:
            logger.info(f"Output schema validation failed: {ve}. Falling back to rule-based.")
            fb_content = self.fallback_generator.generate(prompt_id, variables)
            return AIDraftResult(
                content=fb_content,
                raw_response=raw_response_text,
                is_ai_draft=False,
                label="Rule-based summary",
                prompt_id=prompt_id,
                prompt_version=f"{prompt_id}.{version}",
                model=self.config.model,
                provider=self.config.provider,
                outcome="schema_error",
                redaction_applied=redaction_applied,
                vendor_mapping=vendor_map,
                warning=f"AI response failed schema validation: {ve.message}",
            )

        # Banned phrases check
        banned_phrases_found = OutputValidator.check_banned_phrases(raw_response_text)
        banned_flag = len(banned_phrases_found) > 0

        # Evidence ID check
        valid_evidence_ids = OutputValidator.extract_evidence_ids_from_obj(redacted_vars)
        evidence_flag = self._sanitize_evidence_ids(parsed_output, valid_evidence_ids)

        # Number mismatch check (§8.2 DEC-026)
        valid_numbers = OutputValidator.extract_numbers_from_obj(redacted_vars)
        number_mismatch_flag = False
        parsed_output, number_mismatch_flag = self._apply_number_checks(
            parsed_output, valid_numbers
        )

        # Check if entire output was stripped
        if self._is_wholly_stripped(parsed_output):
            fb_content = self.fallback_generator.generate(prompt_id, variables)
            return AIDraftResult(
                content=fb_content,
                raw_response=raw_response_text,
                is_ai_draft=False,
                label="Rule-based summary",
                prompt_id=prompt_id,
                prompt_version=f"{prompt_id}.{version}",
                model=self.config.model,
                provider=self.config.provider,
                number_mismatch_flag=True,
                outcome="ok",
                warning="AI draft figures did not match data; replaced with rule-based summary.",
            )

        return AIDraftResult(
            content=parsed_output,
            raw_response=raw_response_text,
            is_ai_draft=True,
            label="AI draft — review before use.",
            prompt_id=prompt_id,
            prompt_version=f"{prompt_id}.{version}",
            model=self.config.model,
            provider=self.config.provider,
            number_mismatch_flag=number_mismatch_flag,
            banned_phrase_flag=banned_flag,
            evidence_flag=evidence_flag,
            redaction_applied=redaction_applied,
            vendor_mapping=vendor_map,
            outcome="ok",
        )

    @staticmethod
    def _parse_json_strictly(text: str) -> tuple[dict | None, str | None]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.DOTALL).strip()
        try:
            data = json.loads(cleaned)
            return data, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def _sanitize_evidence_ids(output_data: dict[str, Any], valid_ids: set[str]) -> bool:
        """Strips unknown evidence IDs and returns True if any was stripped."""
        flag = False

        def clean_ids(ids: list[str]) -> list[str]:
            nonlocal flag
            filtered = []
            for i in ids:
                if i in valid_ids:
                    filtered.append(i)
                else:
                    flag = True
            return filtered

        if "drivers" in output_data and isinstance(output_data["drivers"], list):
            for d in output_data["drivers"]:
                if "evidence_ids" in d and isinstance(d["evidence_ids"], list):
                    d["evidence_ids"] = clean_ids(d["evidence_ids"])

        if "suggestions" in output_data and isinstance(output_data["suggestions"], list):
            for s in output_data["suggestions"]:
                if "evidence_ids" in s and isinstance(s["evidence_ids"], list):
                    s["evidence_ids"] = clean_ids(s["evidence_ids"])

        if "groups" in output_data and isinstance(output_data["groups"], list):
            for g in output_data["groups"]:
                if "exception_ids" in g and isinstance(g["exception_ids"], list):
                    g["exception_ids"] = clean_ids(g["exception_ids"])

        if "items_referenced" in output_data and isinstance(output_data["items_referenced"], list):
            output_data["items_referenced"] = clean_ids(output_data["items_referenced"])

        return flag

    @classmethod
    def _apply_number_checks(
        cls, output_data: dict[str, Any], valid_numbers: set[str]
    ) -> tuple[dict[str, Any], bool]:
        """Applies sentence-level number validation to commentary and messages."""
        mismatch_flag = False

        if "commentary" in output_data and isinstance(output_data["commentary"], str):
            new_comm, flag = OutputValidator.validate_and_sanitize_numbers(
                output_data["commentary"], valid_numbers
            )
            output_data["commentary"] = new_comm
            mismatch_flag = mismatch_flag or flag

        if "body_markdown" in output_data and isinstance(output_data["body_markdown"], str):
            new_body, flag = OutputValidator.validate_and_sanitize_numbers(
                output_data["body_markdown"], valid_numbers
            )
            output_data["body_markdown"] = new_body
            mismatch_flag = mismatch_flag or flag

        if "summary" in output_data and isinstance(output_data["summary"], str):
            new_sum, flag = OutputValidator.validate_and_sanitize_numbers(
                output_data["summary"], valid_numbers
            )
            output_data["summary"] = new_sum
            mismatch_flag = mismatch_flag or flag

        return output_data, mismatch_flag

    @staticmethod
    def _is_wholly_stripped(output_data: dict[str, Any]) -> bool:
        """Returns True if commentary or body consists only of removal placeholders."""
        target_fields = ["commentary", "body_markdown", "summary"]
        for f in target_fields:
            if f in output_data and isinstance(output_data[f], str):
                text = output_data[f].replace("[figure removed — not from your data]", "").strip()
                if not text:
                    return True
        return False
