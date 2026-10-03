"""DEF-019: sample-data baseline must be genuinely double-entry (Option B).

Root cause (docs/28 §12 DEF-019): `sample-data/generate_sample_data.py`
emitted every baseline row single-sided -- revenue as bare credits, expenses
as bare debits, no offsetting leg. Measured on the committed corpus:
250,037 rows, debit 24,626,607,267.80 vs credit 6,682,091,688.47, residual
17,944,515,579.33 with every entity imbalanced, so `IMP-023` (docs/04 §12)
rejected the file with 0 rows committed. A single suspense plug was ruled
out: `evaluate_exc_024` reads `suspense_accounts` at a 100,000 floor (a
17.9B plug would corrupt planted P24 into a ~17.94B finding), per-entity /
per-period balance (docs/04 §12) cannot be fixed by one line, and docs/03
§3.2 permits no new account (an invented code trips EXC-002).

Option B (this fix): the baseline loop emits balanced voucher pairs --
revenue Cr offset by Dr to `1200`/`1010`, expense Dr offset by Cr to
`2000`/`1010` -- routine postings to `1999` net exactly 0.00 so only
planted P24 fires, and the planted block (docs/06 §7, incl. the P23
voucher imbalance and single-sided plant rows) stays unbalanced by design.
`scripts/verify_trial_balance.py` reports balance per voucher as well as
per entity/period.

Every test generates a small corpus into `tmp_path` (the committed
`sample-data/` corpus is untouched). Tests 1, 3 and 5 fail on the pre-fix
generator -- with single-sided rows no baseline voucher balances and no
offset leg exists. Tests 2 (1999 purity) and 4 (P23 plant) pass both
before and after: they are guards pinning that the fix added no suspense
plug and left the planted block alone, so a future "cleanup" of either
goes red.
Verified by running the same assertions against the pre-fix generator from
`git show HEAD:sample-data/generate_sample_data.py` before merging
(3 FAIL / 2 PASS, as predicted).
"""

import csv
import importlib.util
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = REPO_ROOT / "sample-data" / "generate_sample_data.py"
VERIFIER_PATH = REPO_ROOT / "scripts" / "verify_trial_balance.py"

# Planted voucher ids all carry a 3-digit sequence (< 1000); the baseline
# loop sequences from 1000 upward, so the numeric suffix discriminates the
# two populations without hardcoding any planted id list.
BASELINE_SEQ_FLOOR = 1000

# (planted) P23 signal: the two INV-IMB lines of VCH-2026-0912-004 net to a
# 5,000.00 debit imbalance. The voucher id itself is shared with a P7 plant
# row, so the assertion keys on the invoice number, not the voucher total.
P23_INVOICE = "INV-IMB"
P23_RESIDUAL = Decimal("5000.00")

# The only voucher allowed to touch the suspense account is planted P24.
P24_VOUCHER = "VCH-2026-0930-040"
SUSPENSE_ACCOUNT = "1999"

REVENUE_OFFSETS = {"1200", "1010"}
EXPENSE_OFFSETS = {"2000", "1010"}


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _generate(tmp_path: Path, scale: int = 2000) -> Path:
    gen = _load_module("sample_gen_def019", GENERATOR_PATH)
    out_dir = tmp_path / "corpus"
    # Positional (base_dir, scale): the pre-fix signature has no `seed`
    # parameter, so keyword use would fail there for the wrong reason.
    gen.generate_dataset(str(out_dir), scale)
    return out_dir / "d365_gl_actuals.csv"


