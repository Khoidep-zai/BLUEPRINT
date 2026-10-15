---
name: insecure-defaults
description: Audits codebases for dangerous default configurations, fallback secrets, default credentials, fail-open switches, weak cryptographic algorithms, and permissive access controls. Use during QC security reviews to prevent accidental deployment of insecure developer settings to production.
---

# Insecure Defaults Detection Skill

## Overview
Identifies dangerous fallback patterns and developer defaults that can introduce security vulnerabilities in production environments, particularly in banking systems where authentication, encryption, and authorization must remain strictly enforced.

## Vulnerability Categories Checked
1. **Fallback Secrets (`references/fallback-secrets.md`)**:
   - `SECRET = env.get('KEY') or 'dev'`
   - Hardcoded HMAC/AES keys or default JWT signing secrets.
2. **Default Credentials (`references/default-credentials.md`)**:
   - Seeded database credentials (`admin` / `admin123`, `root` / `toor`).
3. **Fail-Open Switches (`references/fail-open-security.md`)**:
   - `getenv('REQUIRE_AUTH', 'false')` or bypassing mTLS/signature checks when connection fails.
4. **Weak Cryptography (`references/weak-crypto.md`)**:
   - MD5, SHA-1, DES, RC4, or insecure ECB block cipher modes in financial transactions.
5. **Permissive Access (`references/permissive-access.md`)**:
   - Wildcard CORS (`*`), overly permissive file permissions (`0o666`), or public AWS S3 bucket ACLs.
6. **Debug & Information Leakage (`references/debug-features.md`)**:
   - Stack trace exposure in API responses (`traceback.format_exc()`, Spring Boot `/actuator/env` open).

## When to Use
- QC audits before merging code to staging/production branches.
- Inspecting configuration properties files (`application.yml`, `application.properties`, environment configs).
- Ensuring compliance with APRA CPS 234 and banking data-protection policies.
