"""Tests for prompt template version management, immutability, and 5-step edit process per doc 10 §5."""

import pytest

from app.engine.ai.prompts import SHIP_PROMPTS, PromptTemplateStore


def test_shipped_prompts_are_immutable():
    """Verify shipped baseline prompt templates are immutable per doc 10 §5.1."""
    store = PromptTemplateStore()
    prompts = store.list_prompts()

    assert len(prompts) == len(SHIP_PROMPTS)
    for p in prompts:
        assert len(p["versions"]) >= 1
        baseline = p["versions"][0]
        assert baseline["isImmutable"] is True
        assert "Baseline" in baseline["versionName"]


def test_edit_prompt_creates_new_version_without_mutating_baseline():
    """Verify editing a prompt creates a NEW version (v2+) and never mutates shipped baseline per doc 10 §5.2."""
    store = PromptTemplateStore()
    prompt_id = "PROMPT-01"

    initial_list = store.list_prompts()
    p1_family = next(f for f in initial_list if f["promptId"] == prompt_id)
    baseline_text = p1_family["versions"][0]["templateText"]

    # Attempting edit without changelog note should raise ValueError (CHANGELOG-first discipline)
    with pytest.raises(ValueError):
        store.edit_prompt(prompt_id, "Updated text", "")

    # Valid edit with changelog note
    new_version = store.edit_prompt(
        prompt_id=prompt_id,
        new_template_text="Updated template text with enhanced variance reasoning.",
        changelog_note="Added enhanced clarity for unfavorable variances in Q3 review.",
        author="Aarti",
    )

    assert new_version["versionId"].startswith(prompt_id)
    assert new_version["isImmutable"] is False
    assert new_version["changelogNote"] != ""

    # Verify baseline v1 was NOT mutated
    updated_list = store.list_prompts()
    updated_p1 = next(f for f in updated_list if f["promptId"] == prompt_id)
    assert updated_p1["versions"][0]["templateText"] == baseline_text
    assert len(updated_p1["versions"]) >= 2
