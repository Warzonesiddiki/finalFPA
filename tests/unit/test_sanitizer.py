import pytest
from decimal import Decimal
from app.engine.security.sanitizer import Sanitizer

def test_sanitizer_hashing():
    mapping_profile = {"name": "hash"}
    sanitizer = Sanitizer(mapping_profile)
    row = {"name": "John Doe"}
    sanitized = sanitizer.sanitize_row(row)
    assert sanitized["name"] != "John Doe"
    assert len(sanitized["name"]) == 64  # SHA-256 hex length

def test_sanitizer_integrity():
    sanitizer = Sanitizer({})
    original = [
        {"debit": "100.00", "credit": "0.00"},
        {"debit": "0.00", "credit": "100.00"}
    ]
    sanitized = [
        {"debit": "100.00", "credit": "0.00"},
        {"debit": "0.00", "credit": "100.00"}
    ]
    assert sanitizer.verify_integrity(original, sanitized) == True

def test_sanitizer_integrity_uppercase_keys():
    sanitizer = Sanitizer({})
    original = [
        {"Debit": "100.00", "Credit": "0.00"},
        {"Debit": "0.00", "Credit": "100.00"}
    ]
    sanitized = [
        {"Debit": "100.00", "Credit": "0.00"},
        {"Debit": "0.00", "Credit": "100.00"}
    ]
    assert sanitizer.verify_integrity(original, sanitized) == True

def test_sanitizer_integrity_fail():
    sanitizer = Sanitizer({})
    original = [
        {"debit": "100.00", "credit": "0.00"},
        {"debit": "0.00", "credit": "100.00"}
    ]
    sanitized = [
        {"debit": "100.00", "credit": "0.00"},
        {"debit": "0.00", "credit": "110.00"} # Imbalance induced
    ]
    with pytest.raises(ValueError, match="Credit integrity failed"):
        sanitizer.verify_integrity(original, sanitized)
