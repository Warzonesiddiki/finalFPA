"""GL Trial-Balance Verifier with minor-unit exact Decimal arithmetic.

Proves GL trial-balance (per-voucher, per-entity, per-period and whole-file
debit == credit) and prints the residual. Reusable by acceptance harness and
standalone CLI.

Doc 04 §10, §12 (IMP-023: Debit = credit within tolerance, per
file/entity/period). Per-voucher detail additionally supports DEF-019: the
sample-data baseline must be balanced per voucher, while the planted block
(P23 voucher imbalance, single-sided plant rows) is unbalanced by design, so
the voucher section is diagnostic -- the file verdict stays on
file/entity/period per IMP-023.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional


ZERO = Decimal("0.00")


@dataclass
class PeriodBalance:
    period: str
    row_count: int = 0
    total_debit: Decimal = field(default_factory=lambda: Decimal("0.00"))
    total_credit: Decimal = field(default_factory=lambda: Decimal("0.00"))

    @property
    def net_residual(self) -> Decimal:
        return self.total_debit - self.total_credit

    @property
    def is_balanced(self) -> bool:
        return self.net_residual == ZERO


@dataclass
class EntityBalance:
    company_code: str
    row_count: int = 0
    total_debit: Decimal = field(default_factory=lambda: Decimal("0.00"))
    total_credit: Decimal = field(default_factory=lambda: Decimal("0.00"))

    @property
    def net_residual(self) -> Decimal:
        return self.total_debit - self.total_credit

    @property
    def is_balanced(self) -> bool:
        return self.net_residual == ZERO


@dataclass
class VoucherBalance:
    voucher: str
    company_code: str
    row_count: int = 0
    total_debit: Decimal = field(default_factory=lambda: Decimal("0.00"))
    total_credit: Decimal = field(default_factory=lambda: Decimal("0.00"))

    @property
    def net_residual(self) -> Decimal:
        return self.total_debit - self.total_credit

    @property
    def is_balanced(self) -> bool:
        return self.net_residual == ZERO


@dataclass
class TrialBalanceResult:
    file_path: Path
    total_rows: int = 0
    total_debit: Decimal = field(default_factory=lambda: Decimal("0.00"))
    total_credit: Decimal = field(default_factory=lambda: Decimal("0.00"))
    by_entity: Dict[str, EntityBalance] = field(default_factory=dict)
    by_period: Dict[str, PeriodBalance] = field(default_factory=dict)
    by_voucher: Dict[tuple, VoucherBalance] = field(default_factory=dict)

    @property
    def net_residual(self) -> Decimal:
        return self.total_debit - self.total_credit

    @property
    def is_balanced(self) -> bool:
        return (
            self.net_residual == ZERO
            and all(eb.is_balanced for eb in self.by_entity.values())
            and all(pb.is_balanced for pb in self.by_period.values())
        )

    @property
    def balanced_voucher_count(self) -> int:
        return sum(1 for vb in self.by_voucher.values() if vb.is_balanced)

    @property
    def imbalanced_vouchers(self) -> List[VoucherBalance]:
        bad = [vb for vb in self.by_voucher.values() if not vb.is_balanced]
        bad.sort(key=lambda vb: abs(vb.net_residual), reverse=True)
        return bad

    def format_report(self) -> str:
        lines: List[str] = [
            "=" * 70,
            f"GL TRIAL BALANCE VERIFICATION REPORT: {self.file_path.name}",
            "=" * 70,
            f"File Path:     {self.file_path}",
            f"Total Rows:    {self.total_rows:,}",
            f"Total Debit:   INR {self.total_debit:,.2f}",
            f"Total Credit:  INR {self.total_credit:,.2f}",
            f"Net Residual:  INR {self.net_residual:,.2f} ({'BALANCED' if self.net_residual == ZERO else 'UNBALANCED'})",
            "-" * 70,
            "PER-ENTITY BREAKDOWN:",
        ]
        for comp, eb in sorted(self.by_entity.items()):
            status = "BALANCED" if eb.is_balanced else "UNBALANCED"
            lines.append(
                f"  Entity {comp:6s} | Rows: {eb.row_count:7,} | "
                f"Debit: {eb.total_debit:18,.2f} | Credit: {eb.total_credit:18,.2f} | "
                f"Residual: {eb.net_residual:18,.2f} [{status}]"
            )
        lines.append("-" * 70)
        lines.append("PER-PERIOD BREAKDOWN:")
        for per, pb in sorted(self.by_period.items()):
            status = "BALANCED" if pb.is_balanced else "UNBALANCED"
            lines.append(
                f"  Period {per:7s} | Rows: {pb.row_count:7,} | "
                f"Debit: {pb.total_debit:18,.2f} | Credit: {pb.total_credit:18,.2f} | "
                f"Residual: {pb.net_residual:18,.2f} [{status}]"
            )
        lines.append("-" * 70)
        lines.append("PER-VOUCHER SUMMARY (diagnostic: planted vouchers are unbalanced by design):")
        lines.append(
            f"  Vouchers: {len(self.by_voucher):,} | "
            f"Balanced: {self.balanced_voucher_count:,} | "
            f"Imbalanced: {len(self.imbalanced_vouchers):,}"
        )
        for vb in self.imbalanced_vouchers[:20]:
            lines.append(
                f"  Voucher {vb.voucher:24s} ({vb.company_code:6s}) | Rows: {vb.row_count:4,} | "
                f"Debit: {vb.total_debit:18,.2f} | Credit: {vb.total_credit:18,.2f} | "
                f"Residual: {vb.net_residual:18,.2f} [UNBALANCED]"
            )
        if len(self.imbalanced_vouchers) > 20:
            lines.append(
                f"  ... and {len(self.imbalanced_vouchers) - 20:,} further imbalanced vouchers (not shown)"
            )
        lines.append("-" * 70)
        lines.append(f"OVERALL VERDICT: {'PASS - PERFECT BALANCE' if self.is_balanced else 'FAIL - IMBALANCED'}")
        lines.append("=" * 70)
        return "\n".join(lines)


def parse_decimal(val: str) -> Decimal:
    """Parse string to Decimal safely without float rounding."""
    clean = val.strip().replace(",", "") if val else ""
    if not clean:
        return ZERO
    return Decimal(clean)


def verify_gl_trial_balance(file_path: str | Path) -> TrialBalanceResult:
    """Read GL CSV file and verify debit == credit per entity and whole file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"GL file not found: {path}")

    res = TrialBalanceResult(file_path=path)

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = None
        for row in reader:
            if not row or not row[0].strip() or row[0].strip().startswith("#"):
                continue
            header = row
            break
        if not header:
            return res

        header_idx = {col.strip().lower().replace("_", ""): idx for idx, col in enumerate(header)}
        comp_idx = header_idx.get("companycode")
        date_idx = header_idx.get("postingdate")
        voucher_idx = header_idx.get("voucher")
        debit_idx = header_idx.get("debit")
        credit_idx = header_idx.get("credit")

        if debit_idx is None or credit_idx is None:
            raise ValueError(f"Required 'debit' and 'credit' columns not found in {path.name}")

        for row in reader:
            if not row:
                continue
            res.total_rows += 1
            comp = row[comp_idx].strip() if comp_idx is not None and comp_idx < len(row) else "UNKNOWN"
            date_str = row[date_idx].strip() if date_idx is not None and date_idx < len(row) else ""
            period = date_str[:7] if len(date_str) >= 7 else "UNKNOWN"
            voucher = row[voucher_idx].strip() if voucher_idx is not None and voucher_idx < len(row) else "UNKNOWN"

            debit_str = row[debit_idx] if debit_idx < len(row) else "0"
            credit_str = row[credit_idx] if credit_idx < len(row) else "0"

            d = parse_decimal(debit_str)
            c = parse_decimal(credit_str)

            res.total_debit += d
            res.total_credit += c

            if comp not in res.by_entity:
                res.by_entity[comp] = EntityBalance(company_code=comp)
            eb = res.by_entity[comp]
            eb.row_count += 1
            eb.total_debit += d
            eb.total_credit += c

            if period not in res.by_period:
                res.by_period[period] = PeriodBalance(period=period)
            pb = res.by_period[period]
            pb.row_count += 1
            pb.total_debit += d
            pb.total_credit += c

            vkey = (comp, voucher)
            if vkey not in res.by_voucher:
                res.by_voucher[vkey] = VoucherBalance(voucher=voucher, company_code=comp)
            vb = res.by_voucher[vkey]
            vb.row_count += 1
            vb.total_debit += d
            vb.total_credit += c

    return res


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify GL trial balance debit == credit.")
    parser.add_argument("file", nargs="?", default="sample-data/d365_gl_actuals.csv",
                        help="GL actuals CSV file (default: sample-data/d365_gl_actuals.csv)")
    args = parser.parse_args()

    result = verify_gl_trial_balance(args.file)
    print(result.format_report())
    return 0 if result.is_balanced else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
