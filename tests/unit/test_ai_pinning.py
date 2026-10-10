"""Tests for AI model pinning, deprecation notices, and fallback order per doc 10 §2 & §3."""

from app.engine.ai.pinning import (
    SUPPORTED_MODELS,
    get_model_pinning_config,
    validate_model_selection,
)


def test_pinned_default_model_is_declared():
    """Verify pinned default model is explicitly set and visible per doc 10 §2."""
    config = get_model_pinning_config()
    assert "pinnedDefaultModel" in config
    assert config["pinnedDefaultModel"] == "gpt-4o"
    assert isinstance(config["models"], list)
    pinned = next((m for m in config["models"] if m["modelId"] == "gpt-4o"), None)
    assert pinned is not None
    assert pinned["status"] == "pinned_active"


def test_deprecated_model_has_retirement_notice():
    """Verify that deprecated models carry a documented deprecation notice per doc 10 §2."""
    deprecated = [m for m in SUPPORTED_MODELS if m["status"] in ("deprecated", "retired")]
    assert len(deprecated) >= 1
    for m in deprecated:
        assert m["deprecationNotice"] is not None
        assert len(m["deprecationNotice"]) > 10


def test_fallback_order_has_three_steps_ending_in_keyless_fallback():
    """Verify documented fallback order ends in keyless rule-based terminal state per doc 10 §3."""
    config = get_model_pinning_config()
    fallback = config["fallbackOrder"]
    assert len(fallback) == 3
    last_step = fallback[-1]
    assert last_step["step"] == 3
    assert "Keyless" in last_step["state"] or "keyless" in last_step["description"].lower()


def test_validate_active_model():
    """Active pinned model should validate cleanly."""
    res = validate_model_selection("gpt-4o")
    assert res["valid"] is True
    assert res["status"] == "pinned_active"
    assert res["warning"] is None


def test_validate_deprecated_model_returns_warning():
    """Deprecated model returns a non-silent warning per doc 10 §3 (never silent switch)."""
    res = validate_model_selection("gpt-4-0315")
    assert res["status"] == "deprecated"
    assert res["warning"] is not None
    assert len(res["warning"]) > 0


def test_validate_unknown_model_is_rejected():
    """Unknown model IDs are rejected cleanly to prevent silent switches."""
    res = validate_model_selection("unknown-model-xyz")
    assert res["valid"] is False
    assert "not in the approved FPA model pinning registry" in res["warning"]


def test_policy_states_non_silent_enforcement():
    """Verify policy field documents non-silent switching enforcement per doc 10 §3."""
    config = get_model_pinning_config()
    policy = config.get("policy", "")
    assert "Non-silent" in policy or "non-silent" in policy.lower()
