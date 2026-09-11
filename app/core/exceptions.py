from typing import Any


class AppError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"
    message = "Internal server error"

    def __init__(self, message: str | None = None, details: Any = None):
        super().__init__(message or self.message)
        self.message = message or self.message
        self.details = details


class UnsupportedDocumentError(AppError):
    status_code = 422
    code = "UNSUPPORTED_DOCUMENT"
    message = "Document cannot be parsed as supported text content"


class InvalidUploadError(AppError):
    status_code = 422
    code = "INVALID_UPLOAD"
    message = "Uploaded file is invalid"


class DuplicateDocumentError(AppError):
    status_code = 409
    code = "DUPLICATE_DOCUMENT"
    message = "Document content already exists"


class DocumentNotFoundError(AppError):
    status_code = 404
    code = "DOCUMENT_NOT_FOUND"
    message = "Document not found"


class ProviderError(AppError):
    status_code = 502
    code = "PROVIDER_ERROR"
    message = "External model provider error"


class ProviderTimeoutError(AppError):
    status_code = 504
    code = "PROVIDER_TIMEOUT"
    message = "External model provider timed out"


class StorageError(AppError):
    status_code = 500
    code = "STORAGE_ERROR"
    message = "Storage operation failed"


class ModelOutputInvalidError(AppError):
    status_code = 502
    code = "MODEL_OUTPUT_INVALID"
    message = "Model output contains invalid source citations"
