---
name: spring-data-jpa-patterns
description: "Spring Data JPA design patterns, entity modeling, query optimization, and multi-database compatibility (MySQL 8, PostgreSQL 16/18, H2). Use when designing entities, writing custom queries, tuning indexes, preventing N+1 problems with EntityGraph or JOIN FETCH, implementing pagination/filtering for jobs and applications, handling transactions, or setting up JPA auditing."
---

# Spring Data JPA Patterns & Optimization (Project CDTN2)

Guidelines for database modeling and query optimization in the **Marketplace platform**, supporting 1,470+ job postings across 16 categories and 34 provinces with MySQL 8, PostgreSQL 16/18, and H2 in-memory.

## 1. Entity Modeling & Relationships

The system contains 7 core tables: `users`, `categories`, `jobs`, `applications`, `reviews`, `skills`, `job_skills`.

### Best Practices:
1. **Always use LAZY fetching**:
   ```java
   @ManyToOne(fetch = FetchType.LAZY)
   @JoinColumn(name = "employer_id", nullable = false)
   private User employer;
   ```
2. **Avoid Bi-directional `@OneToMany` unless strictly needed**:
   - Prefer querying children through child repositories (e.g., `applicationRepository.findByJobId(jobId)` instead of `job.getApplications()`).
3. **Auditing Base Entity**:
   Inherit from an abstract `BaseEntity` to automatically track creation and updates:
   ```java
   @MappedSuperclass
   @EntityListeners(AuditingEntityListener.class)
   public abstract class BaseEntity {
       @CreatedDate
       @Column(name = "created_at", nullable = false, updatable = false)
       private LocalDateTime createdAt;

       @LastModifiedDate
       @Column(name = "updated_at")
       private LocalDateTime updatedAt;
   }
   ```

---

## 2. Preventing the N+1 Query Problem

With `spring.jpa.open-in-view: false`, accessing uninitialized proxies outside of transactions throws `LazyInitializationException`.

### Solution 1: `@EntityGraph`
```java
public interface JobRepository extends JpaRepository<Job, Long>, JpaSpecificationExecutor<Job> {

    @EntityGraph(attributePaths = {"employer", "category"})
    @Query("SELECT j FROM Job j WHERE j.status = 'OPEN'")
    Page<Job> findAllOpenJobsWithDetails(Pageable pageable);

    @EntityGraph(attributePaths = {"employer", "category", "skills"})
    Optional<Job> findWithDetailsById(Long id);
}
```

### Solution 2: Explicit `JOIN FETCH`
```java
@Query("SELECT a FROM Application a " +
       "JOIN FETCH a.student " +
       "JOIN FETCH a.job " +
       "WHERE a.id = :id")
Optional<Application> findByIdWithStudentAndJob(@Param("id") Long id);
```

---

## 3. Dynamic Filtering & Index Optimization

The database schema defines 13 indexes (e.g., `idx_jobs_category`, `idx_jobs_status`, `idx_jobs_location`, `idx_applications_student`).

### 3.1 Utilizing JPA Specifications for Dynamic Filters
When users search jobs by keyword, category, province, salary range, and job status:
```java
public class JobSpecifications {
    public static Specification<Job> withFilters(JobFilterCriteria criteria) {
        return (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();
            if (criteria.keyword() != null && !criteria.keyword().isBlank()) {
                String search = "%" + criteria.keyword().toLowerCase() + "%";
                predicates.add(cb.or(
                    cb.like(cb.lower(root.get("title")), search),
                    cb.like(cb.lower(root.get("description")), search)
                ));
            }
            if (criteria.categoryId() != null) {
                predicates.add(cb.equal(root.get("category").get("id"), criteria.categoryId()));
            }
            if (criteria.location() != null) {
                predicates.add(cb.equal(root.get("location"), criteria.location()));
            }
            if (criteria.status() != null) {
                predicates.add(cb.equal(root.get("status"), criteria.status()));
            }
            return cb.and(predicates.toArray(new Predicate[0]));
        };
    }
}
```

### 3.2 Pagination
Never use `findAll()` on large collections without `Pageable`:
```java
Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "createdAt"));
Page<Job> jobPage = jobRepository.findAll(specs, pageable);
```

---

## 4. Multi-Database Compatibility Rules

The application supports MySQL 8, PostgreSQL 16/18, and H2:
1. **Identifiers & Case Sensitivity**:
   - Use lowercase snake_case for all table and column names (`@Table(name = "job_applications")`, `@Column(name = "created_at")`).
2. **Boolean Types**:
   - Use `Boolean` in Java; Hibernate maps to `TINYINT(1)` in MySQL and `BOOLEAN` in PostgreSQL/H2 automatically.
3. **Enum Mapping**:
   - Use `@Enumerated(EnumType.STRING)` to avoid integer mismatch across different databases.
4. **Primary Key Strategy**:
   - Use `GenerationType.IDENTITY` for auto-increment compatibility across MySQL, PostgreSQL, and H2.
