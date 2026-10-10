"""Unit tests for AI Integration Client and Redaction Engine.

Per docs/10_AI_INTEGRATION_SPEC.md §1 through §7.
"""

from app.engine.ai.client import (
    RedactionEngine,
)


def test_redaction_engine_sanitization():
    """Verify input sanitization: stripping HTML, control chars, and delimiters."""
    engine = RedactionEngine()
    raw = "<p>Vendor invoice with <data>internal payload</data> and \x00 null bytes.</p>"
    clean = engine.sanitize_text(raw)
    assert "<p>" not in clean
    assert "<data>" not in clean
    assert "\x00" not in clean


def test_redaction_engine_mask_description():
    """Verify masking email, phone, URL, long digits in description."""
    engine = RedactionEngine()
    desc = "Payment to user@alpha.com on +91 98765 43210 ref https://portal.in/inv 123456789012"
    masked = engine.mask_description(desc)
    assert "user@alpha.com" not in masked
    assert "https://portal.in/inv" not in masked
    assert "123456789012" not in masked


def test_redaction_engine_vendor_masking():
    """Verify vendor names and IDs are replaced with deterministic aliases."""
    engine = RedactionEngine()
    text = "Transferred funds to V-00412 and Acme Supplies Ltd on Monday."
    masked, mapping = engine.mask_vendors(text, known_vendors=["Acme Supplies Ltd"])
    assert "V-00412" not in masked
    assert "Acme Supplies Ltd" not in masked
    assert len(mapping) >= 1

    # Unmasking restores original
    restored = engine.reverse_mask_vendors(masked, mapping)
    assert "V-00412" in restored
    assert "Acme Supplies Ltd" in restored


def test_rule_based_narrative_generator_fallback():
    """Verify offline deterministic narrative generation (PROMPT-01 fallback)."""
    from app.engine.ai.client import RuleBasedNarrativeGenerator

    variables = {
        "period_label": "September 2026",
        "data_block_json": {
            "subject": {"account_name": "Travel & Entertainment"},
            "measures": [
                {"label": "Variance %", "value": "15.0"},
                {"label": "Favourability", "value": "Unfavourable"},
                {"label": "Variance", "value": "45,000.00", "currency": "INR"},
            ],
            "contributors": [{"label": "Airfare", "amount": "30,000.00", "id": "cont-1"}],
        },
    }
    result = RuleBasedNarrativeGenerator.generate_prompt_01(variables)
    assert result is not None
    assert "commentary" in result
    assert "Travel & Entertainment" in result["commentary"]
    assert "15.0%" in result["commentary"]
    assert result["confidence"] == "low"
