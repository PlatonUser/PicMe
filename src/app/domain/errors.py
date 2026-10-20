class DomainError(Exception):
    pass


class NotFound(DomainError):
    pass


class Conflict(DomainError):
    pass


class InvalidInput(DomainError):
    pass


class Forbidden(DomainError):
    pass


class PayloadTooLarge(DomainError):
    pass
