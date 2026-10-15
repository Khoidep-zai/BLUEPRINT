---
name: insecure-defaults
description: "Audits a codebase for insecure default configurations, weak JWT secrets, hardcoded credentials, fail-open security switches, weak cryptography, permissive access permissions, and debug information leakage. Use when checking security configurations, reviewing environment variable fallbacks, or hardening backend services."
allowed-tools: Read Grep Glob
---

# Insecure Defaults Detection

Audits a codebase for insecure default configuration, tracing each candidate before reporting it.

## When to Use

- Auditing application configuration files (`application.properties`, `application.yml`, `.env`, `docker-compose.yml`)
- Checking for hardcoded secrets, fallback secrets, or weak JWT signature keys
- Reviewing authentication/authorization configurations for fail-open behaviors
- Verifying CORS configurations, CSRF protection, and file permission defaults
- Detecting debug endpoints or verbose error traces exposed to clients

## What It Finds

| Category | Description & Example | Reference |
|---|---|---|
| **Fallback secrets** | Hardcoded secrets used when environment variable is not set (`jwt.secret = ${JWT_SECRET:secret123}`) | `references/fallback-secrets.md` |
| **Default credentials** | Hardcoded database or admin user/password (`admin / admin123`, `root / root`) | `references/default-credentials.md` |
| **Fail-open switches** | Disabling security checks if variable is unset (`security.auth.enabled = false`) | `references/fail-open-security.md` |
| **Weak crypto** | MD5/SHA1 for passwords, DES/RC4/ECB mode ciphers | `references/weak-crypto.md` |
| **Permissive access** | CORS `Access-Control-Allow-Origin: *` with credentials, open security matcher `permitAll()` on sensitive endpoints | `references/permissive-access.md` |
| **Debug leakage** | Stack traces returned in REST responses, Swagger/Actuator exposed in production | `references/debug-features.md` |

## Audit Methodology

1. **Reconnaissance**:
   - Locate configuration files (`src/main/resources/application*.properties`, `application*.yml`, `.env*`).
   - Identify configuration properties classes and environment variable lookup calls.

2. **Detection & Verification**:
   - Trace each candidate finding: Does it have a fallback default? Is the default insecure?
   - Verify if the setting is reachable in production profiles.
   - Differentiate between dev/test profiles vs production defaults.

3. **Remediation**:
   - Require explicit configuration without weak fallbacks.
   - Fail startup immediately if essential secrets (e.g., `JWT_SECRET`) are missing in production.
   - Use secure defaults: strong hashing (BCrypt/Argon2), secure CORS origins, disabled debug endpoints.
