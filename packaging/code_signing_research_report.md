# Code-Signing Options Research Report (OQ-012)

## 1. Quoted Context (`OQ-012`)
From `docs/18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md`:
> **OQ-012**: *"Is there budget/lead time for a code-signing certificate? SmartScreen posture and the install experience. Not purchased; the mitigation ladder applies (`ADR-003`). Owner: Project owner."*

---

## 2. Windows Authenticode Code-Signing Options

### A. Certificate Types & Validation Levels
1. **Standard OV (Organization Validation) Code Signing**:
   - **Validation**: Verifies organization legal identity, name, and physical address.
   - **SmartScreen Reputation**: Helps build reputation over time, but raw OV certificates still trigger Windows SmartScreen "Unknown Publisher" warnings upon initial downloads until cryptographic and download volume reputation accumulates (Microsoft SmartScreen reputation filter).
   - **Hardware Token Requirement**: As of mid-2023 (CA/Browser Forum baseline requirements), standard OV private keys must be stored on physical FIPS-compliant hardware tokens (USB token / cryptographic module) or HSM (Hardware Security Module), or managed via cloud HSM (e.g., Azure Key Vault with Managed HSM).
   - **Indicative Cost**: ~$150 – $400 / year (depending on Certificate Authority: DigiCert, Sectigo, SSL.com, GlobalSign).
   - **Lead Time**: 3 to 7 business days for organizational vetting and token delivery.

2. **EV (Extended Validation) Code Signing**:
   - **Validation**: Rigorous vetting of legal identity, operational existence, and physical address.
   - **SmartScreen Reputation**: **Immediate SmartScreen reputation bypass.** An application signed with an EV certificate is immediately trusted by Windows SmartScreen, completely eliminating the "Windows protected your PC / Unknown Publisher" blue blocking prompt.
   - **Hardware Token Requirement**: Mandatory FIPS 140-2 Level 2 (or higher) hardware USB token or Cloud HSM.
   - **Indicative Cost**: ~$300 – $700 / year.
   - **Lead Time**: 5 to 10 business days for rigorous validation.

---

## 3. Tooling Workflow Integration (`AzureSignTool` & `SignTool`)

- **Inno Setup Pipeline Integration**:
  - The Inno Setup compiler (`iscc.exe`) compiles the installer `.exe`.
  - Immediately following compilation, the signing utility (`SignTool` or `AzureSignTool`) signs the binary:
    ```powershell
    signtool sign /tr http://timestamp.digicert.com /td sha256 /fd sha256 /sha1 <Thumbprint> "output/fpa_copilot_setup_v0.1.0.exe"
    ```
  - For automated CI/CD build servers (like `build.py`), cloud HSM providers (such as Azure Key Vault / AzureSignTool) enable non-interactive signing using service principal credentials without requiring a physical USB token plugged into the build machine.

---

## 4. Impact on the Doc 15 SmartScreen Mitigation Ladder (`ADR-003`)

| Dimension | Unsigned Build (Current v0.1.0 State) | Signed OV Build | Signed EV Build |
|---|---|---|---|
| **SmartScreen Prompt** | Full blue warning dialog ("Windows protected your PC") requiring user click on "More info" → "Run anyway". | Initial downloads still show warning until global download volume builds; later downloads trusted. | **Zero warnings.** Direct, frictionless installation. |
| **User Walkthrough Requirement** | Mandatory inclusion of Doc 15 §8.3 non-technical screenshots and step-by-step instructions. | Simplified walkthrough for OV; optional/minimal for EV. | Minimal / none required. |
| **Delivery Friction** | Requires client IT awareness or user instruction. | Moderate initial friction. | Frictionless enterprise deployment. |

---

## 5. Conclusion & Recommendation
- **Current Baseline (`ADR-003`)**: Retain the fully documented unsigned path with published SHA-256 checksums (`15` §8) as the baseline for the pilot wave.
- **Go-Live Upgrade Path**: If the client requires frictionless onboarding without SmartScreen prompts, procure an **EV Code Signing Certificate** ($300–$700/yr, 5–10 day lead time) and integrate `AzureSignTool` into `build.py` using a cloud HSM.
