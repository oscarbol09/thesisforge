# Security Policy 🛡️

The **ThesisForge** team takes security seriously. We value the input of security researchers and the open-source community to help keep our software safe for researchers and students worldwide.

---

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

---

## Reporting a Vulnerability

> [!IMPORTANT]
> **Please do NOT report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability in ThesisForge, please report it privately:

1. **GitHub Security Advisory:** Navigate to the [Security Advisories tab](https://github.com/oscarbol09/thesisforge/security/advisories/new) of this repository and click **"Report a vulnerability"**.
2. **Direct Contact:** Alternatively, contact the maintainer directly via GitHub profile ([@oscarbol09](https://github.com/oscarbol09)).

### What to Include in Your Report
- Type of issue (e.g., SSRF bypass, local credential leak, formula injection, arbitrary code execution).
- Full paths of source file(s) related to the manifestation of the issue.
- Step-by-step instructions to reproduce the issue (proof-of-concept script or payload).
- Any potential remediation or patch you have identified.

---

## Security Architecture & Design Guarantees

ThesisForge is designed with defense-in-depth security principles:

1. **SSRF Guard (`thesisforge.core.security.SSRFGuard`):**
   - Resolves all external literature and paper download URLs.
   - Strictly verifies that resolved IPs do not belong to loopback, private, carrier-grade NAT, or link-local subnets (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1/128`).
2. **Local Key Vault (`thesisforge.repository.keystore_repository.KeyStoreRepository`):**
   - Symmetric 256-bit Fernet encryption for all user BYOK API keys stored locally in SQLite.
   - Keys are decrypted only transiently in memory when creating LLM router requests and never written in plaintext to disk.
3. **Log Injection Defense (CWE-117):**
   - Structured logging strips or encodes carriage returns (`\r`, `\n`) from all user-controlled strings before logging.
4. **Formula Injection Sanitization:**
   - Word and spreadsheet table export layers sanitize cells starting with `=`, `+`, `-`, `@`, `\t`, or `\r` to protect researchers opening exported documents in office suites.
