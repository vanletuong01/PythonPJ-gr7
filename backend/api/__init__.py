# API package - chứa tất cả các routes (controllers)
# from .student_routes import router as student_router
# from .attendance_routes import router as attendance_router
# from .stats_routes import router as stats_router
from .auth_routes import router as auth_router

__all__ = [
    # "student_router",
    # "attendance_router",
    # "stats_router",
    "auth_router"
]
