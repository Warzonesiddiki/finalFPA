# Rule Audit: Account 1999/Suspense/Clearing/balance_sheet References

As requested, I have audited all rule files to identify any references to account '1999', 'Suspense', 'Clearing', or 'balance_sheet'.

## 1. Rule References

| Rule ID | Catalog Rule ID | File Path | Reference Context |
| :--- | :--- | :--- | :--- |
| **EXC-024** | EXC-024 | `app/engine/rules/rules_17_24.py` | `suspense_accounts = context.config.get("suspense_accounts", {"1999", "9999", "SUSPENSE"})` |
| **EXC-024** | EXC-024 | `app/engine/rules/rules_17_24.py` | `evaluate_exc_024` maps `suspense_accounts` to `1999`. |

No other rule file contains explicit references to '1999'.

Note: 'balance_sheet' and 'Clearing' did not appear as explicit strings in the rules I audited; `EXC-024` explicitly targets "Suspense / clearing account" as per its docstring, and the code uses the `suspense_accounts` config.

## 2. Impact Analysis

The only rule referencing account '1999' is **EXC-024 (Suspense / clearing account residual)**.

If a large balancing credit line of ~17.9B is posted to account '1999':

1.  **Direct Impact on EXC-024**: This rule explicitly monitors account '1999'. A credit of ~17.9B will be processed as a material residual balance in the period.
2.  **Result**: `evaluate_exc_024` will absolutely trigger and raise a `Finding` for account '1999' with a massive `amount_at_risk`.
3.  **Corruption**: While technically 'accurate' (the balance *is* in 1999), it effectively creates a false-positive 'finding' for the very act of balancing the trial balance, masking the actual operational exceptions in account 1999 (like the planted P24 exception VCH-2026-0930-040).

## 3. Verdict

- **Trivial fix (17.9B balancing credit to 1999)**: **NOT RECOMMENDED**. It will corrupt `EXC-024` findings.
- **Expensive fix (Full double-entry rebuild)**: **REQUIRED**. To maintain data integrity without polluting the exception findings, the trial balance must be corrected through proper double-entry, not a single 'plug' entry to a monitored suspense/clearing account.
- **Doc-03 Verdict**: The chart of accounts should not be used as a 'plug'. The data generator must be corrected to produce a fully balanced trial balance through legitimate transaction entries. The planted suspense residual (P24) for 1999 must remain independent of any balancing fix.
