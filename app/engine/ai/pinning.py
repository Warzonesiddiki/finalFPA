from typing import Any

SUPPORTED_MODELS = [
    {
        "modelId": "gpt-4o",
        "displayName": "GPT-4o (Pinned Production Default)",
        "status": "pinned_active",
        "deprecationNotice": None,
    },
    {
        "modelId": "gpt-4-turbo",
        "displayName": "GPT-4 Turbo",
        "status": "active",
        "deprecationNotice": None,
    },
    {
        "modelId": "gpt-4-0315",
        "displayName": "GPT-4 (0315 Snapshot)",
        "status": "deprecated",
        "deprecationNotice": "Model deprecated by upstream provider. Will auto-fallback to gpt-4o.",
    },
    {
        "modelId": "gpt-3.5-turbo",
        "displayName": "GPT-3.5 Turbo",
        "status": "retired",
        "deprecationNotice": "Model retired. Unsupported for financial FPA reporting compliance.",
    },
]

DOCUMENTED_FALLBACK_ORDER = [
    {
        "step": 1,
        "state": "Primary Pinned Model",
        "description": "Configured production model (e.g. gpt-4o) with strict schema guardrails.",
    },
    {
        "step": 2,
        "state": "Secondary Regional Fallback",
        "description": "Configured regional endpoint / failover model instance.",
    },
    {
        "step": 3,
        "state": "Keyless Rule-Based Fallback Terminal State",
        "description": "Deterministic rule-based generator (Prompt 01-04) labeled 'Rule-based summary (keyless fallback)' ensuring 100% availability.",
    },
]


def get_model_pinning_config() -> dict[str, Any]:
    """Get model pinning registry, deprecation notices, and documented fallback order per doc 10 §2 & §3."""
    return {
        "pinnedDefaultModel": "gpt-4o",
        "models": SUPPORTED_MODELS,
        "fallbackOrder": DOCUMENTED_FALLBACK_ORDER,
        "policy": "Non-silent switching enforced. Fallback always emits explicit labeling.",
    }


def validate_model_selection(model_id: str) -> dict[str, Any]:
    """Validate selected model against pinning & deprecation registry."""
    found = next((m for m in SUPPORTED_MODELS if m["modelId"] == model_id), None)
    if not found:
        return {
            "valid": False,
            "status": "unknown",
            "warning": f"Model '{model_id}' is not in the approved FPA model pinning registry.",
        }
    if found["status"] in ("deprecated", "retired"):
        return {
            "valid": found["status"] == "deprecated",
            "status": found["status"],
            "warning": found["deprecationNotice"],
        }
    return {
        "valid": True,
        "status": found["status"],
        "warning": None,
    }
