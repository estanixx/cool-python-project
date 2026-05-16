class NotFoundError(Exception):
    """Raised when a requested item cannot be found."""


class ValidationError(Exception):
    """Raised when input validation fails."""


class DynamoError(Exception):
    """Raised when DynamoDB operations fail unexpectedly."""
