---
name: api-skill
description: "Comprehensive REST API toolkit for API design, OpenAPI/Swagger specifications, Postman collection generation, API test scripts, and API security patterns. Use when designing endpoints, creating API contracts, generating OpenAPI specs, creating Postman collections, or validating API requests and responses."
category: api-testing
languages:
  - Java
  - TypeScript
  - JavaScript
  - Python
---

# API Skill Suite

A comprehensive toolkit for designing, documenting, testing, and securing RESTful APIs, especially tailored for backend systems (Spring Boot, Node.js, etc.).

## When to Use

- Designing REST API endpoints and specifications for resources
- Creating and maintaining `api-contract.md` or OpenAPI/Swagger (YAML/JSON) specifications
- Generating Postman Collections (v2.1) and writing Newman test suites
- Implementing and validating API security patterns (JWT Bearer tokens, RBAC, OAuth2)
- Reviewing, analyzing, and validating HTTP request/response models and status codes

## Core Modules & Capabilities

This skill directory bundles several specialized modules:

| Module | Location | Purpose |
|---|---|---|
| **API Designer** | `api-designer/` | Designs REST endpoints with request/response schemas, error codes, and pagination envelopes |
| **OpenAPI Spec Generator** | `openapi-spec-generator/` | Generates valid OpenAPI 3.x / Swagger 2.0 YAML & JSON specs |
| **API Documentation** | `api-documentation/` | Generates structured markdown API documentation from code or endpoint specs |
| **Postman Generator** | `postman/postman-collection-generator/` | Produces Postman Collection v2.1 JSON files with variables and pre-request scripts |
| **Postman Tests** | `postman/postman-testcase-generator/` | Generates automated test scripts for Postman requests |
| **OpenAPI to Postman** | `postman/postman-openapi-converter/` | Converts OpenAPI YAML/JSON specs into Postman Collections |
| **Newman CI/CD** | `newman/` | CLI execution and report analysis for automated API testing in CI/CD pipelines |
| **API Security Patterns** | `api-security-patterns/` | Implements JWT authentication, role-based authorization, rate limiting, and CORS headers |
| **API Analyzer** | `api-analyzer/` | Validates HTTP requests, curls, status codes, and payload correctness |

## REST API Design Guidelines

When designing APIs for the backend:

1. **URL Naming**:
   - Use plural nouns for resources (e.g., `/api/v1/jobs`, `/api/v1/applications`, `/api/v1/users`).
   - Use sub-resources for relationships (e.g., `/api/v1/jobs/{jobId}/applications`).
   - Use standard HTTP methods: `GET` (retrieve), `POST` (create), `PUT` (replace), `PATCH` (partial update), `DELETE` (delete).

2. **Standard Pagination Envelope**:
   ```json
   {
     "data": [...],
     "pagination": {
       "total": 100,
       "page": 1,
       "limit": 20,
       "totalPages": 5
     }
   }
   ```

3. **Standard Error Response**:
   ```json
   {
     "timestamp": "2026-10-06T12:00:00Z",
     "status": 400,
     "error": "Bad Request",
     "message": "Validation failed for field 'title'",
     "errors": [
       {"field": "title", "message": "Title cannot be blank"}
     ],
     "path": "/api/v1/jobs"
   }
   ```

4. **Authentication & Authorization**:
   - Send JWT tokens in `Authorization: Bearer <token>` header.
   - Enforce RBAC (e.g. Student, Recruiter, Admin) on endpoints.
