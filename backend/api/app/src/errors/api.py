"""Base APIError class for custom API exceptions."""


class APIError(Exception):
    """Base exception for all API errors with status code and optional payload."""

    def __init__(self, message, status_code=400, payload=None):
        super().__init__(self)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv

    def __str__(self):
        return self.message if self.message else "An API error occurred"
