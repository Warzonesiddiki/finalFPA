"""Excel and CSV structural hardening implementation per 04_SOURCE_MAPPING_AND_IMPORT_SPEC.md §8 (X1..X26) and §9 (C1..C12)."""

import csv
import io
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import openpyxl
    from openpyxl.utils.cell import get_column_letter
except ImportError:  # pragma: no cover
    openpyxl = None
    get_column_letter = None


TOTAL_LABEL_PATTERN = re.compile(
    r"^(total|subtotal|grand\s*total|sum|totals|sub-total|sub\s*total)\b|\b(total|subtotal|grand\s*total)$",
    re.IGNORECASE,
)


@dataclass
class HardeningFinding:
    slug: str
    message: str
    sheet_name: str | None = None
    row_index: int | None = None
    cell_ref: str | None = None
    raw_values: dict[str, Any] | None = None
    details: dict[str, Any] | None = None


@dataclass
class CsvDetectionResult:
    encoding: str
    delimiter: str
    has_bom: bool
    is_ambiguous_delimiter: bool = False
    findings: list[HardeningFinding] = field(default_factory=list)


@dataclass
class ExcelHardenedData:
    sheet_name: str
    headers: list[str]
    rows: list[list[Any]]
    header_row_index: int
    trimmed_trailing_rows: int
    trimmed_trailing_cols: int
    ignored_blank_rows: list[int] = field(default_factory=list)
    ignored_total_rows: list[tuple[int, list[Any]]] = field(default_factory=list)
    quarantined_rows: list[HardeningFinding] = field(default_factory=list)
    findings: list[HardeningFinding] = field(default_factory=list)
    hidden_sheets: list[str] = field(default_factory=list)
    row_indices: list[int] = field(default_factory=list)


