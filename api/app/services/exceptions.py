from __future__ import annotations


class ServiceError(Exception):
    """Base service-layer error."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = message


class NotFoundError(ServiceError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status_code=404)


class ConflictError(ServiceError):
    def __init__(self, message: str = "Conflicting resource") -> None:
        super().__init__(message, status_code=409)


class UnauthorizedError(ServiceError):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message, status_code=401)


class ForbiddenError(ServiceError):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message, status_code=403)

