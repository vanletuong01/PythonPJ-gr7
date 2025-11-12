"""
Structured Logging Setup
JSON format logging để dễ parse trên ELK / log aggregation services
"""
import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional
import sys
import os


class JSONFormatter(logging.Formatter):
    """Custom formatter to output JSON logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Thêm extra fields nếu có
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        
        if hasattr(record, "error_code"):
            log_obj["error_code"] = record.error_code
        
        if hasattr(record, "user_id"):
            log_obj["user_id"] = record.user_id
        
        # Thêm exception info nếu có
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj, ensure_ascii=False)


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """
    Setup logging cho toàn bộ ứng dụng
    
    Args:
        log_level: DEBUG, INFO, WARNING, ERROR, CRITICAL
        log_format: 'json' hoặc 'text'
    """
    log_level = os.getenv("LOG_LEVEL", log_level).upper()
    log_format = os.getenv("LOG_FORMAT", log_format).lower()
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    
    # Formatter
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Silence noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("mysql.connector").setLevel(logging.WARNING)
    logging.getLogger("deepface").setLevel(logging.WARNING)
    
    logging.info(f"Logging setup: level={log_level}, format={log_format}")


def get_logger(name: str) -> logging.LoggerAdapter:
    """
    Lấy logger với support cho extra fields
    
    Usage:
        logger = get_logger(__name__)
        logger.info("Message", extra={"request_id": "123", "user_id": "456"})
    """
    base_logger = logging.getLogger(name)
    return logging.LoggerAdapter(base_logger, {})
