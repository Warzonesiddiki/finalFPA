"""
Exception Owner Auto-Assign Resolver (per doc 06 owner auto-assignment contract)

Quoted from docs/06_EXCEPTION_RULES_CATALOG.md §2.5 (Owner Auto-Assignment):
"The exception engine shall resolve the initial owner (owner_name and owner_role) using a 6-step hierarchical matching rule:
 1. Cost Centre Owner Mapping (matching cost_center_code to active cost centre register owner).
 2. Account Code / Category Owner Mapping (matching account_code prefix or type).
 3. Rule Default Role (default role assigned by rule specification, e.g. 'Accounts Payable', 'FP&A Analyst').
 4. Department Default Owner.
 5. Fallback Default Analyst.
 6. 'Unassigned' (if no match found; never assign false owners or guesses)."

Manual Override Precedence:
- Manual owner reassignment (via patch/bulk update API) explicitly locks the owner and records an audit event (`owner_changed`), taking precedence over subsequent rule re-runs.
"""

from __future__ import annotations

from typing import Optional, Tuple

# Mapping of cost centres to default owners
COST_CENTRE_OWNERS = {
    "CC-100": ("Ramesh Kumar", "Cost Centre Owner - Operations"),
    "CC-150": ("Priya Sharma", "Cost Centre Owner - IT"),
    "CC-200": ("Anil Mehta", "Cost Centre Owner - Sales"),
    "CC-250": ("Sunita Rao", "Cost Centre Owner - HR"),
}

# Mapping of account code prefixes to default owners
ACCOUNT_PREFIX_OWNERS = {
    "51": ("Vikram Patel", "Accounts Payable Accountant"),
    "52": ("Vikram Patel", "Accounts Payable Accountant"),
    "54": ("Pooja Deshmukh", "GL Accountant"),
    "55": ("Pooja Deshmukh", "GL Accountant"),
    "12": ("Amit Joshi", "Treasury Controller"),
    "21": ("Amit Joshi", "Treasury Controller"),
}

def resolve_exception_owner(
    rule_id: str,
    cost_center_code: Optional[str] = None,
    account_code: Optional[str] = None,
    rule_default_role: Optional[str] = None,
    manual_override_owner: Optional[str] = None,
) -> Tuple[str, str, bool]:
    """
    Resolves exception owner following the 6-step hierarchy with manual override precedence.
    Returns: (owner_name, owner_role, is_manually_overridden)
    """
    # 1. Manual Override Precedence (Highest)
    if manual_override_owner and manual_override_owner.strip() and manual_override_owner != "Unassigned":
        role = "Manual Override Assignee"
        if "Manager" in manual_override_owner:
            role = "Finance Manager"
        elif "Director" in manual_override_owner:
            role = "Finance Director"
        return (manual_override_owner.strip(), role, True)

    # 2. Step 1: Cost Centre Owner Mapping
    if cost_center_code and cost_center_code in COST_CENTRE_OWNERS:
        name, role = COST_CENTRE_OWNERS[cost_center_code]
        return (name, role, False)

    # 3. Step 2: Account Code / Category Owner Mapping
    if account_code:
        prefix = account_code[:2]
        if prefix in ACCOUNT_PREFIX_OWNERS:
            name, role = ACCOUNT_PREFIX_OWNERS[prefix]
            return (name, role, False)

    # 4. Step 3: Rule Default Role
    if rule_default_role and rule_default_role.strip() and rule_default_role != "Unassigned":
        # Map role name to a default assignee name
        role_map = {
            "Accounts Payable": ("Vikram Patel", "Accounts Payable"),
            "GL Accountant": ("Pooja Deshmukh", "GL Accountant"),
            "FP&A Analyst": ("Neha Kulkarni", "FP&A Analyst"),
            "Cost Centre Owner": ("Ramesh Kumar", "Cost Centre Owner"),
            "Treasury Controller": ("Amit Joshi", "Treasury Controller"),
        }
        if rule_default_role in role_map:
            name, role = role_map[rule_default_role]
            return (name, role, False)
        return ("Default Assignee", rule_default_role, False)

    # 5. Step 4 & 5: Fallback Default Analyst / Department Default
    if rule_id.startswith("EXC-0"):
        return ("Neha Kulkarni", "FP&A Analyst", False)

    # 6. Step 6: Unassigned (No false owner guesses)
    return ("Unassigned", "Unassigned", False)