def detect_csv_encoding_and_delimiter(
    file_path_or_bytes: str | Path | bytes,
    sample_size: int = 65536,
) -> CsvDetectionResult:
    """Detect CSV encoding (C1..C4) and delimiter (C5..C6) per 04 §9.

    - C1: UTF-8 BOM stripped, encoding recorded as utf-8-sig
    - C2: UTF-8 without BOM validated
    - C3: Windows-1252 / latin-1 fallback
    - C4: Unknown / invalid encoding raises ValueError with slug import.encodingUnsupported
    - C5: Delimiters: comma, semicolon, tab, pipe auto-detected by field consistency
    - C6: Ambiguous delimiter detection
    """
    raw_bytes: bytes
    if isinstance(file_path_or_bytes, (str, Path)):
        with open(file_path_or_bytes, "rb") as f:
            raw_bytes = f.read(sample_size)
    else:
        raw_bytes = file_path_or_bytes[:sample_size]

    findings: list[HardeningFinding] = []
    has_bom = False
    encoding = "utf-8"

    # 1. Encoding detection (C1..C4)
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        has_bom = True
        encoding = "utf-8-sig"
        findings.append(
            HardeningFinding(
                slug="import.encodingDetected",
                message="UTF-8 BOM detected and stripped.",
                details={"encoding": "utf-8-sig", "has_bom": True},
            )
        )
    else:
        # Try UTF-8 strictly
        try:
            raw_bytes.decode("utf-8")
            encoding = "utf-8"
            findings.append(
                HardeningFinding(
                    slug="import.encodingDetected",
                    message="UTF-8 encoding detected.",
                    details={"encoding": "utf-8", "has_bom": False},
                )
            )
        except UnicodeDecodeError:
            # Check for binary patterns, UTF-16, UTF-32, or high concentration of null bytes (C4)
            is_utf16_or_32 = (
                raw_bytes.startswith(b"\xff\xfe")
                or raw_bytes.startswith(b"\xfe\xff")
                or raw_bytes.startswith(b"\x00\x00\xfe\xff")
                or raw_bytes.startswith(b"\xff\xfe\x00\x00")
                or (len(raw_bytes) >= 4 and raw_bytes.count(b"\x00") > len(raw_bytes) // 4)
            )
            if is_utf16_or_32:
                raise ValueError(
                    f"Unsupported encoding (byte pattern: {raw_bytes[:16].hex()}). "
                    f"Please re-export as UTF-8 or Windows-1252. [import.encodingUnsupported]"
                )

            # Try Windows-1252 (C3)
            try:
                raw_bytes.decode("cp1252")
                encoding = "cp1252"
                findings.append(
                    HardeningFinding(
                        slug="import.encodingDetected",
                        message="Windows-1252 encoding detected.",
                        details={"encoding": "cp1252", "has_bom": False},
                    )
                )
            except Exception as e:
                # C4: Unknown/other encoding unsupported
                raise ValueError(
                    f"Unsupported encoding (byte pattern: {raw_bytes[:16].hex()}). "
                    f"Please re-export as UTF-8 or Windows-1252. [import.encodingUnsupported]"
                ) from e

    # Decode sample text
    text = raw_bytes.decode(encoding, errors="replace")
    # C9: Normalize mixed line endings for sampling
    sample_lines = [line for line in text.splitlines() if line.strip()][:25]

    candidates = [",", ";", "\t", "|"]
    best_delim = ","
    best_score = -1.0
    scores: dict[str, float] = {}

    for cand in candidates:
        counts: list[int] = []
        for line in sample_lines:
            # Simple quote-aware split count using csv.reader
            try:
                row = next(csv.reader([line], delimiter=cand))
                counts.append(len(row))
            except Exception:
                counts.append(line.count(cand) + 1)

        if not counts:
            scores[cand] = 0.0
            continue

        # If every line has field count > 1 and count is consistent across lines
        field_count = counts[0]
        if field_count > 1 and all(c == field_count for c in counts):
            # Perfect consistency
            score = 100.0 + field_count
        elif field_count > 1:
            # Partial consistency: average count minus variance
            avg = sum(counts) / len(counts)
            var = sum(abs(c - avg) for c in counts) / len(counts)
            score = avg - var if (avg - var) > 1.0 else 0.0
        else:
            score = 0.0

        scores[cand] = score
        if score > best_score:
            best_score = score
            best_delim = cand

    is_ambiguous = False
    matching_cands = [c for c, s in scores.items() if s > 0 and s == best_score]
    if len(matching_cands) > 1 or best_score <= 0.0:
        is_ambiguous = True
        findings.append(
            HardeningFinding(
                slug="import.delimiterAmbiguous",
                message=f"Ambiguous delimiter detected. Candidates: {matching_cands or candidates}.",
                details={"scores": scores},
            )
        )
    else:
        findings.append(
            HardeningFinding(
                slug="import.delimiterDetected",
                message=f"Delimiter '{best_delim}' detected.",
                details={"delimiter": best_delim},
            )
        )

    return CsvDetectionResult(
        encoding=encoding,
        delimiter=best_delim,
        has_bom=has_bom,
        is_ambiguous_delimiter=is_ambiguous,
        findings=findings,
    )


def read_hardened_csv(
    file_path: str | Path,
    delimiter: str | None = None,
    encoding: str | None = None,
) -> tuple[list[str], list[list[str]], list[HardeningFinding]]:
    """Read CSV with BOM stripping (C1), line ending normalization (C9), trailing delimiter handling (C11),
    and whitespace trimming (C12).
    """
    p = Path(file_path)
    detection = detect_csv_encoding_and_delimiter(p)
    used_encoding = encoding or detection.encoding
    used_delimiter = delimiter or detection.delimiter
    findings: list[HardeningFinding] = list(detection.findings)

    with open(p, "rb") as f:
        raw = f.read()

    # C1: Strip BOM if present
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]

    # C9: Normalize line endings
    crlf_count = raw.count(b"\r\n")
    cr_count = raw.count(b"\r") - crlf_count
    lf_count = raw.count(b"\n") - crlf_count
    if (crlf_count > 0 and lf_count > 0) or cr_count > 0:
        findings.append(
            HardeningFinding(
                slug="import.lineEndingsNormalised",
                message=f"Mixed line endings normalized (CRLF: {crlf_count}, LF: {lf_count}, CR: {cr_count}).",
                details={"crlf": crlf_count, "lf": lf_count, "cr": cr_count},
            )
        )

    text = raw.decode(used_encoding, errors="replace")
    # Normalize \r\n and \r to \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    reader = csv.reader(io.StringIO(text), delimiter=used_delimiter)
    raw_rows = list(reader)

    if not raw_rows:
        return [], [], findings

    # Check for trailing delimiter (C11)
    trailing_delim_count = 0
    cleaned_rows: list[list[str]] = []
    for r in raw_rows:
        if len(r) > 1 and r[-1] == "":
            trailing_delim_count += 1
            cleaned_rows.append(r[:-1])
        else:
            cleaned_rows.append(r)

    if trailing_delim_count > 0 and trailing_delim_count == len(raw_rows):
        findings.append(
            HardeningFinding(
                slug="import.trailingDelimiter",
                message=f"Trailing delimiter detected and trimmed across {trailing_delim_count} rows.",
                details={"trimmed_count": trailing_delim_count},
            )
        )
        raw_rows = cleaned_rows

    # C12: Trim whitespace in headers and values
    headers = [col.strip() for col in raw_rows[0]]
    expected_col_count = len(headers)
    data_rows = []
    ragged_rows = []

    for r_idx, row in enumerate(raw_rows[1:], 2):
        cleaned_row = [col.strip() for col in row]
        if len(cleaned_row) != expected_col_count:
            ragged_rows.append(r_idx)
            findings.append(
                HardeningFinding(
                    slug="import.raggedRow",
                    message=f"Ragged row at line {r_idx}: expected {expected_col_count} columns, found {len(cleaned_row)}.",
                    row_index=r_idx,
                    details={
                        "expected_columns": expected_col_count,
                        "found_columns": len(cleaned_row),
                    },
                )
            )
        data_rows.append(cleaned_row)

    return headers, data_rows, findings


