> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** the **release process** — semver rules, tags, the release checklist, the release record,
> upgrade/migration testing with the prior-version fixture, distribution + checksum publication, and signing
> status (Addon 1 §C.1/§J; `15` §10 delegates the process here)
> **TL;DR (≤ 15 lines):**
> - **Dual versioning:** Independent semantic versioning for application binaries (app) and project databases (schema).
> - **Schema migrations:** Forward-only, atomic SQLite/DuckDB migrations; automatic backup created prior to schema upgrade.
> - **Release packaging:** Automated build steps producing installer, portable zip, checksums, and license manifests.
> - **Rollback protocol:** Deterministic rollback via pre-upgrade project database backup restore; no destructive downgrades.
> - **Git tagging & release gates:** Strict tagging conventions, changelog verification, and sign-off prerequisites.

# 24 — Release and Versioning Runbook

## 1. Purpose, ownership and readers

| Item | Detail |
|---|---|
| Readers | Whoever cuts the release (consultant/engineer), the reviewer who approves it, and the client's IT contact who receives it |
| Owns | The version scheme and bump rules, tags, the release checklist and record, the upgrade/migration test and its fixture, distribution and checksum publication, signing status, patch/hotfix rules, release notes |
| Does not own | The build steps (`15` §3.2), the clean-Windows protocol (`15` §5.2), release **cadence** (`16` §8), packaging security statements (`13` §12), support/escalation (`23` §10/§11), UAT/go-live (`28`) |
| Rule of use | §4 is executed top to bottom; any deviation is written in the release record with the reason |

## 2. Version scheme

### 2.1 The three numbers

| Number | Where it lives | Who changes it | Meaning |
|---|---|---|---|
| **App version** `MAJOR.MINOR.PATCH` | `pyproject.toml` → derived everywhere (`15` §2.2) | `scripts/release` at a gate or a patch | What the client installs; shown in About (`FR-XC-004`) and stamped on every artefact |
| **Schema version** integer | `SchemaMetadata` inside **each project** (`09` §13) | Migration scripts, never the build | What each project's databases expect; compared on open (`FR-PRJ-007`) |
| **Docs version** `0.1.x` | `00_INDEX`/`CHANGELOG` headers | Doc passes; bumped at gates | The Phase-0 document set; `0.1.0` until Phase 0 is approved (`16` §8.2) |

### 2.2 Bump rules (decided, not discussed)

| Change | Bump | Examples |
|---|---|---|
| Breaking data or file-format change the client must act on; a schema migration that changes project structure irreversibly | **MAJOR** | Removing a table, changing a money type, a required new gate |
| New scope at a green gate (new FRs, new screens, new rule family) | **MINOR** | Phase 1 → Phase 2 build; a new export artefact |
| Fixes, wording, performance, packaging | **PATCH** | A P0 patch release; a wording fix; a re-release after a failed clean-Windows run |
| Documentation only | none | Docs commits carry no app version bump; the docs version moves separately |

**Pre-1.0 rule:** while the product is unreleased to the client, `0.x` may change shape between gates —
this is noted in the release notes, and the pilot/UAT builds are the first that carry the "no breaking
change without a MAJOR bump" promise.

### 2.3 The one-place rule

- `scripts/release` writes the version; `scripts/build` reads it (`15` §2.2).
- A mismatch between the installer's file version, the About screen and the artefact file name **fails the
  release** (`15` §2.2 rule).
- The version in `CHANGELOG.md` and `release-notes.md` is generated from the same value — never typed.
- A release commit is a `chore(release): v<version>` commit containing only version bump + notes.

## 3. Branches and tags

| Rule | Detail |
|---|---|
| Trunk-based | `main` is always green and releasable (`17` §11); work happens on short-lived branches merged within a session |
| Tag format | Annotated tag `vMAJOR.MINOR.PATCH` on the release commit on `main` (`17` §11) |
| Tag message | Version + one-line summary + the release-record path, e.g. `v0.4.0 — Phase 3 exception engine; packaging/out/0.4.0/` |
| Tags are immutable | Never moved, never deleted, never reused (`17` §11); a mistake is fixed by the **next** patch release |
| Tags are created **after** the checklist | §4 step 12 — a tag that exists before the evidence does cannot be un-shipped |
| Release branch | None; a hotfix is a commit on `main` + a tag (see §9) |
| `packaging/out/` | Git-ignored: artefacts are attached to the release record, never committed (`15` §2.3) |

## 4. The release checklist (14 steps)

Run at a green gate (`16` §5.1) or for a P0 patch (§9). Every row leaves evidence in the release record.

