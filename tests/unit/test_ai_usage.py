from app.engine.ai.usage import AIUsageStore


def test_ai_usage_store_and_cap_enforcement():
    """Test AI usage log schema and monthly hard token cap enforcement per doc 10 §8 & §9."""
    store = AIUsageStore()
    with store._get_conn() as conn:
        conn.execute("DELETE FROM AiUsageLog")
        conn.commit()

    # Set cap low for testing
    store.set_monthly_token_cap(5000)
    assert store.get_monthly_token_cap() == 5000

    # Initially cap should not be exceeded
    assert not store.check_cap_exceeded()

    # Log a call that uses tokens
    log_res = store.log_call(
        prompt_id="PROMPT-01",
        prompt_version="PROMPT-01.v1",
        model="gpt-4o",
        provider="openai",
        input_row_count=10,
        tokens_in=3000,
        tokens_out=1500,
        outcome="ok",
    )

    assert log_res["callId"].startswith("aicall_")
    assert log_res["tokensIn"] == 3000
    assert log_res["tokensOut"] == 1500
    assert log_res["estimatedCostUsd"] > 0.0

    # Now cumulative tokens (4500) is close to 5000. If we check with additional 1000, cap is exceeded.
    assert store.check_cap_exceeded(additional_tokens=1000)

    # Get usage stats
    stats = store.get_usage_stats()
    assert stats["totalCalls"] >= 1
    assert stats["totalTokens"] == 4500
    assert stats["monthlyTokenCap"] == 5000
    assert "logs" in stats
    assert len(stats["logs"]) >= 1
