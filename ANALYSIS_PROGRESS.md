"""
=============================================================================
PHÂN TÍCH: NHỮNG GÌ ĐÃ LÀM vs YÊU CẦU
=============================================================================

YÊU CẦU CÔNG NGHỆ:
✅ Streamlit (UI gọi API HTTP)
✅ FastAPI (Backend server)
✅ MySQL (Database)
✅ MTCNN (Face detection + alignment)
✅ InceptionResnetV1 (VGGFace2 embeddings)
✅ Deep Learning CNN + LBP (feature truyền thống)
✅ NumPy search (similarity matching)
✅ Docker-compose (containerization)

=============================================================================
GIAI ĐOẠN CODE - NHỮNG BEST PRACTICES CẦN LÀM
=============================================================================

1. ✅ DONE - Tách config ra env vars
   - Đã tạo: backend/db/config.py (load from .env)
   - Còn cần: .env.example (template), .gitignore (không commit .env)

2. ⚠️  PARTIAL - Pin dependencies
   - Đã có: requirements.txt (nhưng không pin version)
   - Cần: requirements.txt với == version cụ thể

3. ❌ TODO - Viết API + health check
   - Đã có: backend/main.py với @app.get("/"), @app.post("/test-post")
   - Cần: /health, /health/ready (liveness + readiness probe)
   - Cần: Structured logging, error codes, response schemas

4. ❌ TODO - Xử lý lỗi toàn cầu
   - Cần: Custom exception handlers (GlobalExceptionHandler)
   - Cần: Structured error responses (với error_code, message, trace)
   - Cần: Input validation (Pydantic models)

5. ❌ TODO - Cache (embedding cache, model cache)
   - Cần: In-memory cache (@lru_cache) cho embeddings
   - Cần: Redis (optional) để share cache giữa instances

6. ❌ TODO - Background job pattern
   - Cần: Task queue (Celery + Redis) cho heavy operations
   - Cần: Async endpoints (async/await trong FastAPI)

7. ❌ TODO - Reuse HTTP client
   - Cần: httpx.AsyncClient (connection pooling)
   - Cần: Session reuse thay vì mỗi request tạo mới

8. ❌ TODO - Tests cơ bản
   - Cần: pytest fixtures (mock DB, mock API responses)
   - Cần: Unit tests cho repositories, services
   - Cần: Integration tests cho API endpoints

9. ❌ TODO - Logging (structured logging)
   - Cần: Python logging với JSON format
   - Cần: Log levels (DEBUG, INFO, WARNING, ERROR)
   - Cần: Correlation ID để tracking requests

10. ❌ TODO - Không commit secrets
    - Cần: .gitignore (.env, *.pem, keys/)
    - Cần: Git hooks (pre-commit) để check secrets

11. ❌ TODO - Docker + docker-compose
    - Cần: Dockerfile (FastAPI service)
    - Cần: Dockerfile (Streamlit service)
    - Cần: docker-compose.yml (FastAPI + MySQL + Redis)
    - Cần: .dockerignore

12. ❌ TODO - CI/CD (optional nhưng tốt)
    - Cần: GitHub Actions / GitLab CI workflows
    - Cần: Run tests, lint, build images trước deploy

=============================================================================
CÓ GIỐNG LOGIC CHẠY CODE KHÔNG?
=============================================================================

✅ CÓ GIỐNG (những thứ mình đã làm):

1. Architecture Pattern (MVC → Repository + Service):
   - ✅ Mình đã tách: Database Layer (repositories.py)
   - ✅ Mình đã tách: Business Logic Layer (embedding_service.py)
   - ✅ Mình đã tách: API Layer (face_routes.py)

2. Centralize operations:
   - ✅ SQL queries tập trung ở repositories
   - ✅ Embedding logic tập trung ở service
   - ✅ Tái sử dụng code, DRY principle

3. Quản lý resource (cursor/connection):
   - ✅ try-finally để close cursor/connection
   - ✅ Tránh connection leak

4. NumPy + Deep Learning:
   - ✅ MTCNN (face detection)
   - ✅ InceptionResnetV1 (embeddings)
   - ✅ cosine_similarity (matching)

❌ KHÔNG GIỐNG / CHƯA LÀM (cần bổ sung):

1. Config management (env vars, .env.example, .gitignore)
2. API health checks + structured logging
3. Global error handling + input validation
4. Cache layer (embeddings, models)
5. Async patterns + background jobs
6. HTTP client pooling
7. Unit + integration tests
8. Docker + docker-compose
9. Pre-commit hooks (secrets check)

=============================================================================
ROADMAP TỪ ĐÂY - BƯỚC TỪA TIẾP
=============================================================================

GIAI ĐOẠN 1 (FOUNDATION - 2-3 ngày):
├─ Setup config / env vars
├─ Pin dependencies (requirements.txt)
├─ Add health checks (/health, /health/ready)
├─ Global error handling
├─ Input validation (Pydantic)
├─ Structured logging (JSON format)
└─ .env.example + .gitignore

GIAI ĐOẠN 2 (OPTIMIZATION - 2-3 ngày):
├─ Cache layer (@lru_cache embeddings, models)
├─ HTTP client pooling (httpx.AsyncClient)
├─ Async endpoints (async/await)
├─ Background tasks (optional: Celery)
└─ Batch processing (nhiều ảnh cùng lúc)

GIAI ĐOẠN 3 (TESTING - 1-2 ngày):
├─ Unit tests (repositories, services)
├─ Integration tests (API endpoints)
├─ Mock DB + fixtures
├─ Test coverage > 70%
└─ Pre-commit hooks

GIAI ĐOẠN 4 (CONTAINERIZATION - 1-2 ngày):
├─ Dockerfile (FastAPI)
├─ Dockerfile (Streamlit)
├─ docker-compose.yml (FastAPI + MySQL + Redis)
├─ Build images
└─ Test locally

GIAI ĐOẠN 5 (CI/CD - OPTIONAL - 1 ngày):
├─ GitHub Actions workflows
├─ Run tests on push
├─ Build + push images
└─ Deploy to staging

=============================================================================
CÁC FILE CẦN TẠO/CẬP NHẬT
=============================================================================

✅ ĐÃ TẠO:
- backend/db/repositories.py (StudentRepository, EmbeddingRepository, AttendanceRepository)
- backend/services/embedding_service.py (EmbeddingService)
- REFACTOR_GUIDE.md (hướng dẫn sử dụng)

❌ CẦN TẠO:
- .env.example (template environment variables)
- .gitignore (không commit secrets)
- requirements-pinned.txt (frozen dependencies)
- backend/core/config.py (centralized config + validation)
- backend/core/logger.py (structured logging setup)
- backend/core/exceptions.py (custom exceptions + handlers)
- backend/core/cache.py (caching utilities)
- backend/api/schemas.py (Pydantic models for validation)
- backend/tests/ (unit + integration tests)
- Dockerfile (FastAPI + Streamlit)
- docker-compose.yml (orchestration)
- .dockerignore
- .pre-commit-config.yaml (detect-secrets hook)

=============================================================================
"""
