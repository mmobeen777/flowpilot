import logging


class SlowQueriesFilter(logging.Filter):
    """Filter slow queries and attach stack_info."""

    def filter(self, record):
        try:
            duration = record.duration
            # 300 ms
            if duration > 0.3:
                # Same as in _log for when stack_info=True is used.
                # fn, lno, func, sinfo = logging.Logger.findCaller(None, True)
                # record.stack_info = sinfo
                return True
            return False
        except Exception:
            return False
