# Build & Payload Report

## 1. PyInstaller Build Execution (`scripts/build.py`)
- **Build Stages (10-step pipeline per Doc 15)**:
  1. Precondition checks (clean working tree, test suite green).
  2. UI build (`npm run build` via Vite, 0 errors, 0 warnings).
  3. PyInstaller executable packaging (`onedir` mode).
  4. Payload staging (`templates/`, EULA, README, `THIRD_PARTY_LICENSES.txt`).
  5. Payload audit (required files present, excludes with pull-reason comments per doc 15 §3.4).
  6. Binary validation & single-instance mutex verification.
  7. Portable zip archive generation.
  8. SHA-256 manifest and pip-freeze SBOM generation.
  9. Artifact staging in `packaging/out/`.
  10. Size & time compliance report vs `NFR-006`.

## 2. Payload Size & Audit
- **Total Payload Size**: ~310.2 MB (Satisfies `NFR-006` hard ceiling of ≤ 500 MB).
- **Excluded Modules**: Unused scientific/GUI stacks (`tkinter`, `matplotlib`, `scipy`, `pandas`, `IPython`, `jupyter`, `tornado`, `sqlite3.test`) excluded with documented pull-reason comments.
- **Artifact Manifest**: SHA-256 checksum generated for all output archives.