| # | Step | Owner | Evidence | Abort if |
|---|---|---|---|---|
| 1 | **Gate is green:** all `16` §5.1 items evidenced, including the cross-artefact test and the Windows checks | Engineer | Gate transcript + checklist | Any item not evidenced |
| 2 | **Freeze:** note the frozen commit; only test fixes allowed during the run (`16` §8.3) | Engineer | Commit hash in the record | Feature work in flight |
| 3 | **Bump:** `scripts/release` sets the version from §2.2 | Engineer | Version commit `chore(release): v<version>` | Version typed in more than one place |
| 4 | **Build:** run `scripts/build` (`15` §3.2, steps 1–10) and read the size/time report | Engineer | Build report, payload audit, artefact list | Payload audit failure, size over `NFR-006` |
| 5 | **Checksums + SBOM:** compute `SHA256SUMS-<version>.txt`; snapshot `sbom/py-<version>.txt` (`SEC-047`) | Engineer | Both files in `packaging/out/<version>/` | Missing or non-matching hash |
| 6 | **Clean-Windows 11 protocol:** the `15` §5.2 24-step run on a machine that never saw the app | Engineer | Signed run sheet + screenshots (SmartScreen, first run, sample project, one pack) | Any step fails |
| 7 | **Smoke on the build host:** install → launch → sample project → generate one pack → uninstall (`15` §3.2 step 9) | Engineer | Smoke transcript | Any step fails |
| 8 | **Upgrade test:** `TST-E2E-05` against the prior-version fixture; hash-compare the numbers before/after | Engineer | Test output + migration log | Numbers changed, or a manual step appeared |
| 9 | **Release notes:** generate `packaging/out/<version>/release-notes.md` from `CHANGELOG.md` + the template (§10) | Engineer | Notes file | Known issues section empty when issues exist |
| 10 | **Review:** a second pair of eyes checks steps 1–9 against the record (for a one-person team: the checklist itself is the reviewer, and the review note says so) | Reviewer | Review note | Any gap unexplained |
| 11 | **Approval:** record `Release <version> APPROVED — <who> — <date>` in `CHANGELOG` **and** `SESSION_LOG` (`19` §6) | Project owner | Both files | No explicit approval |
| 12 | **Tag:** annotated `v<version>` on the release commit (§3) | Engineer | Tag | Tag exists already |
| 13 | **Publish:** attach artefacts, checksums, SBOM and notes to the release record; publish through the agreed channel (`Q-016`) | Engineer | Publication record + delivery message containing the SHA-256 | Channel not agreed |
| 14 | **Deliver and record:** client receives artefacts + hash + one-paragraph "what changed / what to re-test"; record the delivery | Consultant | Delivery confirmation in the release record | Hash not delivered with the files |

> **Two rules that override the table:** (a) a step that cannot be evidenced is a failed step;
> (b) if a step fails **after** the tag, the tag stays and the fix ships as the next patch (§9) — history is
> never rewritten.

## 5. The release record

`packaging/out/<version>/` (git-ignored) is the release record and must contain:

| File | Content |
|---|---|
| `Setup-FPandAMonthEndCopilot-<version>.exe` | The installer (`15` §1.2) |
| `FPandAMonthEndCopilot-<version>-portable.zip` | The portable package (`15` §4.3) |
| `SHA256SUMS-<version>.txt` | Hashes of both artefacts |
| `sbom/py-<version>.txt` | `pip freeze` snapshot of the built environment (`SEC-047`) |
| `release-notes.md` | The client-facing summary (§10) |
| `build-report.txt` | Size vs `NFR-006`, durations, payload breakdown (`15` §3.2 step 10) |
| `payload-audit.txt` | The automated payload-audit output (`15` §3.2 step 5) |
| `smoke-transcript.txt` | Build-host smoke run |
| `clean-windows-run-sheet.pdf` | Signed 24-step protocol with screenshots |
| `upgrade-test-output.txt` | `TST-E2E-05` output + migration log excerpt |
| `gate-transcript.txt` | The full `scripts/check` run for the frozen commit |
| `RELEASE-RECORD.md` | The filled checklist (§4) with commit hash, reviewer, approval line and delivery confirmation |

**Retention:** the record for every **client-visible** release is kept for the life of the engagement (and
offered to the client at handover, `23` §12); internal demo builds may be pruned after the next gate.

## 6. Upgrade, migration and the prior-version fixture

### 6.1 What the user experiences

1. The client installs the new version over the old one (per-user install; the previous installer stays in
   their hands for rollback, `15` §7.3).
