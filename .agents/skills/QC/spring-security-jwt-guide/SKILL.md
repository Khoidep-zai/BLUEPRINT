---
name: spring-security-jwt-guide
description: "Implementation guide and security checklist for Spring Security 6 and stateless JWT authentication in Spring Boot 3.2+. Use when configuring SecurityFilterChain, setting up JWT token generation/validation, defining RBAC rules for ROLE_STUDENT, ROLE_EMPLOYER, ROLE_ADMIN, implementing ownership checks (IDOR prevention), handling 401/403 exceptions, or hardening CORS/CSRF configurations."
---

# Spring Security 6 & JWT Guide (Project CDTN2)

Guide and security rules for securing the **Freelance & Marketplace Platform** using Spring Security 6, stateless JWT (HS256), BCrypt, and Role-Based Access Control (RBAC).

## 1. Spring Security 6 Architecture

Spring Security 6 deprecates `WebSecurityConfigurerAdapter`. All configurations must use `@Bean SecurityFilterChain` with lambda DSL:

```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity(prePostEnabled = true)
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtAuthenticationFilter jwtAuthenticationFilter;
    private final JwtAuthenticationEntryPoint authEntryPoint;
    private final CustomAccessDeniedHandler accessDeniedHandler;

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .csrf(AbstractHttpConfigurer::disable)
            .cors(cors -> cors.configurationSource(corsConfigurationSource()))
            .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .exceptionHandling(ex -> ex
                .authenticationEntryPoint(authEntryPoint)
                .accessDeniedHandler(accessDeniedHandler)
            )
            .authorizeHttpRequests(auth -> auth
                // Public endpoints
                .requestMatchers("/auth/**", "/public/**").permitAll()
                .requestMatchers(HttpMethod.GET, "/jobs/**", "/categories/**").permitAll()
                .requestMatchers("/api-docs/**", "/swagger-ui/**", "/swagger-ui.html").permitAll()
                .requestMatchers("/h2-console/**").permitAll()

                // Role-restricted endpoints
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .requestMatchers("/employer/**").hasAnyRole("EMPLOYER", "ADMIN")
                .requestMatchers("/student/**").hasAnyRole("STUDENT", "ADMIN")

                // Any other request must be authenticated
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);

        // Required if H2 console is enabled in dev
        http.headers(headers -> headers.frameOptions(HeadersConfigurer.FrameOptionsConfig::sameOrigin));

        return http.build();
    }
}
```

---

## 2. Stateless JWT Authentication Flow

1. **Client Login (`POST /api/v1/auth/login`)**:
   - `AuthenticationManager.authenticate(...)` validates credentials with `CustomUserDetailsService` + `BCryptPasswordEncoder`.
   - On success, `JwtTokenProvider` generates an HS256 JWT containing `userId`, `username`, and `roles`.
2. **Subsequent Requests**:
   - `JwtAuthenticationFilter` intercepts the request, checks `Authorization: Bearer <token>`.
   - Validates signature, issuer, and expiration date.
   - Builds `UsernamePasswordAuthenticationToken` and injects it into `SecurityContextHolder.getContext().setAuthentication(auth)`.
3. **No Session Storage**:
   - The server maintains zero session state (`SessionCreationPolicy.STATELESS`).

---

## 3. RBAC Matrix & IDOR Prevention

### 3.1 Role Hierarchy & Permissions

| Endpoint / Resource | `ROLE_STUDENT` | `ROLE_EMPLOYER` | `ROLE_ADMIN` |
|---|---|---|---|
| `GET /jobs`, `GET /jobs/{id}` | Read | Read | Read |
| `POST /employer/jobs` | ❌ | Create | Create |
| `PUT /employer/jobs/{id}` | ❌ | Update (Own only) | Update (Any) |
| `POST /student/applications` | Apply | ❌ | ❌ |
| `PUT /employer/applications/{id}/status` | ❌ | Review (Own job) | Manage |
| `POST /reviews` | Review employer (If hired) | Review student (If hired) | Manage |
| `DELETE /admin/**` | ❌ | ❌ | Full Access |

### 3.2 IDOR Prevention (Ownership Verification)
Never trust client-supplied IDs blindly. Always verify ownership in the service layer:
```java
@Transactional
public JobResponse updateJob(Long jobId, JobUpdateRequest req, Long currentUserId) {
    Job job = jobRepository.findById(jobId)
        .orElseThrow(() -> new ResourceNotFoundException("Công việc không tồn tại"));

    // Prevent IDOR: Only creator or ADMIN can update
    boolean isAdmin = SecurityUtils.hasRole("ROLE_ADMIN");
    if (!job.getEmployer().getId().equals(currentUserId) && !isAdmin) {
        throw new AccessDeniedException("Bạn không có quyền chỉnh sửa tin đăng này");
    }

    job.updateFrom(req);
    return jobMapper.toDto(jobRepository.save(job));
}
```

---

## 4. Hardening & Production Checklist

1. **JWT Secret Strength**:
   - Secret key must be at least 256 bits (32+ bytes) for HS256.
   - Never commit production secrets to Git. Always use `${JWT_SECRET}`.
2. **BCrypt Work Factor**:
   - Use `BCryptPasswordEncoder(10)` or `12`.
3. **Disable Debug Endpoints in Production**:
   - Disable H2 console in `application-prod.yml` (`spring.h2.console.enabled: false`).
   - Restrict Actuator `/actuator/**` to internal networks or ADMIN role.
4. **CORS Policy**:
   - Never allow `*` when `allowCredentials(true)` is enabled.
   - Configure allowed origins to specific frontend origins (e.g., `http://localhost:3000`, `http://localhost:5173`).