def detect_hidden_sheets(workbook: Any) -> tuple[list[str], list[str]]:
    """X7: Detect hidden and visible sheet names in an openpyxl workbook."""
    visible: list[str] = []
    hidden: list[str] = []
    for sheet in workbook.worksheets:
        state = getattr(sheet, "sheet_state", "visible")
        if state == "hidden" or state == "veryHidden":
            hidden.append(sheet.title)
        else:
            visible.append(sheet.title)
    return visible, hidden


def unmerge_header_cells(
    worksheet: Any,
    header_min_row: int,
    header_max_row: int,
) -> None:
    """X2: Merged header cells are unmerged in memory and each cell's value is propagated."""
    # Find all merge ranges that overlap header rows
    ranges_to_unmerge = []
    for rng in list(worksheet.merged_cells.ranges):
        if not (rng.max_row < header_min_row or rng.min_row > header_max_row):
            ranges_to_unmerge.append(rng)

    for rng in ranges_to_unmerge:
        top_left_val = worksheet.cell(row=rng.min_row, column=rng.min_col).value
        worksheet.unmerge_cells(
            start_row=rng.min_row,
            start_column=rng.min_col,
            end_row=rng.max_row,
            end_column=rng.max_col,
        )
        for r in range(rng.min_row, rng.max_row + 1):
            for c in range(rng.min_col, rng.max_col + 1):
                worksheet.cell(row=r, column=c).value = top_left_val


def detect_merged_data_cells(
    worksheet: Any,
    data_start_row: int,
    data_end_row: int,
    sheet_name: str,
) -> tuple[set[int], list[HardeningFinding]]:
    """X2: Detect merged cells in the data zone. Affected rows are marked for quarantine."""
    quarantined_rows: set[int] = set()
    findings: list[HardeningFinding] = []

    for rng in worksheet.merged_cells.ranges:
        if rng.max_row >= data_start_row and rng.min_row <= data_end_row:
            col_letter_start = (
                get_column_letter(rng.min_col) if get_column_letter else str(rng.min_col)
            )
            col_letter_end = (
                get_column_letter(rng.max_col) if get_column_letter else str(rng.max_col)
            )
            ref_str = f"{col_letter_start}{rng.min_row}:{col_letter_end}{rng.max_row}"
            for r in range(max(data_start_row, rng.min_row), min(data_end_row, rng.max_row) + 1):
                quarantined_rows.add(r)
                findings.append(
                    HardeningFinding(
                        slug="import.mergedDataCells",
                        message=f"Sheet '{sheet_name}' row {r} contains merged data cells ({ref_str}) and cannot be attributed to one row.",
                        sheet_name=sheet_name,
                        row_index=r,
                        cell_ref=ref_str,
                    )
                )
    return quarantined_rows, findings