def _read_rows(gl_csv: Path):
    with open(gl_csv, mode="r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = None
        for row in reader:
            if not row or not row[0].strip() or row[0].strip().startswith("#"):
                continue
            header = row
            break
        assert header is not None, f"No header found in {gl_csv}"
        idx = {c.strip(): i for i, c in enumerate(header)}
        rows = [r for r in reader if r]
    return idx, rows


def _is_baseline(voucher: str) -> bool:
    try:
        return int(voucher.rsplit("-", 1)[-1]) >= BASELINE_SEQ_FLOOR
    except (ValueError, IndexError):
        return False


def test_baseline_vouchers_balance_per_voucher(tmp_path):
    """Every baseline voucher nets to exactly 0.00 (Dr == Cr).

    Pre-fix this fails on every baseline voucher: each was a single-sided
    row with no offsetting leg.
    """
    idx, rows = _read_rows(_generate(tmp_path))
    legs = defaultdict(lambda: [Decimal("0.00"), Decimal("0.00")])
    baseline_vouchers = set()
    for row in rows:
        voucher = row[idx["Voucher"]].strip()
        if not _is_baseline(voucher):
            continue
        baseline_vouchers.add(voucher)
        legs[voucher][0] += Decimal(row[idx["Debit"]] or "0.00")
        legs[voucher][1] += Decimal(row[idx["Credit"]] or "0.00")

    assert len(baseline_vouchers) == 1000, (
        f"Expected 1000 baseline vouchers (scale 2000 // 2), found "
        f"{len(baseline_vouchers)}"
    )
    imbalanced = {
        v: (d, c) for v, (d, c) in legs.items() if d - c != Decimal("0.00")
    }
    assert not imbalanced, (
        f"{len(imbalanced)} baseline vouchers do not balance "
        f"(showing 5): {dict(list(imbalanced.items())[:5])}"
    )


def test_baseline_never_posts_to_suspense_1999(tmp_path):
    """Routine postings to 1999 net to exactly 0.00.

    Only planted P24 may touch the suspense account; a baseline leg there
    (or a suspense plug) would corrupt the EXC-024 signal, which must read
    exactly the planted 1,240,000.00 debit.
    """
    idx, rows = _read_rows(_generate(tmp_path))
    touching = set()
    net = Decimal("0.00")
    for row in rows:
        if row[idx["MainAccount"]].strip() != SUSPENSE_ACCOUNT:
            continue
        voucher = row[idx["Voucher"]].strip()
        touching.add(voucher)
        net += Decimal(row[idx["Debit"]] or "0.00")
        net -= Decimal(row[idx["Credit"]] or "0.00")

    assert touching == {P24_VOUCHER}, (
        f"Suspense account 1999 touched by unexpected vouchers: "
        f"{sorted(touching)} (only planted {P24_VOUCHER} may post there)"
    )
    assert net == Decimal("1240000.00"), (
        f"Suspense net is {net}, expected exactly the planted P24 "
        f"1,240,000.00 debit"
    )


def test_baseline_offset_pairings(tmp_path):
    """Revenue vouchers pair Cr-revenue with Dr 1200/1010; expense vouchers
    pair Dr-expense with Cr 2000/1010. No other offset account may appear in
    a baseline voucher.

    Pre-fix this fails: baseline vouchers were single legs with no offset.
    """
    idx, rows = _read_rows(_generate(tmp_path))
    by_voucher = defaultdict(list)
    for row in rows:
        voucher = row[idx["Voucher"]].strip()
        if _is_baseline(voucher):
            by_voucher[voucher].append(row)

    bad = []
    for voucher, legs in by_voucher.items():
        if len(legs) != 2:
            bad.append((voucher, f"expected 2 legs, found {len(legs)}"))
            continue
        accounts = {r[idx["MainAccount"]].strip() for r in legs}
        debits = [Decimal(r[idx["Debit"]] or "0.00") for r in legs]
        credits = [Decimal(r[idx["Credit"]] or "0.00") for r in legs]
        amounts = {f"{d:.2f}" for d in debits if d} | {
            f"{c:.2f}" for c in credits if c
        }
        if len(amounts) != 1:
            bad.append((voucher, f"legs disagree on amount: {amounts}"))
            continue
        revenue_leg = [r for r in legs if Decimal(r[idx["Credit"]] or "0.00") > 0
                       and r[idx["MainAccount"]].strip() not in REVENUE_OFFSETS | EXPENSE_OFFSETS]
        expense_leg = [r for r in legs if Decimal(r[idx["Debit"]] or "0.00") > 0
                       and r[idx["MainAccount"]].strip() not in REVENUE_OFFSETS | EXPENSE_OFFSETS]
        offset_leg = [r for r in legs
                      if r[idx["MainAccount"]].strip() in REVENUE_OFFSETS | EXPENSE_OFFSETS]
        if len(offset_leg) != 1 or len(revenue_leg) + len(expense_leg) != 1:
            bad.append((voucher, f"not one P&L leg + one offset leg: {accounts}"))
            continue
        offset_acct = offset_leg[0][idx["MainAccount"]].strip()
        if revenue_leg:
            if offset_acct not in REVENUE_OFFSETS or not (
                Decimal(offset_leg[0][idx["Debit"]] or "0.00") > 0
            ):
                bad.append((voucher, f"revenue leg offset by {offset_acct}, want Dr 1200/1010"))
        else:
            if offset_acct not in EXPENSE_OFFSETS or not (
                Decimal(offset_leg[0][idx["Credit"]] or "0.00") > 0
            ):
                bad.append((voucher, f"expense leg offset by {offset_acct}, want Cr 2000/1010"))

    assert not bad, (
        f"{len(bad)} baseline vouchers break the pairing rule "
        f"(showing 5): {bad[:5]}"
    )


def test_planted_p23_imbalance_preserved(tmp_path):
    """The planted P23 signal survives the rebuild: its INV-IMB lines net
    to exactly 5,000.00 Dr. Balancing the plant would silence EXC-023
    (`evaluate_exc_023` sums Dr vs Cr per voucher), so this test fails if
    anyone "fixes" the planted block.
    """
    idx, rows = _read_rows(_generate(tmp_path))
    net = Decimal("0.00")
    count = 0
    for row in rows:
        if row[idx["InvoiceNumber"]].strip() != P23_INVOICE:
            continue
        count += 1
        net += Decimal(row[idx["Debit"]] or "0.00")
        net -= Decimal(row[idx["Credit"]] or "0.00")

    assert count == 2, f"Expected the 2 planted P23 INV-IMB lines, found {count}"
    assert net == P23_RESIDUAL, (
        f"Planted P23 nets to {net}, expected exactly {P23_RESIDUAL} "
        f"(the EXC-023 signal must survive the rebuild)"
    )


def test_verifier_reports_per_voucher_entity_period(tmp_path):
    """`verify_trial_balance` per-voucher detail agrees with per
    entity/period -- all baseline vouchers balanced, planted P23 flagged.

    (Verifies the script entry point used for DEF-019 acceptance.)
    """
    gl_csv = _generate(tmp_path)
    verifier = _load_module("verify_tb_def019", VERIFIER_PATH)
    result = verifier.verify_gl_trial_balance(gl_csv)

    assert result.by_voucher, "Verifier reports no per-voucher detail"
    baseline_bad = [
        vb.voucher for vb in result.by_voucher.values()
        if _is_baseline(vb.voucher) and not vb.is_balanced
    ]
    assert not baseline_bad, (
        f"{len(baseline_bad)} baseline vouchers flagged imbalanced by the "
        f"verifier (showing 5): {baseline_bad[:5]}"
    )
    flagged = {vb.voucher for vb in result.imbalanced_vouchers}
    assert "VCH-2026-0912-004" in flagged, (
        "Planted P23 voucher VCH-2026-0912-004 must appear in the "
        "verifier's imbalanced-voucher list"
    )
    assert result.by_entity and result.by_period, (
        "Verifier must still report per-entity and per-period breakdowns"
    )
