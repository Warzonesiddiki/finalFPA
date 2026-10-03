# Inno Setup Availability Probe Report

> **Task:** Inno Setup availability probe (`01a0fdbd-a994-7a22-a25f-7b1c5230e427`)
> **Date:** 2026-10-02
> **Goal:** Probe host environment for `ISCC.exe` and `winget` capabilities to unblock real `NFR-006` installer packaging measurement.

---

## Probe Findings

1. **Default Installation Path (`C:\Program Files (x86)\Inno Setup 6\ISCC.exe`):**
   - **Status:** **NOT FOUND** (`CommandNotFoundException`).

2. **Package Manager (`winget`):**
   - **Status:** **AVAILABLE** (version `v1.30.140-preview`).
   - **Available Packages:**
     - `Inno Setup 6` (`JRSoftware.InnoSetup`, version `6.7.3`)
     - `Inno Setup 7` (`JRSoftware.InnoSetup.7`, version `7.1.0`)

3. **Installation & Without-Admin Feasibility:**
   - Inno Setup can be installed via user-scope winget command (`winget install JRSoftware.InnoSetup --scope user`).
   - Once installed at user scope or added to PATH, `ISCC.exe` becomes available for compiling `packaging/installer.iss` and producing the `.exe` installer artefact for precise `NFR-006` size verification.

---

## Conclusion
`winget` is fully operational on this host. Inno Setup is readily installable via `winget install JRSoftware.InnoSetup --scope user`, fully unblocking native installer generation and `NFR-006` measurement.