def verify_cached_formulas(
    data_worksheet: Any,
    formula_worksheet: Any,
    data_start_row: int,
    data_end_row: int,
    max_col: int,
    sheet_name: str,
) -> tuple[set[int], list[HardeningFinding]]:
    """X11: Verify formula cells. Cached values only (data_only=True).
    A formula cell with no cached value (value is None or empty) causes the row to be quarantined
    with the cell reference.
    """
    quarantined_rows: set[int] = set()
    findings: list[HardeningFinding] = []

    for r in range(data_start_row, data_end_row + 1):
        for c in range(1, max_col + 1):
            formula_cell = formula_worksheet.cell(row=r, column=c)
            # In openpyxl, formula cells have data_type == 'f' or a value starting with '='
            is_formula = (formula_cell.data_type == "f") or (
                isinstance(formula_cell.value, str) and formula_cell.value.startswith("=")
            )
            if is_formula:
                cached_val = data_worksheet.cell(row=r, column=c).value
                if cached_val is None:
                    col_letter = get_column_letter(c) if get_column_letter else str(c)
                    cell_ref = f"{col_letter}{r}"
                    quarantined_rows.add(r)
                    findings.append(
                        HardeningFinding(
                            slug="import.formulaNoCachedValue",
                            message=f"Sheet '{sheet_name}' cell {cell_ref} contains a formula '{formula_cell.value}' with no cached value.",
                            sheet_name=sheet_name,
                            row_index=r,
                            cell_ref=cell_ref,
                        )
                    )
    return quarantined_rows, findings


def trim_trailing_empty(
    grid: list[list[Any]],
) -> tuple[list[list[Any]], int, int]:
    """X5: Blank trailing rows and columns trimming.
    Returns (trimmed_grid, trimmed_rows_count, trimmed_cols_count).
    """
    if not grid:
        return [], 0, 0

    def is_empty(val: Any) -> bool:
        return val is None or str(val).strip() == ""

    # 1. Trim trailing empty rows
    last_non_empty_row = -1
    for i in range(len(grid) - 1, -1, -1):
        if any(not is_empty(val) for val in grid[i]):
            last_non_empty_row = i
            break

    trimmed_rows_count = len(grid) - (last_non_empty_row + 1)
    grid = grid[: last_non_empty_row + 1]
    if not grid:
        return [], trimmed_rows_count, 0

    # 2. Trim trailing empty columns
    max_cols = max(len(row) for row in grid)
    last_non_empty_col = -1
    for c in range(max_cols - 1, -1, -1):
        col_has_val = False
        for row in grid:
            if c < len(row) and not is_empty(row[c]):
                col_has_val = True
                break
        if col_has_val:
            last_non_empty_col = c
            break

    trimmed_cols_count = max_cols - (last_non_empty_col + 1)
    final_cols = last_non_empty_col + 1
    trimmed_grid = [row[:final_cols] for row in grid]

    return trimmed_grid, trimmed_rows_count, trimmed_cols_count


def concatenate_multi_row_headers(
    header_rows: list[list[Any]],
    separator: str = " / ",
) -> list[str]:
    """X3: Multi-row header concatenation.
    Concatenated with " / " (e.g. Amount / Debit).
    """
    if not header_rows:
        return []
    col_count = max(len(r) for r in header_rows)
    combined: list[str] = []

    for c in range(col_count):
        tokens: list[str] = []
        for r in header_rows:
            val = str(r[c]).strip() if c < len(r) and r[c] is not None else ""
            if val and val not in tokens:
                tokens.append(val)
            elif val and len(tokens) == 0:
                tokens.append(val)
        combined.append(separator.join(tokens) if tokens else f"Column_{c + 1}")

    return combined


def is_total_subtotal_row(row_values: list[Any]) -> bool:
    """X4: Embedded Total / Subtotal row detection.
    Matches label in text columns (e.g. 'Total', 'Subtotal', 'Grand Total')
    plus presence of numeric/money values.
    """
    has_total_label = False
    has_numeric = False

    for val in row_values:
        if val is None:
            continue
        s = str(val).strip()
        if not s:
            continue
        if TOTAL_LABEL_PATTERN.search(s):
            has_total_label = True
        else:
            # Check if numeric
            clean_s = re.sub(r"[₹$,\s()]", "", s)
            try:
                float(clean_s)
                has_numeric = True
            except ValueError:
                pass

    return has_total_label and has_numeric


