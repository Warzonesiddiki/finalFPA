# SmartScreen walkthrough — PRINT THIS PAGE

**For:** the person doing the install, on the day.
**Print single-sided. Keep it next to the machine.**

---

## The short version

You will probably see a blue box that says **"Windows protected your PC"** and names a publisher
as **Unknown publisher**. This is expected. It means Windows has not seen this download before —
not that the file is dangerous.

**But check the fingerprint first.** It takes two minutes and it is what makes it safe to click
through. Part 1 below.

---

## PART 1 — Check the fingerprint (do this first)

### 1. Open Command Prompt

Press the **Windows key**. Type `cmd`. Press **Enter**.

A black window opens.

### 2. Go to the folder where you saved the installer

If you saved it in your Downloads folder, type this and press **Enter**:

```
cd %USERPROFILE%\Downloads
```

If you saved it somewhere else, type `cd` followed by the full path, for example
`cd "C:\Users\asha\Desktop\FPA"`, and press **Enter**.

> **If the file is "blocked":** right-click the installer file → **Properties** → tick **Unblock**
> near the bottom → **Apply**. Then continue.

### 3. Get the fingerprint

Type this, replacing `1.0.0` with the version number you were told, and press **Enter**:

```
certutil -hashfile "Setup-FPandAMonthEndCopilot-1.0.0.exe" SHA256
```

One long line of letters and numbers appears — about 64 characters.

### 4. Compare

Open the file called `SHA256SUMS-1.0.0.txt` and find the same file name in it.

**If the two strings match** → go to Part 2.

**If they do not match** → **stop. Do not run the file.** Contact `[consultant name]` on
`[phone]`.

---

## PART 2 — If Windows shows the blue box

The message will look something like this:

> **Windows protected your PC**
> Microsoft Defender SmartScreen prevented an unrecognised app from starting. Running this app
> might put your PC at risk.
> App: Setup-FPandAMonthEndCopilot-1.0.0.exe
> Publisher: Unknown publisher
> `[ More info ]` `[ Don't run ]`

Do this:

| Step | Do this |
|---|---|
| 1 | Click **More info** (bottom left). |
| 2 | Read the line that appears. Check the app name is **FP&A Month-End Copilot** and the version matches what we told you. |
| 3 | Click **Run anyway**. |
| 4 | If your **browser** also warned the file "isn't commonly downloaded", choose **Keep**, then run the file. |

Then the installer opens. Continue to Part 3.

---

## PART 3 — Installing

- The installer installs **for your Windows user only**.
- It does **not** ask for administrator rights. **If it asks you to run as administrator, stop and
  call us** — that is not expected.
- Accept the licence text. The **Advisory tool — not professional advice** notice appears here and
  is required — please read it.
- Choose the default install location unless we told you otherwise.
- Let it finish. On first run the app may take a little longer than usual.

---

## PART 4 — While you are here

> ### Never do these things
> - Do **not** turn off Defender or SmartScreen.
> - Do **not** add an exclusion for this file or folder.
> - Do **not** run the installer "as administrator" if Windows does not ask for it.
> - Do **not** ignore a warning that names a **different** file or a **different** publisher than
>   the ones above. That is a different situation — call us.

**If Microsoft Defender removes the file on its own:** do not add an exclusion and do not turn
Defender off. Contact `[consultant name]` on `[phone]`. We submit the file to Microsoft for review
and the fix comes from them, not from weakening your security.

---

## PART 5 — First run, the short version

The app opens on a sample project so you can look around safely before touching your own data.
Nothing you click in the sample leaves your machine and no real data is involved.

When you are ready for your own data: create a new project, point it at a **local** folder — **not**
a OneDrive, Dropbox or Google Drive folder — and import your month-end files. The app copies them
into the project folder and never writes back to your originals.

---

## If something goes wrong

Call `[consultant name]` — `[phone]` / `[email]`.

Please tell us, in your own words, what you saw and what you expected to happen. That is more
useful than any screenshot. If you took a photo of the screen, send the photo too.

---

*Prepared by `[consultant]`, `[date]`. Version offered: `[version]`.
This walkthrough matches the project's own documented procedure (`docs/15` §8.3).*