; Inno Setup Script for FP&A Month-End Copilot per ADR-001, ADR-005, and 15_PACKAGING_DEPLOYMENT_RUNBOOK.md
; Per-user install, no elevation required (PrivilegesRequired=lowest)
;
; Doc 15 section 2.2 (single source of truth): the version lives in
; pyproject.toml. scripts/build passes it with /DMyAppVersion=<version> and
; cross-checks it against app/__init__.py (build precondition 3). The #ifndef
; fallback below exists ONLY so a direct ISCC invocation still compiles - it
; is not a release mechanism. Never bump the fallback to cut a release; bump
; pyproject.toml and rebuild via scripts/build.
;
; Doc 15 section 4.1 (installer contract) implemented here: per-user install
; location (deliberately {localappdata}\Programs\..., NOT the data directory
; %LOCALAPPDATA%\FP&A Month-End Copilot, which the app creates on first run
; per ADR-004 / 09 section 7.1); components app-required + sample-default-on;
; EULA page with required acceptance; HKCU-only registry (the uninstall entry
; plus [Registry] below - nothing under HKLM, ProgramData, PATH, services,
; or file associations); version metadata; versioned uninstall entry.
;
; D-18 GO-LIVE GATE (owner EULA - do not "fix" by editing legal text here):
; LicenseFile wires packaging/EULA.txt, whose section 3 is still a
; [PLACEHOLDER] for commercial indemnification / warranty / governing-law
; terms owned by client legal counsel (OQ-016; docs 01 section 16, 22/23/29).
; Internal pilot builds may ship against that placeholder. CLIENT-VISIBLE
; builds require owner-approved EULA text before go-live.

#ifndef MyAppVersion
#define MyAppVersion "0.1.0"
#endif
#define MyAppName "FP&A Month-End Copilot"
#define MyAppPublisher "FP&A Solutions"
#define MyAppCopyright "Copyright (c) FP&A Solutions"
#define MyAppExeName "FPandAMonthEndCopilot.exe"

[Setup]
AppId={{9B34A99F-637E-44E2-8456-32E7C6981A7D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppCopyright={#MyAppCopyright}
VersionInfoCompany={#MyAppPublisher}
VersionInfoCopyright={#MyAppCopyright}
VersionInfoDescription={#MyAppName} Setup
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoVersion={#MyAppVersion}
VersionInfoTextVersion={#MyAppVersion}
UninstallDisplayName={#MyAppName} {#MyAppVersion}
UninstallDisplayIcon={app}\{#MyAppExeName}
DefaultDirName={localappdata}\Programs\FP&A Month-End Copilot
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
LicenseFile=EULA.txt
SetupIconFile=icons\app.ico
OutputDir=out\{#MyAppVersion}
OutputBaseFilename=Setup-FPandAMonthEndCopilot-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Types]
Name: "full"; Description: "Full installation"
Name: "custom"; Description: "Custom installation"; Flags: iscustom

[Components]
Name: "main"; Description: "Application (required)"; Types: full custom; Flags: fixed
Name: "sample"; Description: "Sample project offer on first run (recommended)"; Types: full

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\FPandAMonthEndCopilot\*"; DestDir: "{app}"; Components: main; Flags: ignoreversion recursesubdirs createallsubdirs

[Registry]
; HKCU only (per-user install). The uninstall entry itself lands under HKCU
; via PrivilegesRequired=lowest; these are the only other writes. The
; SampleOffer value records the [Components] choice for future builds - the v1
; app always offers the bundled sample project on first run (15 section 6.1),
; so this flag changes no v1 behaviour; it is the contract hook, not a stub.
Root: HKCU; Subkey: "Software\FP&A Solutions\FP&A Month-End Copilot"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletevalue; Components: main
Root: HKCU; Subkey: "Software\FP&A Solutions\FP&A Month-End Copilot"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletevalue; Components: main
Root: HKCU; Subkey: "Software\FP&A Solutions\FP&A Month-End Copilot"; ValueType: string; ValueName: "SampleOffer"; ValueData: "1"; Flags: uninsdeletevalue; Components: sample

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Components: main
Name: "{group}\First-run guide (README)"; Filename: "{app}\README.txt"; Components: main
; Target is created by the app on first run (09 section 7.1), never by the installer (15 section 4.1).
Name: "{group}\Open data folder"; Filename: "{localappdata}\FP&A Month-End Copilot"; Components: main
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"; Components: main
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Components: main

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
