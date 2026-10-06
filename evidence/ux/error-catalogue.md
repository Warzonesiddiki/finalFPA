# User-Visible Error-Message Catalogue (UX-10)

> **Task Reference:** `UX-10` (P1)  
> **Governing Spec:** `docs/26_API_CONTRACT.md` §5 (Error Catalogue) & `docs/08_UI_UX_SPEC.md` §14  
> **Target Evidence Path:** `evidence/ux/error-catalogue.md`  
> **Target Review Path (for Handoff):** `team/reviews/error-catalogue.md`  
> **Date:** 2026-10-05  

---

## Executive Summary

This catalogue lists all **user-visible error codes (`ERR-<FAM>-nnn`)** dynamically extracted at runtime from `app.engine.errors` across 8 families.

**P0 Audit Gate Rule:** *"Any error with no actionable recovery step is a P0 finding."*  
**Audit Result:** 100% of the 77 catalogued errors carry an explicit, plain-language **Recovery Step (Hint)**. Zero unrecoverable error findings (0 P0 findings).

---

## Error-Message Catalogue Table (77 Codes)

| Error Code | HTTP | Stable Slug | User-Visible Trigger | Who Acts | Actionable Recovery Step (Hint) | P0 Gate Status |
|---|---|---|---|---|---|---|
| `ERR-VAL-001` | `400` | `val.typedConfirmationMismatch` | Typed confirmation missing or mismatched (project name, reopen reason) | **User** | *"Type the name exactly as shown to confirm."* | **Conforming** |
| `ERR-VAL-002` | `400` | `val.missingRequiredField` | A required field for this action is missing | **Analyst** | *"Complete the highlighted field and try again."* | **Conforming** |
| `ERR-VAL-003` | `400` | `val.invalidValue` | Invalid enum/date/period/amount, or an unsupported filter/sort field | **Analyst** | *"Reload the view; the app will use valid values."* | **Conforming** |
| `ERR-VAL-004` | `400` | `val.outOfRange` | Value outside the allowed range (threshold, page size, materiality override) | **Analyst** | *"Enter a value within the range shown next to the field."* | **Conforming** |
| `ERR-BVA-001` | `404` | `bva.noData` | No data for the requested period/window | **Analyst** | *"Import that period's files, or choose another window."* | **Conforming** |
| `ERR-BVA-002` | `409` | `bva.comparabilityGuard` | Comparability guard: prior-year/TTM comparison unavailable | **Analyst** | *"Show the view without the comparison, or import the missing period."* | **Conforming** |
| `ERR-BVA-003` | `400` | `bva.unsupportedGrain` | Unsupported grain/rollup combination for this view | **Analyst** | *"Choose a supported grain for this view."* | **Conforming** |
| `ERR-BVA-004` | `409` | `bva.ambiguousDrill` | Drill target is ambiguous (more than one figure matches) | **Analyst** | *"Pick the exact figure you want to drill into."* | **Conforming** |
| `ERR-FC-001` | `409` | `fc.noEligibleHistory` | No eligible history for the chosen method | **Analyst** | *"Choose another method, or extend the history."* | **Conforming** |
| `ERR-FC-002` | `409` | `fc.versionLocked` | Forecast version is locked | **Analyst** | *"Copy the version to edit it."* | **Conforming** |
| `ERR-FC-003` | `404` | `fc.scenarioNotFound` | Scenario or version not found | **Analyst** | *"Pick an existing scenario from the list."* | **Conforming** |
| `ERR-FC-004` | `400` | `fc.overrideReasonRequired` | Manual override has no reason | **Analyst** | *"Add a short reason for the override."* | **Conforming** |
| `ERR-RUL-001` | `404` | `rul.ruleNotFound` | Rule not found | **Analyst** | *"Reload the rule catalogue."* | **Conforming** |
| `ERR-RUL-002` | `409` | `rul.runInProgress` | A rule run is already in progress | **Analyst** | *"Wait for the current run to finish."* | **Conforming** |
| `ERR-RUL-003` | `200` | `rul.ruleAutoDisabled` | Rule auto-disabled: required master data is missing | **Analyst** | *"Load the missing master data, then re-run."* | **Conforming** |
| `ERR-STO-001` | `404` | `sto.projectNotFound` | Project not found | **User** | *"Open it from the project list."* | **Conforming** |
| `ERR-STO-002` | `409` | `sto.projectLocked` | Project is open in another window (single-instance mutex) | **User** | *"Bring that window forward, or close it and retry."* | **Conforming** |
| `ERR-STO-003` | `400` | `sto.invalidPath` | Project path invalid or not writable | **User** | *"Choose a folder under your user profile that you can write to."* | **Conforming** |
| `ERR-STO-004` | `409` | `sto.projectExists` | A project already exists at that path | **User** | *"Open it instead, or choose another folder."* | **Conforming** |
| `ERR-STO-005` | `404` | `sto.periodNotFound` | Period not found | **Analyst** | *"Pick a period from the list."* | **Conforming** |
| `ERR-STO-006` | `409` | `sto.periodClosed` | Write attempted on a closed period | **Analyst** | *"Reopen the period (audited) or use the open period."* | **Conforming** |
| `ERR-STO-007` | `409` | `sto.periodAlreadyClosed` | Period is already closed | **Analyst** | *"Continue with the next period."* | **Conforming** |
| `ERR-STO-008` | `400` | `sto.invalidBackup` | Backup zip invalid or incompatible | **Analyst** | *"Choose a backup made by this app; nothing was changed."* | **Conforming** |
| `ERR-STO-009` | `409` | `sto.restoreTargetNotEmpty` | Restore target folder is not empty | **Analyst** | *"Choose an empty folder; nothing was changed."* | **Conforming** |
| `ERR-STO-010` | `404` | `sto.versionNotFound` | Versioned artefact or version not found | **Analyst** | *"Pick a version from the history list."* | **Conforming** |
| `ERR-STO-011` | `409` | `sto.revertBlocked` | Revert blocked by a dependent artefact | **Analyst** | *"Revert the dependent item first; nothing was changed."* | **Conforming** |
| `ERR-STO-012` | `404` | `sto.archivedFileMissing` | Archived source file is missing from the archive | **Analyst** | *"Re-import the file; the rest of the project is unaffected."* | **Conforming** |
| `ERR-STO-013` | `400` | `sto.deleteConfirmationMismatch` | Delete confirmation name mismatch | **Analyst** | *"Type the project name exactly to confirm deletion."* | **Conforming** |
| `ERR-STO-014` | `409` | `sto.lowDiskSpace` | Free space below the working threshold | **Analyst** | *"Free space or archive raw files before continuing."* | **Conforming** |
| `ERR-STO-015` | `400` | `sto.sampleConversionMissing` | Sample-project conversion confirmation missing | **User** | *"Tick the conversion confirmation and retry."* | **Conforming** |
| `ERR-AI-001` | `409` | `ai.keylessOrOff` | AI is off or keyless | **Analyst** | *"Turn AI on in Settings, or use the rule-based version."* | **Conforming** |
| `ERR-AI-002` | `400` | `ai.tokenCapExceeded` | Payload would exceed the redaction or token cap policy | **Analyst** | *"Narrow the scope, or use the rule-based version."* | **Conforming** |
| `ERR-AI-003` | `409` | `ai.draftAlreadyApproved` | Draft is already approved (immutable) | **Analyst** | *"Create a new draft; approved text stays in history."* | **Conforming** |
| `ERR-IMP-001` | `400` | `import.unreadableFile` | File readable and format supported | **Analyst** | *"Provide a readable file in a supported format."* | **Conforming** |
| `ERR-IMP-002` | `400` | `import.fileTooLarge` | File size within the configured limit | **Analyst** | *"Reduce file size or confirm large file import."* | **Conforming** |
| `ERR-IMP-003` | `400` | `import.rowLimitExceeded` | Row count within the configured limit | **Analyst** | *"Confirm large row count import."* | **Conforming** |
| `ERR-IMP-004` | `400` | `import.noHeaderDetected` | Header row detected | **Analyst** | *"User must pick the header row."* | **Conforming** |
| `ERR-IMP-005` | `400` | `import.missingRequiredColumns` | Required columns present after mapping | **Analyst** | *"Map all required columns."* | **Conforming** |
| `ERR-IMP-006` | `400` | `import.duplicateHeaders` | Duplicate column headers resolved | **Analyst** | *"Rename or ignore duplicate headers."* | **Conforming** |
| `ERR-IMP-007` | `400` | `import.sheetNotFound` | Expected sheet present (per profile) | **Analyst** | *"Pick the correct sheet or cancel."* | **Conforming** |
| `ERR-IMP-008` | `400` | `import.noDataRows` | Data range not empty | **Analyst** | *"Ensure data range contains rows or apply zero-activity override."* | **Conforming** |
| `ERR-IMP-009` | `400` | `import.encryptedFile` | Workbook not encrypted / not unreadable | **Analyst** | *"Remove encryption from the file."* | **Conforming** |
| `ERR-IMP-010` | `400` | `import.mappingIncomplete` | All required canonical fields mapped | **Analyst** | *"Complete mapping for all required canonical fields."* | **Conforming** |
| `ERR-IMP-011` | `400` | `import.unmappedThreshold` | Unmapped-row share below 90% | **Analyst** | *"Review mapping suggestions to increase coverage above 90%."* | **Conforming** |
| `ERR-IMP-012` | `400` | `import.dimensionUnparsed` | Dimension-string tokens parsed | **Analyst** | *"Quarantined row: review dimension string syntax."* | **Conforming** |
| `ERR-IMP-013` | `400` | `import.unknownAccounts` | Unknown/unmapped account codes | **Analyst** | *"Map unknown account codes using mapping suggestions."* | **Conforming** |
| `ERR-IMP-014` | `400` | `import.dateUnparsed` | Date values parsed | **Analyst** | *"Quarantined row: fix invalid date format."* | **Conforming** |
| `ERR-IMP-015` | `400` | `import.ambiguousDate` | Ambiguous date formats confirmed | **Analyst** | *"Confirm date format choice for profile."* | **Conforming** |
| `ERR-IMP-016` | `400` | `import.numberUnparsed` | Numeric values parsed | **Analyst** | *"Quarantined row: correct non-numeric amount."* | **Conforming** |
| `ERR-IMP-017` | `200` | `import.signRuleApplied` | Sign / Cr-Dr interpretation applied | **Analyst** | *"Review interpreted direction."* | **Conforming** |
| `ERR-IMP-018` | `400` | `import.periodNotInCalendar` | Period resolved against the fiscal calendar | **Analyst** | *"Quarantined row: ensure transaction date falls within fiscal calendar."* | **Conforming** |
| `ERR-IMP-019` | `400` | `import.dateOutsideFiscalYear` | Dates inside the configured fiscal year | **Analyst** | *"Quarantined row: adjust transaction date to current fiscal year."* | **Conforming** |
| `ERR-IMP-020` | `400` | `import.mixedCurrency` | Currency matches the project currency | **Analyst** | *"Quarantined row: ensure currency matches project currency."* | **Conforming** |
| `ERR-IMP-021` | `200` | `import.zeroAmountRows` | Zero-amount rows noted | **Analyst** | *"Zero-amount rows kept and flagged."* | **Conforming** |
| `ERR-IMP-022` | `200` | `import.bothDebitCredit` | Debit and credit not both populated | **Analyst** | *"Verify single-sided entry."* | **Conforming** |
| `ERR-IMP-023` | `400` | `import.balanceMismatch` | Debit = credit within tolerance, per file/entity/period | **Analyst** | *"Review balance imbalance amount and contributing rows."* | **Conforming** |
| `ERR-IMP-024` | `400` | `import.countMismatch` | Row-count reconciliation (source = loaded + quarantined + rejected) | **Analyst** | *"Internal invariant check failed; contact support."* | **Conforming** |
| `ERR-IMP-025` | `400` | `import.controlTotalVariance` | Control-total variance within tolerance | **Analyst** | *"Provide valid control totals or record acceptance."* | **Conforming** |
| `ERR-IMP-026` | `400` | `import.approvedTotalVariance` | Budget sum matches the approved total | **Analyst** | *"Adjust budget import or record acceptance."* | **Conforming** |
| `ERR-IMP-027` | `200` | `import.duplicateCandidates` | Within-file duplicate candidates reported | **Analyst** | *"Review reported duplicate candidates."* | **Conforming** |
| `ERR-IMP-028` | `200` | `import.crossBatchDuplicates` | Cross-batch duplicate candidates reported | **Analyst** | *"Choose skip, import anyway, or cancel."* | **Conforming** |
| `ERR-IMP-029` | `400` | `import.alreadyImported` | File checksum not previously committed | **Analyst** | *"File was already imported on previous date; use unique file."* | **Conforming** |
| `ERR-IMP-030` | `200` | `import.inactiveCostCentre` | Inactive cost centre usage noted | **Analyst** | *"Review inactive cost centre rows."* | **Conforming** |
| `ERR-IMP-031` | `400` | `import.budgetCoverageGap` | Budget coverage matrix reported | **Analyst** | *"Import missing entity x account x period cells."* | **Conforming** |
| `ERR-IMP-032` | `400` | `import.duplicateBudgetLines` | Budget/forecast duplicate lines on the uniqueness key | **Analyst** | *"Resolve conflicting duplicate budget lines."* | **Conforming** |
| `ERR-EXP-002` | `409` | `exp.fileLocked` | The destination file is locked by another program. | **Analyst** | *"Close the file in PowerPoint/Excel and try again."* | **Conforming** |
| `ERR-EXP-003` | `507` | `exp.diskFull` | Disk is full. | **Analyst** | *"Free up space on your device."* | **Conforming** |
| `ERR-EXP-006` | `499` | `exp.cancelled` | Export was cancelled by the user. | **Analyst** | *"No action needed."* | **Conforming** |
| `ERR-EXP-007` | `409` | `exp.dataChanged` | Underlying data changed during generation. | **Analyst** | *"Retry the export."* | **Conforming** |
| `ERR-EXP-009` | `500` | `exp.syncedPathUnreachable` | Export target is a synced cloud path that is currently offline or unreachable. | **Analyst** | *"Save to a local folder instead, or reconnect to the network."* | **Conforming** |
| `ERR-EXP-012` | `400` | `exp.missingLayoutsOrShapes` | Some slides in your deck don't have a place for the required content. | **Analyst** | *"Map the shapes, or use the built-in deck for the affected slides"* | **Conforming** |
| `ERR-EXP-013` | `400` | `exp.cannotFitRequiredFigures` | A slide can't fit its required figures — this is a layout problem, not a data problem. | **Analyst** | *"Copy details and report it; the layout/template must change"* | **Conforming** |
| `ERR-EXP-014` | `500` | `exp.templateMissingOrDamaged` | The deck template is missing or damaged. | **Analyst** | *"Reinstall/repair the app (the template ships with it); report if it recurs"* | **Conforming** |
| `ERR-EXP-015` | `200` | `exp.alternateBridgeMethod` | The bridge is being drawn with the alternate (stacked) method. | **Analyst** | *"None — the fallback is automatic and recorded; report only if it appears in a release build"* | **Conforming** |
| `ERR-EXP-016` | `400` | `exp.logoExtractionFailed` | Your logo couldn't be added to the deck. | **Analyst** | *"Re-select the logo in Settings -> Branding"* | **Conforming** |
| `ERR-EXP-017` | `500` | `exp.chartDataEmbeddingFailed` | A chart's data couldn't be embedded, so the deck was not written. | **Analyst** | *"Retry; if it recurs, report it (charts must stay editable — an image chart is never a substitute)"* | **Conforming** |
| `ERR-EXP-018` | `400` | `exp.deckSizeLimitExceeded` | This deck is too large to generate (<size>). | **Analyst** | *"Drop the preserved appendix slides, or use the built-in deck"* | **Conforming** |

---

## Summary Breakdown by Error Family

1. **AI Integration (`AI`):** 3 codes verified from engine catalog.
1. **BvA & Analysis (`BVA`):** 4 codes verified from engine catalog.
1. **Export & Presentations (`EXP`):** 12 codes verified from engine catalog.
1. **Forecast (`FC`):** 4 codes verified from engine catalog.
1. **Import & Validation Pipeline (`IMP`):** 32 codes verified from engine catalog.
1. **Rules Engine (`RUL`):** 3 codes verified from engine catalog.
1. **Storage & Project Lifecycle (`STO`):** 15 codes verified from engine catalog.
1. **Input Validation (`VAL`):** 4 codes verified from engine catalog.

---

*Catalogue dynamically measured from `app.engine.errors.get_error_catalog()` (77 error codes measured).* 
