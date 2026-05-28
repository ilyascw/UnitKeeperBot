from __future__ import annotations


class DomainError(Exception):
    code = "domain_error"
    status_code = 400

    def __init__(self, message: str, *, details: object | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class AuthenticationError(DomainError):
    code = "authentication_failed"
    status_code = 401


class AuthorizationError(DomainError):
    code = "forbidden"
    status_code = 403


class NotFoundError(DomainError):
    code = "not_found"
    status_code = 404


class ConflictError(DomainError):
    code = "conflict"
    status_code = 409


class ValidationError(DomainError):
    code = "validation_error"
    status_code = 422


class BusinessRuleViolation(DomainError):
    code = "business_rule_violation"
    status_code = 409
