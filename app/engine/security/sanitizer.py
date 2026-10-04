import hashlib
import csv
from decimal import Decimal
from typing import Dict, List, Any

# TODO: Get actual salt from configuration (SEC-041)
SALT = "project-2026-salt"

def hash_value(value: str) -> str:
    """Deterministic hash with salt."""
    return hashlib.sha256((value + SALT).encode()).hexdigest()

def mask_email(value: str) -> str:
    return "<MASKED>"

def mask_address(value: str) -> str:
    # Truncate to zip if possible, or just MASKED
    return "<MASKED_ADDRESS>"

class Sanitizer:
    def __init__(self, mapping_profile: Dict[str, str]):
        self.mapping_profile = mapping_profile

    def sanitize_field(self, field_name: str, value: Any) -> Any:
        strategy = self.mapping_profile.get(field_name.lower())
        if strategy == "hash":
            return hash_value(str(value))
        elif strategy == "email":
            return mask_email(str(value))
        elif strategy == "address":
            return mask_address(str(value))
        elif strategy == "account_number":
            return str(value)[-4:] if len(str(value)) > 4 else str(value)
        return value

    def sanitize_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        # Case insensitive key lookup
        return {k: self.sanitize_field(k, v) for k, v in row.items()}

    def verify_integrity(self, original_data: List[Dict[str, Any]], sanitized_data: List[Dict[str, Any]]):
        """Verifies total batch debit/credit sums remain balanced."""
        def get_sum(data, key):
            # Case insensitive key search
            if not data:
                return Decimal("0.00")
            actual_key = next((k for k in data[0].keys() if k.lower() == key.lower()), None)
            if not actual_key:
                # If key not found, try to use the key provided in get_sum directly
                return sum(Decimal(str(row.get(key, 0) or 0)) for row in data)
            return sum(Decimal(str(row.get(actual_key, 0) or 0)) for row in data)

        orig_debits = get_sum(original_data, 'debit')
        orig_credits = get_sum(original_data, 'credit')

        san_debits = get_sum(sanitized_data, 'debit')
        san_credits = get_sum(sanitized_data, 'credit')

        if orig_debits != san_debits:
            raise ValueError(f"Debit integrity failed: {orig_debits} != {san_debits}")
        if orig_credits != san_credits:
            raise ValueError(f"Credit integrity failed: {orig_credits} != {san_credits}")
        return True