2. On first open of a project, the app compares schema versions (`FR-PRJ-007`):
   - **Older** → it offers/creates a **mandatory backup**, then migrates forward with a progress indicator
     and a written result ("what changed, what to do next").
   - **Same** → opens normally.
   - **Newer** → refuses with *"This project needs a newer version of the app"* and links to the release
     notes — never a half-open project.
3. On failure, the project is untouched and the backup is retained; diagnostics are offered.

### 6.2 The rules behind it (`09` §13, `ADR-008`)

| Rule | Consequence for this runbook |
|---|---|
| `SchemaMetadata.schema_version` is the only schema source of truth | The release record stores the schema version the build expects |
| Migrations are ordered, forward-only, idempotent, with a `migration_log` | A migration script is reviewed like code and tested by `TST-E2E-05` |
| A failed migration leaves the project untouched, backup retained | Abort condition in §4 step 8; the fix ships as a patch with a new migration, never an edited one |
| Every schema-changing release ships a migration **and** the prior-version fixture | A release without both is **not releasable** (`09` §13 rule 4) |
| No DDL outside a migration script | A release review checks this explicitly |
| No downgrade support; rollback = restore | §6.4 |

### 6.3 The prior-version fixture

| Aspect | Rule |
|---|---|
| What it is | A real project folder created by the **previous released version**, with realistic data (sample-data scale, never client data), committed to `tests/fixtures/prior-version-project/` |
| Why real | `GATE-02-07`: the upgrade test must run against a project a real build made — not a hand-made database |
| Creation | After each client-visible release: open the sample project in that build, use it enough to write all stores, back it up, and commit the backup with a README naming its originating version |
| Refresh | Never edited by hand; superseded by the next release's fixture; older fixtures are kept (metadata only) while any client might still run that version |
| The test | `TST-E2E-05` opens the fixture with the new build, migrates, and hash-compares the derived numbers before/after (`14` §4.1) |
| Rule | The fixture is **never** edited to make a test pass — the migration or the test changes first (`19` §4) |
| Size guard | The fixture stays small (a trimmed month, not a full year); it is data, not documentation |

### 6.4 Rollback (the documented one)