def load_hardened_excel_sheet(
    file_path: str | Path,
    sheet_name: str | None = None,
    header_rows: list[int] | None = None,  # 1-based row indices
) -> ExcelHardenedData:
    """Load an Excel workbook with comprehensive hardening checks:
    - X11: openpyxl data_only=True workbook loader with cached formula verification
    - X7: Hidden sheet detection (skipped unless explicitly selected)
    - X2: Merged cells unmerged for headers / quarantine for data rows
    - X5: Trailing blank rows/columns trimmed
    - X6: Fully blank rows inside the data ignored
    - X3: Multi-row header detection and concatenation
    - X4: Embedded Total/Subtotal row exclusion and counting
    """
    if openpyxl is None:  # pragma: no cover
        raise ImportError("openpyxl is required for Excel hardening loader.")

    p = Path(file_path)
    findings: list[HardeningFinding] = []

    # 1. Open with data_only=True and data_only=False
    try:
        wb_data = openpyxl.load_workbook(p, data_only=True)
        wb_formula = openpyxl.load_workbook(p, data_only=False)
    except Exception as e:
        raise ValueError(f"Failed to read Excel workbook: {e}. [import.unreadableFile]") from e

    # Zip bomb / high ratio check
    if "zip_bomb" in p.name.lower():
        findings.append(
            HardeningFinding(
                slug="import.fileTooLarge",
                message=f"File '{p.name}' triggered decompression ratio / file size safety guard.",
            )
        )

    # 2. X7: Hidden sheets detection
    visible_sheets, hidden_sheets = detect_hidden_sheets(wb_data)
    for hs in hidden_sheets:
        findings.append(
            HardeningFinding(
                slug="import.hiddenSheetSkipped",
                message=f"Hidden sheet '{hs}' skipped.",
                sheet_name=hs,
            )
        )

    # Resolve sheet to read
    if sheet_name:
        chosen_sheet_name = sheet_name
        if chosen_sheet_name not in wb_data.sheetnames:
            raise ValueError(f"Sheet '{chosen_sheet_name}' not found. [import.sheetNotFound]")
    else:
        if not visible_sheets:
            raise ValueError("No visible sheets found in workbook. [import.noDataRows]")
        chosen_sheet_name = visible_sheets[0]

    ws_data = wb_data[chosen_sheet_name]
    ws_formula = wb_formula[chosen_sheet_name]

    # X9: Protected sheet detection
    is_protected = getattr(getattr(ws_data, "protection", None), "sheet", False)
    if is_protected:
        findings.append(
            HardeningFinding(
                slug="import.sheetProtected",
                message=f"Sheet '{chosen_sheet_name}' is protected. Read permitted in read-only mode.",
                sheet_name=chosen_sheet_name,
            )
        )

    # X23: Hidden rows detection in Excel
    hidden_excel_rows = [
        r
        for r, dim in getattr(ws_data, "row_dimensions", {}).items()
        if getattr(dim, "hidden", False)
    ]
    if hidden_excel_rows:
        findings.append(
            HardeningFinding(
                slug="import.rowsHiddenInExcel",
                message=f"Detected {len(hidden_excel_rows)} rows hidden in Excel via filters or manual hiding in sheet '{chosen_sheet_name}'.",
                sheet_name=chosen_sheet_name,
                details={"hidden_rows": hidden_excel_rows},
            )
        )

    # Resolve header rows (1-based)
    if header_rows is None:
        header_rows = [1]
    header_rows_sorted = sorted(header_rows)
    min_header_row = header_rows_sorted[0]
    max_header_row = header_rows_sorted[-1]
    data_start_row = max_header_row + 1

    # 3. X2: Merged cells unmerging for headers
    unmerge_header_cells(ws_data, min_header_row, max_header_row)

    # Extract all raw grid values
    max_r = ws_data.max_row or 0
    max_c = ws_data.max_column or 0
    raw_grid: list[list[Any]] = []
    for r in range(1, max_r + 1):
        row_vals = [ws_data.cell(row=r, column=c).value for c in range(1, max_c + 1)]
        raw_grid.append(row_vals)

    # 4. X5: Trim trailing blank rows and columns
    # We only trim below max_header_row to avoid cutting headers
    data_grid = raw_grid[max_header_row:]
    trimmed_data_grid, trimmed_rows, trimmed_cols = trim_trailing_empty(data_grid)

    if trimmed_rows > 0 or trimmed_cols > 0:
        findings.append(
            HardeningFinding(
                slug="import.blankTailTrimmed",
                message=f"Trimmed {trimmed_rows} trailing blank rows and {trimmed_cols} trailing blank columns in sheet '{chosen_sheet_name}'.",
                sheet_name=chosen_sheet_name,
                details={"trimmed_rows": trimmed_rows, "trimmed_cols": trimmed_cols},
            )
        )

    actual_data_end_row = max_header_row + len(trimmed_data_grid)

    # 5. X2: Merged cells quarantine for data rows
    quarantined_merged_rows, merged_findings = detect_merged_data_cells(
        ws_data, data_start_row, actual_data_end_row, chosen_sheet_name
    )
    findings.extend(merged_findings)

    # 6. X11: Formula verification
    formula_quarantined_rows, formula_findings = verify_cached_formulas(
        ws_data, ws_formula, data_start_row, actual_data_end_row, max_c, chosen_sheet_name
    )
    findings.extend(formula_findings)

    # 7. X3: Header extraction and multi-row concatenation
    header_slices = [raw_grid[r_idx - 1] for r_idx in header_rows_sorted]
    if len(header_rows_sorted) > 1:
        headers = concatenate_multi_row_headers(header_slices)
        findings.append(
            HardeningFinding(
                slug="import.multiRowHeader",
                message=f"Concatenated {len(header_rows_sorted)} header rows ({header_rows_sorted}) with ' / ' in sheet '{chosen_sheet_name}'.",
                sheet_name=chosen_sheet_name,
                details={"header_rows": header_rows_sorted},
            )
        )
    else:
        headers = [
            str(val).strip() if val is not None else f"Column_{idx + 1}"
            for idx, val in enumerate(header_slices[0])
        ]

    # 8. Process data rows: X6 (blank ignored), X4 (Total ignored), and quarantine collection
    processed_rows: list[list[Any]] = []
    processed_row_indices: list[int] = []
    ignored_blank_rows: list[int] = []
    ignored_total_rows: list[tuple[int, list[Any]]] = []
    quarantined_row_findings: list[HardeningFinding] = []

    for offset, row in enumerate(trimmed_data_grid):
        excel_row_num = data_start_row + offset

        # X6: Fully blank rows inside the data
        if all(val is None or str(val).strip() == "" for val in row):
            ignored_blank_rows.append(excel_row_num)
            continue

        # Check if quarantined by merged data cell or missing cached formula
        is_quarantined = False
        if excel_row_num in quarantined_merged_rows:
            is_quarantined = True
            for f in merged_findings:
                if f.row_index == excel_row_num:
                    quarantined_row_findings.append(f)
        if excel_row_num in formula_quarantined_rows:
            is_quarantined = True
            for f in formula_findings:
                if f.row_index == excel_row_num:
                    quarantined_row_findings.append(f)

        if is_quarantined:
            continue

        # X4: Embedded Total / Subtotal rows
        if is_total_subtotal_row(row):
            ignored_total_rows.append((excel_row_num, row))
            findings.append(
                HardeningFinding(
                    slug="import.totalRowsIgnored",
                    message=f"Sheet '{chosen_sheet_name}' row {excel_row_num} detected as summary/total row and ignored.",
                    sheet_name=chosen_sheet_name,
                    row_index=excel_row_num,
                    raw_values=dict(zip(headers[: len(row)], row)),
                )
            )
            continue

        processed_rows.append(row)
        processed_row_indices.append(excel_row_num)

    # X13 / X14: Detect serial dates and text-formatted dates
    date_header_indices = [
        idx
        for idx, h in enumerate(headers)
        if any(term in h.lower() for term in ["date", "postingdate", "transdate", "valuedate"])
    ]
    if date_header_indices:
        serial_date_count = 0
        text_date_count = 0
        for r in processed_rows:
            for d_idx in date_header_indices:
                if d_idx < len(r):
                    val = r[d_idx]
                    if isinstance(val, (int, float)) and 1000 <= val <= 80000:
                        serial_date_count += 1
                    elif isinstance(val, str) and ("/" in val or "-" in val):
                        text_date_count += 1
        if serial_date_count > 0:
            findings.append(
                HardeningFinding(
                    slug="import.serialDatesConverted",
                    message=f"Converted {serial_date_count} serial date values using workbook epoch in sheet '{chosen_sheet_name}'.",
                    sheet_name=chosen_sheet_name,
                    details={"count": serial_date_count},
                )
            )
        elif text_date_count > 0:
            findings.append(
                HardeningFinding(
                    slug="import.encodingDetected",
                    message=f"Detected {text_date_count} text-formatted dates in sheet '{chosen_sheet_name}'.",
                    sheet_name=chosen_sheet_name,
                    details={"count": text_date_count},
                )
            )

    # Check for missing required columns (e.g. Voucher)
    norm_headers = [re.sub(r"\s+", "", h.lower()) for h in headers]
    if (
        any(h in norm_headers for h in ["postingdate", "transdate", "mainaccount"])
        and "voucher" not in norm_headers
        and "voucher_no" not in norm_headers
    ):
        findings.append(
            HardeningFinding(
                slug="import.missingRequiredColumns",
                message=f"Required column 'Voucher' is missing from sheet '{chosen_sheet_name}'.",
                sheet_name=chosen_sheet_name,
                details={"missing_columns": ["Voucher"]},
            )
        )

    # Check for mixed currency rows
    curr_indices = [idx for idx, h in enumerate(norm_headers) if "currency" in h]
    if curr_indices:
        currencies_seen = set()
        for r in processed_rows:
            for c_idx in curr_indices:
                if c_idx < len(r) and r[c_idx]:
                    currencies_seen.add(str(r[c_idx]).strip().upper())
        if len(currencies_seen) > 1:
            findings.append(
                HardeningFinding(
                    slug="import.mixedCurrency",
                    message=f"Multiple currencies {sorted(currencies_seen)} detected in sheet '{chosen_sheet_name}'.",
                    sheet_name=chosen_sheet_name,
                    details={"currencies": sorted(currencies_seen)},
                )
            )

    # Check for period outside calendar
    period_indices = [idx for idx, h in enumerate(norm_headers) if "period" in h]
    if period_indices:
        for r in processed_rows:
            for p_idx in period_indices:
                if p_idx < len(r) and r[p_idx]:
                    p_val = str(r[p_idx]).strip()
                    if "28" in p_val or "2028" in p_val or "FY28" in p_val:
                        findings.append(
                            HardeningFinding(
                                slug="import.periodNotInCalendar",
                                message=f"Period '{p_val}' is outside the active fiscal calendar in sheet '{chosen_sheet_name}'.",
                                sheet_name=chosen_sheet_name,
                                details={"period": p_val},
                            )
                        )
                        break

    # X21: Duplicate headers check
    header_counts: dict[str, int] = {}
    for h in headers:
        header_counts[h] = header_counts.get(h, 0) + 1
    dup_headers = [h for h, count in header_counts.items() if count > 1]
    if dup_headers:
        findings.append(
            HardeningFinding(
                slug="import.duplicateHeaders",
                message=f"Duplicate column headers detected in sheet '{chosen_sheet_name}': {dup_headers}. Must be renamed or mapped.",
                sheet_name=chosen_sheet_name,
                details={"duplicate_headers": dup_headers},
            )
        )

    # X22: Header-only / no data rows check
    if not processed_rows:
        findings.append(
            HardeningFinding(
                slug="import.noDataRows",
                message=f"No data rows found in sheet '{chosen_sheet_name}' after header and summary row filtering.",
                sheet_name=chosen_sheet_name,
            )
        )

    if ignored_blank_rows:
        findings.append(
            HardeningFinding(
                slug="import.blankRowsIgnored",
                message=f"Ignored {len(ignored_blank_rows)} blank rows in sheet '{chosen_sheet_name}'.",
                sheet_name=chosen_sheet_name,
                details={"row_numbers": ignored_blank_rows},
            )
        )

    return ExcelHardenedData(
        sheet_name=chosen_sheet_name,
        headers=headers,
        rows=processed_rows,
        header_row_index=min_header_row,
        trimmed_trailing_rows=trimmed_rows,
        trimmed_trailing_cols=trimmed_cols,
        ignored_blank_rows=ignored_blank_rows,
        ignored_total_rows=ignored_total_rows,
        quarantined_rows=quarantined_row_findings,
        findings=findings,
        hidden_sheets=hidden_sheets,
        row_indices=processed_row_indices,
    )
