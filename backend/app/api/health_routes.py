"""
Health Check Endpoints + Readiness Probes
Dùng cho Kubernetes liveness/readiness checks
"""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
import psutil
import os
from datetime import datetime
from db.database import get_connection
from core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/health",
    tags=["Health"]
)


@router.get("/live", status_code=200)
async def liveness_probe():
    """
    Liveness probe - Kiểm tra service còn chạy không
    Dùng cho Kubernetes pod restart nếu lỗi
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0"
        }
    )


@router.get("/ready", status_code=200)
async def readiness_probe():
    """
    Readiness probe - Kiểm tra service sẵn sàng serve requests
    Kiểm tra: DB connection, models loaded, etc.
    """
    try:
        # Kiểm tra database
        db_healthy = check_database()
        if not db_healthy:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "not_ready",
                    "reason": "database_connection_failed",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Kiểm tra disk space
        disk_healthy = check_disk_space()
        if not disk_healthy:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "not_ready",
                    "reason": "disk_space_low",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {
                    "database": "ok",
                    "disk_space": "ok"
                }
            }
        )
    
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "reason": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("", status_code=200)
async def health_check():
    """
    Detailed health check - Thông tin chi tiết về trạng thái service
    """
    try:
        # Database check
        db_status = "ok"
        db_response_time = 0
        try:
            conn = get_connection()
            if conn.is_connected():
                conn.close()
                db_response_time = 0
                db_status = "ok"
            else:
                db_status = "disconnected"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # System resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "2.0.0",
                "checks": {
                    "database": {
                        "status": db_status,
                        "response_time_ms": db_response_time
                    },
                    "cpu": {
                        "percent": cpu_percent,
                        "threshold": 80,
                        "status": "ok" if cpu_percent < 80 else "warning"
                    },
                    "memory": {
                        "used_mb": memory.used / (1024 * 1024),
                        "available_mb": memory.available / (1024 * 1024),
                        "percent": memory.percent,
                        "threshold": 80,
                        "status": "ok" if memory.percent < 80 else "warning"
                    },
                    "disk": {
                        "used_gb": disk.used / (1024 * 1024 * 1024),
                        "free_gb": disk.free / (1024 * 1024 * 1024),
                        "percent": disk.percent,
                        "threshold": 80,
                        "status": "ok" if disk.percent < 80 else "warning"
                    }
                }
            }
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "reason": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


def check_database() -> bool:
    """Kiểm tra kết nối database"""
    try:
        conn = get_connection()
        if conn.is_connected():
            conn.close()
            return True
    except:
        pass
    return False


def check_disk_space(min_free_gb: float = 1.0) -> bool:
    """Kiểm tra disk space còn đủ không"""
    try:
        disk = psutil.disk_usage("/")
        free_gb = disk.free / (1024 * 1024 * 1024)
        return free_gb > min_free_gb
    except:
        return False
