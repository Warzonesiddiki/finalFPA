# Transfer instructions + hash verification — DRAFT for the lead's review

**Status:** proposal only. Not sent. All technical steps are quoted or near-quoted from
`docs/15_PACKAGING_DEPLOYMENT_RUNBOOK.md` §8.2/§8.3 and §1.2.

---

## Part A — what we are sending you

Per `docs/15` §1.2, a release has **four** artefacts. The client receives these, and nothing else:

| # | File name (replace `<version>`) | What it is |
|---|---|---|
| 1 | `Setup-FPandAMonthEndCopilot-<version>.exe` | The installer. Double-click, works. Installs for your Windows user only. |
| 2 | `FPandAMonthEndCopilot-<version>-portable.zip` | The no-install variant, kept as a fallback. You will not normally need it. |
| 3 | `SHA256SUMS-<version>.txt` | The fingerprints of files 1 and 2. This is how you confirm you received exactly what we sent. |
| 4 | `THIRD_PARTY_LICENSES.txt` | The list of open-source components inside the app and their licences. |

**How it is sent.** Through the channel we agreed in writing. Please do not forward these files to
anyone else, and do not post them on a shared drive that others can write to.

**If the files arrive as a `.zip`, unzip them first.** Windows may also add a "blocked" marker to
files that arrive from the internet — Part B step 5 covers that.

---

## Part B — please check the fingerprints before you run anything

This is the one step we ask you not to skip. It takes about two minutes and it is what makes the
"unknown publisher" warning on the next page safe to act on.

**Step 1 — open Command Prompt.**
Press the Windows key, type `cmd`, press Enter.

**Step 2 — move into the folder where you saved the installer.**
For example, if it is in your Downloads folder, type this and press Enter:

```
cd %USERPROFILE%\Downloads
```

**Step 3 — run this, with your real version number substituted in:**

```
certutil -hashfile "Setup-FPandAMonthEndCopilot-<version>.exe" SHA256
```

**Step 4 — read the long string it prints.** It is one line of letters and digits, usually 64
characters long.

**Step 5 — open `SHA256SUMS-<version>.txt` and find the same file name in it.** Compare the two
strings character by character.

| Result | What it means | What to do |
|---|---|---|
| **They match** | You have exactly the file we sent. | Continue to Part C. |
| **They do not match** | The file changed in transit, or it is not ours. | **Stop. Do not run it.** Contact `[name]` at `[phone]`. |
| **The file is "blocked"** | Windows marked it as from the internet. | Right-click the file → **Properties** → tick **Unblock** at the bottom → **Apply**. Then repeat from step 3. |
| **Windows Defender removed the file** | A false positive, not a judgement about the file. | Contact `[name]`. **Do not** add an exclusion or turn Defender off. We handle this with Microsoft. |

---

## Part C — the "Windows protected your PC" message

This happens because the app is new and not yet a "known" download; it does **not** mean the file
is harmful. The following is the project's own walkthrough, used verbatim in the user guide and the
client pack (`docs/15` §8.3).

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

---

## Part D — why the installer is not signed

`docs/01_PRD.md` §15 / `docs/18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md` `PEND-02` record the decision
(approved 2026-10-03, owner auto-decide): **unsigned installer for the pilot**, with the fingerprint
check above as the authentication mechanism. A code-signing certificate was not purchased for this
version (`ADR-003` in `docs/09`).

We are telling you this plainly rather than letting you find the warning on your own. The
certificate options and their costs are recorded in `docs/15` §8.2; if your IT team prefers a
signed installer for a wider rollout, that is a legitimate requirement and we will quote for it.

---

## Part E — when you have a problem

Contact `[name]` at `[phone]` or `[email]`. Please describe what happened **in your own words** —
that is genuinely the most useful thing you can send us.

If the app offers you a support bundle, you may send it, but please read this first:

- By default the bundle contains **no amounts and no vendor names**.
- You will see a preview of exactly which files it contains before anything is written.
- The app never sends it. You attach it yourself, from your own mail.
- If you tick the box to include data rows, it will tell you so explicitly, and you should look at
  it before sending.

We will never ask you for your AI key, a copy of your database, remote access to your machine, or
your Windows password (`docs/15` §9.4).

---

## Source of every claim

| Claim | Source |
|---|---|
| Four release artefacts and their names | `docs/15` §1.2 — table "The four artefacts of a release" |
| `certutil -hashfile ... SHA256` command and match rule | `docs/15` §8.3 — verbatim |
| "Windows protected your PC" walkthrough | `docs/15` §8.3 — quoted verbatim above |
| "Never turn off Defender or SmartScreen" | `docs/15` §8.3 / §8.4 — verbatim |
| Unsigned decision + date | `docs/18` `PEND-02`; `docs/09` `ADR-003` |
| Certificate options/costs | `docs/15` §8.2 |
| Diagnostics bundle is metadata-only, preview first, never auto-sent | `docs/15` §9.1; `docs/13` §7 |
| "We will never ask for…" list | `docs/15` §9.4 |
| Per-user, no-admin install | `docs/15` §1.2, §7 |
| "Unblock" tick on Properties | **NOT VERIFIED against a project document.** It is standard Windows behaviour and is consistent with `docs/15` §8.4's "do not ask the client to add an exclusion" rule, but the lead should confirm it against the clean-VM protocol (`docs/15` §5.2, `TST-WIN-08`) before this document goes to a client. |
| "about two minutes" for the hash check | **NOT A DOCUMENTED CLAIM.** My own estimate. Lead to time it or remove the estimate. |