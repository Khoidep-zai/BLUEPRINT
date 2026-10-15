---
name: static-analysis
description: A comprehensive static analysis toolkit combining CodeQL (deep semantic taint tracking and data flow), Semgrep (fast pattern-based security scans), and SARIF parsing to detect vulnerabilities and enforce security compliance across Java, Spring Boot, and enterprise repositories.
---

# Static Analysis Toolkit (CodeQL, Semgrep, SARIF)

## Overview
This skill provides automated static analysis rules, workflows, and parsing utilities to detect security vulnerabilities, anti-patterns, and compliance issues in enterprise banking codebases (Java, Spring, SQL, configurations).

## Sub-Skills & Capabilities

> **Loading rule (all models):** sub-skills live in nested folders that runtimes do NOT always auto-register as standalone skills. Before running a scan, READ the matching file directly (Antigravity: `view_file`; other runtimes: your equivalent read tool) and follow it — never work from this summary alone.

1. **Semgrep — `.agents/skills/static-analysis/skills/semgrep/SKILL.md`**:
   - Fast syntactic and semantic pattern matching for OWASP Top 10 vulnerabilities, insecure deserialization, SQL injection, and hardcoded secrets.
   - Scan execution: follow the sub-skill's CLI steps. (Claude-Code-style plugin command equivalent: `/static-analysis:semgrep-scan {"target": "<path>", "mode": "run-all"}`.)
2. **CodeQL — `.agents/skills/static-analysis/skills/codeql/SKILL.md`**:
   - Interprocedural taint analysis, data flow tracing from untrusted web/API sources to sinks.
   - Deep query packs: security-extended, Trail of Bits, Community.
3. **SARIF Parsing — `.agents/skills/static-analysis/skills/sarif-parsing/SKILL.md`**:
   - Parse and aggregate SARIF 2.1.0 output files.
   - Deduplicate results, map severity levels, and generate audit-ready QC reports.

## When to Use
- Running pre-merge security checks on Pull Requests.
- Verifying whether untrusted HTTP request parameters reach database queries or reflection calls.
- Validating SARIF reports generated during CI/CD execution.
