import logging
import sys

from app.core.config import settings


def setup_logging() -> None:
    # Đảm bảo stdout/stderr trên Windows luôn hỗ trợ ký tự UTF-8 (tiếng Việt)
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    level = getattr(logging, settings.log_level.upper(), logging.INFO) if hasattr(settings, "log_level") else logging.INFO

    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
