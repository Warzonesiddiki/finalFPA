> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** build → installer → clean-Windows-11 validation, installer contract (per-user, no
> admin), first-run experience, uninstall and data-lifecycle semantics, the SmartScreen/Defender reality and
> the signing ladder (`ADR-003`), the portable-zip option, version metadata, and the support
> "export diagnostics" flow (`FR-XC-004`/`005`, `FR-XC-014`); Addon 1 §G (Windows hardening), §J
> (delivery/upgrade), Addon 2 §B.6 (`scripts/build`/`release`)
> **TL;DR (≤ 15 lines):**
> - **Self-contained installer:** Single Inno Setup installer bundling Python engine, React UI, and binaries with zero user prerequisites.
> - **Zero admin rights:** Installs per-user to %LOCALAPPDATA%; completely isolated from system-wide Python or runtime dependencies.
> - **Portable fallback:** Standalone zip package with portable.flag for restricted corporate environments without installation rights.
> - **SmartScreen mitigation:** Documented hash publication and step-by-step walkthrough for unsigned v1 executable launching.
> - **Clean-VM verification:** 24-step repeatable verification protocol executed on vanilla Windows 11 prior to release sign-off.

# 15 — Packaging & Deployment Runbook

## 1. Purpose, ownership and the release artefacts

### 1.1 What this document owns

| Fact | Owner |
|---|---|
| Build → installer → clean-Windows-11 validation steps, first-run UX, uninstall, SmartScreen/code-signing notes, support diagnostics flow | **`15` (this document)** |
| Semver, tags, the release checklist, upgrade/migration process, distribution and publication | `24` |
| Packaging ADRs (`ADR-003`, `ADR-005`), `scripts/*`, storage layout, migrations | `09` |
| Diagnostics-bundle contents and redaction | `13` §7 |
| The app's first-run screens and copy | `08` |
| What the client is told about installing | `22`, `23`, `29` |

### 1.2 The four artefacts of a release

| Artefact | Name | Purpose |
|---|---|---|
| Installer | `Setup-FPandAMonthEndCopilot-<version>.exe` | The primary delivery: double-click → works (Inno Setup, per-user) |
| Portable package | `FPandAMonthEndCopilot-<version>-portable.zip` | No-install variant for locked-down machines and demos |
| Checksums | `SHA256SUMS-<version>.txt` | Published with the artefacts; verified by the client before running (`Addon 1 §J`) |
| Supply-chain set | `THIRD_PARTY_LICENSES.txt`, `sbom/py-<version>.txt` (`SEC-029`, `SEC-047`) | Licence compliance and the per-release dependency snapshot |

Everything above is produced by `scripts/build` and listed by `scripts/release` (`09` §15.4). Nothing else
is shipped: no installer script fragments, no build logs, no test fixtures, no `sample-data/` generator or
malformed corpus; the only sample content is the bundled synthetic sample project, watermarked and flagged
(`FR-ONB-008`, `Addon 4 §H` sample-data integrity). No client file ever enters the payload (`SEC-007`), and deliverables produced
from a sample project carry the watermark onward (`FR-XC-013`).

## 2. Build environment and version stamping

### 2.1 The build host

| Requirement | Rule |
|---|---|
| OS | Windows 11 x64 (the artefact targets Windows; a Windows build host removes a whole class of "works on my machine" risk) |
| Toolchain | Python from `.python-version`, Node LTS from `.nvmrc`, `uv` for Python deps, `npm ci` for UI deps — all from lockfiles (`ADR-002`) |
| Inno Setup | Pinned major version recorded in `packaging/README` and in the release notes; the compiler path is discovered, never hard-coded per machine |
| Clean checkout | `scripts/build` must succeed from a fresh `git clone` with no machine-local steps (`Addon 4 §I.2`); secrets are never needed to build |
| Deterministic inputs | Lockfiles + `packaging/pyinstaller.spec` + `packaging/installer.iss` are the only build inputs that matter; the build records their hashes into the release notes |
| No client data | Nothing from a client project may exist on the build host; fixtures are synthetic (`SEC-007`) |

### 2.2 Version stamping (single source of truth)

| Place | Value | Written by |
|---|---|---|
| `pyproject.toml` `version` | `MAJOR.MINOR.PATCH` (semver) | `scripts/release` (bump) |
| `app/__init__.py` `__version__` | Read from the package metadata — never duplicated by hand | build |
| Windows file version (`packaging/version_info.txt`) | Same version + product name + company | `scripts/build` generates it |
| Inno `AppVersion` | Same version | `scripts/build` passes it via `/DMyAppVersion=` |
| UI build | `VITE_APP_VERSION` + build date injected at build time, shown in About (`FR-XC-004`) | `npm run build` step |
| Schema version | Integer in `SchemaMetadata`, stored inside every project (`09` §13) | migrations, not the build |
| Release notes | `CHANGELOG.md` + `packaging/out/<version>/release-notes.md` | `scripts/release` |

**Rule:** a version string is never typed twice. A mismatch between the installer's file version, the About
screen and the artefact name fails `scripts/release` and the release checklist (`24`).

### 2.3 Repository/packaging layout

