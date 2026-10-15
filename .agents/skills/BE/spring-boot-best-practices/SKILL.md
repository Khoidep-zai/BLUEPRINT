---
name: spring-boot-best-practices
description: "Best practices, architectural patterns, and conventions for Spring Boot 3.2+ and Java 17/21 backend development in the Freelance Marketplace system. Use when implementing layered architecture (Controller -> Service -> Repository -> DTO), creating REST endpoints, handling bean validation, building GlobalExceptionHandler, structuring ApiResponse wrappers, configuring Spring profiles (mysql, postgres, dev), or writing clean maintainable backend code."
---

# Spring Boot 3.2+ Best Practices (Project CDTN2)

Guidelines and conventions for developing robust, maintainable, and high-performance backend modules in the **Freelance & Part-time Marketplace Platform** (`com.nhom8.freelance`).

## 1. Architectural Layers & Responsibilities

Follow strict separation of concerns across packages:

```
com.nhom8.freelance
├── config/          # Spring beans, SecurityConfig, CorsConfig, OpenApiConfig
├── controllers/     # REST controllers, input validation (@Valid), route mappings
├── dto/             # Request & Response Data Transfer Objects
│   ├── request/     # Input payloads (LoginRequest, JobCreateRequest...)
│   └── response/    # Output payloads (ApiResponse, JobResponse, AuthResponse...)
├── exceptions/      # Custom domain exceptions & GlobalExceptionHandler
├── models/          # JPA entities with table/index annotations
├── repositories/    # Spring Data JPA repositories & custom queries
├── security/        # JWT filter, UserPrincipal, CustomUserDetailsService
└── services/        # Business logic interfaces and ServiceImpl classes
```

### Layer Rules
- **Controllers**:
  - Never call Repositories directly; always delegate to Services.
  - Return `ResponseEntity<ApiResponse<T>>` for uniform client contracts.
  - Apply `@Valid` on request bodies to catch invalid inputs at boundary.
  - Keep controllers thin: no business logic, no SQL/HQL.
- **Services**:
  - Encapsulate all business rules, authorization checks, and transaction boundaries.
  - Return DTOs or domain models (DTOs preferred for API boundaries).
  - Use `@Transactional(readOnly = true)` by default on service classes, and override with `@Transactional` on write operations.
- **Repositories**:
  - Leverage Spring Data JPA derived query methods and `@Query` JPQL.
  - Use `@EntityGraph` or `JOIN FETCH` to prevent N+1 queries.
  - Return `Page<T>` when handling lists to prevent memory exhaustion.

---

## 2. Standardized API Response & Error Handling

### 2.1 Uniform Response Contract (`ApiResponse<T>`)
Every REST endpoint must return the standardized `ApiResponse<T>`:

```java
public class ApiResponse<T> {
    private boolean success;
    private String message;
    private T data;
    private LocalDateTime timestamp;

    public static <T> ApiResponse<T> success(T data, String message) {
        return new ApiResponse<>(true, message, data, LocalDateTime.now());
    }

    public static <T> ApiResponse<T> error(String message) {
        return new ApiResponse<>(false, message, null, LocalDateTime.now());
    }
}
```

### 2.2 Global Exception Handling (`@RestControllerAdvice`)
Handle errors centrally in `GlobalExceptionHandler.java`:
- `ResourceNotFoundException`: Return 404 NOT_FOUND.
- `MethodArgumentNotValidException`: Return 400 BAD_REQUEST with field error map.
- `BadCredentialsException`: Return 401 UNAUTHORIZED with generic "Tên đăng nhập hoặc mật khẩu không chính xác".
- `AccessDeniedException`: Return 403 FORBIDDEN.
- `BusinessLogicException`: Return 400 or 409 CONFLICT with domain error message.
- `Exception`: Catch unhandled errors, log stack trace with SLF4J, return 500 INTERNAL_SERVER_ERROR without exposing internal traces to the client.

---

## 3. Input Validation (`jakarta.validation`)

Always validate inputs on DTOs:

```java
public record JobCreateRequest(
    @NotBlank(message = "Tiêu đề công việc không được để trống")
    @Size(min = 10, max = 200, message = "Tiêu đề phải từ 10 đến 200 ký tự")
    String title,

    @NotBlank(message = "Mô tả công việc không được để trống")
    String description,

    @NotNull(message = "Ngân sách không được để trống")
    @DecimalMin(value = "10000.0", message = "Ngân sách tối thiểu là 10.000 VNĐ")
    BigDecimal budget,

    @NotNull(message = "Hạn chót ứng tuyển không được để trống")
    @Future(message = "Hạn chót phải sau ngày hiện tại")
    LocalDate deadline,

    @NotNull(message = "Danh mục không được để trống")
    Long categoryId
) {}
```

---

## 4. Multi-Profile Environment Configuration

The project supports 3 primary profiles: `mysql`, `postgres`, and `dev` (H2).
- Base settings: `src/main/resources/application.yml`
- Environment override: Set `SPRING_PROFILES_ACTIVE=mysql` or `postgres`
- Secret management: Always load secrets from environment variables with safe dev fallbacks:
  ```yaml
  app:
    jwt:
      secret: ${JWT_SECRET:default-dev-secret-replace-in-production}
      expiration-ms: ${JWT_EXPIRATION_MS:86400000}
  ```

---

## 5. Performance & Transaction Checklist

1. **Lazy Loading**: Set `FetchType.LAZY` for all `@ManyToOne` and `@OneToMany` relationships.
2. **OSIV Disabled**: Ensure `spring.jpa.open-in-view: false` to detect accidental N+1 queries early.
3. **Pagination**: Always paginate listing endpoints with `Pageable pageable` (e.g., `GET /jobs?page=0&size=20`).
4. **Log Levels**: Use `log.debug(...)` for query inspection in dev, and `log.info(...)` / `log.error(...)` in prod.
