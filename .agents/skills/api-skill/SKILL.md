---
name: api-skill
description: Comprehensive suite of API testing, specification, and mocking tools. Generates automated API tests, Postman/Newman collections, OpenAPI 3.x specifications, security audits, rate-limiting validations, and contract testing for REST, GraphQL, and gRPC endpoints in banking architectures.
---

# API Testing & Specification Master Skill

## Overview
This master skill coordinates end-to-end API testing, validation, and contract compliance for modern banking architectures (Open Banking CDR, FAPI, REST, and gRPC microservices).

## Sub-Skills & Toolsets

> **Loading rule (all models):** sub-skills live in nested folders that runtimes do NOT always auto-register as standalone skills. When a request matches a sub-skill below, READ its file directly (Antigravity: `view_file`; other runtimes: your equivalent read tool) and follow it — never work from this summary alone.

1. **API Test Case & Automation Generation**:
   - `.agents/skills/api-skill/api-to-testcase-generator/SKILL.md` — Derives positive, negative, and boundary test cases directly from OpenAPI / Swagger definitions.
   - `.agents/skills/api-skill/postman/postman-testcase-generator/SKILL.md` — Creates Newman-ready Postman test suites with automated assertions on status codes, response times, and payload schemas.
   - `.agents/skills/api-skill/newman/newman-script-helper/SKILL.md` & `.agents/skills/api-skill/newman/newman-cicd-helper/SKILL.md` — Automates command-line Newman execution in CI/CD pipelines (GitHub Actions, GitLab CI, Azure DevOps).
   - `.agents/skills/api-skill/newman/newman-report-analyzer/SKILL.md` — Analyzes Newman runs/reports, summarizes failures, and identifies slow requests.
2. **API Mocking & Sandboxing**:
   - `.agents/skills/api-skill/api-mocking/SKILL.md` — Spawns mock servers and response stubs for external bank rails, payment gateways, and third-party partner APIs.
3. **API Security & Regulatory Compliance**:
   - `.agents/skills/api-skill/api-security-patterns/SKILL.md` — Tests OAuth 2.0 / OIDC tokens, MTLS validation, RBAC/ABAC authorization boundaries, and input sanitization.
   - `.agents/skills/api-skill/api-compliance/SKILL.md` — Verifies compliance with Australian Open Banking CDR, FAPI (Financial-grade API), and PCI-DSS requirements.
   - `.agents/skills/api-skill/api-ratelimit-helper/SKILL.md` — Validates rate limits, sliding windows, and HTTP 429 Too Many Requests response headers.
4. **Specification & Documentation**:
   - `.agents/skills/api-skill/openapi-spec-generator/SKILL.md` — Reverse-engineers or authors clean OpenAPI 3.x contracts from existing controllers or DTOs.
   - `.agents/skills/api-skill/api-designer/SKILL.md` — Generates complete REST endpoint specifications (paths, methods, payloads, status codes).
   - `.agents/skills/api-skill/api-documentation/SKILL.md` — Turns specs, route lists, or controller code into readable API reference documentation.
   - `.agents/skills/api-skill/graphql-grpc-helper/SKILL.md` — Analyzes GraphQL schema types and Protobuf `.proto` gRPC contracts.
   - `.agents/skills/api-skill/api-inference-from-files/SKILL.md` — Infers endpoint lists from project file names or directory structures.
   - `.agents/skills/api-skill/api-versioning-helper/SKILL.md` — Versioning strategies, deprecation flows, and breaking-change classification.
5. **Validation, Integration, Observability & SDKs**:
   - `.agents/skills/api-skill/api-analyzer/SKILL.md` — Validates whether a given API request (method, URL, headers, body, auth, query params) is correct.
   - `.agents/skills/api-skill/api-integration-helper/SKILL.md` — Webhooks, event streaming, API chaining flows, and ETL integration patterns.
   - `.agents/skills/api-skill/api-health-monitoring/SKILL.md` — Health checks, SLAs/SLOs, alerting rules, and API observability strategy.
   - `.agents/skills/api-skill/api-sdk-generator/SKILL.md` — Client SDKs, API wrappers, and request/response models from a spec.
   - `.agents/skills/api-skill/ai-based-api/SKILL.md` — AI-powered API features: LLM tool/function schemas, MCP tools, agentic workflows.
   - `.agents/skills/api-skill/popular-api-fetcher/SKILL.md` — Real-world endpoint conventions from well-known platforms (Stripe, GitHub, Twilio, …).
   - `.agents/skills/api-skill/postman/postman-collection-generator/SKILL.md` — Builds import-ready Postman Collection v2.1 from descriptions or cURL.
   - `.agents/skills/api-skill/postman/postman-openapi-converter/SKILL.md` — Converts OpenAPI 3.x / Swagger 2.0 specs into Postman collections.
   - `.agents/skills/api-skill/postman/postman-to-newman/SKILL.md` — Newman CLI commands, CI/CD (Jenkins/GitHub) pipelines, and report generation.

## When to Use
- Designing new API contracts for banking services.
- Creating automated integration tests for HTTP endpoints before merging code.
- Running regression test suites against staging environments via Newman.
