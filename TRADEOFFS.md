# Tradeoffs

This project optimizes for a reviewable ESG data workflow over enterprise integration depth. The main tradeoffs are listed below.

## CSV Uploads Instead of Source APIs

SAP fuel, utility electricity, and travel data are ingested through CSV uploads. This keeps the demo easy to run and avoids credentials, OAuth, vendor onboarding, network failures, rate limits, and source-specific API contracts.

The cost is that CSVs are less reliable than managed integrations. Column formats can drift, uploads can be duplicated, and there is no automatic sync from SAP, utility portals, or travel systems.

## Celery Upload Jobs Instead of Inline Processing

Uploads create an `UploadJob` and Celery processes the file in the background. This keeps the API responsive, gives analysts job status, and makes failed uploads retryable.

The cost is operational complexity. Production needs a worker process, Redis or another broker, result backend configuration, and monitoring for stuck or failed jobs. Local development uses eager execution to stay simple, which is not identical to production behavior.

## Redis for Both Cache and Queue

Redis is used as the cache backend and can also act as the Celery broker. This reduces the number of infrastructure services and is enough for assignment scale.

The cost is shared dependency risk. If Redis is unavailable, cached dashboards degrade and background processing can stop. A larger deployment may separate cache, queue, and result storage.

## Separate Record Tables

Fuel, electricity, and travel records use separate models instead of one generic activity table. This keeps fields explicit, serializers easier to read, and validation rules source-specific.

The cost is duplication. List, edit, delete, validation, and export behavior must be repeated or carefully abstracted across record types. Adding a new source type requires new model, serializer, API, and validation work.

## Application-Level Tenant Isolation

Tenant isolation is enforced in Django querysets and permissions. This is straightforward to inspect and works well for a small multi-tenant prototype.

The cost is that every query path must remember tenant filtering. A production system should consider PostgreSQL row-level security, tenant-scoped audit queries, stronger permission tests, and database-level safeguards.

## S3-Compatible File Storage

Production uploads use S3-compatible storage so web and worker processes can access the same files. This avoids local filesystem issues when the app runs across multiple dynos or containers.

The cost is more environment configuration and more failure modes: bucket permissions, signed URLs, endpoint settings, and credential rotation. Local `media/` storage remains simpler but is not suitable for distributed production workers.

## Deterministic Validation Rules

Validation rules are explicit Python checks for each source type. They are easy to understand, test, and explain during review.

The cost is limited flexibility. Business users cannot configure rules without code changes, and the project does not include versioned validation policies, rule approvals, or emission factor governance.

## Review Locking After Approval

Approved records are locked from further edits. This protects reviewed data and keeps audit history meaningful.

The cost is workflow rigidity. Real teams may need amendment flows, approval withdrawal, reviewer comments, multi-stage approvals, or period close/reopen logic.

## Cached Dashboard Metrics

Dashboard and list responses can be cached with tenant-aware cache versioning. This improves repeated reads and keeps the UI fast.

The cost is freshness complexity. Cache invalidation must be triggered whenever uploads, edits, approvals, rejects, or deletes change the underlying data.

## JWT Authentication Without Enterprise Identity

JWT auth keeps the frontend/backend integration simple and stateless. Demo users can be seeded quickly.

The cost is missing enterprise identity features: SSO, SCIM, password reset, MFA, organization invites, detailed roles, and account lifecycle management.

## PostgreSQL Target With SQLite Fallback

PostgreSQL is the production target, while SQLite keeps local setup lightweight.

The cost is environment drift. SQLite does not behave exactly like PostgreSQL for concurrency, constraints, JSON behavior, schemas, and performance. Important production behavior should be verified against PostgreSQL.