```
packaging/
  pyinstaller.spec          # onedir, hidden imports, excludes, version info, icon
  installer.iss             # Inno Setup script (per-user, shortcuts, uninstall entry)
  icons/                    # app icon (.ico) at the required sizes
  templates/                # FPAMonthEndCopilot_v1.pptx, input .xlsx templates (built assets)
  version_info.txt          # generated
  out/<version>/            # artefacts, checksums, SBOM, release notes (not committed)
```

`packaging/out/` is git-ignored; artefacts are attached to a release, never committed (`27`/`24` rules).

## 3. The build (`scripts/build`)

### 3.1 Preconditions (fail fast, in this order)

| # | Check | Failure message |
|---|---|---|
| 1 | Clean working tree (no uncommitted changes) unless `--dev` is passed | "The repository has uncommitted changes — commit or use `--dev`." |
| 2 | `scripts/check` green (the full form, coverage included) | The check transcript is printed and the build stops |
| 3 | Version resolvable and semver-valid | "Version '<x>' is not semver." |
| 4 | Required assets present (`packaging/icons/app.ico`, `packaging/templates/*.pptx`, `ui/dist` buildable) | Names the missing asset |
| 5 | Inno Setup compiler found (or `--skip-installer`) | "Inno Setup not found — install it or pass `--skip-installer`." |

### 3.2 Steps

| Step | Action | Output |
|---|---|---|
| 1 | `npm ci` → `npm run build` (Vite, production) with the version injected | `ui/dist/` |
| 2 | Copy `ui/dist/` into the API's static-asset location (`ADR-009`) | `app/static/` (build-time only, not committed) |
| 3 | PyInstaller `onedir` with `packaging/pyinstaller.spec` | `dist/FPandAMonthEndCopilot/` |
| 4 | Stage the payload beside the exe: `templates/` (deck + input `.xlsx`), `THIRD_PARTY_LICENSES.txt` (Python **and** UI dependencies), `README.txt` (first-run pointer, portable-mode note), the EULA/disclaimer text | payload complete |
| 5 | **Payload audit** (automated): required files present; no `tests/`, no `docs/`, no `sample-data/generator`, no `.env`, no `.py` sources of client code beyond what PyInstaller needs, no key material (`SEC-031`) | audit report |
| 6 | Inno Setup compile with `/DMyAppVersion=<version>` | `packaging/out/<version>/Setup-FPandAMonthEndCopilot-<version>.exe` |
| 7 | Build the portable zip from the same payload directory (with `portable.flag` documentation inside) | `…-portable.zip` |
| 8 | Compute SHA-256 of both artefacts; write `SHA256SUMS-<version>.txt`; attach the SBOM snapshot (`pip freeze` of the frozen environment) | checksums + SBOM |
| 9 | **Smoke test on the build host** (install → launch → sample project → generate one pack → uninstall) | smoke transcript |
| 10 | Size and time report: installer size vs `NFR-006`, build duration, payload breakdown by component | build report |

### 3.3 Size budget (`NFR-006` ≤ 500 MB)

| Component | Expected share | How it is controlled |
|---|---|---|
| Python runtime + stdlib | large, unavoidable | `onedir` (no per-launch unpack), `--exclude-module` for unused scientific stacks |
| DuckDB, Polars, openpyxl, python-pptx, FastAPI, httpx | the real payload | Pinned versions; no duplicate wheels; no test-only deps |
| UI bundle | modest | Vite production build, no source maps in the package |
| Templates, icons, licences | small | Compressed |
| **Not shipped** | — | `tests/`, `docs/`, dev tooling, type stubs, `pip`/`uv` caches, `.pyi`, sample generators, matplotlib/OpenCV-scale packages (explicit excludes) |

The CI/gate records the installer size; crossing 500 MB fails `NFR-006` and the release checklist.

### 3.4 Excludes are auditable, not folklore

`packaging/pyinstaller.spec`'s `excludes` list carries a comment per entry naming what pulled the module in
and why it is safe to drop. An unexplained exclude is a review failure (`15` §1.2's "nothing else ships"
rule). The payload audit (step 5) is the backstop: it fails on a module that reappears through a hidden
import.

## 4. The installer contract (Inno Setup)

### 4.1 Install behaviour

