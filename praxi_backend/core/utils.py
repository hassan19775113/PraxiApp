import logging
import time
from contextlib import contextmanager

from .models import AuditLog

logger = logging.getLogger(__name__)


@contextmanager
def timed_block(label: str, *, log: logging.Logger | None = None, level: str = 'debug'):
    """Lightweight timing context manager for internal micro-benchmarks.

    - No external dependencies
    - Does not alter return values / business logic
    - Logging is best-effort and defaults to DEBUG
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        end = time.perf_counter()
        log_obj = log or logger
        msg = 'timing %s: %.3fms'
        ms = (end - start) * 1000.0
        try:
            if level == 'info':
                log_obj.info(msg, label, ms)
            elif level == 'warning':
                log_obj.warning(msg, label, ms)
            else:
                log_obj.debug(msg, label, ms)
        except Exception:
            # Never let timing/logging break main code paths.
            pass


def log_patient_action(user, action, patient_id=None, meta=None):
    """Schreibt Patient-Access-Aktionen in die system-DB (alias: default)."""

    role_name = ''
    try:
        role = getattr(user, 'role', None)
        if role is not None:
            role_name = getattr(role, 'name', '') or ''
    except Exception:
        role_name = ''

    try:
        AuditLog.objects.using('default').create(
            user=user if getattr(user, 'is_authenticated', False) else None,
            role_name=role_name,
            action=action,
            patient_id=patient_id,
            meta=meta,
        )
    except Exception:
        logger.exception('AuditLog write failed (action=%s, patient_id=%s)', action, patient_id)
