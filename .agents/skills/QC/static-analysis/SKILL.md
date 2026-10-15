---
name: static-analysis
description: "Static code analysis toolkit utilizing CodeQL, Semgrep, and SARIF result processing for security vulnerability scanning, taint tracking, and code quality checks (supporting Java/Spring Boot, JavaScript, and more). Use when performing automated vulnerability scans, reviewing static analysis findings, or configuring security checks in CI/CD."
allowed-tools: Read Grep Glob
---

# Static Analysis Toolkit

A comprehensive static analysis toolkit combining **CodeQL**, **Semgrep**, and **SARIF parsing** for automated security vulnerability scanning and taint tracking across backend codebases.

## When to Use

- Performing security vulnerability detection on Java/Spring Boot or Node.js codebases
- Running fast, pattern-based security scans using Semgrep
- Running deep interprocedural taint analysis with CodeQL
- Parsing and aggregating SARIF reports from security scanners
- Integrating static analysis checks into build and CI/CD pipelines

## Included Components

| Component | Location | Role & Capabilities |
|---|---|---|
| **Semgrep** | `skills/semgrep/` | Fast pattern-based security scanning (OWASP Top 10, CWE, Spring Security vulnerabilities, SQL injection, IDOR) |
| **CodeQL** | `skills/codeql/` | Semantic code analysis, deep taint tracking, data-flow analysis, and query suites for Java / Spring |
| **SARIF Parsing** | `skills/sarif-parsing/` | Processing, filtering, deduplicating, and reporting findings from SARIF 2.1.0 output |

## Quick Start: Semgrep Scanning

1. Ensure Semgrep is installed:
   ```bash
   python -m pip install semgrep
   ```
2. Run a scan targeting backend code:
   ```bash
   semgrep scan --config auto src/backend
   # Or with specific rulesets:
   semgrep scan --config "p/security-audit" --config "p/owasp-top-ten" src/backend
   ```

## Quick Start: CodeQL Analysis

1. Create a CodeQL database for Java:
   ```bash
   codeql database create codeql-db --language=java --source-root=.
   ```
2. Analyze the database:
   ```bash
   codeql database analyze codeql-db java-security-extended.qls --format=sarif-latest --output=codeql-results.sarif
   ```

## Common Vulnerabilities Detected in Spring Boot

- **SQL Injection**: Unsanitized parameters concatenated in JPQL / native queries.
- **Broken Access Control (IDOR)**: Missing `@PreAuthorize` or tenant isolation checks on user resource queries.
- **Insecure Deserialization**: Untrusted object streams or unsafe Jackson polymorphic typing.
- **Cross-Site Scripting (XSS)**: Unescaped inputs in HTML views or responses.
- **Mass Assignment**: Entity classes directly bound in `@RequestBody` parameters instead of DTOs.
