from app.engine.ai.provenance import AiProvenanceStore


def test_ai_provenance_version_retention_and_approval():
    """Test Doc 10 §4, §5, §6: Draft provenance stamping, version retention upon regeneration, and PPT approval flow."""
    store = AiProvenanceStore()
    subject_key = "Operating Expenses"
    period_id = 9

    # Save draft version 1
    d1 = store.save_draft(
        subject_key=subject_key,
        period_id=period_id,
        content="Draft version 1 commentary content.",
        model="gpt-4o",
        prompt_id="PROMPT-01",
        prompt_version="PROMPT-01.v1",
        author="Aarti",
    )
    assert d1["draftId"].startswith("aidraft_")
    assert d1["status"] == "draft"

    # Save regenerated draft version 2 (verifying previous version is retained per §5)
    d2 = store.save_draft(
        subject_key=subject_key,
        period_id=period_id,
        content="Draft version 2 re-generated commentary content.",
        model="gpt-4o",
        prompt_id="PROMPT-01",
        prompt_version="PROMPT-01.v2",
        author="Aarti",
    )

    # List drafts: should contain both versions
    drafts = store.list_drafts(subject_key=subject_key, period_id=period_id)
    assert len(drafts) >= 2
    assert any(d["draftId"] == d1["draftId"] for d in drafts)
    assert any(d["draftId"] == d2["draftId"] for d in drafts)

    # Approve draft version 2 for PPT export per §6
    approved = store.approve_draft(d2["draftId"])
    assert approved is not None
    assert approved["status"] == "approved"

    # Verify version 1 is no longer approved (only one active approval per subject)
    updated_drafts = store.list_drafts(subject_key=subject_key, period_id=period_id)
    approved_list = [d for d in updated_drafts if d["status"] == "approved"]
    assert len(approved_list) == 1
    assert approved_list[0]["draftId"] == d2["draftId"]
