class PermanentEventError(ValueError):
    """Ошибка события, которое не исправится при повторной доставке."""


class RetryableEventError(Exception):
    """Временная ошибка, которую имеет смысл повторить."""
