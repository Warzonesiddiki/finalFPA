"""Unit tests for MappingRepository per 04_SOURCE_MAPPING_AND_IMPORT_SPEC.md §5 and 03_DATA_DICTIONARY.md §3.8, §5.5."""

from pathlib import Path

import pytest

from app.engine.imports.profiles import (
    MappingProfile,
)
from app.engine.store.db import DatabaseManager
from app.engine.store.mapping_repo import MappingRepository


@pytest.fixture
def repo(tmp_path: Path) -> MappingRepository:
    """Provides a MappingRepository with isolated SQLite and DuckDB databases."""
    db_mgr = DatabaseManager(tmp_path)
    return MappingRepository(db_mgr, auto_seed=True)


def test_builtin_profiles_seeded(repo: MappingRepository):
    """Test that all 6 built-in profiles are seeded with is_builtin=True per 04 §5.4."""
    profiles = repo.list_profiles()
    assert len(profiles) >= 6

    d365 = repo.get_active_profile_by_source_type("actuals_d365")
    assert d365 is not None
    assert d365.name == "D365 GL (default)"
    assert d365.is_builtin is True
    assert "voucher" in d365.column_map
    assert d365.column_map["voucher"] == "voucher_no"
    assert d365.header_signature != ""

    bank = repo.get_active_profile_by_source_type("actuals_procurement")
    assert bank is not None
    assert bank.name == "Procurement / Bank Ledger"
    assert bank.is_builtin is True

    payroll = repo.get_active_profile_by_source_type("actuals_payroll")
    assert payroll is not None
    assert payroll.name == "Payroll Summary"
    assert payroll.is_builtin is True

    budget = repo.get_active_profile_by_source_type("budget")
    assert budget is not None
    assert budget.name == "Budget Template"


def test_builtin_profiles_dim_mappings(repo: MappingRepository):
    """Test that DimMapping entries are populated in DuckDB for built-in profiles."""
    d365 = repo.get_active_profile_by_source_type("actuals_d365")
    assert d365 is not None

    dim_mappings = repo.get_dim_mappings(d365.profile_id)
    assert len(dim_mappings) > 0
    voucher_mapping = next((m for m in dim_mappings if m.source_column == "voucher"), None)
    assert voucher_mapping is not None
    assert voucher_mapping.canonical_field == "voucher_no"
    assert voucher_mapping.is_active is True
    assert voucher_mapping.version_no == 1


def test_save_new_custom_profile(repo: MappingRepository):
    """Test saving a new user-defined mapping profile (MappingProfile, Version, DimMapping)."""
    custom_profile = MappingProfile(
        profile_id=0,
        name="Custom Bank CSV",
        source_type="actuals_procurement",
        column_map={
            "txn_id": "voucher_no",
            "val_date": "posting_date",
            "comp_code": "company_code",
            "gl_acct": "account_code",
            "dr_amt": "debit",
            "cr_amt": "credit",
        },
        delimiter=";",
        encoding="utf-8",
        date_rule="dd-mm-yyyy",
        number_rule="parens_negative",
        transforms={"gl_acct": {"strip": True}},
    )

    saved = repo.save_profile(
        profile=custom_profile,
        change_note="Initial custom bank profile",
        effective_from_period_id=1,
        created_by="finance_analyst",
    )

    assert saved.profile_id > 0
    assert saved.is_builtin is False
    assert saved.version_no == 1

    # Verify retrieval by profile_id
    retrieved = repo.get_active_profile_by_id(saved.profile_id)
    assert retrieved is not None
    assert retrieved.name == "Custom Bank CSV"
    assert retrieved.delimiter == ";"
    assert retrieved.column_map["txn_id"] == "voucher_no"
    assert retrieved.transforms["gl_acct"] == {"strip": True}

    # Verify custom profile is preferred over builtin when querying by source_type
    active_for_source = repo.get_active_profile_by_source_type("actuals_procurement")
    assert active_for_source is not None
    assert active_for_source.profile_id == saved.profile_id
    assert active_for_source.name == "Custom Bank CSV"

    # Verify DimMapping entries created in DuckDB
    mappings = repo.get_dim_mappings(saved.profile_id)
    assert len(mappings) == 6
    txn_map = next((m for m in mappings if m.source_column == "txn_id"), None)
    assert txn_map is not None
    assert txn_map.canonical_field == "voucher_no"
    assert txn_map.notes == "Initial custom bank profile"


def test_builtin_profile_cannot_be_mutated(repo: MappingRepository):
    """Test that attempting to edit a built-in profile raises ValueError per 04 §5.4."""
    d365 = repo.get_active_profile_by_source_type("actuals_d365")
    assert d365 is not None
    assert d365.is_builtin is True

    with pytest.raises(ValueError, match="Built-in profiles are read-only; clone to edit"):
        repo.create_version(
            profile_id=d365.profile_id,
            column_map={"new_col": "voucher_no"},
            change_note="Trying to modify builtin directly",
        )


