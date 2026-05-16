class ECCToolError(Exception):
    """Base exception for all ECC tool errors."""
    pass


class ConfigurationError(ECCToolError):
    """Raised when ECC configuration is invalid or missing."""
    pass


class ScanError(ECCToolError):
    """Raised when an ECC scan encounters an unrecoverable error."""
    pass


class ReportGenerationError(ECCToolError):
    """Raised when report generation fails."""
    pass


class RuleLoadError(ECCToolError):
    """Raised when ECC rules cannot be loaded."""
    pass
