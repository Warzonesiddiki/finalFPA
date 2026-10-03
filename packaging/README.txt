================================================================================
FP&A MONTH-END COPILOT — README & FIRST-RUN GUIDE
================================================================================

Welcome to the FP&A Month-End Copilot. This desktop application assists finance teams
in performing monthly close analysis, variance checks, exception rule evaluations,
and financial pack issuance.

--------------------------------------------------------------------------------
1. First-Run & Data Storage Pointer
--------------------------------------------------------------------------------
- On first launch, the application initializes its local DuckDB database and
  working files directory in your user profile:
  `%LOCALAPPDATA%\FPAMonthEndCopilot`
- Ensure your data folder is stored on a local drive (do not run live databases
  directly inside synced folders like OneDrive or SharePoint to prevent file locking
  and database corruption).

--------------------------------------------------------------------------------
2. Portable Mode Note
--------------------------------------------------------------------------------
- To run in portable mode (e.g. from a USB drive or secure folder), launch the
  executable with the working directory set to a local writable path or use the
  portable package distribution archive.

--------------------------------------------------------------------------------
3. Advisory Disclaimer (Summary)
--------------------------------------------------------------------------------
"Potential exceptions only — advisory tool, not professional advice. Review by a
qualified accountant required. Figures may be revised."
(See EULA.txt for the full canonical advisory disclaimer per Doc 01 §15.1).