def test_clone_builtin_profile(repo: MappingRepository):
    """Test cloning a built-in profile to create an editable custom copy per 04 §5.4."""
    d365 = repo.get_active_profile_by_source_type("actuals_d365")
    assert d365 is not None

    cloned = repo.clone_profile(
        source_profile_id=d365.profile_id,
        new_name="Custom D365 Tailored",
        created_by="controller",
    )

    assert cloned.profile_id != d365.profile_id
    assert cloned.name == "Custom D365 Tailored"
    assert cloned.is_builtin is False
    assert cloned.version_no == 1
    assert cloned.column_map == d365.column_map
    assert cloned.header_signature == d365.header_signature

    # Now verify that the cloned profile CAN be edited (creates v2)
    new_cols = dict(cloned.column_map)
    new_cols["extra_col"] = "description"
    v2 = repo.create_version(
        profile_id=cloned.profile_id,
        column_map=new_cols,
        change_note="Added extra_col mapping",
        created_by="controller",
    )

    assert v2.version_no == 2
    assert v2.change_note == "Added extra_col mapping"
    assert v2.is_current is True

    # Retrieve updated profile
    updated = repo.get_active_profile_by_id(cloned.profile_id)
    assert updated.version_no == 2
    assert "extra_col" in updated.column_map


def test_version_immutability_and_effective_from_period(repo: MappingRepository):
    """Test version immutability and mid-year source changes per 04 §5.3 (FR-IMP-026)."""
    # 1. Create a custom profile effective from period 1
    profile = MappingProfile(
        profile_id=0,
        name="Entity A ERP",
        source_type="actuals_d365",
        column_map={
            "voucher": "voucher_no",
            "account": "account_code",
            "amount": "amount",
        },
    )
    saved = repo.save_profile(
        profile=profile,
        change_note="v1 for Q1/Q2",
        effective_from_period_id=1,
    )
    p_id = saved.profile_id

    # 2. Mid-year ERP change in period 7 (July): column renamed to 'trans_ref' and 'main_acct'
    v2_cols = {
        "trans_ref": "voucher_no",
        "main_acct": "account_code",
        "amount": "amount",
    }
    v2 = repo.create_version(
        profile_id=p_id,
        column_map=v2_cols,
        change_note="ERP upgraded in July (P07), columns changed",
        effective_from_period_id=7,
        created_by="admin",
    )
    assert v2.version_no == 2
    assert v2.effective_from_period_id == 7

    # 3. Verify history integrity (both versions preserved, immutable)
    versions = repo.list_profile_versions(p_id)
    assert len(versions) == 2
    assert versions[0].version_no == 1
    assert versions[0].is_current is False
    assert versions[0].effective_from_period_id == 1
    assert versions[0].definition["column_map"]["voucher"] == "voucher_no"

    assert versions[1].version_no == 2
    assert versions[1].is_current is True
    assert versions[1].effective_from_period_id == 7
    assert versions[1].definition["column_map"]["trans_ref"] == "voucher_no"

    # 4. Point-in-time retrieval by period_id:
    # A batch loading Period 3 (March) must reconcile using Version 1!
    profile_p3 = repo.get_active_profile_by_id(p_id, period_id=3)
    assert profile_p3 is not None
    assert profile_p3.version_no == 1
    assert "voucher" in profile_p3.column_map
    assert "trans_ref" not in profile_p3.column_map

    # A batch loading Period 8 (August) must use Version 2!
    profile_p8 = repo.get_active_profile_by_id(p_id, period_id=8)
    assert profile_p8 is not None
    assert profile_p8.version_no == 2
    assert "trans_ref" in profile_p8.column_map
    assert "voucher" not in profile_p8.column_map

    # No period specified -> returns current version (v2)
    profile_current = repo.get_active_profile_by_id(p_id)
    assert profile_current.version_no == 2

    # 5. Verify DimMapping versions in DuckDB
    duck_v1_mappings = repo.get_dim_mappings(p_id, version_no=1)
    assert any(m.source_column == "voucher" for m in duck_v1_mappings)

    duck_v2_mappings = repo.get_dim_mappings(p_id, version_no=2)
    assert any(m.source_column == "trans_ref" for m in duck_v2_mappings)


def test_list_profiles_filtering(repo: MappingRepository):
    """Test filtering profiles by source_type and builtin status."""
    # List actuals_d365 profiles (at least builtin)
    d365_list = repo.list_profiles(source_type="actuals_d365")
    assert len(d365_list) >= 1
    assert all(p.source_type == "actuals_d365" for p in d365_list)

    # Without builtins before adding custom
    custom_only_before = repo.list_profiles(include_builtin=False)
    assert len(custom_only_before) == 0

    # Add custom
    repo.save_profile(
        MappingProfile(
            profile_id=0,
            name="Payroll Custom Entity",
            source_type="actuals_payroll",
            column_map={"a": "company_code"},
        )
    )

    custom_only_after = repo.list_profiles(include_builtin=False)
    assert len(custom_only_after) == 1
    assert custom_only_after[0].name == "Payroll Custom Entity"
