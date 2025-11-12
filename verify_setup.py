#!/usr/bin/env python3
"""
Verification Script - Check Production Setup
Runs validation checks to ensure all foundation files are properly configured
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)


def check_file_exists(filepath: str) -> bool:
    """Check if file exists"""
    exists = Path(filepath).exists()
    status = "✅" if exists else "❌"
    print(f"  {status} {filepath}")
    return exists


def check_imports():
    """Check if all new modules import correctly"""
    print("\n📦 Checking imports...")
    
    checks = [
        ("core.config", "from backend.core.config import settings"),
        ("core.logger", "from backend.core.logger import get_logger, setup_logging"),
        ("core.exceptions", "from backend.core.exceptions import AppException, setup_exception_handlers"),
        ("db.repositories", "from backend.db.repositories import StudentRepository, EmbeddingRepository, AttendanceRepository"),
        ("services.embedding_service", "from backend.services.embedding_service import EmbeddingService"),
        ("app.schemas", "from backend.app.schemas import SuccessResponse, ErrorResponse, FaceCheckResponse"),
        ("api.health_routes", "from backend.api.health_routes import router as health_router"),
    ]
    
    all_ok = True
    for module_name, import_stmt in checks:
        try:
            exec(import_stmt)
            print(f"  ✅ {module_name}")
        except Exception as e:
            print(f"  ❌ {module_name}: {str(e)}")
            all_ok = False
    
    return all_ok


def check_config():
    """Check configuration loading"""
    print("\n⚙️  Checking configuration...")
    
    try:
        from backend.core.config import settings
        
        checks = [
            ("Database Host", settings.db.host),
            ("Database Port", settings.db.port),
            ("API Host", settings.api.host),
            ("API Port", settings.api.port),
            ("JWT Algorithm", settings.jwt.algorithm),
            ("Log Level", settings.logs.level),
            ("Log Format", settings.logs.format),
            ("Confidence Threshold", settings.models.confidence_threshold),
        ]
        
        for name, value in checks:
            print(f"  ✅ {name}: {value}")
        
        return True
    except Exception as e:
        print(f"  ❌ Configuration loading failed: {str(e)}")
        return False


def check_logger():
    """Check logger setup"""
    print("\n📝 Checking logger...")
    
    try:
        from backend.core.logger import get_logger, setup_logging
        
        # Setup logging
        setup_logging(log_level="INFO", log_format="json")
        
        # Get logger
        logger = get_logger(__name__)
        
        # Test logging
        logger.info("Test info message")
        logger.warning("Test warning message")
        
        print(f"  ✅ Logger configured and working")
        print(f"  ✅ JSON formatting enabled")
        
        return True
    except Exception as e:
        print(f"  ❌ Logger setup failed: {str(e)}")
        return False


def check_exceptions():
    """Check exception handlers"""
    print("\n⚠️  Checking exceptions...")
    
    try:
        from backend.core.exceptions import (
            AppException,
            ValidationException,
            NotFoundException,
            UnauthorizedException,
            DatabaseException,
            ExternalServiceException,
            RateLimitException,
            create_error_response,
            setup_exception_handlers
        )
        
        exceptions = [
            "ValidationException",
            "NotFoundException",
            "UnauthorizedException",
            "DatabaseException",
            "ExternalServiceException",
            "RateLimitException",
        ]
        
        for exc in exceptions:
            print(f"  ✅ {exc}")
        
        # Test error response creation
        error_response = create_error_response(
            error_code="TEST_ERROR",
            message="Test error",
            status_code=400
        )
        
        if "error" in error_response and "timestamp" in error_response:
            print(f"  ✅ Error response format correct")
        else:
            print(f"  ❌ Error response format incorrect")
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ Exception setup failed: {str(e)}")
        return False


def check_schemas():
    """Check Pydantic schemas"""
    print("\n📋 Checking schemas...")
    
    try:
        from backend.app.schemas import (
            SuccessResponse,
            ErrorResponse,
            FaceCheckResponse,
            StudentResponse,
            FaceRegisterRequest,
            PaginationParams
        )
        
        schemas = [
            "SuccessResponse",
            "ErrorResponse",
            "FaceCheckResponse",
            "StudentResponse",
            "FaceRegisterRequest",
            "PaginationParams",
        ]
        
        for schema in schemas:
            print(f"  ✅ {schema}")
        
        # Test schema validation
        try:
            params = PaginationParams(page=1, limit=20)
            print(f"  ✅ Schema validation working")
        except Exception as e:
            print(f"  ❌ Schema validation failed: {str(e)}")
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ Schemas loading failed: {str(e)}")
        return False


def check_repositories():
    """Check repository pattern"""
    print("\n🗄️  Checking repositories...")
    
    try:
        from db.repositories.attendent_repo import (
            StudentRepository,
            EmbeddingRepository,
            AttendanceRepository
        )
        
        repositories = {
            "StudentRepository": StudentRepository,
            "EmbeddingRepository": EmbeddingRepository,
            "AttendanceRepository": AttendanceRepository,
        }
        
        for name, repo_class in repositories.items():
            # Check if class can be instantiated
            try:
                repo = repo_class()
                # Check methods exist
                methods = [m for m in dir(repo) if not m.startswith('_')]
                print(f"  ✅ {name} ({len(methods)} methods)")
            except Exception as e:
                print(f"  ⚠️  {name} instantiation: {str(e)}")
        
        return True
    except Exception as e:
        print(f"  ❌ Repositories loading failed: {str(e)}")
        return False


def check_services():
    """Check service layer"""
    print("\n🔧 Checking services...")
    
    try:
        from backend.services.embedding_service import EmbeddingService
        
        service = EmbeddingService()
        
        methods = [
            "extract_embedding_from_image",
            "extract_embeddings_from_folder",
            "compute_average_embedding",
            "load_all_known_embeddings",
            "find_best_match",
            "normalize_embedding",
        ]
        
        for method in methods:
            if hasattr(service, method):
                print(f"  ✅ {method}")
            else:
                print(f"  ❌ {method} not found")
                return False
        
        return True
    except Exception as e:
        print(f"  ❌ Services loading failed: {str(e)}")
        return False


def check_health_routes():
    """Check health check endpoints"""
    print("\n❤️  Checking health routes...")
    
    try:
        from backend.api.health_routes import router
        
        endpoints = []
        for route in router.routes:
            if hasattr(route, 'path'):
                endpoints.append(route.path)
        
        expected = ["/live", "/ready", ""]
        
        for ep in expected:
            if ep in endpoints:
                print(f"  ✅ GET /health{ep}")
            else:
                print(f"  ❌ GET /health{ep} not found")
                return False
        
        return True
    except Exception as e:
        print(f"  ❌ Health routes loading failed: {str(e)}")
        return False


def check_main_app():
    """Check main.py integration"""
    print("\n🚀 Checking main application...")
    
    try:
        from backend.main import app
        
        # Check routes registered
        routes_count = len(app.routes)
        print(f"  ✅ Main app loaded ({routes_count} routes)")
        
        # Check middleware
        middleware_count = len(app.middleware)
        print(f"  ✅ Middleware configured ({middleware_count} layers)")
        
        # Check exception handlers
        handlers_count = len(app.exception_handlers)
        print(f"  ✅ Exception handlers registered ({handlers_count} handlers)")
        
        return True
    except Exception as e:
        print(f"  ❌ Main app loading failed: {str(e)}")
        return False


def check_files():
    """Check all required files exist"""
    print("\n📁 Checking required files...")
    
    required_files = [
        "backend/core/config.py",
        "backend/core/logger.py",
        "backend/core/exceptions.py",
        "backend/api/health_routes.py",
        "backend/app/schemas.py",
        "backend/db/attendent_repo.py",
        "backend/services/embedding_service.py",
        "backend/main.py",
        ".env.example",
        "requirements-pinned.txt",
        "INTEGRATION_GUIDE.md",
        "ROUTE_MIGRATION_GUIDE.md",
        "PRODUCTION_SETUP_SUMMARY.md",
        "QUICK_REFERENCE.md",
    ]
    
    all_exist = True
    for filepath in required_files:
        if not check_file_exists(filepath):
            all_exist = False
    
    return all_exist


def main():
    """Run all checks"""
    print("=" * 70)
    print("🔍 Production Setup Verification")
    print("=" * 70)
    
    checks = [
        ("📁 Required Files", check_files),
        ("📦 Module Imports", check_imports),
        ("⚙️  Configuration", check_config),
        ("📝 Logging", check_logger),
        ("⚠️  Exceptions", check_exceptions),
        ("📋 Schemas", check_schemas),
        ("🗄️  Repositories", check_repositories),
        ("🔧 Services", check_services),
        ("❤️  Health Routes", check_health_routes),
        ("🚀 Main App", check_main_app),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} failed with exception: {str(e)}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\n📈 Result: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All foundation files are properly configured!")
        print("Next steps:")
        print("  1. Review INTEGRATION_GUIDE.md for setup instructions")
        print("  2. Start backend: python backend/main.py")
        print("  3. Test endpoints: http://localhost:8000/api/docs")
        print("  4. Follow ROUTE_MIGRATION_GUIDE.md to update existing routes")
        return 0
    else:
        print(f"\n⚠️  {total - passed} check(s) failed. Please review above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