| Aspect | Rule |
|---|---|
| Privileges | **Per-user install, no admin** (`PrivilegesRequired=lowest`) — `Addon 1 §G.2`. An all-users install is an explicit, documented exception for IT (`--all-users` build flavour) and is not the default artefact |
| Install location | `%LOCALAPPDATA%\Programs\FP&A Month-End Copilot\` (the Windows per-user convention). **Never** `%LOCALAPPDATA%\FP&A Month-End Copilot\`, which is the *data* directory (`ADR-004`) — the two must not collide |
| Data location | Untouched by the installer; created by the app on first run (`09` §7.1) |
| Components | App (required) · sample project (default on, removable) · desktop shortcut (opt-out) · Start-menu folder (default on) · EULA/disclaimer page (required acceptance) |
| Prerequisite | None. WebView2 is present on Windows 11; the installer **detects** it and shows the documented fallback path if absent (default browser, `ADR-001`) — it never downloads or bundles a runtime |
| Registry | Only the minimal uninstall entry under `HKCU`. No file associations (the app never claims `.xlsx`/`.pptx`), no services, no scheduled tasks, no firewall rules, no drivers |
| Shortcuts | Start menu: app, user guide (`22` as a PDF/HTML shipped in the payload), "Open data folder", uninstall |
| Silent/IT flags | `/S` (silent), `/D=` (directory), `/LOG=` (log file), `/NORESTART`; documented in `23` for the client's IT |
| Rollback of a failed install | Inno's standard rollback removes partial program files; the log path is shown in the failure dialog |
| Version metadata | Product name, version, publisher string (`FP&A Month-End Copilot`, unsigned in v1), copyright from `01` §16 |
| Uninstall entry | "FP&A Month-End Copilot <version>" in Apps & features, with the app icon |

### 4.2 What the installer must never do

1. Write outside its own install directory and `HKCU` (no `ProgramData`, no system folders, no PATH changes).
2. Touch, move or delete anything under the data directory.
3. Require or request elevation, or silently request it on first run.
4. Download anything (no web bootstrap, no prerequisite download).
5. Install a background process, a service, an updater or a browser extension.
6. Delete or overwrite an existing project, backup or export.
7. Present a dialog a non-technical user cannot answer ("OK/Cancel" on an internal error is not a message
   — `08` §16 applies to installer copy too).

### 4.3 The portable package (documented fallback)

| Aspect | Rule |
|---|---|
| Contents | The same payload as the installer's program files, with a `README.txt` that states exactly what portable mode does and does not do |
| Default data location | Still `%LOCALAPPDATA%\FP&A Month-End Copilot\` — **portable means "no install", not "no trace"** |
| True self-contained mode (opt-in) | A `portable.flag` file beside the executable moves data to `<app>\data\`; the app then shows a persistent banner warning that the folder travels with the app and must not sit in a synced folder (`ADR-004`) |
| No registry | Portable mode writes nothing to the registry |
| Updates | Replace the folder; the schema migrates forward on first open (`ADR-008`) with the mandatory backup |
| Limitations | Stated in the README: no Start-menu/uninstall entry, no file-version metadata in Explorer, and the synced-folder warning applies |

## 5. Clean-Windows-11 validation protocol (the gate evidence)

Every gate releases only with this protocol executed on a **real Windows 11 machine or VM** and recorded
(`ADR-005`, `Addon 1 §G.6`). The transcript is the answer to `GATE-01-06`; `TST-WIN-*` and `TST-E2E-08`
are its automated halves.

### 5.1 The machine and the artefacts

| Item | Requirement |
|---|---|
| OS | Clean Windows 11 (23H2 or later), fully patched, **Defender on**, no dev tools, no Python/Node installed |
| User | A standard (non-admin) local account — this is what the client's analyst actually is |
| Display | 1366×768 minimum; the scaling matrix (`NFR-013`) is part of the run |
| Artefacts | The exact files to be delivered: installer, portable zip, `SHA256SUMS-<version>.txt`, release notes |
| Channel | The same mechanism the client will use (secure link), not a developer share |
| Baseline | A VM snapshot before the run, so the run is repeatable |

### 5.2 The 24-step script

**Phase A — preparation (steps 1–5)**

| # | Action | Expected result | Evidence |
|---|---|---|---|
| 1 | Snapshot and record the VM: OS build, patch level, Defender state, user type, resolution/scaling | Values recorded in the checklist header | Checklist header |
| 2 | Download the artefacts through the delivery channel | Files arrive intact | Screenshot |
| 3 | Verify SHA-256 of installer and portable zip against `SHA256SUMS-<version>.txt` | Hashes match exactly | Terminal/Explorer screenshot |
| 4 | Open file properties | Product name, version and company correct; Signature shows **unsigned** as documented (`ADR-003`) | Properties screenshot |
| 5 | Snapshot the filesystem and registry state (for the leftover audit in step 24) | Baseline captured | `reg export`/tree listing |

**Phase B — install (steps 6–11)**

| # | Action | Expected result | Evidence |
|---|---|---|---|
| 6 | Run the installer as the standard user | **No UAC prompt**; no elevation request | Screenshot + checklist |
| 7 | Walk the SmartScreen path if presented (fresh machine, unsigned artefact) | The §8.3 walkthrough matches reality exactly (no extra or different dialog) | Screenshots of every dialog |
| 8 | EULA/disclaimer page | Text matches `01` §15.1; it cannot be skipped; declining exits cleanly | Screenshot |
| 9 | Install with default options; record duration and install path | `< 2 min` typical; path `%LOCALAPPDATA%\Programs\FP&A Month-End Copilot\`; no admin | Checklist |
| 10 | Inspect the program directory and the data directory | Program files present incl. `THIRD_PARTY_LICENSES.txt`, `templates\`, `README.txt`; the **data directory is not created by the installer** | Explorer screenshot |
| 11 | Check Start menu, desktop shortcut (if accepted) and Apps & features | Entries correct, version shown, uninstall available | Screenshots |

**Phase C — first run and function (steps 12–19)**

| # | Action | Expected result | Evidence |
|---|---|---|---|
| 12 | Launch the app; measure cold start to the interactive Home | ≤ 10 s (`NFR-001`); WebView2 path used; no console window | Timing + screenshot |
| 13 | Watch the network while the app starts, the sample project loads and the tour runs | **Zero outbound connections** (`NFR-008`, `SEC-001`/`002`) | Packet capture or resource-monitor screenshot |
| 14 | Complete the first-run wizard; confirm AI is off and no key is requested | Sample project open; keyless mode; guidance visible | Screenshots |
| 15 | Function sweep: import a malformed corpus file, then the good GL file; run rules; open an exception; refresh the forecast; generate the Excel pack and the deck; open both in Office | Every step works; the malformed file produces its documented message (`14` §6.3); Office opens both files with no repair prompt; files contain the sample watermark | Screenshots + the two artefacts |
| 16 | Export diagnostics (default settings) | Preview lists contents; bundle ≤ 20 MB; contains no amounts/vendor names (`SEC-016`); manifest hashes present | Bundle inspection |
| 17 | Edit a comment, change a threshold, then close and reopen the app | Session state persists; the recent project is listed; the stale-data banner appears after the threshold change and clears after a re-run | Screenshots |
| 18 | Open the storage screen and compare with Explorer; run `doctor` | Numbers within 5 %; `doctor --json` reports healthy | Screenshots / JSON |
| 19 | Environment checks: second instance (friendly message), sleep/standby mid-import (clean recovery), 150 % scaling, 1366×768 layout, export to a OneDrive path (warning) | Each behaves as specified (`TST-WIN-02/04/05/06`) | Screenshots |

**Phase D — upgrade (step 20)**

| # | Action | Expected result | Evidence |
|---|---|---|---|
| 20 | With a project created and data present, install the **next** version over the top (after first installing the previous version, or by restoring a prior-version snapshot) | Install-over succeeds without uninstalling; first open prompts the **mandatory backup** (`ADR-008`); migration runs; numbers and workflow state are unchanged (hash-compared before/after); About shows the new version and the migrated schema version | Before/after hashes + screenshots |

**Phase E — lifecycle and leftovers (steps 21–24)**

| # | Action | Expected result | Evidence |
|---|---|---|---|
| 21 | Uninstall via Apps & features as the standard user | No UAC; program files removed; shortcuts removed; **no prompt about data**; user data untouched | Screenshots + Explorer |
| 22 | Reinstall and launch | Existing projects still listed and open normally | Screenshot |
| 23 | Uninstall again, this time ticking *"Also delete my project data"* and completing the typed confirmation | Data directory removed; the dialog states exactly what is deleted; a pre-delete backup offer appeared | Screenshots |
| 24 | Leftover audit against the step-5 baseline | No files outside the user profile; no services, scheduled tasks, drivers or firewall rules; registry difference limited to the uninstall entry that was itself removed | Diff report |

### 5.3 Evidence and failure rules

**Variations.** Four checks run in the same session but are not part of the 24 numbered steps, because
they need extra setup: **V1** a project and an export in a long Unicode path (a Devanagari client-name
folder, `TST-WIN-03`); **V2** a locked export target — the file open in Excel, plus a simulated antivirus
hold (`TST-WIN-07`); **V3** kill the process from Task Manager mid-import and mid-export, then relaunch
(`TST-WIN-09`); **V4** change the Windows timezone and locale, reopen the project, and compare a KPI and the
period label (`TST-WIN-13`).

**Coverage of the Windows suite.** Every `TST-WIN-*` test maps to this protocol:

| Test | Covered by |
|---|---|
| `TST-WIN-01` | Steps 6–11, 21–24 |
| `TST-WIN-02` | Step 19 (plus the 100/125/150 % scaling matrix) |
| `TST-WIN-03` | V1 |
| `TST-WIN-04` | Step 19 (sleep/standby mid-import) |
| `TST-WIN-05` | Step 19 (second instance) |
| `TST-WIN-06` | Step 19 (export to a OneDrive path) |
| `TST-WIN-07` | V2 |
| `TST-WIN-08` | Steps 3, 4, 7 |
| `TST-WIN-09` | V3 |
| `TST-WIN-10` | Step 15 (Office opens both artefacts) |
| `TST-WIN-11` | Step 12 (plus the WebView2-absent path, §6.3) |
| `TST-WIN-12` | Step 18 |
| `TST-WIN-13` | V4 |
| `TST-WIN-14` | Steps 13–15 (fresh machine, network off, no key) |


| Rule | Detail |
|---|---|
| Format | The filled checklist (Markdown or PDF) + screenshots + hash outputs + the diff report, attached to the gate and referenced in `CHANGELOG`/`SESSION_LOG` |
| Sign-off | Whoever ran it signs and dates it; the checklist names the VM build and the artefact hashes |
| Failure | Any unexpected result **blocks the gate**; the fix gets a test (`14`) and the run is repeated from step 1 |
| Known issues | A deferred defect needs a `27` backlog ID and must be visible to the user (a documented limitation, never a silent one) |
| Re-run trigger | Any change to the installer, the payload, a dependency, the version, or the OS baseline invalidates the previous run |
| Frequency | Every phase gate, every release candidate, and after any packaging-affecting change (`24`) |

## 6. First-run experience (installer → first useful screen)

### 6.1 The sequence

| # | Stage | What happens | Failure path |
|---|---|---|---|
| 1 | Launch | No console window, no splash longer than a moment; the app window appears and is keyboard-usable | WebView2 missing → the documented default-browser fallback with the "how to install WebView2" hint (`ERR-ENG-001`) |
| 2 | Environment check | Data directory created/validated; permissions checked; disk space checked; a synced path is recognised | Not writable → `ERR-ENG-002`; low disk → `ERR-ENG-003` with the free-space number |
| 3 | Project choice (`SCR-003`) | First run offers **"Open the sample project"** (recommended) or "Create a project" or "Open a project"; the sample loads immediately and is visibly watermarked | Corrupt/missing sample → rebuild the seed and offer *Settings → Restore sample project*; never a blank app (`FR-ONB-001`) |
| 4 | Guided tour (`SCR-043`, six steps) | Skippable, restartable, pointing at Home → Import → BvA → Exceptions → Pack | — |
| 5 | Orientation | A one-line state of play: no project data yet, what to do next ("Start <month> close"), where help lives | — |
| 6 | AI notice | A single line stating AI is **off** and optional, with the Settings link — no key prompt, no nag | — |
| 7 | Assurance | The advisory disclaimer is present (About) and the EULA was accepted at install; the storage location is shown with a reveal action | — |

### 6.2 First-run rules

1. **No network at any point** (`NFR-008`); the update check exists only as a manual action (`FR-XC-015`).
2. **No empty dead ends**: every empty screen offers the sample project, a template download, or the
   next step (`08` §17 state matrix).
3. **Timing:** cold start ≤ 10 s on the reference machine; the first-run wizard adds ≤ 2 s and is skippable.
4. **No key, no account, no email** — nothing to sign up for.
5. **Nothing is written outside** the data directory, the app's own folders and the user's chosen export
   location.
6. A crash during first run leaves a recoverable state: the next launch resumes the wizard (`FR-XC-008`).

### 6.3 Closely related failure modes

| Condition | Behaviour | Code |
|---|---|---|
| WebView2 absent | Offer the documented fallback (open the built UI in the default browser against the local API) + a help link | `ERR-ENG-001` |
| Data directory not writable | Explain, offer "choose another folder" or a per-user fix; never proceed silently | `ERR-ENG-002` |
| Disk full / below threshold | Name the free space and the requirement; block writes that would lose data | `ERR-ENG-003` |
| Data directory on a synced path | Block by default with the recorded-override path (`09` §7.2) | `ERR-SEC-007` |
| A second instance holds the project | Friendly "already open in another window" with a bring-to-front action | `ERR-ENG-008` |
| Project schema newer than the app | Refuse to open, explain, link to the newer version; never a silent downgrade | `ERR-ENG-005` |
| Antivirus/Defender holds a file | Retry offer, then the locked-file message (`ERR-EXP-002` family) | — |
| Interrupted upgrade | The pre-migration backup is retained; the message names the backup path and the next action | `ERR-ENG-004` |

## 7. Uninstall, repair and the data lifecycle

### 7.1 What uninstall does

| Item | Default behaviour |
|---|---|
| Program files (`%LOCALAPPDATA%\Programs\FP&A Month-End Copilot\`) | Removed |
| Shortcuts, Start-menu folder, Apps & features entry | Removed |
| Registry | The uninstall entry and the app's `HKCU` keys are removed; nothing else is touched |
| **Project data** (`%LOCALAPPDATA%\FP&A Month-End Copilot\`) | **Retained**; the uninstaller states where it is |
| Machine settings and the AI key (`%APPDATA%\FP&A Month-End Copilot\`, DPAPI blob) | **Retained** (the key is unreadable by any other user; it can be removed from Settings first if the user prefers) |
| A checkbox *"Also delete my project data (cannot be undone)"* | **Unchecked by default**; ticking it requires the typed project-name confirmation for each project, and shows total size and paths before deleting (`FR-PRJ-012` semantics) |
| Backups the user created elsewhere and exported packs | Never touched |

### 7.2 Repair, reinstall and portability

| Situation | Guidance |
|---|---|
| Reinstall over the same version | Repairs/refreshes program files; data untouched |
| Clean reinstall | Uninstall → install; data survives; the app reopens existing projects after migration (`ADR-008`) |
| Move a project to another machine | Copy the project folder (or restore a backup) — the data is portable; the **AI key is not** (`13` §5.2) |
| Reproduce a support issue | Ask for a project backup + the diagnostics bundle, then reproduce via the CLI (`09` §5) — never remote access |
| Portable package update | Replace the folder; schema migrates on first open with the mandatory backup |

### 7.3 Downgrade stance

Downgrading the app is **not supported** (`09` §13). The documented rollback is: keep the previous
installer available (`28` go-live), restore the pre-migration backup, and reinstall the previous version.
The message the user sees on a schema-newer project says exactly this (`ERR-ENG-005`).

## 8. SmartScreen, Defender and code-signing notes (`ADR-003`)

### 8.1 The reality (launch-blocking, `Addon 1 §G.3`)

An unsigned PyInstaller installer downloaded from the internet triggers **SmartScreen** ("Windows protected
your PC" → *Unknown publisher*), and on some machines **Defender** may quarantine the file as a
false positive. The client is a finance analyst with no IT support on call; a scary dialog at the first
step can end the deployment. This section therefore defines the mitigation ladder, the exact user
walkthrough, and what we must never ask the user to do.

### 8.2 The mitigation ladder (in order)

Until a formal code-signing certificate decision and budget allocation are recorded (`OQ-012`), the **unsigned build with SHA-256 checksum verification and the user walkthrough (§8.3)** remains the default path. If certificate procurement is approved, the deployment follows either the OV or EV branch:

| Step / Branch | Action / Option | Cost & Lead Time | SmartScreen Reputation & User Impact | When |
|---|---|---|---|---|
| **Default (Unsigned)** | Published SHA-256 checksum + written walkthrough (§8.3) | $0 / Instant | Triggers "Windows protected your PC" (Unknown Publisher); requires §8.3 walkthrough ("More info" → "Run anyway"). | Current baseline for v0.1.0 pilot wave. |
| **Branch A (Standard OV)** | Organization Validation certificate; sign installer & executable via SignTool / Azure Key Vault HSM | ~$150 – $400 / yr<br>3–7 business days | Initial downloads still trigger SmartScreen warnings until global download volume accumulates reputation over time. | Intermediate corporate deployments with IT oversight. |
| **Branch B (Extended Validation - Recommended for Frictionless)** | EV Code Signing certificate; FIPS hardware token or Cloud HSM; sign installer & executable | ~$300 – $700 / yr<br>5–10 business days | **Immediate SmartScreen reputation bypass.** Zero warnings; direct, frictionless installation. | Recommended if client demands zero-prompt enterprise rollout. |
| **Mitigation 2** | Microsoft malware-analysis false-positive submission (WDSI) if Defender flags build; record submission ID in release notes | $0 / 24–48 hours | Clears Defender heuristic false positives. | Whenever a false positive occurs. |
| **Mitigation 3** | Walk-through support (`22` guide, `23` handover); live assisted first install | Internal time | High confidence during pilot phase. | First rollout / pilot wave. |

### 8.3 The user walkthrough (verbatim, non-technical)

> **When Windows shows a blue "Windows protected your PC" box**
> This happens because the app is new and not yet a "known" download; it does **not** mean the file is
> harmful. To continue:
> 1. Click **More info**.
> 2. Check that the app name is **FP&A Month-End Copilot** and that the version matches what you were told.
> 3. Click **Run anyway**.
> 4. If your browser warns that the file *"isn't commonly downloaded"*, choose **Keep** — then run the file.
> **Check the file's fingerprint first (recommended).** Right-click the downloaded file → **Properties** →
> *Digital signatures*/*File hashes* are not shown for unsigned files, so instead compare the SHA-256 we
> sent you using this command in a terminal:
> `certutil -hashfile "Setup-FPandAMonthEndCopilot-<version>.exe" SHA256`
> The long string that appears must match the one in `SHA256SUMS-<version>.txt`. If it does not match, stop
> and contact us — do not run the file.
> **Never** do these things: do not turn off Defender or SmartScreen, do not run the installer "as
> administrator" if Windows does not ask for it, and do not ignore a warning that names a **different**
> file or publisher than the ones above.

This text is owned here (§8.3), reused verbatim in `22` and `29`, and checked by `TST-SEC-19`'s copy audit.

### 8.4 If Defender quarantines the build

1. Do **not** ask the client to add an exclusion.
2. Submit the exact artefact to Microsoft (WDSI) with the detection name; record the submission ID and
   date in the release notes and `SESSION_LOG`.
3. Wait for the re-scan to clear, then re-verify the hash (the file must not be changed by the process).
4. If it recurs on a subsequent build, treat it as a packaging-blocking defect (check the PyInstaller
   bootloader, the icon/version metadata, compression, and whether a dependency is the trigger).
5. Only after the vendor clears it does the artefact reach the client.

### 8.5 Signing checklist (when a certificate exists)

| Step | Check |
|---|---|
| 1 | Sign the installer **and** the main executable (not only the installer) |
| 2 | Timestamp with an RFC 3161 timestamp server; verify the signature after a clock change |
| 3 | Verify on the clean VM: publisher name shown, SmartScreen not triggered, Properties → Digital Signatures valid |
| 4 | Publish the signer's certificate thumbprint in the release notes so the client's IT can verify |
| 5 | Keep the private key off the build host after the release (`24`); no key material in the repo (`SEC-031`) |

## 9. Support and the diagnostics flow

### 9.1 What the user does (the only supported path)

1. **Help → About & diagnostics** (`SCR-040`, `FR-XC-004`): app version, build date, schema version, data-folder
   reveal, storage used, last diagnostics export, the advisory disclaimer, and two actions:
   **"Export diagnostics"** and **"Check for updates"** (manual; a link, `FR-XC-015`).
2. Clicking **Export diagnostics** shows the **preview** first: the exact file list, the sentence *"This
   bundle contains no amounts and no vendor names"*, the opt-in checkboxes for data rows (off by default,
   separately labelled for exact values), and the destination folder.
3. The bundle is written to the chosen folder; the app never sends it (`SEC-018`).
4. The user attaches it to an email to the agreed support contact and describes what happened in their own
   words. The screen shows the support address and the escalation note from `23`.

### 9.2 What support does

| Step | Action |
|---|---|
| 1 | Read `manifest.json` first (versions, platform, redaction flags, `data_rows_included`) |
| 2 | Run `doctor --json` against the bundle's `health/doctor.json`; check migration state, disk, profile versions |
| 3 | Scan the log tail for the error code and the job stage; correlate with `job.*` timings |
| 4 | Reproduce with the CLI over a project backup when the issue is engine-level (`09` §5) |
| 5 | Answer with: what happened, what was not lost, one next action — or escalate with the bundle reference |
| 6 | If a fix is needed: file it, classify severity (`14` §14.1), and tell the user the workaround today |

### 9.3 Escalation and SLAs (with `23`/`28`)

| Level | Owner | Handles | Target |
|---|---|---|---|
| L1 | Consultant (day-to-day support) | Install/upgrade, how-to, wording, mapping questions | Same business day |
| L2 | Engineer (build owner) | Reproducible defects, data issues, packaging | ≤ 2 business days for a first assessment |
| L3 | Change control | Spec gaps → `27`/impact note (`Addon 4 §E.3`) | Next gate |

### 9.4 What support must never ask for

| Never | Why |
|---|---|
| The AI API key, or a screenshot of it | `SEC-009`/`010`; there is no reason to see it |
| A copy of the client's database or a full data dump by default | The diagnostics bundle is metadata-only; data rows require the user's explicit, informed opt-in (`SEC-016`) |
| Remote access, screen sharing of a live project, or an admin account | No remote support exists by design; the product is local-only (`SEC-004`) |
| Disabling Defender/SmartScreen/exclusions as a first response | §8.4 — vendor submission first |
| The user's Windows password | Never |

### 9.5 When the app will not start at all

1. Windows Event Viewer → Application, filtered to the app, screenshot the error.
2. Run `fpa doctor --json` from a terminal against the data directory (`09` §5.2); if the CLI runs, the
   engine is healthy and the issue is in the shell/WebView2 path (`ERR-ENG-001`).
3. Collect the newest files in `%APPDATA%\FP&A Month-End Copilot\logs\` and any crash dumps.
4. If the app cannot start at all, the **portable package** on a USB stick is the documented recovery
   path for demos and triage; the data directory is untouched by it.
5. Reinstall over the top (repair) as the last resort before a project restore — in that order, because a
   repair cannot lose data and a restore can overwrite.

## 10. Versioning and release-artefact conventions (summary; `24` owns the process)

| Topic | Convention |
|---|---|
| Version scheme | Semver `MAJOR.MINOR.PATCH` for the app; an integer schema version per project (`Addon 1 §J`) |
| Artefact names | `Setup-FPandAMonthEndCopilot-<version>.exe`, `FPandAMonthEndCopilot-<version>-portable.zip`, `SHA256SUMS-<version>.txt` |
| Hash publication | SHA-256 listed in the release notes **and** in the message that delivers the artefacts (`Addon 1 §J`); recomputed by the client with `certutil` (§8.3) |
| Release notes | `CHANGELOG.md` (authoritative) + the per-release `release-notes.md` (user-facing summary, upgrade steps, known issues) |
| Upgrade contract (user's view) | Install over the previous version; the app offers a backup, migrates forward, and keeps the previous installer available for rollback (`28`) |
| What `24` adds | The release checklist, tag/build ordering, the upgrade test with the prior-version fixture, publication and distribution, and the version-bump policy |

## 11. Test and gate mapping

| This document's rules | Proven by |
|---|---|
| Build from a clean checkout, payload audit, size budget | `scripts/build` + `TST-PRF-06` (`NFR-006`) + `GATE-01-06` (working installer from the script) + `GATE-02-09` (licence/SBOM in the payload) |
| Install without admin, shortcuts, uninstall semantics | `TST-WIN-01`, `TST-E2E-08`, §5 steps 6–11 and 21–24 |
| First-run behaviour and failure paths | `TST-E2E-08`, `TST-E2E-03`, `TST-UI-17`, `TST-WIN-11` |
| SmartScreen walkthrough and signing state | §5 steps 4/7 + `TST-WIN-08` + the verbatim copy in §8.3 |
| Upgrade and migration | `TST-E2E-05`, §5 step 20, `24`'s release checklist |
| Diagnostics flow | `TST-SEC-12/13`, `TST-E2E-07`, §5 step 16 |
| Clean-VM protocol as gate evidence | `GATE-01-06`, `ADR-005`, `Addon 1 §G.6`; §5.3 maps all 14 `TST-WIN-*` tests to its steps and variations |
| Licence file and SBOM in the payload | `TST-SEC-20`, §3 step 5, `GATE-02-09` |
| Portable package behaves as documented (§4.3) | §5 step 24 leftover audit + the portable-mode run inside `TST-WIN-01` |

## 12. Failure modes and error codes (family `ENG`)

`ERR-ENG-nnn` is allocated here for **environment, installation and lifecycle** failures and aggregated
into the catalog in `26` (`00_INDEX` §8). Copy follows `08` §16: what happened, what was not lost, one
action.

| ID | Trigger | Headline + hint | Not lost |
|---|---|---|---|
| `ERR-ENG-001` | WebView2 missing or blocked | *"This PC is missing a Windows component the app uses to draw its window."* → Follow the fallback (open in your browser) or ask IT to install WebView2 | All data; the app is usable via the fallback |
| `ERR-ENG-002` | Data directory not writable (permissions, policy, full disk) | *"The app can't save into its data folder."* → Choose another folder or ask IT to restore permissions | Nothing was changed |
| `ERR-ENG-003` | Free disk below the working threshold | *"There isn't enough free space to work safely (need ~<X> GB, free <Y> GB)."* → Free space, move the data folder, or archive old projects | Nothing was changed |
| `ERR-ENG-004` | Upgrade/migration interrupted or failed | *"The upgrade didn't finish. Your project was not changed."* → The backup path is shown; restore it or retry the upgrade | The project and its pre-migration backup |
| `ERR-ENG-005` | Project schema newer than the app | *"This project was created by a newer version of the app."* → Install the newer version; downgrades are not supported | The project (opened read-only is not attempted) |
| `ERR-ENG-006` | A file is held by antivirus/backup software | *"Another program is scanning these files right now."* → Retry in a moment | Nothing |
| `ERR-ENG-007` | Path too long / invalid characters | *"That folder path is too long for Windows."* → Pick a shorter path | Nothing |
| `ERR-ENG-008` | Project already open in another window | *"This project is already open in another window."* → Bring the other window forward | Nothing |
| `ERR-ENG-009` | Payload incomplete (missing template/asset) | *"A file the app needs is missing."* → Repair by reinstalling; the expected file is named | User data and projects |
| `ERR-ENG-010` | Portable mode cannot write beside the app | *"Portable mode can't save next to the app in this folder."* → Remove the flag or move the folder to a writable location | Nothing was changed |

**Installer-level copy** (shown by Inno Setup) follows the same rules: name the object, state the next
action, and never expose an internal error code as the headline (`08` §16).

## 13. Open items, deferrals and assumptions

| Item | Status |
|---|---|
| Code-signing certificate: cost/lead time to be put to the client (`ADR-003` step 5); if funded, a signing ADR supersedes `ADR-003` and §8.5 becomes the checklist | Open (client decision, `21`/`29`) |
| WebView2 in the packaged build (sizing, 150 % DPI, clipboard) and the default-browser fallback (`ERR-ENG-001`) | Spike `SPK-04`; fallback documented |
| Per-machine (all-users) installer variant | Parked unless the client's IT requires it (`27`) |
| Portable mode: no Explorer file-version metadata; documented, not fixed | Accepted limitation (§4.3) |
| Inno Setup major-version pin recorded and re-verified each release | Maintenance item (`24`) |
| MSIX/Store packaging, auto-update, and machine-wide deployment scripts | Explicitly parked (`Addon 1 §N`, `27`) |
| Installer EULA text is owned by `01` §15.1/§16; this document only places it | Cross-reference |

**Assumptions.** (a) The client's machines run Windows 11 x64 with WebView2 present and a standard user
account; (b) the delivery channel can carry a ~500 MB file and a checksum; (c) the client's IT is available
for the one-time install if SmartScreen requires it — the ladder in §8.2 is what happens if not.

## 14. Change control and cross-document obligations

### 14.1 Obligations this document places elsewhere

| Obligation | Owner |
|---|---|
| Release checklist consumes §5 as its Windows proof; artefact naming and hash publication per §10 | `24` |
| Tests `TST-WIN-01`…`14`, `TST-E2E-05/07/08` and the `NFR-006` size check implemented as specified | `14` |
| Payload ships `THIRD_PARTY_LICENSES.txt` and the SBOM snapshot; the secret/licence scans run on the payload | `13` §12, `17` |
| Installer copy, first-run copy and the About/support screen match §6 and §9 | `08` |
| The §8.3 walkthrough is quoted verbatim; the diagnostics flow is explained in user language | `22`, `23` |
| The client pack states the install path, no-admin guarantee, data location, and the checksum step | `29` |
| Go-live keeps the previous installer available and states the rollback steps | `28` |
| `ERR-ENG-001`…`010` and the installer copy are added to the catalog with this wording | `26` |
| `ERR-ENG` is registered in `00` §8 as "environment/install/lifecycle"; this document's wording for `ERR-ENG-001`…`010` is authoritative for `26` | `00` (done) |

### 14.2 Changes to this document

| Change | Requires |
|---|---|
| A build step, exclude list, or payload-content change | `packaging/pyinstaller.spec` + §3 updated; the payload audit and size check re-run; a clean-VM re-run |
| An installer behaviour change (paths, privileges, components, registry) | This document first, then the `.iss`; `24`'s release checklist re-run; `TST-WIN-01` re-run |
| A new error code or copy change | `26` and `08` §16 alignment; `TST-SEC-19` copy audit extended |
| A change to the clean-VM protocol | `14` §15 gate-checks updated in the same pass; previous evidence is invalidated |
| A signing change | New/updated ADR (superseding `ADR-003` if a certificate is bought), §8 updated, the checklist re-run on a clean VM |
| Any change here | `CHANGELOG.md` + `SESSION_LOG.md` entry; the next gate re-runs §5 in full |

**Frozen constants owned by this document:** the artefact names and the four-artefact set (§1.2) · the
version-stamping sources (§2.2) · the build steps and payload-audit rule (§3) · the installer contract
(per-user, no admin, registry limits, "must never" list — §4.1/§4.2) · the portable-mode semantics (§4.3) ·
the 24-step clean-VM protocol (§5.2) · the first-run sequence and rules (§6) · the uninstall/data-lifecycle
semantics (§7) · the SmartScreen ladder and the verbatim walkthrough (§8.2/§8.3) · the support flow and the
"never ask for" list (§9) · `ERR-ENG-001`…`010` (§12).


