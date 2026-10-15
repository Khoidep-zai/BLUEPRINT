---
name: testing-handbook-skills
description: Advanced security testing, fuzzing, sanitizers, and edge-case testing handbook based on Trail of Bits Application Security Testing methodology. Includes libFuzzer, AFL++, AddressSanitizer, constant-time verification, coverage analysis, and Wycheproof cryptographic test vectors.
---

# Trail of Bits Testing Handbook Skills

## Overview
Comprehensive repository of testing methodologies and tools focused on low-level correctness, memory safety, fuzzing, timing invariance, and cryptographic boundary testing for security-critical enterprise software.

## Included Testing Capabilities

> **Loading rule (all models):** sub-skills live in nested folders that runtimes do NOT always auto-register as standalone skills. When a capability below matches the task, READ its file directly (Antigravity: `view_file`; other runtimes: your equivalent read tool) and follow it — never work from this summary alone.

1. **Fuzzing Engines & Frameworks**:
   - `.agents/skills/testing-handbook-skills/skills/libfuzzer/SKILL.md` — LLVM in-process coverage-guided fuzzing engine.
   - `.agents/skills/testing-handbook-skills/skills/aflpp/SKILL.md` — American Fuzzy Lop plus plus (AFL++) for binary and instrumented source fuzzing.
   - `.agents/skills/testing-handbook-skills/skills/cargo-fuzz/SKILL.md` — Fuzzing toolkit for Rust modules and JNI native libraries.
   - `.agents/skills/testing-handbook-skills/skills/atheris/SKILL.md` — Coverage-guided Python fuzzing engine.
   - `.agents/skills/testing-handbook-skills/skills/libafl/SKILL.md` — Custom fuzzers built from modular Rust components (LibAFL).
   - `.agents/skills/testing-handbook-skills/skills/ruzzy/SKILL.md` — Coverage-guided fuzzing for Ruby and its native C extensions.
   - `.agents/skills/testing-handbook-skills/skills/ossfuzz/SKILL.md` — Enroll a project in OSS-Fuzz continuous fuzzing.
2. **Sanitizers & Dynamic Verification**:
   - `.agents/skills/testing-handbook-skills/skills/address-sanitizer/SKILL.md` — Detect out-of-bounds memory accesses, use-after-free, and stack corruption in native libraries (ASan).
   - `.agents/skills/testing-handbook-skills/skills/constant-time-testing/SKILL.md` — Verify timing-attack resistance in cryptographic calculations and authentication logic.
3. **Coverage, Harnesses & Inputs**:
   - `.agents/skills/testing-handbook-skills/skills/coverage-analysis/SKILL.md` — Identify unreached branches and dead-code paths in complex transaction handlers.
   - `.agents/skills/testing-handbook-skills/skills/harness-writing/SKILL.md` — Design and improve fuzzing harnesses (C/C++, Rust).
   - `.agents/skills/testing-handbook-skills/skills/fuzzing-dictionary/SKILL.md` — Build optimized token dictionaries for parsers and protocols.
   - `.agents/skills/testing-handbook-skills/skills/fuzzing-obstacles/SKILL.md` — Overcome comparison and checksum bottlenecks in deep code paths.
4. **Cryptographic & Edge-Case Testing**:
   - `.agents/skills/testing-handbook-skills/skills/wycheproof/SKILL.md` — Comprehensive test suites against known vulnerabilities and edge cases in cryptographic implementations.
   - `.agents/skills/testing-handbook-skills/skills/testing-handbook-generator/SKILL.md` — Generate new skill files from the Trail of Bits Testing Handbook (appsec.guide).

## When to Use
- Validating native cryptographic libraries, payment signature verifiers, or high-throughput protocol parsers.
- Conducting adversarial robustness testing before major core banking releases.