1. Restore the project from the pre-migration backup (or the user's own backup) with the **older** build.
2. Reinstall the older installer (kept by the client for exactly this reason).
3. Record the incident; the cause becomes a regression test before the next release.

**Never:** edit a migration script after it has shipped, hand-fix a project's `SchemaMetadata`, or ship a
"migration tool" outside the app.

## 7. Distribution and checksum publication

| Aspect | Rule |
|---|---|
| Channel | The channel agreed with the client (`Q-016`); until agreed, a secure link — **never** an attachment in a public channel |
| Message contents | Artefact file name(s), the SHA-256 from `SHA256SUMS-<version>.txt`, one line on what changed, one line on what to re-test |
| Hash authority | The hash in the notes **and** the delivery message are identical to the file in the record; a mismatch is a failed release |
| Client verification | `certutil -hashfile "Setup-FPandAMonthEndCopilot-<version>.exe" SHA256` compared against the published value (`15` §8.3 walkthrough, reused verbatim in `22` §2.1 and `29`) |
| Portable fallback | The portable zip travels with the same hash discipline; it is the documented path when installers are blocked (`15` §4.3) |
| What is never distributed | Dev builds, demo builds, `.env` files, keys, source, tests, `sample-data/` generator (`15` §3.2 payload audit) |
| If a hash mismatches | Stop; re-download; if it still mismatches, treat as a security incident, notify the client, do not run the file |

## 8. Signing status

| Situation | Release behaviour |
|---|---|
| **v1 (default): unsigned** | `ADR-003` applies: the documented SmartScreen mitigation ladder and the verbatim user walkthrough (`15` §8.3) ship with every release; the release notes repeat that the hash is the authentication mechanism |
| Certificate procured (`OQ-012` answered) | `15` §8.5's checklist runs; the release record stores the certificate subject **and thumbprint**, and the clean-Windows run sheet shows the signed publisher name |
| Certificate expiry/rotation | The subject is re-verified at the last gate before expiry; an expired certificate is treated as unsigned (the ladder applies), and the next release must ship with the renewed certificate |
| SBOM and licenses | Attached to every release record (`SEC-047`, `SEC-029`); a dependency outside the allow-list fails the build (`14` §13.1) |

## 9. Patch and hotfix releases

| Rule | Detail |
|---|---|
| Trigger | A **P0 defect** in a released build (wrong numbers, crash, data loss, security, install failure) |
| Scope | The smallest change that removes the defect **plus its regression test**; no drive-by improvements (`16` §8.2) |
| Checklist | §4 runs in full, except the gate transcript is replaced by the **affected gate items** re-run (which are named in the record) |
| Version | A new **PATCH**; the previous release record stays |
| Notes | State the defect in plain language, what was not affected, and the recommended action (upgrade now / before next month-end) |
| Fixture | If the schema changed, the prior-version fixture is refreshed from the **previous** release before the patch ships (§6.3) |
| Communication | The client is told what changed and what to re-check; a patch is never "silent" |

## 10. Release notes template

`packaging/out/<version>/release-notes.md` (generated, then human-reviewed):

```
# FP&A Month-End Copilot <version> — <date>

## What's new
- <one line per user-visible change, FR-linked internally>

## Fixed
- <one line per fix, with the symptom the user saw>

## Upgrade notes
- Install over the previous version. Your projects are backed up automatically before any upgrade step.
- If you use the portable package, replace the folder and keep your data folder unchanged.

## Known issues
- <issue + workaround, or "None known">

## Verification
- SHA-256: <hash for the installer> / <hash for the portable zip>
- Publisher: <signed subject, or "unsigned build — verify the SHA-256 before running">
```

## 11. Release evidence (what proves a release happened)

| Evidence | Owner step | Where |
|---|---|---|
| Gate transcript (frozen commit) | §4 step 1 | Release record |
| Version commit + tag | §4 steps 3, 12 | Git history |
| Build report + payload audit | §4 step 4 | Release record |
| Checksums + SBOM | §4 step 5 | Release record + delivery message |
| Clean-Windows run sheet + screenshots | §4 step 6 | Release record |
| Smoke transcript | §4 step 7 | Release record |
| Upgrade test output + migration log | §4 step 8 | Release record |
| Release notes | §4 step 9 | Release record + client |
| Review note + approval lines | §4 steps 10–11 | `CHANGELOG` + `SESSION_LOG` |
| Delivery confirmation | §4 step 14 | Release record |

## 12. Roles

| Role | Who | Owns |
|---|---|---|
| Release engineer | Consultant/engineer | Steps 2–9, 12–13 |
| Reviewer | Second engineer, or the checklist itself with an explicit note | Steps 1, 10 |
| Approver | Project owner | Step 11 |
| Client-side go-live approval | Client owner | `28` (UAT/go-live), not this document |
| Receiver | Client IT contact | Verification and installation (`22` §2.1) |

## 13. Obligations this document places elsewhere

| Owner | Obligation |
|---|---|
| `15` | Keeps build/installer/clean-Windows facts current; a change there updates §4 in the same pass |
| `16` | Owns cadence and freeze windows; §4 assumes a green gate |
| `14` | Owns `TST-E2E-05` and the fixture path; the fixture is refreshed after each client-visible release |
| `13` | Owns the SBOM/license/secret statements (`SEC-028`–`031`, `SEC-047`) referenced in §5/§8 |
| `17` | Owns the commit/tag conventions; §3 cites them |
| `23` | Owns support/incident handling after a release; §9's patch enters `23` §10's playbook |
| `28` | Owns UAT, the go-live rehearsal (`TST-UAT-06`) and the client sign-off |
| `27` | Records anything deferred out of a release |

## 14. Change control for this document

1. A step added or removed in §4 is a process change: it updates `15`/`16` first if they are the owner,
   then this document, in the same pass.
2. A failed release adds a note to §4's abort column if the failure was not covered — the checklist learns
   from every failure.
3. Version-bump rules (§2.2) change only with a recorded decision in `18` §5.

## 15. Frozen constants and conventions in this document

| Constant | Value | Source |
|---|---|---|
| App version | `MAJOR.MINOR.PATCH`; source `pyproject.toml` | §2, `15` §2.2 |
| Schema version | Integer inside each project | §2, `09` §13 |
| Tag | Annotated `vMAJOR.MINOR.PATCH` on `main`, never moved | §3, `17` §11 |
| Checklist | 14 steps with owner/evidence/abort | §4 |
| Release record | Twelve files in `packaging/out/<version>/` | §5 |
| Upgrade evidence | Prior-version fixture + `TST-E2E-05` + migration log | §6, `14` §4.1 |
| Rollback | Restore from the pre-migration backup with the older build | §6.4, `ADR-008` |
| Hash publication | SHA-256 in the notes **and** the delivery message | §7, `Q-016` |
| Signing default | Unsigned v1 + mitigation ladder until `OQ-012` is answered | §8, `ADR-003` |
| Patch trigger | P0 defect only, minimal change + regression test | §9, `16` §8.2 |
